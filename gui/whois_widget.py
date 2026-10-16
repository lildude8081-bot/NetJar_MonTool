import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class WhoisWorker(QThread):
    rezultat = pyqtSignal(str)
    finalizat = pyqtSignal()

    def __init__(self, tinta):
        super().__init__()
        self.tinta = tinta

    def run(self):
        try:
            out = subprocess.check_output(["whois", self.tinta], text=True, stderr=subprocess.STDOUT)
            self.rezultat.emit(out)
        except Exception as e:
            self.rezultat.emit(f"Error executing Whois:\n{str(e)}")
        self.finalizat.emit()

class WhoisWidget(QWidget):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Dicționarul complet simetric pentru Whois în cele 3 limbi
        self.traduceri = {
            "ro": {
                "lbl_info": "ℹ️ Investigare Identitate Rețea (Cine este în spatele IP-ului / Domeniului):",
                "btn_cauta": "🔍 Investighează", "btn_run": "⏳ Căutare...",
                "ph_text": "Introduceți un IP de pe ecran (ex: 192.168.0.1) sau un domeniu public (ex: google.com)",
                "err_titlu": "Eroare", "err_text": "Vă rugăm să introduceți o adresă IP sau un domeniu valid!"
            },
            "en": {
                "lbl_info": "ℹ️ Network Identity Investigation (Whois lookup for IP / Domain):",
                "btn_cauta": "🔍 Investigate", "btn_run": "⏳ Searching...",
                "ph_text": "Enter an IP address (e.g., 192.168.0.1) or a public domain (e.g., google.com)",
                "err_titlu": "Error", "err_text": "Please enter a valid IP address or domain name!"
            },
            "it": {
                "lbl_info": "ℹ️ Investigazione Identità Rete (Whois lookup per IP / Dominio):",
                "btn_cauta": "🔍 Investiga", "btn_run": "⏳ Ricerca...",
                "ph_text": "Inserisci un indirizzo IP (es: 192.168.0.1) o un dominio pubblico (es: google.com)",
                "err_titlu": "Errore", "err_text": "Per favore inserisci un indirizzo IP o un dominio valido!"
            }
        }

        # Rând superior fluid pentru input
        layout_input = QHBoxLayout()
        layout_input.setSpacing(8)
        
        self.lbl_info = QLabel(self)
        self.lbl_info.setStyleSheet("font-size: 13px; font-weight: bold; color: #a6adc8;")
        layout.addWidget(self.lbl_info)

        self.input_tinta = QLineEdit(self)
        self.input_tinta.setStyleSheet("QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 5px; padding: 6px 10px; font-size: 13px; }")
        layout_input.addWidget(self.input_tinta)

        self.btn_cauta = QPushButton(self)
        self.btn_cauta.setStyleSheet("QPushButton { background-color: #fab387; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 15px; font-size: 12px; }")
        self.btn_cauta.clicked.connect(self.executa_whois)
        layout_input.addWidget(self.btn_cauta)
        layout.addLayout(layout_input)

        # Zona mare de jurnalizare text (Consolă Terminal)
        self.consola = QTextEdit(self)
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("QTextEdit { background-color: #11111b; color: #a6e3a1; font-family: monospace; font-size: 13px; border: 1px solid #313244; border-radius: 6px; padding: 10px; }")
        layout.addWidget(self.consola)

        self.actualizeaza_limba()

    def obtine_limba_curenta(self):
        if self.parent_win and hasattr(self.parent_win, 'limba_curenta'):
            return self.parent_win.limba_curenta
        return "ro"

    def actualizeaza_limba(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_info.setText(L["lbl_info"])
        self.input_tinta.setPlaceholderText(L["ph_text"])
        if self.btn_cauta.isEnabled():
            self.btn_cauta.setText(L["btn_cauta"])

    def executa_whois(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        tinta = self.input_tinta.text().strip()
        if not tinta:
            QMessageBox.warning(self, L["err_titlu"], L["err_text"])
            return

        self.btn_cauta.setEnabled(False)
        self.btn_cauta.setText(L["btn_run"])
        self.consola.clear()

        self.worker = WhoisWorker(tinta)
        self.worker.rezultat.connect(self.consola.setText)
        self.worker.finalizat.connect(self.whois_gata)
        self.worker.start()

    def whois_gata(self):
        self.btn_cauta.setEnabled(True)
        self.actualizeaza_limba()
