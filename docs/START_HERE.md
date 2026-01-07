# 🚀 Ready to Deploy!

Your **Beat Ampacimon Crew** app is now configured for GitHub + Portainer deployment.

## Quick Start (3 Steps)

### 1️⃣ Push to GitHub

Run the automated setup script:
```bash
./setup-github.sh
```

Or manually:
```bash
git init
git add .
git commit -m "Initial commit - Beat Ampacimon Crew"
git remote add origin https://github.com/YOUR_USERNAME/beat-ampacimon-crew.git
git push -u origin main
```

### 2️⃣ Deploy in Portainer

1. Open http://nas.local:9000/
2. Go to **Stacks** → **Add stack**
3. Configure:
   - **Name:** `beat-ampacimon-crew`
   - **Build method:** Repository
   - **Repository URL:** `https://github.com/YOUR_USERNAME/beat-ampacimon-crew`
   - **Compose path:** `docker-compose.yml`
   - *Optional:* Enable automatic updates
4. Click **Deploy the stack**

### 3️⃣ Access Your App

Open: **http://nas.local:5000**

## ✨ That's It!

Your app is now:
- ✅ Running 24/7 on your NAS
- ✅ Automatically updating NBA data daily
- ✅ Easy to update (just `git push`)
- ✅ Fully branded with Ampacimon design
- ✅ Production-ready with Gunicorn

## 📚 Documentation

- **[GITHUB_DEPLOY.md](GITHUB_DEPLOY.md)** - Complete GitHub deployment guide
- **[DEPLOY.md](DEPLOY.md)** - General deployment overview
- **[README_GITHUB.md](README_GITHUB.md)** - Will become README.md on GitHub

## 🔄 Making Updates

```bash
# Edit files
vim templates/index.html

# Commit and push
git add .
git commit -m "Updated UI"
git push

# Redeploy in Portainer
# (or wait for auto-update if enabled)
```

## 🎯 Why This Approach?

✅ **No manual file transfers** - Portainer pulls from GitHub  
✅ **Version control** - Full git history  
✅ **Easy rollbacks** - Revert to any commit  
✅ **Auto-updates** - Optional automatic redeployment  
✅ **Professional workflow** - Industry standard practice  
✅ **Team collaboration** - Others can contribute via GitHub  

## 🛠️ What's Configured

- **Docker image:** Builds from source in Portainer
- **Web server:** Gunicorn (production-ready)
- **Database:** SQLite in persistent Docker volume
- **Updates:** Cron jobs run daily at 6 AM ET
- **Port:** 5000 (configurable)
- **Timezone:** Europe/Madrid (configurable)

## 📊 Monitoring

Once deployed, monitor via:
- **Portainer UI:** Real-time logs and stats
- **Health checks:** Automatic container restart if unhealthy
- **Logs:** Docker volumes persist logs

---

**Ready?** Run `./setup-github.sh` to begin! 🎉
