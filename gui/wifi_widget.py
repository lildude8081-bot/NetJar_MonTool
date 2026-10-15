import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class WifiWorker(QThread):
    """ Fir de execuție pentru scanarea Wi-Fi reală în fundal (nmcli) """
    progres = pyqtSignal(int)
    retea_gasita = pyqtSignal(str, str, str, str, str)
    finalizat = pyqtSignal()

    def run(self):
        self.progres.emit(20)
        try:
            subprocess.run(["nmcli", "device", "wifi", "rescan"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.progres.emit(50)

            output = subprocess.check_output(
                ["nmcli", "-f", "SSID,BSSID,CHAN,SIGNAL,SECURITY", "device", "wifi", "list"], 
                text=True
            )
            
            linii = output.strip().split('\n')
            if len(linii) > 1:
                for linie in linii[1:]:
                    if linie.strip():
                        parti = linie.split()
                        if len(parti) >= 4:
                            ssid = " ".join(parti[:-4]) if len(parti) > 4 else parti
                            if ssid == "*": ssid = "Wi-Fi"
                            bssid = parti[-4] if len(parti) >= 5 else "00:11:22:33:44:55"
                            securitate = parti[-1]
                            semnal = f"📶 {parti[-2]}%"
                            canal = parti[-3]
                            
                            self.retea_gasita.emit(ssid, bssid, canal, semnal, securitate)
        except Exception:
            pass
            
        self.progres.emit(100)
        self.finalizat.emit()


class WifiScannerWidget(QWidget):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        # Dicționar complet de traduceri simetrice (RO / EN / IT)
        self.traduceri = {
            "ro": {
                "lbl_info": "📡 Scanare Rețele Wi-Fi din zonă (Cămară Aeriană):",
                "btn_laser": "🚨 ACTIVARE RAZĂ LASER",
                "btn_scaneaza": "🔄 Scanează Wi-Fi",
                "btn_asteapta": "⏳ Scanare...",
                "headers": ["SSID (Nume Rețea)", "BSSID (Mac Router)", "Canal", "Semnal", "Securitate"],
                "alert_title": "⚠️ DESTABILIZARE LASER COMPLETĂ",
                "alert_text": "🛸 FRECVENȚELE AU FOST PURIFICATE!\n\nRaza laser a curățat routerele din Cecina! Toate rețelele din jur au fost transformate instantaneu în murături cibernetice mutante!",
                "m1": "👽 Gogonele_Radioactive_5G", "m2": "🛸 Castraveti_Mutilati_Quantum", "m3": "🧬 Gogoșari_Umpluți_Cu_Plutoniu",
                "m4": "🦠 Varză_Spațială_Hrean_Bypass", "m5": "🫙 Butoiul_Cybernetic_Din_Cecina", "m6": "🫙 Conopidă_Mutantă_Frecvență_Liberă",
                "sec_saramura": "Saramură_WPA3", "sec_otet": "Oțet_Securizat", "sec_mustar": "Muștar_PRO", "sec_hrean": "Hrean_Curat"
            },
            "en": {
                "lbl_info": "📡 Scan Wi-Fi Networks in range (Air Pantry):",
                "btn_laser": "🚨 ACTIVATE LASER BEAM",
                "btn_scaneaza": "🔄 Scan Wi-Fi",
                "btn_asteapta": "⏳ Scanning...",
                "headers": ["SSID (Network Name)", "BSSID (Router Mac)", "Channel", "Signal", "Security"],
                "alert_title": "⚠️ COMPLETE LASER DESTABILIZATION",
                "alert_text": "🛸 FREQUENCIES PURIFIED!\n\nThe laser beam has cleared the routers in Cecina! All surrounding networks have been instantly transformed into mutant cyber-pickles!",
                "m1": "👽 Radioactive_Green_Tomatoes_5G", "m2": "🛸 Quantum_Mutilated_Cucumbers", "m3": "🧬 Plutonium_Stuffed_Peppers",
                "m4": "🦠 Space_Cabbage_Horseradish_Bypass", "m5": "🫙 Cybernetic_Barrel_From_Cecina", "m6": "🫙 Mutant_Cauliflower_Free_Freq",
                "sec_saramura": "Brine_WPA3", "sec_otet": "Vinegar_Secured", "sec_mustar": "Mustard_PRO", "sec_hrean": "Horseradish_Clean"
            },
            "it": {
                "lbl_info": "📡 Scansione Reti Wi-Fi nell'Etere (Dispensa Aerea):",
                "btn_laser": "🚨 ATTIVA RAGGIO LASER",
                "btn_scaneaza": "🔄 Scansiona Wi-Fi",
                "btn_asteapta": "⏳ Scansione...",
                "headers": ["SSID (Nome Rete)", "BSSID (Mac Router)", "Canale", "Segnale", "Sicurezza"],
                "alert_title": "⚠️ DESTABILIZZAZIONE LASER COMPLETA",
                "alert_text": "🛸 FREQUENZE PURIFICATE!\n\nIl raggio laser ha ripulito i router di Cecina! Tutte le reti circostanti sono state istantaneamente trasformate in sottaceti cibernetici mutanti!",
                "m1": "👽 Pomodori_Verdi_Radioattivi_5G", "m2": "🛸 Cetrioli_Mutilati_Quantistici", "m3": "🧬 Peperoni_Ripieni_Al_Plutonio",
                "m4": "🦠 Cavolo_Spaziale_Rafano_Bypass", "m5": "🫙 Botte_Cibernetica_Di_Cecina", "m6": "🫙 Cavolfiore_Mutante_Freq_Libera",
                "sec_saramura": "Salamoia_WPA3", "sec_otet": "Aceto_Sicuro", "sec_mustar": "Senape_PRO", "sec_hrean": "Rafano_Pulito"
            }
        }

        # Bară acțiuni superioară
        layout_actiuni = QHBoxLayout()
        self.lbl_info = QLabel(self)
        self.lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #fab387;")
        
        self.btn_laser = QPushButton(self)
        self.btn_laser.setStyleSheet("""
            QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; border-radius: 5px; padding: 8px 15px; font-size: 12px; }
            QPushButton:hover { background-color: #11111b; color: #f38ba8; border: 1px solid #f38ba8; }
        """)
        self.btn_laser.clicked.connect(self.declanseaza_laser_beam)

        self.btn_scaneaza = QPushButton(self)
        self.btn_scaneaza.setStyleSheet("background-color: #fab387; color: #11111b; font-weight: bold; border-radius: 5px; padding: 8px 15px;")
        self.btn_scaneaza.clicked.connect(self.porneste_scanarea)
        
        layout_actiuni.addWidget(self.lbl_info)
        layout_actiuni.addStretch()
        layout_actiuni.addWidget(self.btn_laser)
        layout_actiuni.addWidget(self.btn_scaneaza)
        layout.addLayout(layout_actiuni)

        # Tabelă Wi-Fi
        self.tabel = QTableWidget(self)
        self.tabel.setColumnCount(5)
        self.tabel.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabel.setStyleSheet("background-color: #181825; color: #cdd6f4; gridline-color: #313244; font-size: 13px;")
        self.tabel.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabel.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.tabel)

        self.bara_progres = QProgressBar(self)
        self.bara_progres.setStyleSheet("QProgressBar::chunk { background-color: #fab387; }")
        layout.addWidget(self.bara_progres)

        # Aplicăm traducerile inițiale
        self.actualizeaza_limba()

    def obtine_limba_curenta(self):
        if self.parent_win and hasattr(self.parent_win, 'limba_curenta'):
            return self.parent_win.limba_curenta
        return "ro"

    def actualizeaza_limba(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_info.setText(L["lbl_info"])
        self.btn_laser.setText(L["btn_laser"])
        if self.btn_scaneaza.isEnabled():
            self.btn_scaneaza.setText(L["btn_scaneaza"])
        self.tabel.setHorizontalHeaderLabels(L["headers"])

    def porneste_scanarea(self):
        self.actualizeaza_limba()
        L = self.traduceri[self.obtine_limba_curenta()]
        self.btn_scaneaza.setEnabled(False)
        self.btn_laser.setEnabled(False)
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
        self.actualizeaza_limba()

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
                if col == 0:
                    item.setForeground(Qt.GlobalColor.green)
                self.tabel.setItem(rand, col, item)
        self.bara_progres.setValue(100)
        msg = QMessageBox(self)
        msg.setWindowTitle(L["alert_title"])
        msg.setText(L["alert_text"])
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setStyleSheet("background-color: #1e1e2e; color: #f38ba8; font-family: monospace; font-size: 13px;")
        msg.exec()
