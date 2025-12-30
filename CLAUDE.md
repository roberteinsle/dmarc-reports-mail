# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DMARC Reports Mail Analyzer - A Python Flask application that automatically fetches DMARC email reports, analyzes them using Claude AI, and sends alerts when issues are detected.

**Key Technologies:**
- Python 3.11+ with Flask web framework
- SQLite database with SQLAlchemy ORM
- APScheduler for background jobs (5-minute intervals)
- Anthropic Claude API for intelligent analysis
- IMAP for email retrieval, AWS SES SMTP for alerts
- Docker deployment for Synology NAS

## Essential Commands

### Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run application locally
python run.py

# Run tests
pytest                                    # Run all tests
pytest tests/test_parser_service.py       # Run specific test file
pytest -k test_function_name              # Run specific test
pytest --cov=app --cov-report=html        # Run with coverage report

# Database migrations
alembic upgrade head
alembic revision --autogenerate -m "description"
```

### Docker/Production

```bash
# Build and start
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Execute commands in container
docker exec -it dmarc-analyzer bash
```

## Architecture Overview

### Processing Pipeline

The application follows this workflow every 5 minutes (orchestrated by `scheduler_service.py`):

1. **IMAP Service** (`app/services/imap_service.py`): Connect to IMAP server, fetch unread emails
2. **Parser Service** (`app/services/parser_service.py`): Extract XML attachments, decompress .gz/.zip, parse DMARC XML structure
3. **Database Layer** (`app/models/database.py`): Save Report and Record entries to SQLite
4. **Claude Service** (`app/services/claude_service.py`): Send report data to Claude API for analysis
5. **Alert Service** (`app/services/alert_service.py`): Evaluate alert criteria, send email via AWS SES if needed
6. **IMAP Service**: Delete processed email
7. **Processing Log**: Log results in `processing_log` table

### Database Schema

**Four main tables:**

- `reports` - DMARC report metadata, policy published, Claude analysis (JSON), status
- `records` - Individual authentication results per source IP (SPF/DKIM/DMARC disposition)
- `alerts` - Generated alerts with severity, type, email tracking
- `processing_log` - Audit trail of all job executions

**Relationships:**
- Report → Records (one-to-many, cascade delete)
- Report → Alerts (one-to-many, cascade delete)

### Service Responsibilities

**IMAPService** (`imap_service.py`):
- Manages IMAP4_SSL connection lifecycle
- Searches for unread emails
- Extracts and decompresses attachments (.gz, .zip)
- Deletes processed emails
- Use as context manager for automatic cleanup

**DMARCParserService** (`parser_service.py`):
- Parses DMARC XML (RFC 7489 format)
- Extracts: report_metadata, policy_published, records
- Validates XML structure
- Returns dict matching database schema

**ClaudeService** (`claude_service.py`):
- Formats analysis prompts with report statistics
- Calls Claude API (model: claude-sonnet-4-5-20250929)
- Implements retry logic with exponential backoff for rate limits
- Returns JSON with: summary, failures, unauthorized_sources, anomalies, severity, recommendations

**AlertService** (`alert_service.py`):
- Evaluates alert criteria based on records + Claude analysis
- Triggers on: DMARC failures (quarantine/reject), SPF/DKIM failures (>5 count), unauthorized sources, suspicious patterns
- Formats HTML and plain text email alerts
- Sends via AWS SES SMTP with STARTTLS
- Implements throttling (60-minute window per alert type)

**SchedulerService** (`scheduler_service.py`):
- Initializes APScheduler BackgroundScheduler
- Orchestrates entire pipeline in `process_dmarc_reports()`
- Handles errors gracefully (rollback DB, log failures)
- Never crashes scheduler even if individual jobs fail

### Configuration Management

**Three config classes** in `app/config.py`:
- `DevelopmentConfig` - DEBUG=True, local SQLite
- `ProductionConfig` - DEBUG=False, Docker volume SQLite
- `TestingConfig` - In-memory SQLite, skips validation

**Required environment variables** (validated on startup):
- IMAP_HOST, IMAP_USER, IMAP_PASSWORD
- ANTHROPIC_API_KEY
- SMTP_HOST, SMTP_USER, SMTP_PASSWORD
- ALERT_RECIPIENT

All credentials via `.env` file (dev) or Docker ENV vars (prod) - **NEVER hardcoded**.

### Web Dashboard

**Routes** (`app/routes/dashboard.py`):
- `/` - Dashboard overview with statistics cards
- `/reports` - Paginated report list
- `/reports/<id>` - Detailed report view with Claude analysis
- `/alerts` - Alert history with severity filtering
- `/api/stats` - JSON endpoint for chart data
- `/health` - Health check (200=healthy, 503=unhealthy)

**Templates** use Bootstrap 5 with custom severity color coding.

## Common Development Tasks

### Adding a New Alert Criterion

1. Edit `AlertService.evaluate_alert_criteria()` in `alert_service.py`
2. Add detection logic for new criterion
3. Append to `alerts` list with type, severity, message
4. Update alert type enum if needed

### Modifying DMARC XML Parsing

1. Update `DMARCParserService._extract_*()` methods in `parser_service.py`
2. If adding new fields, update `Report` or `Record` model in `database.py`
3. Create Alembic migration: `alembic revision --autogenerate -m "add field"`
4. Test with sample XML in `tests/fixtures/`

### Changing Scheduler Interval

Update `SCHEDULER_INTERVAL_MINUTES` in `.env` file (no code changes needed).

### Customizing Claude Analysis Prompt

Edit `ClaudeService._format_prompt()` in `claude_service.py`. The prompt receives:
- Report metadata (domain, reporter, dates)
- Aggregated statistics (total emails, SPF/DKIM failures, dispositions)
- Top 10 records (to save tokens)

### Adding Database Indexes

1. Edit model in `database.py`, add `index=True` to column
2. Generate migration: `alembic revision --autogenerate -m "add index"`
3. Apply: `alembic upgrade head`

## Critical File Paths

- **Configuration**: `app/config.py`, `.env.example`
- **Database Models**: `app/models/database.py`
- **Core Services**: `app/services/{imap,parser,claude,alert,scheduler}_service.py`
- **Routes**: `app/routes/dashboard.py`
- **Templates**: `app/templates/*.html`
- **Entry Point**: `run.py`
- **Docker**: `docker/Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yml`
- **Migrations**: `migrations/env.py`, `alembic.ini`

## Security Considerations

1. **Credentials**: Never commit `.env` file. Check `.gitignore` includes `.env`
2. **Docker Security**: Application runs as non-root user (appuser:1000)
3. **Database**: SQLite with parameterized queries via SQLAlchemy (SQL injection safe)
4. **Logging**: Never log passwords/API keys. Redact sensitive data in error messages
5. **IMAP/SMTP**: Always use SSL/TLS (port 993) and STARTTLS (port 587)
6. **Flask Security Headers**: Set in `app/__init__.py` (X-Frame-Options, X-XSS-Protection, etc.)

## Error Handling Patterns

**Service-level**:
```python
try:
    # IMAP/SMTP/API operations
except SpecificError as e:
    logger.error(f"Context: {e}", exc_info=True)
    log_processing_error('job_type', str(e))
    raise or return None
finally:
    cleanup_resources()
```

**Scheduler jobs**: Must never crash scheduler
```python
try:
    process_dmarc_reports()
except Exception as e:
    logger.error(f"Job failed: {e}", exc_info=True)
    # Don't re-raise, just log
```

**Database operations**: Rollback on error
```python
try:
    db.session.add(obj)
    db.session.commit()
except IntegrityError:
    db.session.rollback()
    # Handle duplicate
```

## Testing Strategy

**Fixtures**: Sample DMARC XML in `tests/fixtures/sample_dmarc_report.xml`

**Mocking**: Use `pytest-mock` for external services (IMAP, Claude API, SMTP)

**Database**: Use in-memory SQLite for tests (TestingConfig)

**Key test areas**:
- Parser: Valid/invalid XML, missing fields, malformed data
- IMAP: Connection handling, attachment extraction, decompression
- Claude: Prompt formatting, response parsing, rate limit handling
- Alerts: Criteria evaluation, email formatting, throttling

## Deployment Notes

**Synology NAS specific**:
- Use Docker Compose
- Data persists in Docker volume `dmarc-data`
- Logs mapped to `./logs` directory for easy access
- Health check endpoint `/health` for monitoring
- Port 3551 exposed externally (maps to internal port 5000)
- Container name: `dmarc-analyzer`

**Environment variables** must be set before first run - app validates on startup and fails fast if missing.

**Database migrations** run automatically via `entrypoint.sh` on container start.

## Debugging Tips

1. **Scheduler not running**: Check logs for scheduler initialization errors
2. **IMAP connection fails**: Test connectivity with `telnet mail.einsle.cloud 993`
3. **Claude API errors**: Check API key, rate limits, Anthropic status page
4. **No alerts received**: Check alert criteria, throttling window (60 min), SMTP logs
5. **Database errors**: Check volume permissions, SQLite file accessibility
6. **Container crashes**: Check health endpoint, resource limits, logs

## Future Enhancement Ideas

- Multi-domain support (currently single domain)
- Advanced ML-based anomaly detection
- Slack/Discord webhook integrations
- RESTful API for external integrations
- User authentication for dashboard
- Export reports as CSV/JSON
- Sender reputation scoring
- Historical trend analysis

---

**Remember**: This application processes email automatically and sends alerts. Always test changes thoroughly in development before deploying to production. Use `.env.example` as template and never commit actual credentials.
