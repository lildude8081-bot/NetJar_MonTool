# NetJar MonTool 🌐🫙

O unealtă modulară de monitorizare și administrare a rețelei concepută pentru Linux, construită în **Python 3** și **PyQt6**. Aplicația împarte logica de control în module independente și oferid suport simetric pentru trei limbi (RO / EN / IT).

## 🚀 Caracteristici Principale / Key Features / Caratteristiche

*   **🔍 Scanner & Pinger (RO/EN/IT):** Detectează automat dispozitivele active din rețeaua locală și din rețeaua Tailscale. Dispune de un sistem contextual de click-dreapta pentru a copia instantaneu adresa IP în clipboard-ul sistemului Linux.
*   **🖥️ SSH Launcher:** Un panou administrativ de unde poți salva conexiunile favorite (utilizator, etichetă, IP). La dublu-click, aplicația invocă terminalul nativ `io.elementary.terminal` pentru a lansa sesiunea direct.
*   **📊 Traffic Monitor & Speedometer:** Monitorizează în timp real consumul de bandă (Download/Upload) direct din kernel (`/proc/net/dev`) și desenează un grafic ASCII dinamic. Include un test de viteză maximă bazat pe `speedtest-cli`.
*   **ℹ️ Whois / DNS Query:** Investighează identitatea IP-urilor sau domeniilor publice, păstrând un istoric continuu în consolă (append log). Rulează un Whois local corelând tabela ARP cu vendorul plăcii de rețea.
*   **📡 Wi-Fi Scanner & Easter Egg:** Scanează rețelele wireless din eter folosind `nmcli`.
    *   **🚨 ACTIVATE LASER BEAM:** Butonul secret care destabilizează routerele clasice din Cecina și le transformă în murături cibernetice mutante (Gogonele Radioactive, Butoiul Cybernetic), traduse simetric pe limbi și luminate în verde!

## 📋 Prerequisites & Run

```bash
sudo apt update
sudo apt install python3-pyqt6 speedtest-cli whois
python3 netjar_main.py
```
# NetJar_MonTool
