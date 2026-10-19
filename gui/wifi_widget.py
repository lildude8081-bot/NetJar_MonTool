import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox, QInputDialog, QLineEdit
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class WifiWorker(QThread):
    progres = pyqtSignal(int)
    retea_gasita = pyqtSignal(str, str, str, str, str)
    finalizat = pyqtSignal()

    def run(self):
        self.progres.emit(20)
        try:
            import subprocess
            subprocess.run(["nmcli", "device", "wifi", "rescan"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.progres.emit(50)
            
            # Fenta supremă: Cerem nmcli să folosească o bară verticală '|' ca separator controlat!
            output = subprocess.check_output(["nmcli", "-t", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "device", "wifi", "list"], text=True)
            linii = output.strip().split('\n')
            
            for linie in linii:
                if linie.strip():
                    # Spargem linia strict după caracterul '|'
                    parti = linie.split(':')
                    # nmcli -t folosește uneori ':' ca separator, dar dacă BSSID are și el ':', e mai sigur să mapăm coloanele curat.
                    # Pentru siguranță maximă împotriva semnelor ':' din adresele MAC, extragem invers sau folosim split custom:
                    parti = linie.split('\\:') # nmcli banează separatorul nativ prin backslash
                    
            # Varianta cea mai curată și robustă de Senior pentru nmcli -t:
            output = subprocess.check_output(["nmcli", "--terse", "--fields", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "device", "wifi", "list"], text=True)
            for linie in output.strip().split('\n'):
                if linie.strip():
                    # În mod 'terse', nmcli separă prin caractere ':' dar le pune backslash celor din MAC.
                    # O parsam invers, de la coadă la cap, despărțind după ':' curat
                    parti = []
                    rest = linie
                    for _ in range(4):
                        if ':' in rest:
                            rest, _, bucata = rest.rpartition(':')
                            parti.insert(0, bucata)
                        else:
                            parti.insert(0, rest)
                            rest = ""
                            break
                    parti.insert(0, rest.replace('\\:', ':')) # Restaurăm adresa MAC sau SSID-ul dacă avea ':'
                    
                    if len(parti) >= 5:
                        ssid = parti[0]
                        bssid = parti[1]
                        canal = parti[2]
                        semnal = f"📶 {parti[3]}%"
                        securitate = parti[4]
                        
                        if ssid == "*" or not ssid.strip(): ssid = "Wi-Fi Ascuns"
                        self.retea_gasita.emit(ssid, bssid, canal, semnal, securitate)
        except Exception: 
            pass
        self.progres.emit(100)
        self.finalizat.emit()

class WifiConnectWorker(QThread):
    finalizat = pyqtSignal(int, str)
    def __init__(self, comanda):
        super().__init__()
        self.comanda = comanda
    def run(self):
        rezultat = subprocess.run(self.comanda, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.finalizat.emit(rezultat.returncode, rezultat.stderr)

class WifiScannerWidget(QWidget):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.ssid_curent = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        self.traduceri = {
            "ro": {
                "lbl_info": "📡 Wi-Fi:", "btn_laser": "🚨 ACTIVARE RAZĂ LASER", "btn_scaneaza": "🔄 Scanează Wi-Fi",
                "btn_asteapta": "⏳ Scanare...", "btn_conecteaza": "🔌 Conectare Rețea",
                "headers": ["SSID (Nume Rețea)", "BSSID (Mac Router)", "Canal", "Semnal", "Securitate"],
                "alert_title": "⚠️ DESTABILIZARE LASER COMPLETĂ",
                "alert_text": "🛸 FRECVENȚELE AU FOST PURIFICATE!\n\nRaza laser a curățat routerele din Cecina! Toate rețelele din jur au fost transformate instantaneu în murături cibernetice mutante!",
                "m1": "👽 Gogonele_Radioactive_5G", "m2": "🛸 Castraveti_Mutilati_Quantum", "m3": "🧬 Gogoșari_Umpluți_Cu_Plutoniu",
                "m4": "🦠 Varză_Spațială_Hrean_Bypass", "m5": "🫙 Butoiul_Cybernetic_Din_Cecina", "m6": "🫙 Conopidă_Mutantă_Frecvență_Liberă",
                "sec_saramura": "Saramură_WPA3", "sec_otet": "Oțet_Securizat", "sec_mustar": "Muștar_PRO", "sec_hrean": "Hrean_Curat",
                "pwd_titlu": "Parolă Wi-Fi", "pwd_text": "Introduceți parola pentru rețeaua:",
                "con_ok": "Succes", "con_ok_text": "Te-ai conectat cu succes la rețeaua",
                "con_err": "Eroare", "con_err_text": "Conectarea a eșuat pentru rețeaua", "sel_err": "Selectează o rețea din tabel mai întâi!"
            },
            "en": {
                "lbl_info": "📡 Wi-Fi:", "btn_laser": "🚨 ACTIVATE LASER BEAM", "btn_scaneaza": "🔄 Scan Wi-Fi",
                "btn_asteapta": "⏳ Scanning...", "btn_conecteaza": "🔌 Connect to Network",
                "headers": ["SSID (Network Name)", "BSSID (Router Mac)", "Channel", "Signal", "Security"],
                "alert_title": "⚠️ COMPLETE LASER DESTABILIZATION",
                "alert_text": "🛸 FREQUENCIES PURIFIED!\n\nThe laser beam has cleared the routers in Cecina! All surrounding networks have been instantly transformed into mutant cyber-pickles!",
                "m1": "👽 Radioactive_Green_Tomatoes_5G", "m2": "🛸 Quantum_Mutilated_Cucumbers", "m3": "🧬 Plutonium_Stuffed_Peppers",
                "m4": "🦠 Space_Cabbage_Horseradish_Bypass", "m5": "🫙 Cybernetic_Barrel_From_Cecina", "m6": "🫙 Mutant_Cauliflower_Free_Freq",
                "sec_saramura": "Brine_WPA3", "sec_otet": "Vinegar_Secured", "sec_mustar": "Mustard_PRO", "sec_hrean": "Horseradish_Clean",
                "pwd_titlu": "Wi-Fi Password", "pwd_text": "Enter password for network:",
                "con_ok": "Success", "con_ok_text": "Successfully connected to network",
                "con_err": "Error", "con_err_text": "Connection failed for network", "sel_err": "Select a network from the table first!"
            },
            "it": {
                "lbl_info": "📡 Wi-Fi:", "btn_laser": "🚨 ATTIVA RAGGIO LASER", "btn_scaneaza": "🔄 Scansiona Wi-Fi",
                "btn_asteapta": "⏳ Scansione...", "btn_conecteaza": "🔌 Connetti alla Rete",
                "headers": ["SSID (Nome Rete)", "BSSID (Mac Router)", "Canale", "Segnale", "Sicurezza"],
                "alert_title": "⚠️ DESTABILIZZAZIONE LASER COMPLETA",
                "alert_text": "🛸 FREQUENZE PURIFICATE!\n\nIl raggio laser ha ripulito i router di Cecina! Tutte le reti circostanti sono state istantaneamente trasformate in sottaceti cibernetici mutanti!",
                "m1": "👽 Pomodori_Verdi_Radioattivi_5G", "m2": "🛸 Cetrioli_Mutilati_Quantistici", "m3": "🧬 Peperoni_Ripieni_Al_Plutonio",
                "m4": "🦠 Cavolo_Spaziale_Rafano_Bypass", "m5": "🫙 Botte_Cibernetica_Di_Cecina", "m6": "🫙 Cavolfiore_Mutante_Freq_Libera",
                "sec_saramura": "Salamoia_WPA3", "sec_otet": "Aceto_Sicuro", "sec_mustar": "Senape_PRO", "sec_hrean": "Rafano_Pulito",
                "pwd_titlu": "Password Wi-Fi", "pwd_text": "Inserisci la password per la rete:",
                "con_ok": "Successo", "con_ok_text": "Connessione riuscita alla rete",
                "con_err": "Errore", "con_err_text": "Connessione fallita per la rete", "sel_err": "Seleziona prima una rete dalla tabella!"
            }
        }

        layout_actiuni = QHBoxLayout()
        layout_actiuni.setSpacing(10)
        self.lbl_info = QLabel(self)
        self.lbl_info.setStyleSheet("font-size: 13px; font-weight: bold; color: #fab387;")
        layout_actiuni.addWidget(self.lbl_info)
        
        self.bara_progres = QProgressBar(self)
        self.bara_progres.setFixedWidth(120)
        self.bara_progres.setStyleSheet("QProgressBar { border: 1px solid #313244; border-radius: 4px; text-align: center; background-color: #11111b; } QProgressBar::chunk { background-color: #f38ba8; }")
        layout_actiuni.addWidget(self.bara_progres)
        layout_actiuni.addStretch()
        
        self.btn_laser = QPushButton(self)
        self.btn_laser.setStyleSheet("QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 12px; font-size: 12px; }")
        self.btn_laser.clicked.connect(self.declanseaza_laser_beam)
        layout_actiuni.addWidget(self.btn_laser)

        self.btn_conecteaza = QPushButton(self)
        self.btn_conecteaza.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 12px; font-size: 12px; }")
        self.btn_conecteaza.clicked.connect(self.conecteaza_la_retea)
        layout_actiuni.addWidget(self.btn_conecteaza)

        self.btn_scaneaza = QPushButton(self)
        self.btn_scaneaza.setStyleSheet("QPushButton { background-color: #fab387; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 12px; font-size: 12px; }")
        self.btn_scaneaza.clicked.connect(self.porneste_scanarea)
        layout_actiuni.addWidget(self.btn_scaneaza)
        layout.addLayout(layout_actiuni)

        self.tabel = QTableWidget(self)
        self.tabel.setColumnCount(5)
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabel.setStyleSheet("background-color: #181825; color: #cdd6f4; gridline-color: #313244; font-size: 13px;")
        self.tabel.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabel.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabel)
        self.actualizeaza_limba()

    def obtine_limba_curenta(self):
        if self.parent_win and hasattr(self.parent_win, 'limba_curenta'): return self.parent_win.limba_curenta
        return "ro"

    def actualizeaza_limba(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_info.setText(L["lbl_info"])
        self.btn_laser.setText(L["btn_laser"])
        self.btn_conecteaza.setText(L["btn_conecteaza"])
        if self.btn_scaneaza.isEnabled(): self.btn_scaneaza.setText(L["btn_scaneaza"])
        self.tabel.setHorizontalHeaderLabels(L["headers"])

    def porneste_scanarea(self):
        self.actualizeaza_limba()
        L = self.traduceri[self.obtine_limba_curenta()]
        self.btn_scaneaza.setEnabled(False)
        self.btn_laser.setEnabled(False)
        self.btn_conecteaza.setEnabled(False)
        self.btn_scaneaza.setText(L["btn_asteapta"])
        self.tabel.setRowCount(0)
        self.bara_progres.setValue(0)
        self.worker = WifiWorker()
        self.worker.progres.connect(self.bara_progres.setValue)
        self.worker.retea_gasita.connect(self.adauga_retea)
        self.worker.finalizat.connect(self.scansione_terminata)
        self.worker.start()

    def adauga_retea(self, ssid, bssid, canal, semnal, securitate):
        rand = self.tabel.rowCount()
        self.tabel.insertRow(rand)
        self.tabel.setItem(rand, 0, QTableWidgetItem(ssid))
        self.tabel.setItem(rand, 1, QTableWidgetItem(bssid))
        self.tabel.setItem(rand, 2, QTableWidgetItem(canal))
        self.tabel.setItem(rand, 3, QTableWidgetItem(semnal))
        self.tabel.setItem(rand, 4, QTableWidgetItem(securitate))

    def scansione_terminata(self):
        self.btn_scaneaza.setEnabled(True)
        self.btn_laser.setEnabled(True)
        self.btn_conecteaza.setEnabled(True)
        self.actualizeaza_limba()

    def conecteaza_la_retea(self):
        """ Conectare inteligentă: folosește conexiunea salvată în Aura dacă există, altfel cere parola """
        L = self.traduceri[self.obtine_limba_curenta()]
        rand_selectat = self.tabel.currentRow()
        if rand_selectat == -1:
            QMessageBox.warning(self, "Warning", L["sel_err"])
            return
            
        self.ssid_curent = self.tabel.item(rand_selectat, 0).text()
        securitate = self.tabel.item(rand_selectat, 4).text()
        
        self.bara_progres.setValue(30)
        self.btn_scaneaza.setEnabled(False)
        self.btn_laser.setEnabled(False)
        self.btn_conecteaza.setEnabled(False)

        # Fenta de Senior: Verificăm dacă Aura are deja salvat un profil pentru acest SSID
        import subprocess
        verificare_profil = subprocess.run(["nmcli", "connection", "show", self.ssid_curent], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if verificare_profil.returncode == 0:
            # Cazul 1: Profilul există deja în NetworkManager, îl pornim direct fără parolă!
            comanda = ["nmcli", "connection", "up", self.ssid_curent]
        else:
            # Cazul 2: Rețea nouă. Cerem parola doar dacă nu este o rețea deschisă (OPEN)
            parola = ""
            if securitate and securitate != "--" and "OPEN" not in securitate.upper():
                parola, ok = QInputDialog.getText(self, L["pwd_titlu"], f"{L['pwd_text']} {self.ssid_curent}", QLineEdit.EchoMode.Password)
                if not ok:
                    self.scansione_terminata()
                    return
            comanda = ["nmcli", "device", "wifi", "connect", self.ssid_curent]
            if parola: 
                comanda.extend(["password", parola])

        self.bara_progres.setValue(60)
        self.conn_worker = WifiConnectWorker(comanda)
        self.conn_worker.finalizat.connect(self.conectare_finalizata)
        self.conn_worker.start()

    def conectare_finalizata(self, returncode, stderr):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.bara_progres.setValue(100)
        self.btn_scaneaza.setEnabled(True)
        self.btn_laser.setEnabled(True)
        self.btn_conecteaza.setEnabled(True)
        
        # Ne asigurăm că transformăm octeții sau textul brut într-un șir curat
        text_eroare = stderr.strip() if hasattr(stderr, 'strip') else str(stderr)
        
        if returncode == 0:
            QMessageBox.information(self, L["con_ok"], f"{L['con_ok_text']} '{self.ssid_curent}'!")
        else:
            QMessageBox.critical(self, L["con_err"], f"{L['con_err_text']} '{self.ssid_curent}'!\n\n{text_eroare}")

    def declanseaza_laser_beam(self):
        self.actualizeaza_limba()
        L = self.traduceri[self.obtine_limba_curenta()]
        self.tabel.setRowCount(0)
        self.bara_progres.setValue(30)
        muraturi_cosmice = [
            (L["m1"], "FF:AA:BB:CC:DD:EE", "666", "📶 99%", L["sec_saramura"]),
            (L["m2"], "00:XX:99:88:77:66", "13", "📶 88%", L["sec_otet"]),
            (L["m3"], "AA:BB:CC:11:22:33", "88", "📶 75%", L["sec_mustar"]),
            (L["m4"], "44:55:66:77:88:99", "7", "📶 62%", "Bypass"),
            (L["m5"], "CE:CI:NA:20:26:FF", "100", "📶 100%", "Mihai_Root"),
            (L["m6"], "CA:FE:BA:BE:00:11", "42", "📶 45%", L["sec_hrean"])
        ]
        for m in muraturi_cosmice:
            rand = self.tabel.rowCount()
            self.tabel.insertRow(rand)
            for col, valoare in enumerate(m):
                item = QTableWidgetItem(valoare)
                if col == 0: item.setForeground(Qt.GlobalColor.green)
                self.tabel.setItem(rand, col, item)
        self.bara_progres.setValue(100)
        msg = QMessageBox(self)
        msg.setWindowTitle(L["alert_title"])
        msg.setText(L["alert_text"])
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStyleSheet("background-color: #1e1e2e; color: #f38ba8; font-family: monospace; font-size: 13px;")
        msg.exec()
