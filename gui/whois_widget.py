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
        tinta_curata = self.tinta.strip()
        
        # Preluăm dicționarul tradus trimis din widget
        L = getattr(self, 'traducere_curenta', {
            "lan_titlu": "🖥️ [ Diagnosticare LAN ] Detalii interne pentru IP:",
            "lan_err_nume": "📌 Identificare Nume Rețea: Nu s-a putut obține prin niciun protocol.",
            "lan_mac": "🍏 Adresă Fizică Dispozitiv (MAC):"
        })
        
        if tinta_curata.startswith("192.168."):
            detalii_lan = f"{L['lan_titlu']} {tinta_curata}\n"
            detalii_lan += "="*60 + "\n\n"
            
            # 1. Încercăm să luăm numele de rețea prin mDNS / Avahi, DNS și nmblookup
            try:
                nume_out = "Nedetectat"
                try:
                    import subprocess
                    avahi_out = subprocess.check_output(["avahi-resolve", "-a", tinta_curata], text=True, timeout=1)
                    if avahi_out.strip():
                        nume_out = avahi_out.split()[-1].strip()
                except Exception:
                    try:
                        import socket
                        nume_dns = socket.gethostbyaddr(tinta_curata)
                        nume_out = nume_dns
                    except Exception:
                        nmb_out = subprocess.check_output(["nmblookup", "-A", tinta_curata], text=True, stderr=subprocess.STDOUT)
                        for linie in nmb_out.split("\n"):
                            if "<00>" in linie and "GROUP" not in linie:
                                nume_out = linie.split().strip()
                                break
                
                if nume_out == "Nedetectat":
                    detalii_lan += f"{L['lan_err_nume']}\n\n"
                else:
                    detalii_lan += f"📌 Nume: {nume_out}\n\n"
            except Exception:
                detalii_lan += f"{L['lan_err_nume']}\n\n"
            
            # 2. Citim direct din /proc/net/arp pentru a ocoli parantezele din comanda 'arp'
            try:
                import os
                mac_gasit = "Nu este în cache-ul ARP"
                if os.path.exists("/proc/net/arp"):
                    with open("/proc/net/arp", "r") as f:
                        linii = f.readlines()
                    for linie in linii:
                        parti = linie.split()
                        if len(parti) >= 4 and parti[0] == tinta_curata:
                            mac_gasit = parti[3].upper()
                            break
                # REPARAT: Folosim dinamic cheia din dicționar, fără text fix în română!
                detalii_lan += f"{L['lan_mac']} {mac_gasit}\n"
            except Exception:
                detalii_lan += f"{L['lan_mac']} {mac_gasit}\n"
                
            self.rezultat.emit(detalii_lan)
        else:
            try:
                import subprocess
                out = subprocess.check_output(["whois", tinta_curata], text=True, stderr=subprocess.STDOUT)
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
                "err_titlu": "Eroare", "err_text": "Vă rugăm să introduceți o adresă IP sau un domeniu valid!",
                "lan_titlu": "🖥️ [ Diagnosticare LAN ] Detalii interne pentru IP:",
                "lan_err_nume": "📌 Identificare Nume Rețea: Nu s-a putut obține prin niciun protocol.",
                "lan_mac": "🍏 Adresă Fizică Dispozitiv (MAC):"
            },
            "en": {
                "lbl_info": "ℹ️ Network Identity Investigation (Whois lookup for IP / Domain):",
                "btn_cauta": "🔍 Investigate", "btn_run": "⏳ Searching...",
                "ph_text": "Enter an IP address (e.g., 192.168.0.1) or a public domain (e.g., google.com)",
                "err_titlu": "Error", "err_text": "Please enter a valid IP address or domain name!",
                "lan_titlu": "🖥️ [ LAN Diagnostics ] Internal details for IP:",
                "lan_err_nume": "📌 Network Name Identification: Could not be resolved by any protocol.",
                "lan_mac": "🍏 Device Physical Address (MAC):"
            },
            "it": {
                "lbl_info": "ℹ️ Investigazione Identità Rete (Whois lookup per IP / Dominio):",
                "btn_cauta": "🔍 Investiga", "btn_run": "⏳ Ricerca...",
                "ph_text": "Inserisci un indirizzo IP (es: 192.168.0.1) o un dominio pubblico (es: google.com)",
                "err_titlu": "Errore", "err_text": "Per favore inserisci un indirizzo IP o un dominio valido!",
                "lan_titlu": "🖥️ [ Diagnostica LAN ] Dettagli interni per IP:",
                "lan_err_nume": "📌 Identificazione Nome Rete: Impossibile risolvere con qualsiasi protocollo.",
                "lan_mac": "🍏 Indirizzo Fisico Dispositivo (MAC):"
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
        # CONDUCTA SALVATOARE: Pasăm dicționarul tradus direct în creierul worker-ului!
        self.worker.traducere_curenta = L
        
        self.worker.rezultat.connect(self.consola.setText)
        self.worker.finalizat.connect(self.whois_gata)
        self.worker.start()

    def whois_gata(self):
        self.btn_cauta.setEnabled(True)
        self.actualizeaza_limba()
