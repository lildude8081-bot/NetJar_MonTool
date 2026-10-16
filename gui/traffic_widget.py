import subprocess
import time
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

class SpeedtestWorker(QThread):
    progres = pyqtSignal(int)
    rezultat = pyqtSignal(str, str, str)
    finalizat = pyqtSignal()

    def run(self):
        self.progres.emit(20)
        try:
            out = subprocess.check_output(["speedtest-cli", "--simple"], text=True)
            self.progres.emit(70)
            ping, dl, ul = "0 ms", "0 Mbps", "0 Mbps"
            for linie in out.split("\n"):
                if linie.startswith("Ping:"): ping = linie.split()[1] + " ms"
                elif linie.startswith("Download:"): dl = linie.split()[1] + " Mbps"
                elif linie.startswith("Upload:"): ul = linie.split()[1] + " Mbps"
            self.rezultat.emit(dl, ul, ping)
        except Exception:
            self.rezultat.emit("Error", "Error", "Error")
        self.progres.emit(100)
        self.finalizat.emit()

class TrafficMonitorWidget(QWidget):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.peak_dl = 0.0
        self.istoric_grafic = [0] * 30
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.traduceri = {
            "ro": {
                "title": "📊 Monitorizare Trafic și Viteză Internet (Real-time):",
                "tot_rx": "Total primit:", "tot_tx": "Total trimis:",
                "speed_title": "🚀 Internet Speedometer (Capacitate Maximă):",
                "btn_speed": "⏱️ Pornește Speedtest", "btn_run": "⏳ Rulare...",
                "lbl_dl": "Viteză Download:", "lbl_ul": "Viteză Upload:", "lbl_png": "Latență Ping:",
                "graph_peak": "Trafic în Timp Real (Vârf Download:"
            },
            "en": {
                "title": "📊 Network Traffic & Internet Speedometer (Real-time):",
                "tot_rx": "Total received:", "tot_tx": "Total sent:",
                "speed_title": "🚀 Internet Speedometer (Maximum Capacity):",
                "btn_speed": "⏱️ Run Speedtest", "btn_run": "⏳ Running...",
                "lbl_dl": "Download Speed:", "lbl_ul": "Upload Speed:", "lbl_png": "Ping Latency:",
                "graph_peak": "Real-time Traffic (Download Peak:"
            },
            "it": {
                "title": "📊 Monitoraggio Traffico e Velocità Internet (Real-time):",
                "tot_rx": "Totale ricevuto:", "tot_tx": "Totale inviato:",
                "speed_title": "🚀 Internet Speedometer (Capacità Massima):",
                "btn_speed": "⏱️ Avvia Speedtest", "btn_run": "⏳ Analisi...",
                "lbl_dl": "Velocità Download:", "lbl_ul": "Velocità Upload:", "lbl_png": "Latenza Ping:",
                "graph_peak": "Traffico in Tempo Reale (Picco Download:"
            }
        }

        self.lbl_titlu = QLabel(self)
        self.lbl_titlu.setStyleSheet("font-size: 13px; font-weight: bold; color: #fab387;")
        layout.addWidget(self.lbl_titlu)

        layout_boxuri = QHBoxLayout()
        self.box_dl = QWidget(self)
        self.box_dl.setStyleSheet("background-color: #181825; border: 1px solid #a6e3a1; border-radius: 6px;")
        v_dl = QVBoxLayout(self.box_dl)
        self.lbl_val_dl = QLabel("📥 0.00 KB/s", self.box_dl)
        self.lbl_val_dl.setStyleSheet("font-size: 18px; font-weight: bold; color: #a6e3a1; border:none;")
        self.lbl_tot_rx = QLabel("Total: 0 GB", self.box_dl)
        self.lbl_tot_rx.setStyleSheet("font-size: 11px; color: #a6adc8; border:none;")
        v_dl.addWidget(self.lbl_val_dl)
        v_dl.addWidget(self.lbl_tot_rx)

        self.box_ul = QWidget(self)
        self.box_ul.setStyleSheet("background-color: #181825; border: 1px solid #f38ba8; border-radius: 6px;")
        v_ul = QVBoxLayout(self.box_ul)
        self.lbl_val_ul = QLabel("📤 0.00 KB/s", self.box_ul)
        self.lbl_val_ul.setStyleSheet("font-size: 18px; font-weight: bold; color: #f38ba8; border:none;")
        self.lbl_tot_tx = QLabel("Total: 0 GB", self.box_ul)
        self.lbl_tot_tx.setStyleSheet("font-size: 11px; color: #a6adc8; border:none;")
        v_ul.addWidget(self.lbl_val_ul)
        v_ul.addWidget(self.lbl_tot_tx)

        layout_boxuri.addWidget(self.box_dl)
        layout_boxuri.addWidget(self.box_ul)
        layout.addLayout(layout_boxuri)

        layout_speed = QHBoxLayout()
        self.lbl_speed_title = QLabel(self)
        self.lbl_speed_title.setStyleSheet("font-size: 12px; font-weight: bold; color: #89b4fa;")
        layout_speed.addWidget(self.lbl_speed_title)
        layout_speed.addStretch()

        self.btn_speed = QPushButton(self)
        self.btn_speed.setStyleSheet("QPushButton { background-color: #89b4fa; color: #11111b; font-weight: bold; border-radius: 5px; padding: 5px 12px; font-size: 12px; }")
        self.btn_speed.clicked.connect(self.porneste_speedtest)
        layout_speed.addWidget(self.btn_speed)
        layout.addLayout(layout_speed)

        layout_rez = QHBoxLayout()
        self.lbl_res_dl = QLabel(self)
        self.lbl_res_ul = QLabel(self)
        self.lbl_res_png = QLabel(self)
        for lbl in [self.lbl_res_dl, self.lbl_res_ul, self.lbl_res_png]:
            lbl.setStyleSheet("font-size: 12px; color: #cdd6f4;")
            layout_rez.addWidget(lbl)
        layout.addLayout(layout_rez)

        self.lbl_graph_title = QLabel(self)
        self.lbl_graph_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #f5e0dc; padding-top: 5px;")
        layout.addWidget(self.lbl_graph_title)

        self.lbl_graph = QLabel(self)
        self.lbl_graph.setStyleSheet("font-family: monospace; font-size: 14px; color: #fab387; background-color: #0c0c12; padding: 12px; border-radius: 6px; border: 1px solid #313244;")
        layout.addWidget(self.lbl_graph)

        self.last_rx, self.last_tx = self.citeste_statistici_kernel()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizeaza_metrice_realtime)
        self.timer.start(1000)
        self.actualizeaza_limba()

    def obtine_limba_curenta(self):
        if self.parent_win and hasattr(self.parent_win, 'limba_curenta'): return self.parent_win.limba_curenta
        return "ro"

    def actualizeaza_limba(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_titlu.setText(L["title"])
        self.lbl_speed_title.setText(L["speed_title"])
        if self.btn_speed.isEnabled(): self.btn_speed.setText(L["btn_speed"])
        self.lbl_res_dl.setText(f"{L['lbl_dl']} --")
        self.lbl_res_ul.setText(f"{L['lbl_ul']} --")
        self.lbl_res_png.setText(f"{L['lbl_png']} --")
        self.lbl_graph_title.setText(f"{L['graph_peak']} {self.peak_dl:.1f} KB/s)")
        self.deseneaza_grafic_ascii()

    def citeste_statistici_kernel(self):
        try:
            with open("/proc/net/dev", "r") as f: linii = f.readlines()
            rx, tx = 0, 0
            for l in linii:
                if ":" in l and not "lo:" in l:
                    parti = l.split(":")[1].split()
                    rx += int(parti[0])
                    tx += int(parti[8])
            return rx, tx
        except Exception: return 0, 0

    def actualizeaza_metrice_realtime(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        current_rx, current_tx = self.citeste_statistici_kernel()
        diff_rx = (current_rx - self.last_rx) / 1024.0
        diff_tx = (current_tx - self.last_tx) / 1024.0
        if diff_rx < 0: diff_rx = 0
        if diff_tx < 0: diff_tx = 0
        if diff_rx > self.peak_dl: self.peak_dl = diff_rx

        self.lbl_val_dl.setText(f"📥 {diff_rx:.2f} KB/s")
        self.lbl_val_ul.setText(f"📤 {diff_tx:.2f} KB/s")
        self.lbl_tot_rx.setText(f"{L['tot_rx']} {current_rx / (1024**3):.2f} GB")
        self.lbl_tot_tx.setText(f"{L['tot_tx']} {current_tx / (1024**3):.2f} GB")
        self.lbl_graph_title.setText(f"{L['graph_peak']} {self.peak_dl:.1f} KB/s)")
        
        nivel_bara = min(7, int(diff_rx / 20)) if diff_rx > 2 else (1 if diff_rx > 0 else 0)
        self.istoric_grafic.pop(0)
        self.istoric_grafic.append(nivel_bara)
        self.deseneaza_grafic_ascii()
        self.last_rx, self.last_tx = current_rx, current_tx

    def deseneaza_grafic_ascii(self):
        randuri_grafic = []
        for nivel in range(7, -1, -1):
            linie_rand = ""
            for val in self.istoric_grafic:
                if val >= nivel and nivel > 0: linie_rand += "█ "
                elif val == 0 and nivel == 0: linie_rand += ". "
                else: linie_rand += "  "
            randuri_grafic.append(linie_rand)
        self.lbl_graph.setText("\n".join(randuri_grafic))

    def porneste_speedtest(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.btn_speed.setEnabled(False)
        self.btn_speed.setText(L["btn_run"])
        self.worker = SpeedtestWorker()
        self.worker.rezultat.connect(self.afiseaza_rezultat_speedtest)
        self.worker.finalizat.connect(self.speedtest_gata)
        self.worker.start()

    def afiseaza_rezultat_speedtest(self, dl, ul, ping):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_res_dl.setText(f"{L['lbl_dl']} {dl}")
        self.lbl_res_ul.setText(f"{L['lbl_ul']} {ul}")
        self.lbl_res_png.setText(f"{L['lbl_png']} {ping}")

    def speedtest_gata(self):
        self.btn_speed.setEnabled(True)
        L = self.traduceri[self.obtine_limba_curenta()]
        self.btn_speed.setText(L["btn_speed"])
