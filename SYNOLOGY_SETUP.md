# DMARC Analyzer - Synology NAS Setup Guide (Container Manager)

Diese Anleitung zeigt, wie Sie den DMARC Analyzer über die grafische Oberfläche des Synology **Container Managers** deployen.

## Voraussetzungen

1. **Synology DSM 7.x** mit installiertem **Container Manager**
2. **SSH-Zugang aktiviert** (Systemsteuerung → Terminal & SNMP → Terminal aktivieren)
3. **Git installiert** (optional, siehe Alternative unten)
4. Ihre **Zugangsdaten** bereit:
   - IMAP (mail.einsle.cloud)
   - Anthropic API Key
   - AWS SES SMTP Credentials

## Option 1: Setup mit SSH (Empfohlen)

### Schritt 1: SSH-Verbindung herstellen

```bash
ssh admin@<synology-ip>
```

### Schritt 2: Repository klonen

```bash
cd /volume1/docker
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

### Schritt 3: .env Datei erstellen

```bash
cp .env.example .env
nano .env  # oder vi .env
```

Tragen Sie Ihre echten Zugangsdaten ein:

```env
# IMAP Configuration
IMAP_HOST=mail.einsle.cloud
IMAP_PORT=993
IMAP_USER=dmarc-reports@einsle.cloud
IMAP_PASSWORD=IHR_ECHTES_PASSWORT

# Claude API
ANTHROPIC_API_KEY=sk-ant-api03-IHR_ECHTER_KEY

# AWS SES SMTP
SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=IHR_SES_USER
SMTP_PASSWORD=IHR_SES_PASSWORD
SMTP_FROM=dmarc-reports@einsle.cloud
ALERT_RECIPIENT=robert@einsle.com

# Optional
SCHEDULER_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

Speichern mit `Ctrl+O`, `Enter`, `Ctrl+X` (nano) oder `:wq` (vi).

### Schritt 4: Container Manager öffnen

1. DSM → **Container Manager** öffnen
2. Links zu **Projekt** wechseln
3. Klick auf **Erstellen**

### Schritt 5: Projekt erstellen

1. **Projektnamen** vergeben: `dmarc-analyzer`
2. **Pfad** angeben: `/volume1/docker/dmarc-reports-mail`
3. **Quelle**: `docker-compose.yml` verwenden
4. Klick auf **Weiter**

### Schritt 6: Web Portal-Einstellungen (optional)

Falls Sie Web Portal Zugriff über die Synology-Oberfläche wünschen:

1. **Web-Portal aktivieren** aktivieren
2. **HTTPS** auswählen
3. Klick auf **Weiter**

### Schritt 7: Projekt starten

1. Zusammenfassung prüfen
2. Klick auf **Fertig**
3. Container Manager startet automatisch das Projekt

### Schritt 8: Deployment prüfen

1. Im Container Manager unter **Container** sollte `dmarc-analyzer` als "Running" erscheinen
2. Dashboard öffnen: `http://<synology-ip>:3551`
3. Health-Check: `http://<synology-ip>:3551/health`

## Option 2: Setup ohne Git (File Station)

Falls Git nicht verfügbar ist, können Sie die Dateien manuell hochladen:

### Schritt 1: Repository als ZIP herunterladen

Auf Ihrem PC:
1. https://github.com/roberteinsle/dmarc-reports-mail
2. **Code** → **Download ZIP**
3. ZIP entpacken

### Schritt 2: Dateien hochladen

1. DSM → **File Station** öffnen
2. Ordner `/docker` erstellen (falls nicht vorhanden)
3. In `/docker` den Ordner `dmarc-reports-mail` erstellen
4. Alle entpackten Dateien in `/docker/dmarc-reports-mail/` hochladen

### Schritt 3: .env Datei erstellen

1. Auf Ihrem PC: `.env.example` zu `.env` umbenennen
2. `.env` mit Texteditor öffnen und echte Credentials eintragen
3. `.env` via File Station hochladen (überschreibt die Beispieldatei)

**WICHTIG:** Die `.env` Datei MUSS im Hauptverzeichnis `/volume1/docker/dmarc-reports-mail/` liegen!

### Schritt 4: Container Manager Setup

Wie bei Option 1, Schritt 4-8.

## Troubleshooting

### Problem: "unable to prepare context: unable to evaluate symlinks in Dockerfile path"

**Ursache:** Dockerfile-Pfad in `docker-compose.yml` ist falsch oder Dateien fehlen.

**Lösung:**
1. Prüfen, ob alle Dateien hochgeladen wurden
2. SSH-Zugang: `ls -la /volume1/docker/dmarc-reports-mail/docker/`
3. Dockerfile MUSS existieren: `/volume1/docker/dmarc-reports-mail/docker/Dockerfile`
4. docker-compose.yml prüfen:
```yaml
build:
  context: .
  dockerfile: docker/Dockerfile
```

### Problem: Container startet nicht

**Lösung:**
1. Container Manager → Container → `dmarc-analyzer` → **Details** → **Log**
2. Fehlermeldung analysieren
3. Häufige Fehler:
   - Fehlende Umgebungsvariablen (`.env` prüfen)
   - Port 3551 bereits belegt (anderen Port in `docker-compose.yml` verwenden)
   - Berechtigungsprobleme (Dateirechte prüfen)

### Problem: Dashboard nicht erreichbar (http://<ip>:3551)

**Lösung:**
1. Firewall-Regel für Port 3551 erstellen:
   - Systemsteuerung → Sicherheit → Firewall
   - Port 3551 freigeben
2. Container-Status prüfen (muss "Running" sein)
3. Health-Check testen: `curl http://localhost:3551/health` (via SSH)

### Problem: IMAP/SMTP Verbindung schlägt fehl

**Lösung:**
1. `.env` Datei prüfen (keine Tippfehler in Credentials)
2. Container neu starten (Container Manager → Container → Neustart)
3. Logs prüfen auf IMAP-Fehler
4. Firewall: Port 993 (IMAP) und 587 (SMTP) müssen ausgehend erlaubt sein

## Logs anschauen

### Via Container Manager GUI
1. Container Manager → Container → `dmarc-analyzer`
2. **Details** → **Log**
3. Echtzeit-Logs mit Auto-Scroll

### Via SSH
```bash
cd /volume1/docker/dmarc-reports-mail
docker-compose logs -f
```

### Log-Dateien
Logs werden auch persistiert in `/volume1/docker/dmarc-reports-mail/logs/`:
- `app.log` - Alle Events
- `error.log` - Nur Errors

## Container verwalten

### Container stoppen
Container Manager → Container → `dmarc-analyzer` → **Aktion** → **Stopp**

Oder via SSH:
```bash
cd /volume1/docker/dmarc-reports-mail
docker-compose stop
```

### Container neu starten
Container Manager → Container → `dmarc-analyzer` → **Aktion** → **Neustart**

Oder via SSH:
```bash
cd /volume1/docker/dmarc-reports-mail
docker-compose restart
```

### Container löschen
Container Manager → Container → `dmarc-analyzer` → **Aktion** → **Löschen**

**ACHTUNG:** Datenbank bleibt erhalten (Docker Volume), Container kann neu erstellt werden.

### Container neu bauen (nach Code-Updates)
```bash
cd /volume1/docker/dmarc-reports-mail
git pull  # Repository aktualisieren
docker-compose down  # Container stoppen und löschen
docker-compose build --no-cache  # Neu bauen
docker-compose up -d  # Starten
```

## Backup der Datenbank

### Via SSH
```bash
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db /volume1/docker/dmarc-reports-mail/backup_$(date +%Y%m%d).db
```

### Automatisches Backup (Synology Task Scheduler)
1. Systemsteuerung → Aufgabenplanung
2. **Erstellen** → **Geplante Aufgabe** → **Benutzerdefiniertes Script**
3. Script:
```bash
#!/bin/bash
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db /volume1/backups/dmarc_backup_$(date +%Y%m%d).db
```
4. Zeitplan: Täglich um 3:00 Uhr

## Updates einspielen

```bash
cd /volume1/docker/dmarc-reports-mail
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Support

Bei Problemen:
1. Logs prüfen (Container Manager → Log)
2. Health-Check prüfen (`http://<ip>:3551/health`)
3. GitHub Issues: https://github.com/roberteinsle/dmarc-reports-mail/issues
