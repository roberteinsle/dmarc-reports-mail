# DMARC Reports Mail Analyzer

Automated DMARC report processing with Claude AI analysis and email notifications.

## Features

- **Automatic IMAP Retrieval**: Fetches DMARC reports every 5 minutes from IMAP server
- **XML Parsing**: Processes standard DMARC reports (XML, .gz, .zip)
- **Claude AI Analysis**: Intelligent analysis using Anthropic's Claude API
- **Alert System**: Email notifications for critical issues via AWS SES
- **Web Dashboard**: Flask-based dashboard for visualization
- **Docker-Ready**: Runs as container on Synology NAS or other platforms
- **SQLite Database**: Persistent storage of all reports and analyses

## Prerequisites

- Python 3.11+ (for local development)
- Docker & Docker Compose (for production)
- IMAP access for DMARC reports
- Anthropic API Key (Claude AI)
- AWS SES SMTP credentials (for alert emails)

## Installation

### Local Development

1. Clone repository:
```bash
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and enter your credentials
```

5. Initialize database:
```bash
python
>>> from app import create_app
>>> from app.models.database import db
>>> app = create_app()
>>> with app.app_context():
>>>     db.create_all()
>>> exit()
```

6. Start application:
```bash
python run.py
```

Dashboard: http://localhost:5000

### Docker Deployment (Production)

1. Clone repository:
```bash
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

2. Create `.env` file:
```bash
cp .env.example .env
# IMPORTANT: Enter ALL real credentials!
```

3. Build and start Docker container:
```bash
docker-compose build
docker-compose up -d
```

4. Check logs:
```bash
docker-compose logs -f
```

5. Open dashboard:
```
http://<server-ip>:3551
```

6. Health check:
```
http://<server-ip>:3551/health
```

### Deployment on Synology NAS

1. Enable SSH access (Control Panel > Terminal & SNMP)
2. Connect via SSH: `ssh admin@<synology-ip>`
3. Clone repository into desired directory
4. Create `.env` file with real credentials
5. Install Docker Compose (if not already installed)
6. Start container: `docker-compose up -d`

## Configuration

All configuration is done via environment variables in the `.env` file:

### Required Environment Variables

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

## Usage

### Dashboard

- **/**  - Overview with statistics
- **/reports** - List of all processed reports
- **/reports/<id>** - Detail view of a report
- **/alerts** - Alert history with filtering
- **/health** - Health check endpoint

### API Endpoints

- `GET /api/stats` - JSON statistics for charts
- `GET /health` - Health status (200 = healthy, 503 = unhealthy)

### Alert Criteria

Alerts are automatically sent when:

1. **DMARC Failures**: Emails with disposition = quarantine/reject
2. **SPF Failures**: > 5 emails with SPF fail
3. **DKIM Failures**: > 5 emails with DKIM fail
4. **Unauthorized Senders**: Unknown sources identified by Claude AI
5. **Anomalies**: Suspicious patterns detected by Claude AI

## Testing

Run tests:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app --cov-report=html
```

## Monitoring

### Health Check

```bash
curl http://localhost:3551/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running",
  "last_check": "2025-12-30T10:30:00.000Z"
}
```

### Logs

Logs are located in `logs/`:
- `app.log` - All application events
- `error.log` - Only errors and critical

In Docker:
```bash
docker-compose logs -f
```

### Database Backup

SQLite database is located in Docker volume `dmarc-data`.

Create backup:
```bash
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup_$(date +%Y%m%d).db
```

## Troubleshooting

### Problem: Scheduler not running

Solution: Check logs, possibly restart container:
```bash
docker-compose restart
docker-compose logs -f
```

### Problem: IMAP connection fails

Solution:
- Check IMAP credentials in `.env`
- Check firewall settings (port 993)
- Test IMAP server reachability: `telnet mail.einsle.cloud 993`

### Problem: Claude API errors

Solution:
- Check API key in `.env`
- Check rate limits (app has retry logic)
- Check Anthropic status page

### Problem: Not receiving alerts

Solution:
- Check SMTP credentials in `.env`
- Check alert criteria in code
- Note alert throttling (60 min)
- Check logs for SMTP errors

## Security Notes

- **NEVER** commit `.env` file!
- **NEVER** hardcode real credentials in code!
- Regularly update Docker images
- Use strong passwords
- IMAP/SMTP only over encrypted connections (SSL/TLS)

## License

This project is intended for private use.

## Support

For issues:
1. Check logs (`docker-compose logs -f`)
2. Check health endpoint (`/health`)
3. Create GitHub issues: https://github.com/roberteinsle/dmarc-reports-mail/issues

## Developer

Robert Einsle (robert@einsle.com)
