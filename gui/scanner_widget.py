import subprocess
import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class ScannerWorker(QThread):
    progres = pyqtSignal(int)
    dispozitiv_gasit = pyqtSignal(str, str, str)
    finalizat = pyqtSignal()

    def run(self):
        self.progres.emit(10)
        try:
            # Preluăm IP-ul local pentru a afla clasa de rețea
            cmd_ip = subprocess.check_output(["hostname", "-I"], text=True).strip().split()[0]
            baza_ip = ".".join(cmd_ip.split(".")[:3]) + ".0/24"
        except Exception:
            baza_ip = "192.168.1.0/24"

        self.progres.emit(30)
        # Scanare rapidă ARP locală
        try:
            arp_out = subprocess.check_output(["arp", "-an"], text=True)
            for linie in arp_out.split("\n"):
                match = re.search(r"\((.*?)\)â  \s+at\s+([0-9a-fA-F:]+)", linie)
                if match:
                    self.dispozitiv_gasit.emit("Dispozitiv Local", match.group(1), "Activ")
        except Exception: pass

        self.progres.emit(70)
        # Scanare rețea Tailscale dacă există
        try:
            ts_out = subprocess.check_output(["tailscale", "status"], text=True)
            for linie in ts_out.split("\n"):
                parti = linie.split()
                if len(parti) >= 2 and not linie.startswith("#"):
                    self.dispozitiv_gasit.emit(parti[1], parti[0], "Online (TS)")
        except Exception: pass

        self.progres.emit(100)
        self.finalizat.emit()

class ScannerWidget(QWidget):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Dicționarul simetric complet pentru cele 3 limbi solicitate
        self.traduceri = {
            "ro": {
                "lbl_info": "🔍 Scanner & Pinger (Local & Tailscale):",
                "btn_scaneaza": "🔄 Scanează Rețeaua",
                "btn_asteapta": "⏳ Scanare...",
                "btn_ping": "⚡ Dă Ping Manual",
                "headers": ["Nume Dispozitiv", "Adresă IP", "Stare"],
                "ping_titlu": "Introduceți IP", "ping_prompt": "Adresă IP pentru Ping:",
                "ping_ok": "Dispozitivul este activ!", "ping_err": "Dispozitivul nu răspunde!"
            },
            "en": {
                "lbl_info": "🔍 Scanner & Pinger (Local & Tailscale):",
                "btn_scaneaza": "🔄 Scan Network",
                "btn_asteapta": "⏳ Scanning...",
                "btn_ping": "⚡ Manual Ping",
                "headers": ["Device Name", "IP Address", "Status"],
                "ping_titlu": "Enter IP", "ping_prompt": "IP Address for Ping:",
                "ping_ok": "Device is alive!", "ping_err": "Device destination unreachable!"
            },
            "it": {
                "lbl_info": "🔍 Scanner & Pinger (Locale & Tailscale):",
                "btn_scaneaza": "🔄 Scansiona Rete",
                "btn_asteapta": "⏳ Scansione...",
                "btn_ping": "⚡ Ping Manuale",
                "headers": ["Nome Dispositivo", "Indirizzo IP", "Stato"],
                "ping_titlu": "Inserisci IP", "ping_prompt": "Indirizzo IP per il Ping:",
                "ping_ok": "Il dispositivo è attivo!", "ping_err": "Il dispositivo non risponde!"
            }
        }

        # Rând superior fluid pentru acțiuni
        layout_actiuni = QHBoxLayout()
        self.lbl_info = QLabel(self)
        self.lbl_info.setStyleSheet("font-size: 13px; font-weight: bold; color: #a6adc8;")
        layout_actiuni.addWidget(self.lbl_info)
        layout_actiuni.addStretch()

        self.btn_scaneaza = QPushButton(self)
        self.btn_scaneaza.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 15px; font-size: 12px; }")
        self.btn_scaneaza.clicked.connect(self.porneste_scanarea)
        layout_actiuni.addWidget(self.btn_scaneaza)
        layout.addLayout(layout_actiuni)

        # Tabelul central
        self.tabel = QTableWidget(self)
        self.tabel.setColumnCount(3)
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabel.setStyleSheet("background-color: #181825; color: #cdd6f4; gridline-color: #313244; font-size: 13px;")
        layout.addWidget(self.tabel)

        # Rând inferior pentru Ping Manual
        layout_jos = QHBoxLayout()
        self.btn_ping = QPushButton(self)
        self.btn_ping.setStyleSheet("QPushButton { background-color: #f9e2af; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 15px; font-size: 12px; }")
        self.btn_ping.clicked.connect(self.executa_ping_manual)
        layout_jos.addWidget(self.btn_ping)
        layout_jos.addStretch()
        layout.addLayout(layout_jos)

        self.actualizeaza_limba()

    def obtine_limba_curenta(self):
        if self.parent_win and hasattr(self.parent_win, 'limba_curenta'):
            return self.parent_win.limba_curenta
        return "ro"

    def actualizeaza_limba(self):
        """ Schimbă din mers textele tuturor componentelor în funcție de limba activă """
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_info.setText(L["lbl_info"])
        self.btn_ping.setText(L["btn_ping"])
        if self.btn_scaneaza.isEnabled():
            self.btn_scaneaza.setText(L["btn_scaneaza"])
        self.tabel.setHorizontalHeaderLabels(L["headers"])

    def porneste_scanarea(self):
        self.actualizeaza_limba()
        L = self.traduceri[self.obtine_limba_curenta()]
        self.btn_scaneaza.setEnabled(False)
        self.btn_scaneaza.setText(L["btn_asteapta"])
        self.tabel.setRowCount(0)

        self.worker = ScannerWorker()
        self.dispozitiv_gasit_conectat = self.worker.dispozitiv_gasit.connect(self.adauga_dispozitiv)
        self.worker.finalizat.connect(self.scanare_terminata)
        self.worker.start()

    def adauga_dispozitiv(self, nume, ip, stare):
        rand = self.tabel.rowCount()
        self.tabel.insertRow(rand)
        self.tabel.setItem(rand, 0, QTableWidgetItem(nume))
        self.tabel.setItem(rand, 1, QTableWidgetItem(ip))
        self.tabel.setItem(rand, 2, QTableWidgetItem(stare))

    def scanare_terminata(self):
        self.btn_scaneaza.setEnabled(True)
        self.actualizeaza_limba()

    def executa_ping_manual(self):
        from PyQt6.QtWidgets import QInputDialog
        L = self.traduceri[self.obtine_limba_curenta()]
        ip, ok = QInputDialog.getText(self, L["ping_titlu"], L["ping_prompt"])
        if ok and ip:
            rez = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL)
            if rez.returncode == 0:
                QMessageBox.information(self, "Ping", f"{L['ping_ok']} ({ip})")
            else:
                QMessageBox.critical(self, "Ping", f"{L['ping_err']} ({ip})")
