# DMARC Analyzer - Schnellstart für Synology NAS

Minimale Anleitung für schnelles Deployment auf Synology NAS via Container Manager.

## Voraussetzungen

- Synology DSM 7.x mit Container Manager
- SSH-Zugang aktiviert

## Setup in 5 Minuten

### 1. Per SSH verbinden

```bash
ssh admin@IHR_SYNOLOGY_IP
```

### 2. Repository klonen

```bash
cd /volume1/docker
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

### 3. .env Datei erstellen

```bash
cp .env.example .env
nano .env
```

**WICHTIG:** Tragen Sie Ihre echten Credentials ein (nicht die Platzhalter!):

```env
IMAP_HOST=mail.einsle.cloud
IMAP_PORT=993
IMAP_USER=dmarc-reports@einsle.cloud
IMAP_PASSWORD=<IHR_ECHTES_IMAP_PASSWORT>

ANTHROPIC_API_KEY=<IHR_ECHTER_ANTHROPIC_API_KEY>

SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=<IHR_SES_SMTP_USER>
SMTP_PASSWORD=<IHR_SES_SMTP_PASSWORD>
SMTP_FROM=dmarc-reports@einsle.cloud
ALERT_RECIPIENT=robert@einsle.com

SCHEDULER_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

Speichern: `Ctrl+O` → `Enter` → `Ctrl+X`

### 4. Container Manager öffnen

DSM → Container Manager → Projekt → **Erstellen**

- **Projektname:** `dmarc-analyzer`
- **Pfad:** `/volume1/docker/dmarc-reports-mail`
- **Quelle:** `docker-compose.yml` verwenden

→ **Weiter** → **Fertig**

### 5. Fertig!

- Dashboard: `http://IHR_SYNOLOGY_IP:3551`
- Health-Check: `http://IHR_SYNOLOGY_IP:3551/health`

## Häufigster Fehler

### "unable to prepare context: unable to evaluate symlinks in Dockerfile path"

**Ursache:** Dateien fehlen oder .env wurde nicht erstellt.

**Lösung:**
```bash
cd /volume1/docker/dmarc-reports-mail
ls -la docker/Dockerfile  # Muss existieren!
ls -la .env               # Muss existieren!
```

Falls Dateien fehlen: Repository erneut klonen und .env erstellen.

## Logs anschauen

Via Container Manager:
- Container → `dmarc-analyzer` → Details → Log

Via SSH:
```bash
cd /volume1/docker/dmarc-reports-mail
docker-compose logs -f
```

## Updates einspielen

```bash
cd /volume1/docker/dmarc-reports-mail
git pull
docker-compose down
docker-compose build
docker-compose up -d
```

## Weitere Hilfe

Ausführliche Anleitung: [SYNOLOGY_SETUP.md](SYNOLOGY_SETUP.md)
