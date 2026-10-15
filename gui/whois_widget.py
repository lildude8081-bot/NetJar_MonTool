import subprocess
import socket
import urllib.request
import json
import re
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTextEdit
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class WhoisWorker(QThread):
    """ Fir de execuție pentru investigații DNS, Whois public și Whois Local (Vendor MAC) """
    rezultat_gata = pyqtSignal(str)

    def __init__(self, tinta):
        super().__init__()
        self.tinta = tinta.strip()

    def run(self):
        # Verificăm dacă ținta este un IP local (ex: 192.168.X.X sau 100.X.X.X)
        if self.este_ip_local(self.tinta):
            output = f"🔍 [WHOIS LOCAL] Investigare Dispozitiv Intern: {self.tinta}\n"
            output += "—" * 60 + "\n"
            
            # 1. Încercăm să aflăm numele DNS local (Hostname)
            try:
                nume_gazda = socket.gethostbyaddr(self.tinta)[0]
                output += f"🖥️ Hostname Local: {nume_gazda}\n"
            except Exception:
                output += "🖥️ Hostname Local: Nedetectat (Fără DNS local)\n"
                
            # 2. Extragem adresa MAC din tabela ARP a sistemului Linux
            mac = self.obtine_mac_local(self.tinta)
            if mac:
                output += f"📌 Adresă Fizică (MAC): {mac}\n"
                # 3. Interogăm producătorul pe baza MAC-ului descoperit
                vendor = self.obtine_vendor_mac(mac)
                output += f"🏢 Producător Echipament (Vendor): {vendor}\n"
            else:
                output += "📌 Adresă Fizică (MAC): Nu a fost găsită în tabela ARP (Dispozitivul ar putea fi în standby/firewall)\n"
                
            self.rezultat_gata.emit(output)
        else:
            # WHOIS PUBLIC / DNS PENTRU ADRESE EXTERNE
            output = f"🌐 [WHOIS PUBLIC] Investigare Domeniu / IP Extern: {self.tinta}\n"
            output += "—" * 60 + "\n"
            
            # Lookup DNS rapid
            try:
                ip_public = socket.gethostbyname(self.tinta)
                output += f"📍 IP Rezolvat (DNS): {ip_public}\n\n"
            except Exception:
                ip_public = self.tinta
                
            # Rulăm comanda nativă whois din Linux
            try:
                rezultat_whois = subprocess.check_output(["whois", ip_public], text=True, stderr=subprocess.STDOUT)
                # Extragem doar liniile importante (Organizație, Țară, Regiune) ca să nu umplem ecranul cu mii de linii de text brut
                linii_filtrate = []
                for linie in rezultat_whois.split("\n"):
                    if any(x in linie.lower() for x in ["orgname:", "netname:", "country:", "descr:", "organization:", "person:"]):
                        linii_filtrate.append(linie)
                
                if linii_filtrate:
                    output += "📋 Detalii Proprietar Descoperite:\n" + "\n".join(linii_filtrate) + "\n\n"
                else:
                    output += "📋 Text Brut Whois (Primele 25 de linii):\n" + "\n".join(rezultat_whois.split("\n")[:25])
            except Exception:
                output += "❌ Utilitarul 'whois' nu este instalat sau interogarea a eșuat. Puteți rula: sudo apt install whois"
                
            self.rezultat_gata.emit(output)

    def este_ip_local(self, ip):
        # Validare rapidă pentru rețeaua locală de acasă sau din Tailscale
        return ip.startswith("192.168.") or ip.startswith("10.211.") or ip.startswith("100.") or ip.startswith("127.")

    def obtine_mac_local(self, ip):
        """ Citește tabela ARP a kernel-ului Linux pentru a găsi MAC-ul asociat IP-ului """
        try:
            with open("/proc/net/arp", "r") as f:
                linii = f.readlines()
            for linie in linii:
                if ip in linie:
                    parti = linie.split()
                    if len(parti) >= 4:
                        mac = parti[3]
                        if re.match(r"[0-9a-fA-F]{2}(:[0-9a-fA-F]{2}){5}", mac):
                            return mac
        except Exception: pass
        return None

    def obtine_vendor_mac(self, mac):
        """ Interoghează un API public gratuit pentru a identifica producătorul plăcii (ex: Apple, Samsung, Intel) """
        try:
            url = f"https://macvendors.com{urllib.parse.quote(mac)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as raspuns:
                return raspuns.read().decode('utf-8')
        except Exception:
            return "Producător Necunoscut (Sau API offline)"


class WhoisWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(12)

        # Bară superioară control
        lbl_info = QLabel("ℹ️ Investigare Identitate Rețea (Cine este în spatele IP-ului / Domeniului):", self)
        lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #fab387;")
        layout_principal.addWidget(lbl_info)

        layout_cautare = QHBoxLayout()
        self.input_tinta = QLineEdit(self)
        self.input_tinta.setPlaceholderText("Introduceți un IP de pe ecran (ex: 192.168.0.1) sau un domeniu public (ex: google.com)")
        self.input_tinta.setStyleSheet("background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 8px; border-radius: 5px; font-size: 13px;")
        self.input_tinta.returnPressed.connect(self.porneste_investigatia)

        self.btn_investigheaza = QPushButton("🔍 Investighează", self)
        self.btn_investigheaza.setStyleSheet("background-color: #fab387; color: #11111b; font-weight: bold; padding: 8px 20px; border-radius: 5px; font-size: 13px;")
        self.btn_investigheaza.clicked.connect(self.porneste_investigatia)

        layout_cautare.addWidget(self.input_tinta)
        layout_cautare.addWidget(self.btn_investigheaza)
        layout_principal.addLayout(layout_cautare)

        # Consolă text afișare rezultate
        self.txt_consola = QTextEdit(self)
        self.txt_consola.setReadOnly(True)
        self.txt_consola.setStyleSheet("""
            QTextEdit {
                background-color: #11111b;
                color: #a6e3a1;
                font-family: 'Courier New', monospace;
                font-size: 13px;
                border: 1px solid #313244;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        layout_principal.addWidget(self.txt_consola)

    def porneste_investigatia(self):
        tinta = self.input_tinta.text().strip()
        if not tinta: return

        self.btn_investigheaza.setEnabled(False)
        self.btn_investigheaza.setText("⏳ Se caută...")
        
        # SCHIMBARE: Folosim append ca să PĂSTRĂM istoricul în timp ce se caută!
        self.txt_consola.append(f"\n📡 Se trimit interogări pachet către {tinta}... Vă rugăm așteptați...")

        self.worker = WhoisWorker(tinta)
        self.worker.rezultat_gata.connect(self.afiseaza_rezultate)
        self.worker.start()

    def afiseaza_rezultate(self, text_rezultat):
        self.btn_investigheaza.setEnabled(True)
        self.btn_investigheaza.setText("🔍 Investighează")
        
        # Eliminăm doar linia de așteptare pe care am pus-o mai sus, ca să punem rezultatul final curat
        continut_vechi = self.txt_consola.toPlainText()
        if "Se trimit interogări pachet către" in continut_vechi:
            # Curățăm textul temporar de procesare
            linii = continut_vechi.split("\n")
            linii = [l for l in linii if "Se trimit interogări pachet către" not in l]
            self.txt_consola.setText("\n".join(linii))
            
        # Lipim rezultatul cel nou și trântim separatorul de Senior dintr-o singură linie curată!
        self.txt_consola.append("\n" + text_rezultat)
        self.txt_consola.append("\n" + "═" * 60 + "\n")
