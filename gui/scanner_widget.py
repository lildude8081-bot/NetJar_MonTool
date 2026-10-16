import subprocess
import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QMenu, QTextEdit
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QGuiApplication

class ScannerWorker(QThread):
    progres = pyqtSignal(int)
    dispozitiv_gasit = pyqtSignal(str, str, str)
    finalizat = pyqtSignal()

    def run(self):
        self.progres.emit(20)
        try:
            arp_out = subprocess.check_output(["arp", "-an"], text=True)
            for linie in arp_out.split("\n"):
                match = re.search(r"\((.*?)\)\s+at\s+([0-9a-fA-F:]+)", linie)
                if match:
                    ip = match.group(1)
                    rez = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL)
                    stare = "🟢 Activ (LAN)" if rez.returncode == 0 else "🔴 Inactiv (LAN)"
                    self.dispozitiv_gasit.emit("Dispozitiv Local", ip, stare)
        except Exception: pass

        self.progres.emit(60)
        try:
            ts_out = subprocess.check_output(["tailscale", "status"], text=True)
            for linie in ts_out.split("\n"):
                linie_curata = linie.strip()
                if linie_curata and not linie_curata.startswith("#"):
                    parti = linie_curata.split()
                    if len(parti) >= 2:
                        ip = parti[0]
                        nume = parti[1]
                        rez = subprocess.run(["ping", "-c", "1", "-W", "1", ip], stdout=subprocess.DEVNULL)
                        stare = "🟢 Online (TS)" if rez.returncode == 0 else "🔴 Offline (TS)"
                        self.dispozitiv_gasit.emit(nume, ip, stare)
        except Exception: pass

        self.progres.emit(100)
        self.finalizat.emit()

class ScannerWidget(QWidget):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        self.traduceri = {
            "ro": {
                "lbl_info": "🔍 Scanner & Pinger (Local & Tailscale):", "btn_scaneaza": "🔄 Scanează Rețeaua",
                "btn_asteapta": "⏳ Scanare...", "btn_ping": "⚡ Dă Ping Manual",
                "headers": ["Nume Dispozitiv", "Adresă IP", "Stare"],
                "ping_titlu": "Introduceți IP", "ping_prompt": "Adresă IP pentru Ping:",
                "ping_ok": "Dispozitivul este activ!", "ping_err": "Dispozitivul nu răspunde!",
                "ctx_copy": "📋 Copiază Adresa IP", "terminal_init": "🖥️ Terminal Diagnosticare Rețea inactiv. Dați dublu-click pe un IP sau folosiți Ping Manual..."
            },
            "en": {
                "lbl_info": "🔍 Scanner & Pinger (Local & Tailscale):", "btn_scaneaza": "🔄 Scan Network",
                "btn_asteapta": "⏳ Scanning...", "btn_ping": "⚡ Manual Ping",
                "headers": ["Device Name", "IP Address", "Status"],
                "ping_titlu": "Enter IP", "ping_prompt": "IP Address for Ping:",
                "ping_ok": "Device is alive!", "ping_err": "Device destination unreachable!",
                "ctx_copy": "📋 Copy IP Address", "terminal_init": "🖥️ Network Diagnostics Terminal idle. Double-click an IP or use Manual Ping..."
            },
            "it": {
                "lbl_info": "🔍 Scanner & Pinger (Locale & Tailscale):", "btn_scaneaza": "🔄 Scansiona Rete",
                "btn_asteapta": "⏳ Scansione...", "btn_ping": "⚡ Ping Manuale",
                "headers": ["Nome Dispositivo", "Indirizzo IP", "Stato"],
                "ping_titlu": "Inserisci IP", "ping_prompt": "Indirizzo IP per il Ping:",
                "ping_ok": "Il dispositivo è attivo!", "ping_err": "Il dispositivo non risponde!",
                "ctx_copy": "📋 Copia Indirizzo IP", "terminal_init": "🖥️ Terminale Diagnostica Rete inattivo. Fai doppio clic su un IP o usa Ping Manuale..."
            }
        }

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

        # Tabelul de computere (Înălțime fixă pentru a lăsa loc consolei de dedesubt)
        self.tabel = QTableWidget(self)
        self.tabel.setColumnCount(3)
        self.tabel.setFixedHeight(180)
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabel.setStyleSheet("background-color: #181825; color: #cdd6f4; gridline-color: #313244; font-size: 13px;")
        self.tabel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabel.customContextMenuRequested.connect(self.afiseaza_meniu_contextual)
        self.tabel.itemDoubleClicked.connect(self.executa_ping_la_dublu_click)
        layout.addWidget(self.tabel)

        # NOU: Consola de terminal integrată direct în fundul tab-ului!
        self.consola_bruta = QTextEdit(self)
        self.consola_bruta.setReadOnly(True)
        self.consola_bruta.setStyleSheet("QTextEdit { background-color: #0c0c12; color: #a6e3a1; font-family: monospace; font-size: 12px; border: 1px solid #313244; border-radius: 6px; padding: 8px; }")
        layout.addWidget(self.consola_bruta)

        layout_jos = QHBoxLayout()
        self.btn_ping = QPushButton(self)
        self.btn_ping.setStyleSheet("QPushButton { background-color: #f9e2af; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 15px; font-size: 12px; }")
        self.btn_ping.clicked.connect(self.executa_ping_manual)
        layout_jos.addWidget(self.btn_ping)
        layout_jos.addStretch()
        layout.addLayout(layout_jos)

        self.actualizeaza_limba()

    def obtine_limba_curenta(self):
        if self.parent_win and hasattr(self.parent_win, 'limba_curenta'): return self.parent_win.limba_curenta
        return "ro"

    def actualizeaza_limba(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_info.setText(L["lbl_info"])
        self.btn_ping.setText(L["btn_ping"])
        if self.btn_scaneaza.isEnabled(): self.btn_scaneaza.setText(L["btn_scaneaza"])
        self.tabel.setHorizontalHeaderLabels(L["headers"])
        if not self.consola_bruta.toPlainText() or "Terminal" in self.consola_bruta.toPlainText():
            self.consola_bruta.setText(L["terminal_init"])

    def porneste_scanarea(self):
        self.actualizeaza_limba()
        L = self.traduceri[self.obtine_limba_curenta()]
        self.btn_scaneaza.setEnabled(False)
        self.btn_scaneaza.setText(L["btn_asteapta"])
        self.tabel.setRowCount(0)
        self.worker = ScannerWorker()
        self.worker.dispozitiv_gasit.connect(self.adauga_dispozitiv)
        self.worker.finalizat.connect(self.scanare_terminata)
        self.worker.start()

    def adauga_dispozitiv(self, nume, ip, stare):
        rand = self.tabel.rowCount()
        self.tabel.insertRow(rand)
        self.tabel.setItem(rand, 0, QTableWidgetItem(nume))
        self.tabel.setItem(rand, 1, QTableWidgetItem(ip))
        item_stare = QTableWidgetItem(stare)
        if "🔴" in stare: item_stare.setForeground(Qt.GlobalColor.red)
        elif "🟢" in stare: item_stare.setForeground(Qt.GlobalColor.green)
        self.tabel.setItem(rand, 2, item_stare)

    def scanare_terminata(self):
        self.btn_scaneaza.setEnabled(True)
        self.actualizeaza_limba()

    def executa_ping_la_dublu_click(self, item):
        rand = self.tabel.currentRow()
        if rand != -1:
            ip = self.tabel.item(rand, 1).text()
            self.rulam_ping_real_in_consola(ip)

    def executa_ping_manual(self):
        from PyQt6.QtWidgets import QInputDialog
        L = self.traduceri[self.obtine_limba_curenta()]
        ip, ok = QInputDialog.getText(self, L["ping_titlu"], L["ping_prompt"])
        if ok and ip:
            self.rulam_ping_real_in_consola(ip)

    def rulam_ping_real_in_consola(self, ip):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.consola_bruta.setText(f"🚀 mihai@Aura:~$ ping -c 3 -W 2 {ip}\n")
        
        rez = subprocess.run(["ping", "-c", "3", "-W", "2", ip], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if rez.returncode == 0:
            self.consola_bruta.append(rez.stdout)
            self.consola_bruta.append(f"\n🟢 Status: {L['ping_ok']}")
        else:
            self.consola_bruta.append(rez.stderr + rez.stdout)
            self.consola_bruta.append(f"\n❌ Status: {L['ping_err']}")

    def afiseaza_meniu_contextual(self, pozitie):
        rand_selectat = self.tabel.currentRow()
        if rand_selectat == -1: return
        item_ip = self.tabel.item(rand_selectat, 1)
        if not item_ip: return
        ip_de_copiat = item_ip.text()
        L = self.traduceri[self.obtine_limba_curenta()]
        meniu = QMenu(self)
        meniu.setStyleSheet("background-color: #313244; color: #cdd6f4;")
        actiune_copiaza = QAction(L["ctx_copy"], self)
        actiune_copiaza.triggered.connect(lambda: QGuiApplication.clipboard().setText(ip_de_copiat))
        meniu.addAction(actiune_copiaza)
        meniu.exec(self.tabel.viewport().mapToGlobal(pozitie))
