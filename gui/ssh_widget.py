import os
import json
import subprocess
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt

class SSHLauncherWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cale_json = os.path.join(os.path.dirname(__file__), "..", "assets", "ssh_hosts.json")
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(12)

        lbl_info = QLabel("🖥️ Gestionare Conexiuni SSH Rapide:", self)
        lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #fab387;")
        layout_principal.addWidget(lbl_info)

        layout_formular = QHBoxLayout()
        self.input_eticheta = QLineEdit(self)
        self.input_eticheta.setPlaceholderText("Etichetă (ex: Laptop Iasmina)")
        self.input_eticheta.setStyleSheet("background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 6px; border-radius: 4px;")
        
        self.input_user = QLineEdit(self)
        self.input_user.setPlaceholderText("Utilizator (ex: iasmina)")
        self.input_user.setStyleSheet("background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 6px; border-radius: 4px;")
        
        self.input_ip = QLineEdit(self)
        self.input_ip.setPlaceholderText("IP (ex: 100.75.72.60)")
        self.input_ip.setStyleSheet("background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; padding: 6px; border-radius: 4px;")
        
        self.btn_adauga = QPushButton("➕ Adaugă", self)
        self.btn_adauga.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-weight: bold; padding: 6px 15px;")
        self.btn_adauga.clicked.connect(self.adauga_host)
        
        layout_formular.addWidget(self.input_eticheta)
        layout_formular.addWidget(self.input_user)
        layout_formular.addWidget(self.input_ip)
        layout_formular.addWidget(self.btn_adauga)
        layout_principal.addLayout(layout_formular)

        self.lista_hosturi = QListWidget(self)
        self.lista_hosturi.setStyleSheet("background-color: #181825; color: #cdd6f4; border: 1px solid #313244; font-size: 14px;")
        self.lista_hosturi.itemDoubleClicked.connect(self.lanseaza_ssh)
        layout_principal.addWidget(self.lista_hosturi)

        layout_butoane = QHBoxLayout()
        self.btn_conecteaza = QPushButton("🚀 Pornește Sesiune SSH", self)
        self.btn_conecteaza.setStyleSheet("background-color: #fab387; color: #11111b; font-weight: bold; padding: 8px 20px;")
        self.btn_conecteaza.clicked.connect(lambda: self.lanseaza_ssh(self.lista_hosturi.currentItem()))
        
        self.btn_sterge = QPushButton("🗑️ Șterge", self)
        self.btn_sterge.setStyleSheet("background-color: #f38ba8; color: #11111b; font-weight: bold; padding: 8px 15px;")
        self.btn_sterge.clicked.connect(self.sterge_host)
        
        layout_butoane.addWidget(self.btn_conecteaza)
        layout_butoane.addStretch()
        layout_butoane.addWidget(self.btn_sterge)
        layout_principal.addLayout(layout_butoane)

        self.incarca_hosturi()

    def incarca_hosturi(self):
        self.lista_hosturi.clear()
        if os.path.exists(self.cale_json):
            try:
                with open(self.cale_json, "r", encoding="utf-8") as f:
                    gazde = json.load(f)
                    for g in gazde:
                        item = QListWidgetItem(f"🖥️ {g['eticheta']}  👉  {g['user']}@{g['ip']}")
                        item.setData(Qt.ItemDataRole.UserRole, g)
                        self.lista_hosturi.addItem(item)
            except Exception: pass

    def adauga_host(self):
        eticheta = self.input_eticheta.text().strip()
        user = self.input_user.text().strip()
        ip = self.input_ip.text().strip()
        if not eticheta or not user or not ip: return

        gazde = []
        if os.path.exists(self.cale_json):
            try:
                with open(self.cale_json, "r", encoding="utf-8") as f: gazde = json.load(f)
            except Exception: pass
        gazde.append({"eticheta": eticheta, "user": user, "ip": ip})
        os.makedirs(os.path.dirname(self.cale_json), exist_ok=True)
        with open(self.cale_json, "w", encoding="utf-8") as f: json.dump(gazde, f, indent=4)
        self.input_eticheta.clear()
        self.input_user.clear()
        self.input_ip.clear()
        self.incarca_hosturi()

    def sterge_host(self):
        item_curent = self.lista_hosturi.currentItem()
        if not item_curent: return
        date_gazda = item_curent.data(Qt.ItemDataRole.UserRole)
        if os.path.exists(self.cale_json):
            try:
                with open(self.cale_json, "r", encoding="utf-8") as f: gazde = json.load(f)
                gazde = [g for g in gazde if not (g['eticheta'] == date_gazda['eticheta'] and g['ip'] == date_gazda['ip'])]
                with open(self.cale_json, "w", encoding="utf-8") as f: json.dump(gazde, f, indent=4)
            except Exception: pass
        self.incarca_hosturi()

    def lanseaza_ssh(self, item):
        if not item: return
        date_gazda = item.data(Qt.ItemDataRole.UserRole)
        # Executăm o sesiune curată apelând terminalul nativ din elementary OS
        comanda_terminal = f"io.elementary.terminal -e 'ssh {date_gazda['user']}@{date_gazda['ip']}'"
        try: subprocess.Popen(comanda_terminal, shell=True)
        except Exception as e: QMessageBox.critical(self, "Eroare", str(e))
