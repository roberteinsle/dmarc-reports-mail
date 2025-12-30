# DMARC Reports Mail Analyzer

Automatisierte DMARC-Report-Verarbeitung mit Claude AI-Analyse und E-Mail-Benachrichtigungen.

## Features

- **Automatischer IMAP-Abruf**: Holt DMARC-Reports alle 5 Minuten von IMAP-Server
- **XML-Parsing**: Verarbeitet Standard-DMARC-Reports (XML, .gz, .zip)
- **Claude AI-Analyse**: Intelligente Analyse mit Anthropic's Claude API
- **Alert-System**: E-Mail-Benachrichtigungen bei kritischen Problemen via AWS SES
- **Web-Dashboard**: Flask-basiertes Dashboard zur Visualisierung
- **Docker-Ready**: Läuft als Container auf Synology NAS oder anderen Plattformen
- **SQLite-Datenbank**: Persistente Speicherung aller Reports und Analysen

## Voraussetzungen

- Python 3.11+ (für lokale Entwicklung)
- Docker & Docker Compose (für Production)
- IMAP-Zugang für DMARC-Reports
- Anthropic API Key (Claude AI)
- AWS SES SMTP-Credentials (für Alert-E-Mails)

## Installation

### Lokale Entwicklung

1. Repository klonen:
```bash
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

2. Virtuelle Umgebung erstellen:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows
```

3. Dependencies installieren:
```bash
pip install -r requirements.txt
```

4. `.env` Datei erstellen:
```bash
cp .env.example .env
# Bearbeiten Sie .env und tragen Sie Ihre Credentials ein
```

5. Datenbank initialisieren:
```bash
python
>>> from app import create_app
>>> from app.models.database import db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

6. Anwendung starten:
```bash
python run.py
```

Dashboard: http://localhost:5000

### Docker Deployment (Production)

1. Repository klonen:
```bash
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

2. `.env` Datei erstellen:
```bash
cp .env.example .env
# WICHTIG: Tragen Sie ALLE echten Credentials ein!
```

3. Docker Container bauen und starten:
```bash
docker-compose build
docker-compose up -d
```

4. Logs prüfen:
```bash
docker-compose logs -f
```

5. Dashboard öffnen:
```
http://<server-ip>:5000
```

6. Health-Check:
```
http://<server-ip>:5000/health
```

### Deployment auf Synology NAS

1. SSH-Zugang aktivieren (Systemsteuerung > Terminal & SNMP)
2. Per SSH verbinden: `ssh admin@<synology-ip>`
3. Repository in gewünschtes Verzeichnis klonen
4. `.env` Datei mit echten Credentials erstellen
5. Docker Compose installieren (falls nicht vorhanden)
6. Container starten: `docker-compose up -d`

## Konfiguration

Alle Konfigurationen erfolgen über Umgebungsvariablen in der `.env` Datei:

### Erforderliche Umgebungsvariablen

```env
# IMAP Configuration
IMAP_HOST=mail.einsle.cloud
IMAP_PORT=993
IMAP_USER=dmarc-reports@einsle.cloud
IMAP_PASSWORD=<your-password>

# Claude API
ANTHROPIC_API_KEY=<your-anthropic-api-key>

# AWS SES SMTP
SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=<your-ses-smtp-user>
SMTP_PASSWORD=<your-ses-smtp-password>
SMTP_FROM=dmarc-reports@einsle.cloud
ALERT_RECIPIENT=robert@einsle.com

# Optional
SCHEDULER_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

## Verwendung

### Dashboard

- **/**  - Übersicht mit Statistiken
- **/reports** - Liste aller verarbeiteten Reports
- **/reports/<id>** - Detailansicht eines Reports
- **/alerts** - Alert-Historie mit Filterung
- **/health** - Health-Check-Endpoint

### API Endpoints

- `GET /api/stats` - JSON-Statistiken für Charts
- `GET /health` - Health-Status (200 = healthy, 503 = unhealthy)

### Alert-Kriterien

Alerts werden automatisch versendet bei:

1. **DMARC-Failures**: E-Mails mit disposition = quarantine/reject
2. **SPF-Failures**: > 5 E-Mails mit SPF fail
3. **DKIM-Failures**: > 5 E-Mails mit DKIM fail
4. **Unautorisierte Sender**: Von Claude AI erkannte unbekannte Quellen
5. **Anomalien**: Von Claude AI erkannte verdächtige Muster

## Testing

Tests ausführen:
```bash
pytest
```

Mit Coverage:
```bash
pytest --cov=app --cov-report=html
```

## Monitoring

### Health Check

```bash
curl http://localhost:5000/health
```

Antwort:
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running",
  "last_check": "2025-12-30T10:30:00.000Z"
}
```

### Logs

Logs befinden sich in `logs/`:
- `app.log` - Alle Application-Events
- `error.log` - Nur Errors und Critical

In Docker:
```bash
docker-compose logs -f
```

### Datenbank-Backup

SQLite-Datenbank befindet sich in Docker Volume `dmarc-data`.

Backup erstellen:
```bash
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup_$(date +%Y%m%d).db
```

## Troubleshooting

### Problem: Scheduler läuft nicht

Lösung: Logs prüfen, evtl. Container neu starten:
```bash
docker-compose restart
docker-compose logs -f
```

### Problem: IMAP-Verbindung schlägt fehl

Lösung:
- IMAP-Credentials in `.env` prüfen
- Firewall-Einstellungen prüfen (Port 993)
- IMAP-Server-Erreichbarkeit testen: `telnet mail.einsle.cloud 993`

### Problem: Claude API-Fehler

Lösung:
- API-Key in `.env` prüfen
- Rate-Limits prüfen (App hat Retry-Logic)
- Anthropic-Status-Page prüfen

### Problem: Keine Alerts erhalten

Lösung:
- SMTP-Credentials in `.env` prüfen
- Alert-Kriterien im Code prüfen
- Alert-Throttling (60 Min) beachten
- Logs auf SMTP-Fehler prüfen

## Sicherheitshinweise

- **NIEMALS** `.env` Datei committen!
- **NIEMALS** echte Credentials in Code hardcoden!
- Regelmäßig Docker Images updaten
- Starke Passwörter verwenden
- IMAP/SMTP nur über verschlüsselte Verbindungen (SSL/TLS)

## Lizenz

Dieses Projekt ist für den privaten Gebrauch bestimmt.

## Support

Bei Problemen:
1. Logs prüfen (`docker-compose logs -f`)
2. Health-Endpoint prüfen (`/health`)
3. GitHub Issues erstellen: https://github.com/roberteinsle/dmarc-reports-mail/issues

## Entwickler

Robert Einsle (robert@einsle.com)
