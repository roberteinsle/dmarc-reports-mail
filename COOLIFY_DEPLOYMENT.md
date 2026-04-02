# Coolify Deployment Guide

This guide explains how to deploy the DMARC Reports Mail Analyzer using Coolify.

## Quick Start

1. **Create new resource** in Coolify → **Docker Compose**
2. **Connect Git repository**: `https://github.com/roberteinsle/dmarc-reports-mail`
3. **Set environment variables** (see below)
4. **Deploy** → Coolify builds the image and starts the container
5. **Configure domain** in Coolify → SSL is handled automatically

---

## Prerequisites

- Coolify instance running (self-hosted or Coolify Cloud)
- Git repository accessible
- Credentials ready:
  - IMAP server details
  - Anthropic API key
  - SMTP credentials (AWS SES or other)
- A domain name (optional, for public access)

## Architecture

```
Internet → Coolify Proxy (Traefik) → DMARC Analyzer Container (Port 5000)
                ↓
         SSL/TLS Termination
         Domain Routing
```

Coolify uses its own Traefik-based proxy. The container only needs to `expose` port 5000 internally — Coolify handles everything else.

---

## Step 1: Create Resource in Coolify

1. Go to your Coolify dashboard → **Projects** → select or create a project
2. Click **+ New Resource** → **Docker Compose**
3. Select **Git Repository** as the source

### Connect Repository

- **Repository URL**: `https://github.com/roberteinsle/dmarc-reports-mail`
- **Branch**: `main`
- **Compose file path**: `docker-compose.yaml`
- For private repos: add your SSH key or GitHub token in Coolify settings

---

## Step 2: Configure Environment Variables

In the Coolify resource settings under **Environment Variables**, add all required variables:

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=your-secret-key-here-change-this-to-random-64-chars
DATABASE_URL=sqlite:////app/data/dmarc_reports.db

# IMAP Configuration
IMAP_HOST=mail.example.com
IMAP_PORT=993
IMAP_USER=dmarc-reports@example.com
IMAP_PASSWORD=your-imap-password
IMAP_FOLDER=INBOX

# Claude API Configuration
ANTHROPIC_API_KEY=sk-ant-your-api-key-here

# SMTP Configuration (for sending alerts)
SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=alerts@example.com
ALERT_RECIPIENT=recipient@example.com

# Scheduler Configuration
SCHEDULER_INTERVAL_MINUTES=5

# Logging
LOG_LEVEL=INFO
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Step 3: Configure Domain & SSL

1. In the resource settings, go to **Domains**
2. Add your domain: `dmarc.yourdomain.com`
3. Set **Port**: `5000`
4. Enable **HTTPS** — Coolify requests a Let's Encrypt certificate automatically

---

## Step 4: Deploy

1. Click **Deploy** in Coolify
2. Coolify will:
   - Clone the repository
   - Build the Docker image
   - Create volumes (`dmarc-data`, `logs`)
   - Start the container
   - Configure Traefik routing for your domain

Monitor the build output in the **Deployments** tab.

---

## Step 5: Verify Deployment

### Check Logs

In Coolify → resource → **Logs** tab, look for:
```
Starting DMARC Reports Mail application...
Fixing volume permissions...
Database tables created/verified successfully
Scheduler started with 5 minute interval
Running initial DMARC report processing on startup
```

### Health Check

```bash
curl https://dmarc.yourdomain.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "scheduler": "running",
  "last_check": "2026-01-11T..."
}
```

---

## Persistent Storage

Coolify automatically manages the Docker volumes defined in `docker-compose.yaml`:

- `dmarc-data` — SQLite database (`/app/data/dmarc_reports.db`)
- `logs` — Application logs (`/app/logs/`)

Volumes persist across redeployments.

### Backup Database

```bash
# Via Docker CLI on the host
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup_$(date +%Y%m%d).db
```

---

## Updating the Application

### Automatic (recommended)

1. In Coolify resource settings, enable **Auto Deploy** on push to `main`
2. Push changes to GitHub → Coolify rebuilds and redeploys automatically

### Manual

1. Go to Coolify → resource → **Deployments**
2. Click **Redeploy**

---

## Monitoring

### Coolify Dashboard

- **Logs**: Real-time log streaming in Coolify UI
- **Resources**: CPU and memory usage visible in container details

### Health Monitoring

Set up monitoring against the `/health` endpoint (e.g., via Uptime Kuma):
- URL: `https://dmarc.yourdomain.com/health`
- Expected status: `200`
- Expected body contains: `"status": "healthy"`

---

## Troubleshooting

### Container Won't Start

1. Check **Logs** in Coolify for startup errors
2. Verify all environment variables are set
3. Ensure the build completed successfully in the **Deployments** tab

### Database Permission Errors

The entrypoint script fixes permissions automatically. If you see "unable to open database file":
- Check logs for "Write permissions verified successfully"
- Restart the container via Coolify

### Cannot Access via Domain

1. Verify DNS points to your Coolify server IP
2. Check the domain is correctly configured in Coolify (port 5000)
3. Check Coolify proxy status in Coolify → **Proxy** settings
4. Ensure ports 80/443 are open on your server firewall

### IMAP/SMTP Connection Issues

```bash
# In container terminal (Coolify → resource → Terminal)
nc -zv mail.example.com 993   # IMAP
nc -zv smtp.example.com 587   # SMTP
```

---

## Useful Commands

```bash
# View container logs
docker logs -f dmarc-analyzer

# Access container shell
docker exec -it dmarc-analyzer bash

# Restart container
docker restart dmarc-analyzer

# Backup database
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup.db
```

---

**Deployment Platform**: Coolify
