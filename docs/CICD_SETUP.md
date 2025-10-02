# CI/CD Setup Guide

## Overview

Your CI/CD pipeline is configured with GitHub Actions to automatically:
- ✅ Run tests on every push
- ✅ Build the application
- ✅ Deploy to production on main/master branch
- ✅ Run health checks
- ✅ Rollback on failure

---

## Setup Instructions

### Step 1: Add SSH Key to GitHub Secrets

1. **Generate a deployment SSH key** (if you don't have one):
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/aquapredict_deploy -N ""
   ```

2. **Add public key to your server**:
   ```bash
   # Copy the public key
   cat ~/.ssh/aquapredict_deploy.pub
   
   # SSH to your server
   ssh opc@92.5.94.60
   
   # Add to authorized_keys
   echo "YOUR_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

3. **Add private key to GitHub Secrets**:
   - Go to your GitHub repository
   - Click **Settings** → **Secrets and variables** → **Actions**
   - Click **New repository secret**
   - Name: `SSH_PRIVATE_KEY`
   - Value: Paste the content of `~/.ssh/aquapredict_deploy` (the private key)
   - Click **Add secret**

### Step 2: Test the Workflow

1. **Make a small change** to your code
2. **Commit and push** to main/master branch:
   ```bash
   git add .
   git commit -m "Test CI/CD deployment"
   git push origin main
   ```

3. **Watch the deployment**:
   - Go to your GitHub repository
   - Click **Actions** tab
   - Watch the workflow run

### Step 3: Verify Deployment

Once the workflow completes:
- ✅ Check http://92.5.94.60 (frontend)
- ✅ Check http://92.5.94.60/health (backend)
- ✅ Check http://92.5.94.60/api/docs (API documentation)

---

## Workflow Details

### Triggers

The workflow runs on:
- Every push to `main` or `master` branch
- Manual trigger via GitHub Actions UI

### Jobs

#### 1. **Test Job**
- Runs Python linting (flake8)
- Runs Python tests (pytest)
- Runs frontend linting
- Builds frontend to verify no errors

#### 2. **Deploy Job**
- Pulls latest code on server
- Updates backend dependencies
- Restarts backend service
- Builds and restarts frontend
- Runs health checks

#### 3. **Rollback Job**
- Automatically triggers if deployment fails
- Reverts to previous git commit
- Restarts services

---

## Environment Variables

The workflow uses these environment variables (defined in `.github/workflows/deploy.yml`):

```yaml
DEPLOY_HOST: 92.5.94.60
DEPLOY_USER: opc
APP_DIR: /opt/AquaPredict
```

To change these, edit `.github/workflows/deploy.yml`.

---

## Adding More Secrets

You can add more secrets for sensitive data:

### Example: Add Database Credentials

1. Go to GitHub **Settings** → **Secrets and variables** → **Actions**
2. Add secrets:
   - `DB_PASSWORD`
   - `API_KEY`
   - etc.

3. Use in workflow:
   ```yaml
   - name: Deploy with secrets
     env:
       DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
     run: |
       echo "DB_PASSWORD=$DB_PASSWORD" >> /opt/AquaPredict/.env
   ```

---

## Manual Deployment

You can also trigger deployment manually:

1. Go to **Actions** tab in GitHub
2. Click **Deploy AquaPredict** workflow
3. Click **Run workflow**
4. Select branch
5. Click **Run workflow**

---

## Monitoring Deployments

### View Logs

```bash
# Backend logs
ssh opc@92.5.94.60
sudo journalctl -u aquapredict-api -f

# Frontend logs
pm2 logs aquapredict-frontend
```

### Check Service Status

```bash
# Backend
sudo systemctl status aquapredict-api

# Frontend
pm2 status
```

---

## Troubleshooting

### Deployment Fails

1. **Check GitHub Actions logs**:
   - Go to Actions tab
   - Click on failed workflow
   - Review error messages

2. **Check server logs**:
   ```bash
   ssh opc@92.5.94.60
   sudo journalctl -u aquapredict-api -n 100
   pm2 logs aquapredict-frontend --lines 100
   ```

3. **Manual rollback**:
   ```bash
   ssh opc@92.5.94.60
   cd /opt/AquaPredict
   git log --oneline -5  # See recent commits
   git reset --hard COMMIT_HASH  # Rollback to specific commit
   sudo systemctl restart aquapredict-api
   pm2 restart aquapredict-frontend
   ```

### SSH Connection Issues

1. **Verify SSH key is correct**:
   ```bash
   # Test SSH connection
   ssh -i ~/.ssh/aquapredict_deploy opc@92.5.94.60
   ```

2. **Check GitHub secret**:
   - Make sure you copied the entire private key
   - Include `-----BEGIN PRIVATE KEY-----` and `-----END PRIVATE KEY-----`

### Health Check Fails

1. **Check if services are running**:
   ```bash
   curl http://92.5.94.60/health
   ```

2. **Increase health check delay** in workflow:
   ```yaml
   - name: Health Check
     run: |
       sleep 10  # Increase from 5 to 10 seconds
       curl -f http://92.5.94.60/health
   ```

---

## Advanced Configuration

### Deploy to Multiple Environments

Create separate workflows for staging and production:

**`.github/workflows/deploy-staging.yml`**:
```yaml
env:
  DEPLOY_HOST: staging.yourdomain.com
  DEPLOY_USER: opc
  APP_DIR: /opt/AquaPredict
```

**`.github/workflows/deploy-production.yml`**:
```yaml
env:
  DEPLOY_HOST: 92.5.94.60
  DEPLOY_USER: opc
  APP_DIR: /opt/AquaPredict
```

### Add Slack/Discord Notifications

Add notification step:

```yaml
- name: Notify Slack
  if: always()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Run Database Migrations

Add migration step before restarting:

```yaml
- name: Run Migrations
  run: |
    ssh -i ~/.ssh/deploy_key opc@92.5.94.60 << 'ENDSSH'
      cd /opt/AquaPredict
      source venv/bin/activate
      python manage.py migrate
    ENDSSH
```

---

## Next Steps

1. ✅ Add SSH key to GitHub Secrets
2. ✅ Test deployment by pushing a change
3. ✅ Monitor first deployment
4. ✅ Set up notifications (optional)
5. ✅ Add more tests (optional)

---

## Summary

Your CI/CD pipeline is ready! Every time you push to main/master:

1. 🧪 Tests run automatically
2. 🏗️ Application builds
3. 🚀 Deploys to production
4. 🏥 Health checks verify deployment
5. ⏮️ Auto-rollback if anything fails

**Happy deploying!** 🎉
