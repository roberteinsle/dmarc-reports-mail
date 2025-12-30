#!/bin/bash
# DMARC Analyzer - Automatische Installation für Synology NAS
# Führen Sie dieses Script per SSH auf Ihrer Synology aus:
# bash <(curl -s https://raw.githubusercontent.com/roberteinsle/dmarc-reports-mail/main/INSTALL_SYNOLOGY.sh)

set -e  # Stop on errors

echo "=========================================="
echo "DMARC Analyzer - Synology Installation"
echo "=========================================="
echo ""

# Variablen
INSTALL_DIR="/volume1/docker/dmarc-reports-mail"
REPO_URL="https://github.com/roberteinsle/dmarc-reports-mail.git"

# Prüfen ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker ist nicht installiert!"
    echo "Bitte installieren Sie den Container Manager über das Synology Package Center."
    exit 1
fi

# Prüfen ob docker-compose installiert ist
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose ist nicht installiert!"
    echo "Bitte installieren Sie docker-compose über SSH:"
    echo "sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
    echo "sudo chmod +x /usr/local/bin/docker-compose"
    exit 1
fi

# Verzeichnis erstellen
echo "1. Erstelle Installationsverzeichnis..."
mkdir -p "$(dirname "$INSTALL_DIR")"

# Repository klonen oder aktualisieren
if [ -d "$INSTALL_DIR" ]; then
    echo "2. Repository existiert bereits. Aktualisiere..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "2. Klone Repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# .env Datei erstellen falls nicht vorhanden
if [ ! -f .env ]; then
    echo "3. Erstelle .env Datei aus Template..."
    cp .env.example .env

    echo ""
    echo "=========================================="
    echo "WICHTIG: .env Datei konfigurieren!"
    echo "=========================================="
    echo ""
    echo "Die .env Datei wurde unter $INSTALL_DIR/.env erstellt."
    echo ""
    echo "Bitte bearbeiten Sie diese Datei und tragen Sie Ihre echten Credentials ein:"
    echo ""
    echo "  nano $INSTALL_DIR/.env"
    echo ""
    echo "Erforderliche Variablen:"
    echo "  - IMAP_PASSWORD (Ihr IMAP-Passwort)"
    echo "  - ANTHROPIC_API_KEY (Ihr Claude API Key)"
    echo "  - SMTP_USER (AWS SES SMTP User)"
    echo "  - SMTP_PASSWORD (AWS SES SMTP Passwort)"
    echo ""
    echo "Nach dem Bearbeiten führen Sie aus:"
    echo "  cd $INSTALL_DIR"
    echo "  docker-compose build"
    echo "  docker-compose up -d"
    echo ""
    echo "Dashboard: http://$(hostname -I | awk '{print $1}'):3551"
    echo ""
else
    echo "3. .env Datei existiert bereits (nicht überschrieben)"

    # Container bauen und starten
    echo "4. Baue Docker Container..."
    docker-compose build

    echo "5. Starte Container..."
    docker-compose up -d

    echo ""
    echo "=========================================="
    echo "Installation erfolgreich!"
    echo "=========================================="
    echo ""
    echo "Dashboard: http://$(hostname -I | awk '{print $1}'):3551"
    echo "Health-Check: http://$(hostname -I | awk '{print $1}'):3551/health"
    echo ""
    echo "Logs anschauen:"
    echo "  cd $INSTALL_DIR"
    echo "  docker-compose logs -f"
    echo ""
    echo "Container verwalten:"
    echo "  docker-compose stop     # Stoppen"
    echo "  docker-compose start    # Starten"
    echo "  docker-compose restart  # Neu starten"
    echo ""
fi
