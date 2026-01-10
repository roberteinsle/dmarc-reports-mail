# Coolify Deployment Guide

This guide explains how to deploy the DMARC Reports Mail Analyzer to Coolify with automatic deployments on Git push.

## Quick Start Zusammenfassung

**Für eilige User - Die wichtigsten Schritte:**

1. **Coolify → Applications → Public Repository**
   - Repository URL: `https://github.com/roberteinsle/dmarc-reports-mail`
   - Branch: `main`
   - Build Pack: Docker Compose

2. **Environment Variables hinzufügen** (alle required!)
   - FLASK_ENV, SECRET_KEY, DATABASE_URL
   - IMAP_HOST, IMAP_USER, IMAP_PASSWORD
   - ANTHROPIC_API_KEY
   - SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM, ALERT_RECIPIENT

3. **Deploy klicken** → Fertig! 🚀

4. **Optional: Auto-Deploy aktivieren**
   - Coolify → Service → Source → Automatic Deployment: ON
   - Für GitHub App: Webhook wird automatisch erstellt

**Detaillierte Anleitung unten ↓**

---

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

### 2.1 Navigate to Applications

1. **Login to Coolify Dashboard**
   - Navigate to your Coolify instance (e.g., `https://coolify.yourdomain.com`)
   - Login with your credentials

2. **Go to Applications**
   - In the left sidebar or top menu, click on **"Applications"**
   - You'll see options for different deployment types

### 2.2 Choose Deployment Type

Since your repository is public on GitHub, you have two recommended options:

#### Option A: Public Repository (Recommended - Einfachste Methode)

1. **Click on "Public Repository"** under "Git Based"
   - No GitHub authentication required
   - Perfect for public repositories

2. **Fill in Repository Details**:
   - **Project Name**: `dmarc-analyzer` (or your preferred name)
   - **Git Repository URL**: `https://github.com/roberteinsle/dmarc-reports-mail`
   - **Branch**: `main`
   - **Build Pack**: Select **"Docker Compose"**

3. **Click "Continue" or "Save"**

#### Option B: Private Repository with GitHub App (Für Auto-Deploy via Webhooks)

If you want automatic deployments triggered by GitHub webhooks:

1. **Click on "Private Repository (with GitHub App)"** under "Git Based"

2. **Install Coolify GitHub App** (if not already installed):
   - Click "Install GitHub App"
   - You'll be redirected to GitHub
   - Select your account/organization
   - Choose repositories: Select **"Only select repositories"**
   - Select: `dmarc-reports-mail`
   - Click "Install & Authorize"

3. **Configure in Coolify**:
   - **Repository**: Select `roberteinsle/dmarc-reports-mail` from dropdown
   - **Branch**: `main`
   - **Build Pack**: Select **"Docker Compose"**

4. **Click "Continue"**

### 2.3 Configure Build Settings

After selecting your repository, configure these settings:

1. **General Settings**:
   - **Port Mapping**: Coolify will detect port `5000` from docker-compose.yaml
   - **Publish Directory**: Leave empty (not needed for Docker Compose)
   - **Base Directory**: `/` (root of repository)
   - **Docker Compose Location**: `/docker-compose.yaml` (default - Coolify expects this)

2. **Advanced Settings** (Optional):
   - **Custom Docker Compose Path**: Leave as `/docker-compose.yaml` (default)
   - **Docker Network**: Use Coolify's default network
   - **Pre-Deploy Command**: Leave empty (migrations run in entrypoint.sh)
   - **Post-Deploy Command**: Leave empty

3. **Click "Save"**

## Step 3: Configure Environment Variables

### 3.1 Access Environment Settings

1. **Navigate to your service** in Coolify
2. Click on **"Environment Variables"** tab or **"Secrets"** tab
3. Click **"Add Variable"** or **"+ New"**

### 3.2 Add Required Variables

**WICHTIG**: Fügen Sie jede Variable einzeln hinzu. Coolify bietet zwei Modi:

- **Normal Variables**: Für nicht-sensitive Werte (sichtbar in UI)
- **Secret Variables**: Für Passwörter und API Keys (versteckt in UI)

#### Schritt-für-Schritt:

Für jede Variable:
1. Click **"Add Variable"** oder **"+ Add"**
2. **Key**: Variablenname eingeben (z.B. `FLASK_ENV`)
3. **Value**: Wert eingeben
4. **Is Secret**: Aktivieren für Passwörter/Keys
5. Click **"Save"** oder **"Add"**

### 3.3 Complete Variable List

Fügen Sie folgende Variablen hinzu:

#### Flask Configuration
```
FLASK_ENV=production
SECRET_KEY=<generate-random-64-char-string>  (Is Secret: ✓)
DATABASE_URL=sqlite:////app/data/dmarc_reports.db
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Oder online: https://generate-secret.vercel.app/64

#### IMAP Configuration
```
IMAP_HOST=mail.einsle.cloud
IMAP_PORT=993
IMAP_USER=dmarc-reports@einsle.cloud
IMAP_PASSWORD=<your-imap-password>  (Is Secret: ✓)
IMAP_FOLDER=INBOX
```

#### Claude API Configuration
```
ANTHROPIC_API_KEY=<your-anthropic-api-key>  (Is Secret: ✓)
```

#### SMTP Configuration
```
SMTP_HOST=email-smtp.eu-central-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=<your-smtp-user>
SMTP_PASSWORD=<your-smtp-password>  (Is Secret: ✓)
SMTP_FROM=dmarc-reports@einsle.cloud
ALERT_RECIPIENT=robert@einsle.com
```

#### Optional Configuration
```
SCHEDULER_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
```

### 3.4 Verify Variables

Nach dem Hinzufügen aller Variablen:
1. Überprüfen Sie die Liste
2. Stellen Sie sicher, dass alle **required** Variablen vorhanden sind
3. Secrets sollten als `***` angezeigt werden

## Step 4: Configure Persistent Storage

Coolify automatically manages volumes defined in `docker-compose.yaml`:

- **dmarc-data**: SQLite database storage (`/app/data`)
- **logs**: Application logs (`/app/logs`)

These are already configured in the `docker-compose.yaml`.

## Step 5: Configure Domain (Optional)

1. In Coolify service settings, go to **Domains**
2. Add your domain (e.g., `dmarc.example.com`)
3. Coolify will automatically:
   - Configure reverse proxy
   - Set up SSL/TLS certificate (Let's Encrypt)
   - Handle port mapping

If you don't configure a domain, Coolify will provide a default URL.

## Step 6: Enable Auto-Deploy on Git Push

### 6.1 Enable Automatic Deployment in Coolify

1. **Navigate to your service** in Coolify Dashboard
2. Go to **"General"** or **"Source"** tab
3. Find **"Automatic Deployment"** or **"Auto Deploy"** section
4. **Toggle ON** the automatic deployment switch
5. **Select trigger branch**: `main` (or your preferred branch)
6. **Save changes**

### 6.2 Configure GitHub Webhook (if using GitHub App)

If you selected **"Private Repository (with GitHub App)"** in Step 2:

#### Option 1: Automatic Webhook (Recommended)

Coolify usually creates the webhook automatically when you use the GitHub App. Verify:

1. Go to your GitHub repository
2. Navigate to **Settings** → **Webhooks**
3. You should see a webhook pointing to your Coolify instance
4. Status should show a green checkmark ✓

#### Option 2: Manual Webhook Setup

If webhook wasn't created automatically:

1. **In Coolify**:
   - Navigate to your service → **"Source"** or **"Webhooks"** tab
   - Copy the **Webhook URL** (usually looks like: `https://coolify.yourdomain.com/api/v1/deploy/webhook/...`)

2. **In GitHub**:
   - Go to your repository: `https://github.com/roberteinsle/dmarc-reports-mail`
   - Click **Settings** → **Webhooks** → **Add webhook**

3. **Configure Webhook**:
   - **Payload URL**: Paste the Coolify webhook URL
   - **Content type**: `application/json`
   - **Secret**: Leave empty (unless Coolify provides one)
   - **Which events would you like to trigger this webhook?**
     - Select: ☑ **Just the push event**
   - **Active**: ☑ Checked
   - Click **Add webhook**

4. **Test Webhook**:
   - GitHub will send a test ping
   - Check **Recent Deliveries** tab
   - Should see a green checkmark for successful delivery

### 6.3 Verify Auto-Deploy Works

Test the automatic deployment:

1. **Make a small change** to your repository (e.g., update README.md)
   ```bash
   echo "# Test Auto-Deploy" >> README.md
   git add README.md
   git commit -m "Test: Verify Coolify auto-deploy"
   git push origin main
   ```

2. **Watch Coolify Dashboard**:
   - Should automatically start a new deployment
   - Monitor logs in real-time
   - Wait for "Deployment successful"

3. **Check GitHub Webhook**:
   - GitHub → Settings → Webhooks → Recent Deliveries
   - Should see the push event with 200 OK response

**🎉 Now every `git push` to `main` branch will automatically trigger a deployment!**

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
3. **Check Docker Compose**: Ensure `docker-compose.yaml` is valid and located at repository root

### Service Unhealthy

1. **Check Application Logs**: Look for errors in Coolify logs
2. **Verify Database**: Ensure volume is properly mounted
3. **Test Health Endpoint**: `curl https://your-domain/health`

### Database Permission Errors

If you see "unable to open database file" or permission errors:

1. **Root Cause**: Docker volumes in Coolify are often mounted with root ownership
2. **Solution**: The application automatically fixes this. The Docker container:
   - Starts as root
   - Fixes volume permissions for the `appuser` (UID 1000)
   - Drops to `appuser` before running the application
3. **Verify**: Check logs for "Fixing volume permissions..." and "Write permissions verified successfully"
4. **Manual Check**: SSH into container and verify:
   ```bash
   docker exec -it dmarc-analyzer ls -la /app/data
   # Should show: drwxr-xr-x appuser appuser
   ```

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
1. Update `docker-compose.yaml` or `Dockerfile`
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
