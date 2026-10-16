import os
import json
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox
from PyQt6.QtCore import Qt

class SSHLauncherWidget(QWidget):
    def __init__(self, parent_win=None):
        super().__init__(parent_win)
        self.parent_win = parent_win
        self.cale_baza = "assets/ssh_hosts.json"
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)

        self.traduceri = {
            "ro": {
                "lbl_info": "🖥️ Gestionare Conexiuni SSH Rapide:", "btn_adauga": "➕ Adaugă",
                "btn_lanseaza": "🚀 Pornește Sesiune SSH", "btn_sterge": "🗑️ Șterge",
                "ph_eticheta": "Etichetă (ex: Laptop Iasmina)", "ph_user": "Utilizator (ex: iasmina)", "ph_ip": "IP (ex: 100.75.72.60)",
                "err_campuri": "Eroare: Toate câmpurile trebuie completate!", "err_selectie": "Selectați o conexiune din listă mai întâi!"
            },
            "en": {
                "lbl_info": "🖥️ Manage Quick SSH Connections:", "btn_adauga": "➕ Add Host",
                "btn_lanseaza": "🚀 Launch SSH Session", "btn_sterge": "🗑️ Delete",
                "ph_eticheta": "Label (e.g., Iasmina's Laptop)", "ph_user": "Username (e.g., iasmina)", "ph_ip": "IP (e.g., 100.75.72.60)",
                "err_campuri": "Error: All fields must be completed!", "err_selectie": "Please select a connection from the list first!"
            },
            "it": {
                "lbl_info": "🖥️ Gestione Connessioni SSH Rapide:", "btn_adauga": "➕ Aggiungi",
                "btn_lanseaza": "🚀 Avvia Sessione SSH", "btn_sterge": "🗑️ Elimina",
                "ph_eticheta": "Etichetta (es: Laptop Iasmina)", "ph_user": "Utente (es: iasmina)", "ph_ip": "IP (es: 100.75.72.60)",
                "err_campuri": "Errore: Tutti i campi devono essere compilati!", "err_selectie": "Seleziona prima una connessione dalla lista!"
            }
        }

        layout_inputuri = QHBoxLayout()
        layout_inputuri.setSpacing(8)
        
        self.lbl_info = QLabel(self)
        self.lbl_info.setStyleSheet("font-size: 13px; font-weight: bold; color: #a6adc8;")
        layout.addWidget(self.lbl_info)

        self.input_eticheta = QLineEdit(self)
        self.input_user = QLineEdit(self)
        self.input_ip = QLineEdit(self)
        
        stil_input = "QLineEdit { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 5px; padding: 5px 8px; font-size: 12px; }"
        for inp in [self.input_eticheta, self.input_user, self.input_ip]:
            inp.setStyleSheet(stil_input)
            layout_inputuri.addWidget(inp)

        self.btn_adauga = QPushButton(self)
        self.btn_adauga.setStyleSheet("QPushButton { background-color: #a6e3a1; color: #11111b; font-weight: bold; border-radius: 5px; padding: 6px 15px; font-size: 12px; }")
        self.btn_adauga.clicked.connect(self.adauga_conexiune)
        layout_inputuri.addWidget(self.btn_adauga)
        layout.addLayout(layout_inputuri)

        self.lista_hosturi = QListWidget(self)
        self.lista_hosturi.setStyleSheet("QListWidget { background-color: #181825; color: #cdd6f4; border: 1px solid #313244; border-radius: 6px; padding: 5px; font-size: 14px; } QListWidget::item:selected { background-color: #45475a; color: #fab387; }")
        self.lista_hosturi.itemDoubleClicked.connect(self.lanseaza_ssh_direct)
        layout.addWidget(self.lista_hosturi)

        layout_jos = QHBoxLayout()
        self.btn_lanseaza = QPushButton(self)
        self.btn_lanseaza.setStyleSheet("QPushButton { background-color: #fab387; color: #11111b; font-weight: bold; border-radius: 5px; padding: 7px 18px; font-size: 12px; }")
        self.btn_lanseaza.clicked.connect(self.lanseaza_ssh_direct)
        
        self.btn_sterge = QPushButton(self)
        self.btn_sterge.setStyleSheet("QPushButton { background-color: #f38ba8; color: #11111b; font-weight: bold; border-radius: 5px; padding: 7px 18px; font-size: 12px; }")
        self.btn_sterge.clicked.connect(self.sterge_conexiune)
        
        layout_jos.addWidget(self.btn_lanseaza)
        layout_jos.addStretch()
        layout_jos.addWidget(self.btn_sterge)
        layout.addLayout(layout_jos)

        self.incarca_hosturi()
        self.actualizeaza_limba()

    def obtine_limba_curenta(self):
        if self.parent_win and hasattr(self.parent_win, 'limba_curenta'): return self.parent_win.limba_curenta
        return "ro"

    def actualizeaza_limba(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        self.lbl_info.setText(L["lbl_info"])
        self.btn_adauga.setText(L["btn_adauga"])
        self.btn_lanseaza.setText(L["btn_lanseaza"])
        self.btn_sterge.setText(L["btn_sterge"])
        self.input_eticheta.setPlaceholderText(L["ph_eticheta"])
        self.input_user.setPlaceholderText(L["ph_user"])
        self.input_ip.setPlaceholderText(L["ph_ip"])

    def incarca_hosturi(self):
        self.lista_hosturi.clear()
        if os.path.exists(self.cale_baza):
            try:
                with open(self.cale_baza, "r") as f:
                    date = json.load(f)
                    for item in date:
                        self.lista_hosturi.addItem(f"🖥️ {item['eticheta']}  -->  {item['user']}@{item['ip']}")
            except Exception: pass

    def adauga_conexiune(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        e, u, i = self.input_eticheta.text().strip(), self.input_user.text().strip(), self.input_ip.text().strip()
        if not e or not u or not i:
            QMessageBox.warning(self, "Error", L["err_campuri"])
            return
        date_existente = []
        if os.path.exists(self.cale_baza):
            try:
                with open(self.cale_baza, "r") as f: date_existente = json.load(f)
            except Exception: pass
        date_existente.append({"eticheta": e, "user": u, "ip": i})
        os.makedirs(os.path.dirname(self.cale_baza), exist_ok=True)
        with open(self.cale_baza, "w") as f: json.dump(date_existente, f, indent=4)
        self.input_eticheta.clear()
        self.input_user.clear()
        self.input_ip.clear()
        self.incarca_hosturi()

    def sterge_conexiune(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        rand = self.lista_hosturi.currentRow()
        if rand == -1:
            QMessageBox.warning(self, "Error", L["err_selectie"])
            return
        if os.path.exists(self.cale_baza):
            try:
                with open(self.cale_baza, "r") as f: date = json.load(f)
                if rand < len(date):
                    date.pop(rand)
                    with open(self.cale_baza, "w") as f: json.dump(date, f, indent=4)
            except Exception: pass
        self.incarca_hosturi()

    def lanseaza_ssh_direct(self):
        L = self.traduceri[self.obtine_limba_curenta()]
        rand = self.lista_hosturi.currentRow()
        if rand == -1:
            QMessageBox.warning(self, "Error", L["err_selectie"])
            return
        if os.path.exists(self.cale_baza):
            try:
                with open(self.cale_baza, "r") as f: date = json.load(f)
                if rand < len(date):
                    item = date[rand]
                    # Lansăm direct în terminalul nativ din elementary OS pe mod interactiv complet!
                    os.system(f"io.elementary.terminal -e 'ssh {item['user']}@{item['ip']}' &")
            except Exception: pass
