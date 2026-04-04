# DMARC Reports Mail Analyzer

Automatische DMARC-Berichtsverarbeitung mit Claude-KI-Analyse und E-Mail-Benachrichtigungen.

## Funktionen

- **Automatischer IMAP-Abruf**: Ruft DMARC-Berichte alle 5 Minuten vom IMAP-Server ab
- **XML-Parsing**: Verarbeitet Standard-DMARC-Berichte (XML, .gz, .zip)
- **Claude-KI-Analyse**: Intelligente Analyse mit Anthropics Claude API (Ausgabe auf Deutsch)
- **Warnsystem**: E-Mail-Benachrichtigungen bei kritischen Problemen über AWS SES
- **Web-Dashboard**: Flask-basiertes Dashboard zur Visualisierung (komplett auf Deutsch)
- **DKIM-Selektor-Tool**: Zeigt alle DKIM-Selektoren einer Domain mit DNS-Prüfung
- **Docker-fähig**: Läuft als Container, deployed über Coolify (Docker Compose aus Git)
- **SQLite-Datenbank**: Persistente Speicherung aller Berichte und Analysen

## Voraussetzungen

- Python 3.11+ (für lokale Entwicklung)
- Docker & Docker Compose (für Produktion)
- IMAP-Zugang für DMARC-Berichte
- Anthropic API Key (Claude AI)
- AWS SES SMTP-Zugangsdaten (für Warn-E-Mails)

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

3. Abhängigkeiten installieren:
```bash
pip install -r requirements.txt
```

4. `.env`-Datei erstellen:
```bash
cp .env.example .env
# .env bearbeiten und Zugangsdaten eintragen
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

### Coolify-Deployment (Produktion)

1. **Neue Ressource erstellen** in Coolify → **Docker Compose** → Git-Repository verbinden

2. **Umgebungsvariablen konfigurieren** in den Coolify-Ressourceneinstellungen:
   ```env
   FLASK_ENV=production
   SECRET_KEY=<sicheren-schlüssel-generieren>
   DATABASE_URL=sqlite:////app/data/dmarc_reports.db

   # IMAP-Konfiguration
   IMAP_HOST=<dein-imap-host>
   IMAP_PORT=993
   IMAP_USER=<dein-imap-benutzer>
   IMAP_PASSWORD=<dein-imap-passwort>
   IMAP_FOLDER=INBOX

   # Claude API
   ANTHROPIC_API_KEY=<dein-anthropic-api-key>

   # AWS SES SMTP
   SMTP_HOST=<dein-smtp-host>
   SMTP_PORT=587
   SMTP_USER=<dein-smtp-benutzer>
   SMTP_PASSWORD=<dein-smtp-passwort>
   SMTP_FROM=<deine-absender-email>
   ALERT_RECIPIENT=<empfänger-email>

   # Optional
   SCHEDULER_INTERVAL_MINUTES=5
   LOG_LEVEL=INFO
   ```

3. **Domain konfigurieren**: Domain und Port `5000` in Coolify setzen — SSL über Let's Encrypt wird automatisch eingerichtet

4. **Deployen**: Coolify baut das Image, erstellt Volumes (`dmarc-data`, `logs`) und startet den Container

5. **Dashboard aufrufen**:
   - Konfigurierte Domain verwenden: `https://dmarc.deinedomain.de`
   - Health-Check: `https://dmarc.deinedomain.de/health`

**Detaillierte Deployment-Anleitung: [`COOLIFY_DEPLOYMENT.md`](COOLIFY_DEPLOYMENT.md)**

### Lokales Docker-Deployment (Entwicklung/Test)

1. Repository klonen:
```bash
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

2. `.env`-Datei erstellen:
```bash
cp .env.example .env
# .env bearbeiten und Zugangsdaten eintragen
```

3. Docker-Container bauen und starten:
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
http://localhost:5000
```

6. Health-Check:
```
http://localhost:5000/health
```

## Konfiguration

Die gesamte Konfiguration erfolgt über Umgebungsvariablen in der `.env`-Datei:

### Erforderliche Umgebungsvariablen

```env
# IMAP-Konfiguration
IMAP_HOST=mail.einsle.cloud
IMAP_PORT=993
IMAP_USER=dmarc-reports@einsle.cloud
IMAP_PASSWORD=<dein-passwort>

# Claude API
ANTHROPIC_API_KEY=<dein-anthropic-api-key>

# AWS SES SMTP
SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=<dein-ses-smtp-benutzer>
SMTP_PASSWORD=<dein-ses-smtp-passwort>
SMTP_FROM=dmarc-reports@einsle.cloud
ALERT_RECIPIENT=robert@einsle.com

# Optional
SCHEDULER_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

## Nutzung

### Dashboard

- **/** - Übersicht mit Statistiken
- **/reports** - Liste aller verarbeiteten Berichte
- **/reports/<id>** - Detailansicht eines Berichts
- **/alerts** - Warnungsverlauf mit Filterung
- **/tools/dkim-selectors** - DKIM-Selektor-Abfrage mit DNS-Status
- **/health** - Health-Check-Endpunkt

### API-Endpunkte

- `GET /api/stats` - JSON-Statistiken für Diagramme
- `GET /health` - Health-Status (200 = gesund, 503 = ungesund)

### Warnungskriterien

Warnungen werden automatisch gesendet bei:

1. **DMARC-Fehler**: E-Mails mit Disposition = quarantine/reject
2. **SPF-Fehler**: > 5 E-Mails mit SPF-Fehler
3. **DKIM-Fehler**: > 5 E-Mails mit DKIM-Fehler
4. **Nicht autorisierte Absender**: Unbekannte Quellen, identifiziert durch Claude KI
5. **Anomalien**: Verdächtige Muster, erkannt durch Claude KI

## Tests

Tests ausführen:
```bash
pytest
```

Mit Coverage:
```bash
pytest --cov=app --cov-report=html
```

## Monitoring

### Health-Check

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
- `app.log` - Alle Anwendungsereignisse
- `error.log` - Nur Fehler und kritische Meldungen

In Docker:
```bash
docker-compose logs -f
```

### Datenbank-Backup

Die SQLite-Datenbank befindet sich im Docker-Volume `dmarc-data`.

Backup erstellen:
```bash
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup_$(date +%Y%m%d).db
```

## Fehlerbehebung

### Problem: Scheduler läuft nicht

Lösung:
- Logs in Coolify oder via `docker-compose logs -f` (lokal) prüfen
- Alle Umgebungsvariablen korrekt gesetzt?
- Dienst neustarten

### Problem: IMAP-Verbindung schlägt fehl

Lösung:
- IMAP-Zugangsdaten in Umgebungsvariablen prüfen
- IMAP-Server-Verbindung überprüfen
- Logs auf spezifische Fehlermeldungen prüfen

### Problem: Claude-API-Fehler

Lösung:
- API-Key in Umgebungsvariablen überprüfen
- Rate-Limits prüfen (App hat Retry-Logik mit exponentiellem Backoff)
- Anthropic-Statusseite prüfen

### Problem: Keine Warnungen erhalten

Lösung:
- SMTP-Zugangsdaten in Umgebungsvariablen prüfen
- Warnungskriterien-Konfiguration überprüfen
- Warnung-Drosselung beachten (60-Minuten-Fenster pro Warnungstyp)
- Logs auf SMTP-Fehler prüfen

### Problem: Coolify-Deployment-Probleme

Lösung:
- Alle erforderlichen Umgebungsvariablen in Coolify-Ressourceneinstellungen gesetzt?
- Persistente Volumes korrekt erstellt?
- Coolify-Deployment-Logs im Deployments-Tab prüfen
- Health-Check-Endpunkt `/health` erreichbar?

### Problem: Domain nicht erreichbar

Lösung:
- Domain- und Port-Konfiguration in Coolify prüfen (Port muss 5000 sein)
- SSL-Zertifikat in Coolify aktiv?
- DNS zeigt auf den richtigen Server?
- Coolify-Proxy (Traefik) Status in Coolify-Einstellungen prüfen

## Sicherheitshinweise

- `.env`-Datei **NIEMALS** committen!
- Echte Zugangsdaten **NIEMALS** im Code hartcodieren!
- Docker-Images regelmäßig aktualisieren
- Starke Passwörter verwenden
- IMAP/SMTP nur über verschlüsselte Verbindungen (SSL/TLS)

## Lizenz

Dieses Projekt ist für den privaten Gebrauch bestimmt.

## Support

Bei Problemen:
1. Logs prüfen (Coolify → Ressource → Logs, oder `docker-compose logs -f` für lokal)
2. Health-Endpunkt prüfen (`/health`)
3. GitHub-Issues erstellen: https://github.com/roberteinsle/dmarc-reports-mail/issues

## Entwickler

Robert Einsle (robert@einsle.com)
