import subprocess
import socket
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QProgressBar, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class ScannerWorker(QThread):
    progres = pyqtSignal(int)
    dispozitiv_gasit = pyqtSignal(str, str, str)
    finalizat = pyqtSignal()

    def run(self):
        self.progres.emit(10)
        
        # 1. SCANARE TAILSCALE CLARĂ
        try:
            rezultat = subprocess.check_output(["tailscale", "status"], text=True)
            for linie in rezultat.strip().split('\n'):
                if linie:
                    parti = linie.split()
                    if len(parti) >= 2:
                        ip = parti[0]
                        nume = parti[1]
                        
                        if "offline" in linie.lower():
                            stare = "🔴 Offline"
                        else:
                            stare = "🟢 Online"
                            
                        if "100." in ip:
                            self.dispozitiv_gasit.emit(nume, ip, stare)
        except Exception:
            pass

        self.progres.emit(40)
        
        # 2. SCANARE REȚEA LOCALĂ
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            baza_ip = ".".join(s.getsockname().split(".")[:3]) + "."
            s.close()
        except Exception:
            baza_ip = "192.168.0."

        total_adrese = 30
        for i in range(1, total_adrese + 1):
            ip_tinta = f"{baza_ip}{i}"
            raspuns = subprocess.run(["ping", "-c", "1", "-W", "1", ip_tinta], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if raspuns.returncode == 0:
                self.dispozitiv_gasit.emit("Dispozitiv Local", ip_tinta, "🟢 Online")
            self.progres.emit(40 + int((i / total_adrese) * 60))

        self.progres.emit(100)
        self.finalizat.emit()


class PingWorker(QThread):
    """ Fir de execuție separat pentru a rula ping-ul manual fără a bloca interfața """
    rezultat_ping = pyqtSignal(str)

    def __init__(self, ip):
        super().__init__()
        self.ip = ip

    def run(self):
        try:
            # Executăm 4 pachete de ping standard pe Linux
            rezultat = subprocess.check_output(["ping", "-c", "4", self.ip], text=True, stderr=subprocess.STDOUT)
            self.rezultat_ping.emit(rezultat)
        except subprocess.CalledProcessError as e:
            self.rezultat_ping.emit(e.output if e.output else "❌ Dispozitivul nu răspunde la ping (Timeout).")
        except Exception as ex:
            self.rezultat_ping.emit(f"❌ Eroare la execuție: {str(ex)}")


class ScannerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Bară de acțiuni superioară
        layout_actiuni = QHBoxLayout()
        lbl_info = QLabel("🔍 Scanner & Pinger (Local & Tailscale):", self)
        
        self.btn_scaneaza = QPushButton("🔄 Scanează Rețeaua", self)
        self.btn_scaneaza.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; padding: 8px 15px;")
        self.btn_scaneaza.clicked.connect(self.porneste_scanarea)
        
        layout_actiuni.addWidget(lbl_info)
        layout_actiuni.addStretch()
        layout_actiuni.addWidget(self.btn_scaneaza)
        layout.addLayout(layout_actiuni)

        # Tabelul cu dispozitive
        self.tabel = QTableWidget(self)
        self.tabel.setColumnCount(3)
        self.tabel.setHorizontalHeaderLabels(["Nume Dispozitiv", "Adresă IP", "Stare"])
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabel.setStyleSheet("background-color: #181825; color: #cdd6f4; gridline-color: #313244; font-size: 13px;")
        self.tabel.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabel.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabel.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabel.customContextMenuRequested.connect(self.deschide_meniu_contextual)
        layout.addWidget(self.tabel)

        # Bară de acțiuni inferioară pentru PING MANUAL
        layout_jos = QHBoxLayout()
        self.btn_ping = QPushButton("⚡ Dă Ping Manual", self)
        self.btn_ping.setStyleSheet("""
            QPushButton { background-color: #fab387; color: #11111b; font-weight: bold; border-radius: 5px; padding: 8px 20px; font-size: 13px; }
            QPushButton:hover { background-color: #f9e2af; }
        """)
        self.btn_ping.clicked.connect(self.executa_ping_manual)
        layout_jos.addWidget(self.btn_ping)
        layout_jos.addStretch()
        layout.addLayout(layout_jos)

        self.bara_progres = QProgressBar(self)
        self.bara_progres.setStyleSheet("QProgressBar::chunk { background-color: #fab387; }")
        layout.addWidget(self.bara_progres)

    def porneste_scanarea(self):
        self.btn_scaneaza.setEnabled(False)
        self.tabel.setRowCount(0)
        self.worker = ScannerWorker()
        self.worker.progres.connect(self.bara_progres.setValue)
        self.worker.dispozitiv_gasit.connect(self.adauga_dispozitiv)
        self.worker.finalizat.connect(lambda: self.btn_scaneaza.setEnabled(True))
        self.worker.start()

    def adauga_dispozitiv(self, nume, ip, stare):
        rand = self.tabel.rowCount()
        self.tabel.insertRow(rand)
        self.tabel.setItem(rand, 0, QTableWidgetItem(nume))
        self.tabel.setItem(rand, 1, QTableWidgetItem(ip))
        self.tabel.setItem(rand, 2, QTableWidgetItem(stare))

    def executa_ping_manual(self):
        """ Preia IP-ul selectat din tabel și trimite pachetele de test """
        rand_selectat = self.tabel.currentRow()
        if rand_selectat == -1:
            QMessageBox.warning(self, "Atenție", "Vă rugăm să selectați un dispozitiv din tabel mai întâi!")
            return
            
        ip_tinta = self.tabel.item(rand_selectat, 1).text()
        nume_tinta = self.tabel.item(rand_selectat, 0).text()
        
        self.btn_ping.setEnabled(False)
        self.btn_ping.setText("⏳ Se trimit pachete...")
        
        # Lansăm workerul de ping ca să nu înghețe interfața modulară
        self.ping_worker = PingWorker(ip_tinta)
        self.ping_worker.rezultat_ping.connect(lambda txt: self.afiseaza_rezultat_ping(nume_tinta, txt))
        self.ping_worker.start()

    def afiseaza_rezultat_ping(self, nume, rezultat):
        self.btn_ping.setEnabled(True)
        self.btn_ping.setText("⚡ Dă Ping Manual")
        
        # Deschidem un popup curat stilizat peste tabel cu output-ul real din terminal
        msg = QMessageBox(self)
        msg.setWindowTitle(f"Ping Console — {nume}")
        msg.setText(rezultat)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("background-color: #1e1e2e; color: #a6e3a1; font-family: monospace; font-size: 13px;")
        msg.exec()


    def deschide_meniu_contextual(self, pozitie):
        rand = self.tabel.currentRow()
        if rand == -1: return
        
        ip_selectat = self.tabel.item(rand, 1).text()
        
        from PyQt6.QtWidgets import QMenu
        meniu = QMenu(self)
        meniu.setStyleSheet("background-color: #313244; color: #cdd6f4; font-size: 13px;")
        
        act_copiaza = meniu.addAction("📋 Copiază Adresă IP")
        actiune = meniu.exec(self.tabel.mapToGlobal(pozitie))
        
        if actiune == act_copiaza:
            # Trimitem IP-ul direct în memoria clipboard a sistemului Linux!
            clipboard = QApplication.instance().clipboard()
            clipboard.setText(ip_selectat)