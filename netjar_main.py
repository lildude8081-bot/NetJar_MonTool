import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtCore import Qt

# Importăm modulele independente din folderul GUI
from gui.scanner_widget import ScannerWidget
from gui.ssh_widget import SSHLauncherWidget
from gui.traffic_widget import TrafficMonitorWidget
from gui.whois_widget import WhoisWidget
from gui.wifi_widget import WifiScannerWidget

class NetJarMonTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.limba_curenta = "ro" # Limba implicită la pornire
        
        self.setWindowTitle("🌐 NetJar MonTool v1.0.0")
        self.resize(1000, 720)
        self.setStyleSheet("background-color: #1e1e2e; color: #cdd6f4; font-family: Arial;")
        
        self.init_ui()

    def init_ui(self):
        widget_central = QWidget(self)
        self.setCentralWidget(widget_central)
        layout_principal = QVBoxLayout(widget_central)
        layout_principal.setContentsMargins(15, 10, 15, 15)
        
        # --- HEADER SUPERIOR CU BRANDING ȘI COMBOBOX DE LIMBI ---
        layout_header = QHBoxLayout()
        
        self.lbl_titlu = QLabel("🫙 NetJar MonTool — Panou Modular", self)
        self.lbl_titlu.setStyleSheet("font-size: 22px; font-weight: bold; color: #fab387; padding: 5px;")
        
        # Selectorul dropdown elegant pentru RO / EN / IT
        self.combo_limbi = QComboBox(self)
        self.combo_limbi.addItems(["🌐 Română", "🌐 English", "🌐 Italiano"])
        self.combo_limbi.setStyleSheet("""
            QComboBox { background-color: #313244; color: #cdd6f4; border: 1px solid #45475a; border-radius: 5px; padding: 5px 10px; font-weight: bold; min-width: 140px; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background-color: #313244; color: #cdd6f4; selection-background-color: #45475a; }
        """)
        self.combo_limbi.currentIndexChanged.connect(self.actiune_schimba_limba_globala)
        
        layout_header.addWidget(self.lbl_titlu)
        layout_header.addStretch()
        layout_header.addWidget(self.combo_limbi)
        layout_principal.addLayout(layout_header)
        
        # --- CONTAINERUL PRINCIPAL DE TAB-URI ---
        self.taburi = QTabWidget(self)
        self.taburi.setStyleSheet("""
            QTabWidget::panel { border: 1px solid #45475a; background-color: #11111b; border-radius: 6px; }
            QTabBar::tab { background-color: #313244; color: #a6adc8; padding: 12px 22px; font-weight: bold; font-size: 13px; }
            QTabBar::tab:selected { background-color: #11111b; color: #fab387; border-bottom: 2px solid #fab387; }
        """)
        
        # Inițializăm instanțele modulelor salvate ca proprietăți
        self.widget_scanner = ScannerWidget(self)
        self.widget_ssh = SSHLauncherWidget(self)
        self.widget_traffic = TrafficMonitorWidget(self)
        self.widget_whois = WhoisWidget(self)
        self.widget_wifi = WifiScannerWidget(self)
        
        # Încărcăm modulele în tab-urile lor oficiale
        self.taburi.addTab(self.widget_scanner, "🔍 Scanner & Pinger")
        self.taburi.addTab(self.widget_ssh, "🖥️ SSH Launcher")
        self.taburi.addTab(self.widget_traffic, "📊 Traffic Monitor")
        self.taburi.addTab(self.widget_whois, "ℹ️ Whois / DNS")
        self.taburi.addTab(self.widget_wifi, "📡 Wi-Fi Scanner")
        
        layout_principal.addWidget(self.taburi)

    def actiune_schimba_limba_globala(self, index):
        """ Schimbă starea aplicației și trimite ordinul de traducere din mers """
        if index == 0:
            self.limba_curenta = "ro"
        elif index == 1:
            self.limba_curenta = "en"
        elif index == 2:
            self.limba_curenta = "it"
            
        # 1. Schimbăm titlul din acoperiș
        titluri = {
            "ro": "🫙 NetJar MonTool — Panou Modular",
            "en": "🫙 NetJar MonTool — Modular Panel",
            "it": "🫙 NetJar MonTool — Pannello Modulare"
        }
        self.lbl_titlu.setText(titluri[self.limba_curenta])
        
        # 2. Redenumim instantaneu etichetele de pe Tab-uri
        tab_names = {
            "ro": ["🔍 Scanner & Pinger", "🖥️ Lansator SSH", "📊 Monitor Trafic", "ℹ️ Whois / DNS", "📡 Scanner Wi-Fi"],
            "en": ["🔍 Scanner & Pinger", "🖥️ SSH Launcher", "📊 Traffic Monitor", "ℹ️ Whois / DNS", "📡 Wi-Fi Scanner"],
            "it": ["🔍 Scanner & Pinger", "🖥️ Lanciatore SSH", "📊 Monitor Traffico", "ℹ️ Whois / DNS", "📡 Scanner Wi-Fi"]
        }
        for i, nume in enumerate(tab_names[self.limba_curenta]):
            self.taburi.setTabText(i, nume)
            
        # 3. Declanșăm funcția de traducere din interiorul modulului Wi-Fi!
        if hasattr(self.widget_wifi, 'actualizeaza_limba'):
            self.widget_wifi.actualizeaza_limba()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    fereastra = NetJarMonTool()
    fereastra.show()
    sys.exit(app.exec())
