# DMARC Reports Mail Analyzer

Automated DMARC report processing with Claude AI analysis and email notifications.

## Features

- **Automatic IMAP Retrieval**: Fetches DMARC reports every 5 minutes from IMAP server
- **XML Parsing**: Processes standard DMARC reports (XML, .gz, .zip)
- **Claude AI Analysis**: Intelligent analysis using Anthropic's Claude API
- **Alert System**: Email notifications for critical issues via AWS SES
- **Web Dashboard**: Flask-based dashboard for visualization
- **Docker-Ready**: Runs as container, deployed via Coolify
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

### Coolify Deployment (Production)

1. **Add Service in Coolify**:
   - Go to your Coolify dashboard
   - Create new service → Docker Compose
   - Connect your Git repository: `https://github.com/roberteinsle/dmarc-reports-mail.git`

2. **Configure Environment Variables**:
   Add the following environment variables in Coolify:
   ```env
   FLASK_ENV=production
   SECRET_KEY=<generate-secure-key>
   DATABASE_URL=sqlite:////app/data/dmarc_reports.db

   # IMAP Configuration
   IMAP_HOST=<your-imap-host>
   IMAP_PORT=993
   IMAP_USER=<your-imap-user>
   IMAP_PASSWORD=<your-imap-password>
   IMAP_FOLDER=INBOX

   # Claude API
   ANTHROPIC_API_KEY=<your-anthropic-api-key>

   # AWS SES SMTP
   SMTP_HOST=<your-smtp-host>
   SMTP_PORT=587
   SMTP_USER=<your-smtp-user>
   SMTP_PASSWORD=<your-smtp-password>
   SMTP_FROM=<your-from-email>
   ALERT_RECIPIENT=<alert-recipient-email>

   # Optional
   SCHEDULER_INTERVAL_MINUTES=5
   LOG_LEVEL=INFO
   ```

3. **Configure Volumes**:
   - Add persistent volume for `/app/data` (database storage)
   - Add persistent volume for `/app/logs` (log files)

4. **Deploy**:
   - Coolify will automatically build and deploy the container
   - Health check endpoint: `/health`
   - Coolify handles SSL/TLS termination and domain mapping

5. **Access Dashboard**:
   - Use the domain/URL provided by Coolify
   - Health check: `https://<your-domain>/health`

### Local Docker Deployment (Development/Testing)

1. Clone repository:
```bash
git clone https://github.com/roberteinsle/dmarc-reports-mail.git
cd dmarc-reports-mail
```

2. Create `.env` file:
```bash
cp .env.example .env
# Edit .env and enter your credentials
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
http://localhost:5000
```

6. Health check:
```
http://localhost:5000/health
```

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

Solution:
- Check logs in Coolify dashboard or via `docker-compose logs -f` (local)
- Verify all environment variables are set correctly
- Restart the service

### Problem: IMAP connection fails

Solution:
- Check IMAP credentials in environment variables
- Verify IMAP server connectivity
- Check logs for specific error messages

### Problem: Claude API errors

Solution:
- Verify API key in environment variables
- Check rate limits (app has retry logic with exponential backoff)
- Check Anthropic status page

### Problem: Not receiving alerts

Solution:
- Check SMTP credentials in environment variables
- Verify alert criteria configuration
- Note alert throttling (60-minute window per alert type)
- Check logs for SMTP errors

### Problem: Coolify deployment issues

Solution:
- Verify all required environment variables are set in Coolify
- Check that persistent volumes are properly configured
- Review Coolify deployment logs
- Ensure health check endpoint `/health` is accessible

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
1. Check logs (Coolify dashboard or `docker-compose logs -f` for local)
2. Check health endpoint (`/health`)
3. Create GitHub issues: https://github.com/roberteinsle/dmarc-reports-mail/issues

## Developer

Robert Einsle (robert@einsle.com)
