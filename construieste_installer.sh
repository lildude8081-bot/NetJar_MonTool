#!/bin/bash
# Script de împachetare nativă .deb cu descriere completă și actualizare cache meniu

NUME_PACHET="netjar-montool"
VERSIUNE="1.0.0"
DIR_CONSTRUCTIE="DEBIAN_BUILD"

echo "📦 Începe împachetarea pentru ${NUME_PACHET}_${VERSIUNE}..."

rm -rf $DIR_CONSTRUCTIE
rm -f ${NUME_PACHET}_${VERSIUNE}_amd64.deb

# Creăm structura oficială de directoare Linux
mkdir -p $DIR_CONSTRUCTIE/DEBIAN
mkdir -p $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/gui
mkdir -p $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/assets
mkdir -p $DIR_CONSTRUCTIE/usr/bin
mkdir -p $DIR_CONSTRUCTIE/usr/share/applications
mkdir -p $DIR_CONSTRUCTIE/usr/share/pixmaps

# 1. Control Debian
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

# 2. Copiem codul și imaginea icoanei create de Mihai
cp netjar_main.py $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/
cp gui/*.py $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/gui/
if [ -f assets/netjar_icon.png ]; then
    cp assets/netjar_icon.png $DIR_CONSTRUCTIE/usr/share/$NUME_PACHET/assets/
    # Copiem icoana în directorul global de pixmaps pentru sistemul grafic
    cp assets/netjar_icon.png $DIR_CONSTRUCTIE/usr/share/pixmaps/netjar-montool.png
fi

# 3. Creăm scriptul executabil global
cat << 'EOB' > $DIR_CONSTRUCTIE/usr/bin/netjar
#!/bin/bash
cd /usr/share/netjar-montool/
python3 netjar_main.py "$@"
EOB
chmod +x $DIR_CONSTRUCTIE/usr/bin/netjar

# 4. FIȘIERUL .DESKTOP ACTUALIZAT CU OPȚIUNEA CERUTĂ DE TINE!
cat << 'EOD' > $DIR_CONSTRUCTIE/usr/share/applications/netjar-montool.desktop
[Desktop Entry]
Version=1.0
Type=Application
Name=Linux NetJar MonTool
Comment=Network Monitor and Utility Tool
Exec=netjar
Icon=netjar-montool
Terminal=false
Categories=Utility;Network;
EOD

# Generăm pachetul fizic .deb
dpkg-deb --build $DIR_CONSTRUCTIE
mv ${DIR_CONSTRUCTIE}.deb ${NUME_PACHET}_${VERSIUNE}_amd64.deb
rm -rf $DIR_CONSTRUCTIE

echo "🚀 Succes! Pachetul cu denumirea Linux NetJar MonTool a fost generat!"
