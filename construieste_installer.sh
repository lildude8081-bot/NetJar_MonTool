#!/bin/bash
# Script de împachetare nativă .deb pentru NetJar MonTool v1.0.0 (2026)

NUME_PACHET="netjar-montool"
VERSIUNE="1.0.0"
DIR_CONSTRUCTIE="DEBIAN_BUILD"

echo "📦 Începe împachetarea pentru ${NUME_PACHET}_${VERSIUNE}..."

# Curățăm eventualele construcții vechi
rm -rf $DIR_CONSTRUCTIE
rm -f ${NUME_PACHET}_${VERSIUNE}_amd64.deb

# Creăm structura oficială de directoare Linux
mkdir -p $DIR_CONSTRUCTIE/DEBIAN
mkdir -p $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/gui
mkdir -p $DIR_CONSTRUCTIE/usr/bin

# 1. Creăm fișierul obligatoriu de control pentru Debian
cat << 'EOC' > $DIR_CONSTRUCTIE/DEBIAN/control
Package: netjar-montool
Version: 1.0.0
Section: utils
Priority: optional
Architecture: amd64
Maintainer: Mihai <lildude8081-bot>
Depends: python3, python3-pyqt6, speedtest-cli, whois
Description: Suita modulara de monitorizare si administrare a retelei (NetJar MonTool).
EOC

# 2. Copiem fișierele de cod proaspăt verificate în structura pachetului
cp netjar_main.py $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/
cp gui/*.py $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/gui/

# 3. Creăm scriptul executabil global care va porni aplicația din terminal prin comanda 'netjar'
cat << 'EOB' > $DIR_CONSTRUCTIE/usr/bin/netjar
#!/bin/bash
cd /usr/share/netjar-montool/
python3 netjar_main.py "$@"
EOB

# Acordăm permisiuni de execuție pentru binarul global
chmod +x $DIR_CONSTRUCTIE/usr/bin/netjar

# 4. Generăm pachetul fizic .deb folosind instrumentele native Debian
dpkg-deb --build $DIR_CONSTRUCTIE

# Redenumim pachetul conform standardului curat
mv ${DIR_CONSTRUCTIE}.deb ${NUME_PACHET}_${VERSIUNE}_amd64.deb

# Curățăm folderul temporar de lucru
rm -rf $DIR_CONSTRUCTIE

echo "🚀 Succes! Pachetul oficial a fost generat: ${NUME_PACHET}_${VERSIUNE}_amd64.deb"
