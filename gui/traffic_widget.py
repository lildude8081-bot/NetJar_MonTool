import time
import os
import subprocess
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class TrafficWorker(QThread):
    date_actualizate = pyqtSignal(float, float, str, str)

    def run(self):
        interfata = self.detecteaza_interfata_activa()
        down_vechi, up_vechi = self.citeste_octeti(interfata)
        time.sleep(1)

        while True:
            down_nou, up_nou = self.citeste_octeti(interfata)
            viteza_down = max(0, down_nou - down_vechi)
            viteza_up = max(0, up_nou - up_vechi)
            down_vechi, up_vechi = down_nou, up_nou
            
            total_down_str = f"{down_nou / (1024**3):.2f} GB"
            total_up_str = f"{up_nou / (1024**3):.2f} GB"

            self.date_actualizate.emit(viteza_down, viteza_up, total_down_str, total_up_str)
            time.sleep(1)

    def detecteaza_interfata_activa(self):
        try:
            output = subprocess.check_output("ip route | grep default", shell=True, text=True)
            parti = output.split()
            if "dev" in parti:
                return parti[parti.index("dev") + 1]
        except Exception: pass
        return "eth0"

    def citeste_octeti(self, interfata):
        try:
            with open("/proc/net/dev", "r") as f: lines = f.readlines()
            for line in lines:
                if interfata in line:
                    date = line.split()
                    return int(date[1]), int(date[9])
        except Exception: pass
        return 0, 0


class SpeedtestWorker(QThread):
    """ Fir de execuție separat pentru rularea testului de viteză la internet (Speedtest) """
    rezultat_speedtest = pyqtSignal(str, str, str) # down_mbps, up_mbps, ping_ms
    eroare = pyqtSignal(str)

    def run(self):
        try:
            # Rulăm speedtest-cli în mod securizat cerând rezultate în format JSON curat
            comanda = ["speedtest-cli", "--json"]
            output = subprocess.check_output(comanda, text=True, stderr=subprocess.STDOUT)
            date = json.loads(output)
            
            # Convertim din biți/s în Megabiți/s (Mbps)
            down_mbps = f"{date['download'] / (1024*1024):.2f} Mbps"
            up_mbps = f"{date['upload'] / (1024*1024):.2f} Mbps"
            ping_ms = f"{date['ping']:.1f} ms"
            
            self.rezultat_speedtest.emit(down_mbps, up_mbps, ping_ms)
        except Exception as e:
            self.eroare.emit(f"❌ Eroare test: {str(e)}")


class TrafficMonitorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.istoric_grafic = [0] * 35
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(12)

        lbl_info = QLabel("📊 Monitorizare Trafic și Viteză Internet (Real-time):", self)
        lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #fab387;")
        layout_principal.addWidget(lbl_info)

        # --- PANOU STATISTICI LIVE ---
        panou_statistici = QHBoxLayout()
        
        self.frame_down = QFrame(self)
        self.frame_down.setStyleSheet("background-color: #181825; border: 1px solid #a6e3a1; border-radius: 6px; padding: 10px;")
        lay_down = QVBoxLayout(self.frame_down)
        self.lbl_down_viteza = QLabel("📥 0.00 KB/s", self)
        self.lbl_down_viteza.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1; border: none;")
        self.lbl_down_total = QLabel("Total primit: 0.00 GB", self)
        self.lbl_down_total.setStyleSheet("color: #a6adc8; border: none; font-size: 12px;")
        lay_down.addWidget(self.lbl_down_viteza)
        lay_down.addWidget(self.lbl_down_total)
        
        self.frame_up = QFrame(self)
        self.frame_up.setStyleSheet("background-color: #181825; border: 1px solid #f38ba8; border-radius: 6px; padding: 10px;")
        lay_up = QVBoxLayout(self.frame_up)
        self.lbl_up_viteza = QLabel("📤 0.00 KB/s", self)
        self.lbl_up_viteza.setStyleSheet("font-size: 18px; font-weight: bold; color: #f38ba8; border: none;")
        self.lbl_up_total = QLabel("Total trimis: 0.00 GB", self)
        self.lbl_up_total.setStyleSheet("color: #a6adc8; border: none; font-size: 12px;")
        lay_up.addWidget(self.lbl_up_viteza)
        lay_up.addWidget(self.lbl_up_total)

        panou_statistici.addWidget(self.frame_down)
        panou_statistici.addWidget(self.frame_up)
        layout_principal.addLayout(panou_statistici)

        # --- SECTIUNEA NOUĂ: INTERNET SPEEDOMETER ---
        self.frame_speedometer = QFrame(self)
        self.frame_speedometer.setStyleSheet("background-color: #11111b; border: 1px solid #89b4fa; border-radius: 6px; padding: 12px;")
        lay_speed = QVBoxLayout(self.frame_speedometer)
        
        layout_speed_titlu = QHBoxLayout()
        lbl_speed_title = QLabel("🚀 Internet Speedometer (Capacitate Maximă):", self)
        lbl_speed_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #89b4fa; border: none;")
        
        self.btn_run_speedtest = QPushButton("⚡ Pornește Speedtest", self)
        self.btn_run_speedtest.setStyleSheet("""
            QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 4px; padding: 5px 12px; font-size: 12px; }
            QPushButton:hover { background-color: #b4befe; }
        """)
        self.btn_run_speedtest.clicked.connect(self.executa_speedtest)
        
        layout_speed_titlu.addWidget(lbl_speed_title)
        layout_speed_titlu.addStretch()
        layout_speed_titlu.addWidget(self.btn_run_speedtest)
        lay_speed.addLayout(layout_speed_titlu)

        # Rezultatele testului de viteză pe un rând elegant
        layout_valori_speed = QHBoxLayout()
        self.lbl_res_down = QLabel("Viteză Download: --", self)
        self.lbl_res_down.setStyleSheet("color: #cdd6f4; font-weight: 500; font-size: 13px; border: none;")
        self.lbl_res_up = QLabel("Viteză Upload: --", self)
        self.lbl_res_up.setStyleSheet("color: #cdd6f4; font-weight: 500; font-size: 13px; border: none;")
        self.lbl_res_ping = QLabel("Latență Ping: --", self)
        self.lbl_res_ping.setStyleSheet("color: #cdd6f4; font-weight: 500; font-size: 13px; border: none;")
        
        layout_valori_speed.addWidget(self.lbl_res_down)
        layout_valori_speed.addWidget(self.lbl_res_up)
        layout_valori_speed.addWidget(self.lbl_res_ping)
        lay_speed.addLayout(layout_valori_speed)
        
        layout_principal.addWidget(self.frame_speedometer)

        # --- PANOU GRAFIC ASCII REAL-TIME ---
        self.lbl_grafic_ascii = QLabel(self)
        self.lbl_grafic_ascii.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.lbl_grafic_ascii.setStyleSheet("background-color: #11111b; color: #fab387; font-family: 'Courier New', monospace; font-size: 12px; border: 1px dashed #45475a; border-radius: 6px; padding: 10px;")
        layout_principal.addWidget(self.lbl_grafic_ascii)

        # Pornim monitorizarea pasivă live
        self.worker = TrafficWorker()
        self.worker.date_actualizate.connect(self.actualizeaza_interfata)
        self.worker.start()

    def actualizeaza_interfata(self, v_down, v_up, t_down, t_up):
        if v_down > 1024 * 1024: self.lbl_down_viteza.setText(f"📥 {v_down / (1024*1024):.2f} MB/s")
        else: self.lbl_down_viteza.setText(f"📥 {v_down / 1024:.2f} KB/s")

        if v_up > 1024 * 1024: self.lbl_up_viteza.setText(f"📤 {v_up / (1024*1024):.2f} MB/s")
        else: self.lbl_up_viteza.setText(f"📤 {v_up / 1024:.2f} KB/s")

        self.lbl_down_total.setText(f"Total primit: {t_down}")
        self.lbl_up_total.setText(f"Total trimis: {t_up}")

        self.istoric_grafic.append(v_down / 1024)
        self.istoric_grafic.pop(0)
        self.deseneaza_grafic_ascii()

    def deseneaza_grafic_ascii(self):
        max_val = max(self.istoric_grafic) if max(self.istoric_grafic) > 10 else 10
        inaltime_linii = 6
        linii_grafic = []

        for linie in range(inaltime_linii, 0, -1):
            prag_linie = (max_val / inaltime_linii) * linie
            text_linie = ""
            for valoare in self.istoric_grafic:
                if valoare >= prag_linie: text_linie += "█ "
                elif valoare >= prag_linie * 0.5: text_linie += "▄ "
                else: text_linie += ". "
            linii_grafic.append(text_linie)

        grafic_final = f"Real-time Traffic (Download Peak: {max_val:.1f} KB/s)\n" + "\n".join(linii_grafic)
        self.lbl_grafic_ascii.setText(grafic_final)

    def executa_speedtest(self):
        """ Declanșează testul de viteză maximă în fundal """
        self.btn_run_speedtest.setEnabled(False)
        self.btn_run_speedtest.setText("⏳ Se testează...")
        
        self.lbl_res_down.setText("Viteză Download: ⏳ ...")
        self.lbl_res_up.setText("Viteză Upload: ⏳ ...")
        self.lbl_res_ping.setText("Latență Ping: ⏳ ...")

        self.speed_worker = SpeedtestWorker()
        self.speed_worker.rezultat_speedtest.connect(self.afiseaza_rezultat_speedtest)
        self.speed_worker.eroare.connect(self.afiseaza_eroare_speedtest)
        self.speed_worker.start()

    def afiseaza_rezultat_speedtest(self, down, up, ping):
        self.btn_run_speedtest.setEnabled(True)
        self.btn_run_speedtest.setText("⚡ Pornește Speedtest")
        
        self.lbl_res_down.setText(f"Viteză Download: 🟢 {down}")
        self.lbl_res_up.setText(f"Viteză Upload: 🔵 {up}")
        self.lbl_res_ping.setText(f"Latență Ping: 🟣 {ping}")

    def afiseaza_eroare_speedtest(self, text_eroare):
        self.btn_run_speedtest.setEnabled(True)
        self.btn_run_speedtest.setText("⚡ Pornește Speedtest")
        self.lbl_res_down.setText(text_eroare)
