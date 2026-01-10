# Coolify Deployment Guide

This guide explains how to deploy the DMARC Reports Mail Analyzer to Coolify with automatic deployments on Git push.

## Prerequisites

1. A Coolify instance (self-hosted or managed)
2. GitHub repository access
3. Your credentials ready:
   - IMAP server details
   - Anthropic API key
   - SMTP credentials (AWS SES or other)

## Step 1: Prepare Repository

Ensure your repository is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Coolify deployment"
git push origin main
```

## Step 2: Create Service in Coolify

1. **Login to Coolify Dashboard**
   - Navigate to your Coolify instance

2. **Add New Resource**
   - Click **+ New Resource**
   - Select **Docker Compose**

3. **Connect Repository**
   - **Source**: Select GitHub
   - **Repository**: `https://github.com/roberteinsle/dmarc-reports-mail.git`
   - **Branch**: `main`
   - **Build Pack**: Docker Compose

4. **Configure Build Settings**
   - **Docker Compose Location**: `docker-compose.yml` (root directory)
   - **Base Directory**: `/` (leave default)

## Step 3: Configure Environment Variables

In Coolify, add the following environment variables:

### Required Variables

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=<generate-random-64-char-string>
DATABASE_URL=sqlite:////app/data/dmarc_reports.db

# IMAP Configuration
IMAP_HOST=mail.einsle.cloud
IMAP_PORT=993
IMAP_USER=dmarc-reports@einsle.cloud
IMAP_PASSWORD=<your-imap-password>
IMAP_FOLDER=INBOX

# Claude API Configuration
ANTHROPIC_API_KEY=<your-anthropic-api-key>

# SMTP Configuration (for sending alerts)
SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=<your-smtp-user>
SMTP_PASSWORD=<your-smtp-password>
SMTP_FROM=dmarc-reports@einsle.cloud
ALERT_RECIPIENT=robert@einsle.com

# Scheduler Configuration
SCHEDULER_INTERVAL_MINUTES=5

# Logging
LOG_LEVEL=INFO
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## Step 4: Configure Persistent Storage

Coolify automatically manages volumes defined in `docker-compose.yml`:

- **dmarc-data**: SQLite database storage (`/app/data`)
- **logs**: Application logs (`/app/logs`)

These are already configured in the `docker-compose.yml`.

## Step 5: Configure Domain (Optional)

1. In Coolify service settings, go to **Domains**
2. Add your domain (e.g., `dmarc.example.com`)
3. Coolify will automatically:
   - Configure reverse proxy
   - Set up SSL/TLS certificate (Let's Encrypt)
   - Handle port mapping

If you don't configure a domain, Coolify will provide a default URL.

## Step 6: Enable Auto-Deploy on Git Push

1. In Coolify service settings, go to **Source**
2. Enable **Automatic Deployment**
3. Configure webhook:
   - Coolify will provide a webhook URL
   - Add this webhook to your GitHub repository
   - Go to GitHub → Settings → Webhooks → Add webhook
   - Paste the Coolify webhook URL
   - Select **Just the push event**
   - Content type: `application/json`
   - Save

**Now every `git push` to `main` branch will automatically trigger a deployment!**

## Step 7: Deploy

1. Click **Deploy** button in Coolify
2. Monitor deployment logs
3. Wait for "Deployment successful" message

## Step 8: Verify Deployment

1. **Access Dashboard**
   - Via configured domain: `https://dmarc.example.com`
   - Or via Coolify-provided URL

2. **Check Health**
   - `https://dmarc.example.com/health`
   - Should return: `{"status": "healthy", ...}`

3. **Verify Logs**
   - In Coolify dashboard, view service logs
   - Look for: "Scheduler initialized successfully"
   - Look for: "Connected to IMAP server"

## Deployment Workflow

Once configured, your workflow is:

```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push origin main

# Coolify automatically:
# 1. Detects the push via webhook
# 2. Pulls latest code
# 3. Rebuilds Docker image
# 4. Deploys new container
# 5. Runs health checks
```

## Monitoring

### View Logs
- **Coolify Dashboard**: Service → Logs tab
- Real-time logs with auto-scroll

### Health Check
- Coolify monitors `/health` endpoint every 30 seconds
- Alerts you if the service becomes unhealthy

### Database Backup

Create periodic backups using Coolify's built-in backup feature or manually:

```bash
# SSH into Coolify server
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup_$(date +%Y%m%d).db
```

## Troubleshooting

### Deployment Failed

1. **Check Coolify Logs**: View build/deployment logs
2. **Verify Environment Variables**: Ensure all required vars are set
3. **Check Docker Compose**: Ensure `docker-compose.yml` is valid

### Service Unhealthy

1. **Check Application Logs**: Look for errors in Coolify logs
2. **Verify Database**: Ensure volume is properly mounted
3. **Test Health Endpoint**: `curl https://your-domain/health`

### IMAP/SMTP Connection Issues

1. **Verify Credentials**: Check environment variables
2. **Test Connectivity**: SSH into container and test connections
3. **Check Firewall**: Ensure outbound ports 993 (IMAP) and 587 (SMTP) are allowed

### Auto-Deploy Not Working

1. **Check Webhook**: Verify webhook URL in GitHub
2. **Test Webhook**: GitHub → Settings → Webhooks → Recent Deliveries
3. **Check Coolify**: Ensure auto-deployment is enabled

## Rollback

If a deployment fails, Coolify keeps previous versions:

1. Go to service **Deployments** tab
2. Select previous successful deployment
3. Click **Redeploy**

## Updating Configuration

### Environment Variables
1. Update in Coolify dashboard
2. Restart service (no rebuild needed)

### Code Changes
1. Make changes locally
2. `git push origin main`
3. Coolify auto-deploys

### Docker Configuration
1. Update `docker-compose.yml` or `Dockerfile`
2. `git push origin main`
3. Coolify rebuilds and redeploys

## Best Practices

1. **Always test locally** before pushing to production
2. **Use semantic commit messages** for better deployment tracking
3. **Monitor logs** after deployment to ensure everything works
4. **Backup database** regularly
5. **Keep credentials secure** - never commit `.env` file
6. **Use tags/releases** for production deployments (optional)

## Security Considerations

1. **Secrets**: All credentials are stored securely in Coolify
2. **SSL/TLS**: Automatic HTTPS via Let's Encrypt
3. **Network**: Coolify manages firewall rules
4. **Updates**: Regularly update base images and dependencies

## Support

For issues:
1. Check Coolify documentation: https://coolify.io/docs
2. Check application logs in Coolify dashboard
3. Create GitHub issues: https://github.com/roberteinsle/dmarc-reports-mail/issues

---

**Last Updated**: 2026-01-10
