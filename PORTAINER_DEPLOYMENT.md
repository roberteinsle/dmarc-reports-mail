# Portainer Deployment Guide

This guide explains how to deploy the DMARC Reports Mail Analyzer using Portainer on a VM with nginx-proxy-manager for reverse proxy and SSL/TLS.

## Quick Start Summary

**For quick deployment - The essential steps:**

1. **Portainer → Stacks → Add stack**
   - Name: `dmarc-analyzer`
   - Build method: Repository
   - Repository URL: `https://github.com/roberteinsle/dmarc-reports-mail`
   - Compose path: `docker-compose.yaml`

2. **Add Environment Variables** (all required!)
   - FLASK_ENV, SECRET_KEY, DATABASE_URL
   - IMAP_HOST, IMAP_USER, IMAP_PASSWORD
   - ANTHROPIC_API_KEY
   - SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, ALERT_RECIPIENT

3. **Deploy** → Done! 🚀

4. **Configure nginx-proxy-manager**
   - Add proxy host pointing to container on port 5000
   - Configure SSL certificate (Let's Encrypt)

**Detailed instructions below ↓**

---

## Prerequisites

1. A VM with Docker and Portainer installed
2. nginx-proxy-manager running and accessible
3. Your credentials ready:
   - IMAP server details
   - Anthropic API key
   - SMTP credentials (AWS SES or other)
4. A domain name (optional, for reverse proxy)

## Architecture Overview

```
Internet → nginx-proxy-manager → Docker Network → DMARC Analyzer Container
                ↓                      ↓                    ↓
           SSL/TLS Termination    Port Forwarding      Port 5000
           Domain Routing         Load Balancing       Flask App
```

## Step 1: Prepare Portainer

### 1.1 Access Portainer Dashboard

1. Navigate to your Portainer instance (e.g., `https://portainer.yourdomain.com`)
2. Login with your credentials
3. Select your **environment** (local Docker endpoint)

### 1.2 Ensure nginx-proxy-manager Network Exists

The application needs to connect to the `nginx-proxy-manager_default` network:

1. Go to **Networks** in Portainer
2. Verify `nginx-proxy-manager_default` exists
3. If it doesn't exist, create it:
   - Name: `nginx-proxy-manager_default`
   - Driver: `bridge`
   - Click **Create network**

## Step 2: Deploy Stack in Portainer

### 2.1 Create New Stack

1. In Portainer, go to **Stacks** → **Add stack**
2. **Name**: `dmarc-analyzer` (or your preferred name)

### 2.2 Choose Deployment Method

You have two options:

#### Option A: Repository (Recommended - Auto-updates)

1. Select **Repository** tab
2. Fill in details:
   - **Repository URL**: `https://github.com/roberteinsle/dmarc-reports-mail`
   - **Repository reference**: `refs/heads/main`
   - **Compose path**: `docker-compose.yaml`
   - **Authentication**: Not required (public repo)

**Benefit**: You can later use the "Pull and redeploy" button to update from GitHub.

#### Option B: Web editor (Manual)

1. Select **Web editor** tab
2. Copy the contents of `docker-compose.yaml` from the repository
3. Paste into the editor

**Note**: Updates require manual copy-paste of new `docker-compose.yaml`.

### 2.3 Configure Environment Variables

Scroll down to **Environment variables** section in Portainer.

**IMPORTANT**: Add all required variables. You can use either:
- **Simple format** (one per line): `KEY=value`
- **Advanced format** (click "Advanced mode"): Full env file syntax

#### Required Environment Variables

Add these variables (adjust values for your setup):

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
Or use: https://generate-secret.vercel.app/64

### 2.4 Verify Stack Configuration

Before deploying, verify:
- ✅ Repository URL is correct (if using Repository method)
- ✅ All environment variables are set
- ✅ No sensitive data in the stack definition (all in env vars)

### 2.5 Deploy Stack

1. Click **Deploy the stack**
2. Portainer will:
   - Clone the repository (or use web editor content)
   - Build the Docker image
   - Create volumes (`dmarc-data`, `logs`)
   - Start the container
   - Connect to `nginx-proxy-manager_default` network

3. Monitor the deployment:
   - Watch for "Stack successfully deployed" message
   - Click on the stack name to view details

## Step 3: Verify Container

### 3.1 Check Container Status

1. Go to **Containers** in Portainer
2. Find `dmarc-analyzer` container
3. Status should be **running** with green indicator
4. Click on container name to view details

### 3.2 View Logs

1. In container details, click **Logs**
2. Look for successful startup messages:
   ```
   Starting DMARC Reports Mail application...
   Fixing volume permissions...
   Database tables created/verified successfully
   Scheduler started with 5 minute interval
   Running initial DMARC report processing on startup
   ```

3. **If you see errors**, check:
   - Environment variables are correctly set
   - Database permissions (should be fixed automatically)
   - IMAP/SMTP credentials are valid

### 3.3 Test Health Endpoint

1. In Portainer container details, go to **Console**
2. Click **Connect** and select `/bin/bash`
3. Run:
   ```bash
   curl http://localhost:5000/health
   ```
4. Should return:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "scheduler": "running",
     "last_check": "2026-01-11T..."
   }
   ```

## Step 4: Configure nginx-proxy-manager

### 4.1 Access nginx-proxy-manager Dashboard

1. Navigate to your nginx-proxy-manager instance
2. Login with your credentials

### 4.2 Add Proxy Host

1. Go to **Hosts** → **Proxy Hosts** → **Add Proxy Host**

2. **Details Tab**:
   - **Domain Names**: `dmarc.yourdomain.com` (your desired subdomain)
   - **Scheme**: `http`
   - **Forward Hostname / IP**: `dmarc-analyzer` (container name)
   - **Forward Port**: `5000`
   - **Cache Assets**: ✓ (optional)
   - **Block Common Exploits**: ✓ (recommended)
   - **Websockets Support**: ☐ (not needed)

3. **SSL Tab**:
   - **SSL Certificate**: Select existing or create new
   - For new certificate:
     - **SSL Certificate**: None → Request a new SSL Certificate
     - **Email Address**: your-email@example.com
     - **Use a DNS Challenge**: ☐ (unless needed)
     - **Agree to Let's Encrypt ToS**: ✓
     - **Force SSL**: ✓ (recommended - redirects HTTP to HTTPS)
     - **HTTP/2 Support**: ✓ (recommended)
     - **HSTS Enabled**: ✓ (recommended for security)
     - **HSTS Subdomains**: ☐ (unless needed)

4. **Advanced** (optional):
   - Can add custom nginx configuration if needed
   - Usually not required

5. Click **Save**

### 4.3 Verify Proxy Configuration

1. **Test DNS**: Ensure `dmarc.yourdomain.com` points to your VM's IP
   ```bash
   nslookup dmarc.yourdomain.com
   ```

2. **Access Dashboard**: Navigate to `https://dmarc.yourdomain.com`
   - Should see the DMARC Reports dashboard
   - SSL certificate should be valid (green padlock)

3. **Test Health Endpoint**: `https://dmarc.yourdomain.com/health`
   - Should return healthy status JSON

## Step 5: Persistent Storage

Portainer automatically manages the volumes defined in `docker-compose.yaml`:

### 5.1 Verify Volumes

1. In Portainer, go to **Volumes**
2. Find volumes:
   - `dmarc-analyzer_dmarc-data` - SQLite database storage
   - `dmarc-analyzer_logs` - Application logs

3. Click on volume to see details:
   - Mount point on host
   - Size
   - Usage

### 5.2 Access Volume Data

To access volume data for backup or inspection:

1. In Portainer, go to container **Console**
2. Connect with `/bin/bash`
3. Navigate to:
   ```bash
   ls -la /app/data/       # Database
   ls -la /app/logs/       # Logs
   ```

### 5.3 Backup Database

**Option A: Via Container Console**
```bash
# In Portainer console
sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
```

**Option B: Via Portainer Volume Browser**
1. Go to **Volumes** → `dmarc-analyzer_dmarc-data`
2. Use Portainer's file browser to download `dmarc_reports.db`

**Option C: Via Docker CLI on VM**
```bash
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup_$(date +%Y%m%d).db
```

## Step 6: Monitoring and Maintenance

### 6.1 View Logs

**In Portainer:**
1. Go to **Containers** → `dmarc-analyzer`
2. Click **Logs**
3. Enable **Auto-refresh** to monitor in real-time
4. Use search to filter logs

**Via Docker CLI:**
```bash
docker logs -f dmarc-analyzer
```

### 6.2 Monitor Resource Usage

In Portainer container details:
- **Stats** tab shows:
  - CPU usage
  - Memory usage
  - Network I/O
  - Block I/O

### 6.3 Restart Container

If needed:
1. Go to **Containers** → `dmarc-analyzer`
2. Click **Restart** button
3. Or use **Quick actions** → **Restart**

### 6.4 Update Application

**Method 1: Pull and Redeploy (if using Repository)**
1. Go to **Stacks** → `dmarc-analyzer`
2. Click **Pull and redeploy**
3. Portainer will:
   - Pull latest code from GitHub
   - Rebuild image
   - Redeploy container

**Method 2: Manual Update**
1. Stop stack
2. Remove stack
3. Recreate with updated configuration
4. Volumes persist automatically

### 6.5 Health Monitoring

**Manual Check:**
```bash
curl https://dmarc.yourdomain.com/health
```

**Automated Monitoring** (optional):
- Use **Uptime Kuma** or similar
- Monitor `/health` endpoint
- Alert on non-200 status or unhealthy response

## Deployment Workflow

Once configured, your workflow is:

```bash
# Make changes locally
git add .
git commit -m "Your changes"
git push origin main

# In Portainer:
# Go to Stacks → dmarc-analyzer → Pull and redeploy
# Or set up automated webhooks (see below)
```

### Optional: Automated Deployment via Webhooks

You can configure Portainer to auto-update on Git push:

1. In Portainer stack settings, enable **Webhooks**
2. Copy the webhook URL
3. Add webhook to GitHub repository:
   - GitHub → Settings → Webhooks → Add webhook
   - Payload URL: Portainer webhook URL
   - Content type: `application/json`
   - Events: Push events

## Troubleshooting

### Container Won't Start

1. **Check logs** in Portainer
2. **Verify environment variables** are all set
3. **Check volumes** are properly created
4. **Verify network** `nginx-proxy-manager_default` exists

### Database Permission Errors

If you see "unable to open database file":

1. **Automatic Fix**: The entrypoint script fixes this automatically
2. **Verify in logs**: Look for "Write permissions verified successfully"
3. **Manual check**:
   ```bash
   # In Portainer console
   ls -la /app/data/
   # Should show: drwxrwxr-x appuser appuser
   ```

### Database Tables Missing

If you see "no such table" errors:

1. **Automatic Fix**: Entrypoint creates tables on every startup
2. **Verify in logs**: Look for "Database tables created/verified successfully"
3. **Manual fix**: Restart container - tables will be recreated

### Cannot Access via nginx-proxy-manager

1. **Check container network**:
   - Portainer → Container → Networks
   - Should include `nginx-proxy-manager_default`

2. **Test direct access**:
   ```bash
   # On the VM
   curl http://localhost:5000/health
   ```

3. **Check nginx-proxy-manager logs**:
   - nginx-proxy-manager dashboard → View Logs

4. **Verify DNS**: Ensure domain points to VM IP

5. **Check firewall**: Ensure ports 80/443 are open

### IMAP/SMTP Connection Issues

1. **Verify credentials** in environment variables
2. **Check logs** for connection errors
3. **Test from container**:
   ```bash
   # In Portainer console
   nc -zv mail.example.com 993   # IMAP
   nc -zv smtp.example.com 587   # SMTP
   ```

### Stack Deployment Fails

1. **Check docker-compose.yaml syntax**
2. **Verify all environment variables** are set
3. **Check Portainer logs** (bottom of deployment page)
4. **Ensure base image is accessible** (python:3.11-slim)

## Security Considerations

1. **Container runs as non-root user** (`appuser` UID 1000)
   - Entrypoint fixes permissions then drops privileges

2. **Secrets in environment variables**
   - Stored securely in Portainer
   - Never logged or exposed

3. **Network isolation**
   - Only exposed via nginx-proxy-manager
   - Internal port 5000 not publicly accessible

4. **SSL/TLS**
   - Handled by nginx-proxy-manager
   - Automatic Let's Encrypt certificates

5. **Regular updates**
   - Update base images regularly
   - Monitor security advisories

## Best Practices

1. **Backups**
   - Backup database regularly (see Step 5.3)
   - Export Portainer stack configuration
   - Keep `.env` template updated

2. **Monitoring**
   - Set up health monitoring
   - Review logs regularly
   - Monitor resource usage

3. **Updates**
   - Test updates locally first
   - Use git tags for production deployments
   - Keep deployment documentation updated

4. **Security**
   - Rotate credentials periodically
   - Use strong passwords
   - Keep Docker and Portainer updated
   - Monitor access logs

5. **Documentation**
   - Document any custom configuration
   - Keep track of environment-specific settings
   - Maintain runbook for common operations

## Advanced Configuration

### Custom nginx Configuration

If you need custom nginx settings in nginx-proxy-manager:

```nginx
# Example: Increase timeout for long-running requests
proxy_read_timeout 300s;
proxy_connect_timeout 75s;

# Example: Custom headers
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-Proto $scheme;
```

### Resource Limits

To limit container resources, edit `docker-compose.yaml`:

```yaml
services:
  dmarc-analyzer:
    # ... existing config ...
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          memory: 256M
```

Then redeploy the stack.

### Multiple Environments

To run dev/staging/production:

1. Create separate stacks in Portainer:
   - `dmarc-analyzer-dev`
   - `dmarc-analyzer-staging`
   - `dmarc-analyzer-prod`

2. Use different environment variables for each

3. Configure different domains in nginx-proxy-manager:
   - `dmarc-dev.example.com`
   - `dmarc-staging.example.com`
   - `dmarc.example.com`

## Support

For issues:
1. Check Portainer container logs
2. Verify health endpoint
3. Check nginx-proxy-manager logs
4. Review this documentation
5. Create GitHub issues: https://github.com/roberteinsle/dmarc-reports-mail/issues

## Useful Commands

```bash
# View container logs
docker logs -f dmarc-analyzer

# Access container shell
docker exec -it dmarc-analyzer bash

# Restart container
docker restart dmarc-analyzer

# View resource usage
docker stats dmarc-analyzer

# Backup database
docker exec dmarc-analyzer sqlite3 /app/data/dmarc_reports.db ".backup /app/data/backup.db"
docker cp dmarc-analyzer:/app/data/backup.db ./backup.db

# Check container networks
docker inspect dmarc-analyzer | grep -A 20 Networks
```

---

**Last Updated**: 2026-01-11
**Deployment Platform**: Portainer + nginx-proxy-manager on VM
