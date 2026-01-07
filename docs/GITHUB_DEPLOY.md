# 🚀 Deploy Beat Ampacimon Crew from GitHub to Portainer

## Quick Setup (One-Time)

### 1. Push to GitHub

```bash
cd /home/velasvalen17/myproject

# Initialize git if not already done
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit - Beat Ampacimon Crew NBA Fantasy App"

# Create repo on GitHub (via web interface)
# Then link and push:
git remote add origin https://github.com/YOUR_USERNAME/beat-ampacimon-crew.git
git branch -M main
git push -u origin main
```

### 2. Deploy in Portainer

1. **Open Portainer:** http://nas.local:9000/

2. **Go to Stacks → Add stack**

3. **Configure:**
   - **Name:** `beat-ampacimon-crew`
   - **Build method:** Select **"Repository"**
   
4. **Repository settings:**
   - **Repository URL:** `https://github.com/YOUR_USERNAME/beat-ampacimon-crew`
   - **Repository reference:** `refs/heads/main`
   - **Compose path:** `docker-compose.yml`
   - **Authentication:** Leave empty (for public repo) or add credentials

5. **Enable auto-update (Optional but recommended):**
   - Check **"Enable automatic updates"**
   - Set interval (e.g., 5 minutes)
   - Portainer will auto-pull and redeploy on git changes

6. **Click "Deploy the stack"**

### 3. Wait for Build

- First build takes 3-5 minutes
- Portainer will:
  - Clone your repository
  - Build the Docker image
  - Start the container
  - Initialize the database (first run only)

### 4. Access Your App

Once deployed, access at:
- **http://nas.local:5000**

## 🔄 Making Updates

This is where it gets amazing! Just:

```bash
# 1. Make your changes locally
# Edit any file (web_app.py, templates, etc.)

# 2. Commit and push
git add .
git commit -m "Updated feature X"
git push

# 3. Redeploy in Portainer
# Option A: If auto-update is enabled, wait ~5 minutes
# Option B: Manual - Go to stack → "Pull and redeploy"
```

That's it! No manual file transfers, no building locally, no image transfers.

## 🎯 Advantages of Git Deployment

✅ **Easy updates:** Just git push  
✅ **Version control:** Full history of changes  
✅ **No file transfers:** Portainer pulls directly from GitHub  
✅ **Automatic updates:** Optional auto-redeploy on git changes  
✅ **Rollback capability:** Easy to revert to previous versions  
✅ **Clean workflow:** Professional development process  

## 📝 Configuration

### Change Port

Edit `docker-compose.yml` before pushing:
```yaml
ports:
  - "8080:5000"  # Change 8080 to your desired external port
```

### Change Timezone

Edit `docker-compose.yml`:
```yaml
environment:
  - TZ=Europe/Madrid  # Change to your timezone
```

Common timezones:
- `America/New_York` (ET)
- `America/Los_Angeles` (PT)
- `Europe/Madrid` (CET)
- `UTC`

### Environment Variables

Add more environment variables in Portainer stack editor or in `docker-compose.yml`.

## 🔐 Private Repository

If your repo is private:

1. **Generate GitHub Personal Access Token:**
   - GitHub → Settings → Developer settings → Personal access tokens
   - Generate new token (classic)
   - Select: `repo` scope
   - Copy the token

2. **In Portainer repository settings:**
   - **Username:** Your GitHub username
   - **Personal Access Token:** Paste the token

## 🐛 Troubleshooting

### Build fails in Portainer

**Check the build logs:**
- Portainer → Stacks → beat-ampacimon-crew → Editor → Build logs

**Common issues:**
- Dockerfile syntax error
- Missing files in repo
- Insufficient Docker resources on NAS

### Can't access after deployment

```bash
# Check if container is running
docker ps | grep beat-ampacimon-crew

# Check logs
docker logs beat-ampacimon-crew

# Check if port is accessible
curl http://localhost:5000
```

### Auto-update not working

- Verify webhook/polling is configured correctly
- Check stack update logs in Portainer
- Ensure GitHub repo is accessible

### Want to test locally first?

```bash
# On your dev machine (or NAS)
git clone https://github.com/YOUR_USERNAME/beat-ampacimon-crew.git
cd beat-ampacimon-crew
docker-compose up -d

# Access at http://localhost:5000
# When satisfied:
docker-compose down
```

## 📊 Monitoring

### View Logs
**In Portainer:**
- Containers → beat-ampacimon-crew → Logs (real-time)

**Via CLI on NAS:**
```bash
docker logs -f beat-ampacimon-crew
```

### Check Health
```bash
docker ps | grep beat-ampacimon-crew
# Look for "healthy" in status
```

### Database Status
```bash
docker exec beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db "SELECT COUNT(*) FROM players;"
```

## 🔄 Rollback to Previous Version

If something breaks after an update:

1. **In Portainer:**
   - Stacks → beat-ampacimon-crew → Editor
   - Change **Repository reference** to specific commit:
     - `refs/heads/main` → `<commit-hash>`
   - Click "Update the stack"

2. **Or revert in Git:**
   ```bash
   git revert HEAD
   git push
   # Wait for auto-update or trigger manual redeploy
   ```

## 🎨 Workflow Example

```bash
# Daily workflow for updates
cd /home/velasvalen17/myproject

# Make changes
vim templates/index.html
vim static/style.css

# Test locally if you want
# python3 web_app.py

# Commit and push
git add .
git commit -m "Improved UI styling"
git push

# Done! ✨
# Access http://nas.local:9000/ and redeploy
# Or wait for auto-update
```

## 💡 Pro Tips

1. **Use branches for testing:**
   ```bash
   git checkout -b experimental-feature
   # Make changes, test
   git push -u origin experimental-feature
   # Deploy this branch in a separate Portainer stack for testing
   # When ready: merge to main
   ```

2. **Tag releases:**
   ```bash
   git tag -a v1.0.0 -m "First production release"
   git push --tags
   # Deploy specific tags in Portainer
   ```

3. **Keep data safe:**
   - Database and logs are in Docker volumes
   - Survive stack deletions and updates
   - Backup: `docker run --rm -v nba-fantasy-data:/data -v $(pwd):/backup alpine tar czf /backup/backup.tar.gz -C /data .`

4. **Multiple environments:**
   - Deploy `main` branch for production (nas.local:5000)
   - Deploy `dev` branch for testing (nas.local:5001)
   - Different stacks in Portainer

---

## 🏁 Ready to Deploy?

1. Push to GitHub
2. Open http://nas.local:9000/
3. Create stack from repository
4. Done! 🎉

Your app will be running 24/7 with easy updates via git push!
