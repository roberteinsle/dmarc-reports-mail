# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projektübersicht

DMARC Reports Mail Analyzer - Eine Python-Flask-Anwendung, die automatisch DMARC-E-Mail-Berichte abruft, sie mit Claude AI analysiert und bei Problemen Warnungen versendet.

**Kerntechnologien:**
- Python 3.11+ mit Flask-Webframework
- SQLite-Datenbank mit SQLAlchemy ORM
- APScheduler für Hintergrund-Jobs (5-Minuten-Intervall)
- Anthropic Claude API für intelligente Analyse
- IMAP für E-Mail-Abruf, AWS SES SMTP für Warnungen
- Docker-Deployment über Coolify (Docker Compose aus Git)

## Wichtige Befehle

### Entwicklung

```bash
# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Anwendung lokal starten
python run.py

# Tests ausführen
pytest                                    # Alle Tests
pytest tests/test_parser_service.py       # Bestimmte Testdatei
pytest -k test_function_name              # Bestimmter Test
pytest --cov=app --cov-report=html        # Mit Coverage-Bericht

# Datenbank-Migrationen
alembic upgrade head
alembic revision --autogenerate -m "beschreibung"
```

### Docker/Produktion

```bash
# Bauen und starten
docker-compose build
docker-compose up -d

# Logs ansehen
docker-compose logs -f

# Dienste neustarten
docker-compose restart

# Dienste stoppen
docker-compose down

# Befehle im Container ausführen
docker exec -it dmarc-analyzer bash
```

## Architekturübersicht

### Verarbeitungspipeline

Die Anwendung folgt diesem Ablauf alle 5 Minuten (orchestriert durch `scheduler_service.py`):

1. **IMAP Service** (`app/services/imap_service.py`): Verbindung zum IMAP-Server, ungelesene E-Mails abrufen
2. **Parser Service** (`app/services/parser_service.py`): XML-Anhänge extrahieren, .gz/.zip dekomprimieren, DMARC-XML-Struktur parsen
3. **Datenbankschicht** (`app/models/database.py`): Report- und Record-Einträge in SQLite speichern
4. **Claude Service** (`app/services/claude_service.py`): Berichtsdaten an Claude API zur Analyse senden
5. **Alert Service** (`app/services/alert_service.py`): Warnungskriterien auswerten, E-Mail über AWS SES senden
6. **IMAP Service**: Verarbeitete E-Mail ins Archiv verschieben
7. **Verarbeitungsprotokoll**: Ergebnisse in `processing_log`-Tabelle protokollieren

### Datenbankschema

**Vier Haupttabellen:**

- `reports` - DMARC-Berichtsmetadaten, veröffentlichte Richtlinie, Claude-Analyse (JSON), Status
- `records` - Einzelne Authentifizierungsergebnisse pro Quell-IP (SPF/DKIM/DMARC-Disposition)
- `alerts` - Generierte Warnungen mit Schweregrad, Typ, E-Mail-Tracking
- `processing_log` - Audit-Trail aller Job-Ausführungen

**Beziehungen:**
- Report → Records (1:n, Kaskaden-Löschung)
- Report → Alerts (1:n, Kaskaden-Löschung)

### Dienstverantwortlichkeiten

**IMAPService** (`imap_service.py`):
- Verwaltet IMAP4_SSL-Verbindungslebenszyklus
- Sucht nach ungelesenen E-Mails
- Extrahiert und dekomprimiert Anhänge (.gz, .zip)
- Verschiebt verarbeitete E-Mails ins Archiv
- Als Context-Manager für automatische Bereinigung nutzbar

**DMARCParserService** (`parser_service.py`):
- Parst DMARC-XML (RFC 7489 Format)
- Extrahiert: report_metadata, policy_published, records
- Validiert XML-Struktur
- Gibt Dict passend zum Datenbankschema zurück

**ClaudeService** (`claude_service.py`):
- Formatiert Analyse-Prompts mit Berichtsstatistiken
- Ruft Claude API auf (Modell: claude-sonnet-4-5-20250929)
- Implementiert Retry-Logik mit exponentiellem Backoff bei Rate-Limits
- Gibt JSON zurück mit: summary, severity, no_action_required, sources (IP→Dienst-Zuordnung), failures, spoofing_attempts (mit abuseipdb_worthy), action_items (priority/title/description/steps), positive_findings
- Infrastruktur-Kontext (bekannte IPs/Dienste) ist fest im Prompt kodiert — bei Änderungen `_format_prompt()` aktualisieren
- Analyse wird auf Deutsch angefordert

**AlertService** (`alert_service.py`):
- Wertet Warnungskriterien basierend auf Records + Claude-Analyse aus
- Löst aus bei: DMARC-Fehlern (quarantine/reject), SPF/DKIM-Fehlern (>5 Stück), nicht autorisierten Quellen, verdächtigen Mustern
- Formatiert HTML- und Klartext-E-Mail-Warnungen (auf Deutsch)
- Sendet über AWS SES SMTP mit STARTTLS
- Implementiert Drosselung (60-Minuten-Fenster pro Warnungstyp)

**IPUtils** (`app/utils/ip_utils.py`):
- Reverse-DNS-Lookup für IP-Adressen
- Erkennt E-Mail-Anbieter anhand des Hostnamens (Google, Microsoft, Amazon SES, SendGrid, etc.)
- Reverse-DNS wird beim Verarbeiten geholt und in `records.source_hostname` gespeichert

**SchedulerService** (`scheduler_service.py`):
- Initialisiert APScheduler BackgroundScheduler
- Orchestriert gesamte Pipeline in `process_dmarc_reports()`
- Behandelt Fehler robust (DB-Rollback, Fehler loggen)
- Scheduler darf niemals abstürzen, auch wenn einzelne Jobs fehlschlagen

### Konfigurationsverwaltung

**Drei Config-Klassen** in `app/config.py`:
- `DevelopmentConfig` - DEBUG=True, lokale SQLite
- `ProductionConfig` - DEBUG=False, Docker-Volume SQLite
- `TestingConfig` - In-Memory SQLite, überspringt Validierung

**Erforderliche Umgebungsvariablen** (werden beim Start validiert):
- IMAP_HOST, IMAP_USER, IMAP_PASSWORD
- ANTHROPIC_API_KEY
- SMTP_HOST, SMTP_USER, SMTP_PASSWORD
- ALERT_RECIPIENT
- AUTH_USERNAME, AUTH_PASSWORD

Alle Zugangsdaten über `.env`-Datei (Entwicklung) oder Docker ENV-Variablen (Produktion) - **NIEMALS hartcodiert**.

### Authentifizierung (Username/Passwort)

Die App ist per Username/Passwort geschützt (`app/auth.py`):
- Benutzer gibt Benutzernamen + Passwort ein → Vergleich mit `AUTH_USERNAME`/`AUTH_PASSWORD` via `hmac.compare_digest` (Timing-sicher)
- Bei Erfolg wird eine Flask-Session erstellt (7 Tage gültig)
- Alle Routen sind geschützt außer `/health`, `/auth/*` und `/static/`
- `before_request`-Hook in `app/__init__.py` prüft die Session

### Web-Dashboard

**Routen** (`app/routes/dashboard.py`) — alle geschützt per Magic-Link-Auth:
- `/` - Dashboard-Übersicht mit Statistik-Karten und manuellem Auslöser
- `/reports` - Paginierte Berichtsliste mit Schweregrad-Spalte
- `/reports/<id>` - Detailansicht eines Berichts mit Claude-Analyse
- `/alerts` - Warnungsverlauf mit Schweregrad-Filter
- `/tools/dkim-selectors` - DKIM-Selektor-Abfrage mit DNS-Prüfung
- `/api/stats` - JSON-Endpunkt für Diagrammdaten
- `/api/trigger-processing` - POST-Endpunkt zum manuellen Auslösen der Verarbeitung
- `/health` - Health-Check (200=gesund, 503=ungesund) — **ohne Auth**

**Auth-Routen** (`app/auth.py`):
- `/auth/login` - Anmeldeseite (E-Mail eingeben)
- `/auth/verify?token=...` - Magic-Link-Verifizierung
- `/auth/logout` - Abmelden

**Templates** verwenden Bootstrap 5 mit benutzerdefinierter Schweregrad-Farbgebung. **Die gesamte UI ist auf Deutsch.**

**Manuelle Verarbeitung**: Der Scheduler läuft automatisch alle 5 Minuten UND sofort beim App-Start. Benutzer können die Verarbeitung auch manuell über den "Berichte jetzt verarbeiten"-Button im Dashboard auslösen.

## Häufige Entwicklungsaufgaben

### Neues Warnungskriterium hinzufügen

1. `AlertService.evaluate_alert_criteria()` in `alert_service.py` bearbeiten
2. Erkennungslogik für neues Kriterium hinzufügen
3. An `alerts`-Liste mit Typ, Schweregrad, Nachricht anhängen
4. Warnungstyp-Enum bei Bedarf aktualisieren

### DMARC-XML-Parsing ändern

1. `DMARCParserService._extract_*()` Methoden in `parser_service.py` aktualisieren
2. Bei neuen Feldern: `Report` oder `Record` Model in `database.py` aktualisieren
3. Alembic-Migration erstellen: `alembic revision --autogenerate -m "feld hinzufügen"`
4. Mit Beispiel-XML in `tests/fixtures/` testen

### Scheduler-Intervall ändern

`SCHEDULER_INTERVAL_MINUTES` in `.env`-Datei aktualisieren (keine Code-Änderungen nötig).

### Claude-Analyse-Prompt anpassen

`ClaudeService._format_prompt()` in `claude_service.py` bearbeiten. Der Prompt erhält:
- Berichtsmetadaten (Domain, Absender, Daten)
- Aggregierte Statistiken (E-Mails gesamt, SPF/DKIM-Fehler, Dispositionen)
- Top 10 Records (um Tokens zu sparen)

### Datenbankindizes hinzufügen

1. Model in `database.py` bearbeiten, `index=True` zur Spalte hinzufügen
2. Migration generieren: `alembic revision --autogenerate -m "index hinzufügen"`
3. Anwenden: `alembic upgrade head`

## Wichtige Dateipfade

- **Konfiguration**: `app/config.py`, `.env.example`
- **Datenbankmodelle**: `app/models/database.py`
- **Authentifizierung**: `app/auth.py`
- **Kern-Services**: `app/services/{imap,parser,claude,alert,scheduler}_service.py`
- **Routen**: `app/routes/dashboard.py`
- **Templates**: `app/templates/*.html`
- **Logging**: `app/utils/logger.py` — rotating file handler (logs/app.log + logs/error.log, je 10MB×5)
- **Einstiegspunkt**: `run.py`
- **Docker**: `docker/Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yaml`
- **Migrationen**: `migrations/env.py`, `alembic.ini`
- **Einmalskripte**: `scripts/migrate_old_reports.py`

## Sicherheitsaspekte

1. **Zugangsdaten**: `.env`-Datei niemals committen. `.gitignore` enthält `.env`
2. **Docker-Sicherheit**:
   - Container startet als root nur um Docker-Volume-Berechtigungen zu korrigieren
   - Nutzt `gosu` um Rechte auf nicht-root `appuser` (UID 1000) zu reduzieren
   - Anwendungsprozess läuft als `appuser`
   - Entrypoint-Skript korrigiert `/app/data` und `/app/logs` Eigentumsrechte beim Start
3. **Datenbank**: SQLite mit parametrisierten Abfragen über SQLAlchemy (SQL-Injection-sicher)
4. **Logging**: Niemals Passwörter/API-Keys loggen. Sensible Daten in Fehlermeldungen reduzieren
5. **IMAP/SMTP**: Immer SSL/TLS (Port 993) und STARTTLS (Port 587) verwenden
6. **Flask Security Headers**: Gesetzt in `app/__init__.py` (X-Frame-Options, X-XSS-Protection, etc.)
7. **Authentifizierung**: Magic-Link per E-Mail, Session-basiert, Anti-Enumeration bei Login

## Fehlerbehandlungsmuster

**Service-Ebene**:
```python
try:
    # IMAP/SMTP/API-Operationen
except SpecificError as e:
    logger.error(f"Kontext: {e}", exc_info=True)
    log_processing_error('job_type', str(e))
    raise or return None
finally:
    cleanup_resources()
```

**Scheduler-Jobs**: Dürfen den Scheduler niemals abstürzen lassen
```python
try:
    process_dmarc_reports()
except Exception as e:
    logger.error(f"Job fehlgeschlagen: {e}", exc_info=True)
    # Nicht erneut auslösen, nur loggen
```

**Datenbankoperationen**: Rollback bei Fehler
```python
try:
    db.session.add(obj)
    db.session.commit()
except IntegrityError:
    db.session.rollback()
    # Duplikat behandeln
```

## Teststrategie

**Fixtures**: Beispiel-DMARC-XML in `tests/fixtures/sample_dmarc_report.xml`

**Mocking**: `pytest-mock` für externe Dienste (IMAP, Claude API, SMTP) verwenden

**Datenbank**: In-Memory SQLite für Tests (TestingConfig) verwenden

**Aktueller Stand**: Nur `tests/test_parser_service.py` existiert. Tests für IMAP, Claude und Alert-Service fehlen noch.

**Wichtige Testbereiche**:
- Parser: Gültiges/ungültiges XML, fehlende Felder, fehlerhafte Daten
- IMAP: Verbindungshandling, Anhang-Extraktion, Dekomprimierung
- Claude: Prompt-Formatierung, Antwort-Parsing, Rate-Limit-Handling
- Warnungen: Kriterienauswertung, E-Mail-Formatierung, Drosselung

## Deployment-Hinweise

**Coolify-Deployment**:
- Anwendung läuft intern auf Port 5000; Coolifys Traefik-Proxy übernimmt externes Routing und SSL
- Daten persistent in Docker-Volume `dmarc-data`
- Logs persistent in Docker-Volume `logs`
- Health-Check-Endpunkt `/health` für Monitoring (gibt 200 bei gesund, 503 bei ungesund zurück)
- Container-Name: `dmarc-analyzer`
- Als **Docker Compose** Ressource in Coolify deployen, auf das Git-Repository zeigen

**Sicherheitsmodell**:
- Container startet als root um Docker-Volume-Berechtigungen zu korrigieren
- Nutzt `gosu` um auf nicht-root `appuser` (UID 1000) zu wechseln
- Entrypoint korrigiert `/app/data` und `/app/logs` Eigentumsrechte beim Start
- Anwendung läuft als `appuser`

**Umgebungsvariablen** müssen vor dem ersten Start gesetzt sein - App validiert beim Start und bricht sofort ab wenn etwas fehlt.

**Datenbank-Migrationen** laufen automatisch über `entrypoint.sh` beim Container-Start.

**Coolify-Setup**:
- Docker Compose Ressource in Coolify erstellen, Git-Repository verbinden
- Erforderliche Umgebungsvariablen in den Coolify-Ressourceneinstellungen setzen
- Domain + Port 5000 in Coolify konfigurieren; SSL über Let's Encrypt ist automatisch
- Siehe `COOLIFY_DEPLOYMENT.md` für detaillierte Setup-Anweisungen

## Debugging-Tipps

1. **Scheduler läuft nicht**: Logs auf Scheduler-Initialisierungsfehler prüfen
2. **IMAP-Verbindung schlägt fehl**: IMAP-Zugangsdaten und Serververbindung überprüfen
3. **Claude-API-Fehler**: API-Key, Rate-Limits, Anthropic-Statusseite prüfen
4. **Keine Warnungen erhalten**: Warnungskriterien, Drosselungsfenster (60 Min), SMTP-Logs prüfen
5. **Datenbankfehler**: Volume-Berechtigungen, SQLite-Dateizugriff prüfen
6. **Container stürzt ab**: Health-Endpunkt, Ressourcenlimits, Logs prüfen
7. **Coolify-Deployment-Probleme**: Coolify-Deployment-Logs, Umgebungsvariablen und Volume-Mounts prüfen
8. **Domain nicht erreichbar**: Domain/Port-Konfiguration in Coolify und Traefik-Proxy-Status prüfen

---

**Hinweis**: Diese Anwendung verarbeitet E-Mails automatisch und versendet Warnungen. Änderungen immer gründlich in der Entwicklungsumgebung testen bevor sie in Produktion deployt werden. `.env.example` als Vorlage verwenden und niemals echte Zugangsdaten committen.
