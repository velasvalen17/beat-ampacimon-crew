# 🏀 Beat Ampacimon Crew - Deployment Quick Start

## What's Ready

Your NBA Fantasy Optimizer "Beat Ampacimon Crew" is now containerized and ready for 24/7 deployment on your Portainer server!

## 🚀 Quick Deploy to Portainer

### Option 1: Deploy from GitHub (⭐ RECOMMENDED)

```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Initial commit - Beat Ampacimon Crew"
git remote add origin https://github.com/YOUR_USERNAME/beat-ampacimon-crew.git
git push -u origin main

# 2. Deploy in Portainer (http://nas.local:9000/)
#    - Stacks → Add stack
#    - Name: beat-ampacimon-crew
#    - Build method: Repository
#    - Repository URL: https://github.com/YOUR_USERNAME/beat-ampacimon-crew
#    - Compose path: docker-compose.yml
#    - Deploy!

# 3. Access your app
#    http://nas.local:5000

# 4. Update anytime
git add .
git commit -m "Made updates"
git push
# Redeploy in Portainer or enable auto-updates!
```

**See detailed guide:** [GITHUB_DEPLOY.md](GITHUB_DEPLOY.md)

### Option 2: Manual Image Transfer (Legacy)

```bash
# Test everything works locally
./test-docker-local.sh

# Access at http://localhost:5000
# When satisfied, proceed with Option 1
```

## 📦 What's Included

The Docker container runs:
- ✅ **Flask web application** (Gunicorn, production-ready)
- ✅ **Automated daily updates** (Cron jobs at 6 AM ET)
- ✅ **SQLite database** (persisted in Docker volume)
- ✅ **Health monitoring** (automatic restart if unhealthy)

## 🎨 Features

- **Ampacimon-branded UI** with company logo
- **Dark blue theme** matching Ampacimon's corporate style
- **Responsive design** for mobile and desktop
- **Real-time lineup analysis**
- **Automated player statistics updates**

## 📊 After Deployment

Your app will be available at:
- **LAN:** http://nas.local:5000
- **Direct IP:** http://[your-nas-ip]:5000

The app will:
1. Initialize database on first start (2-5 minutes)
2. Fetch last 7 days of NBA data
3. Start the web interface
4. Run daily updates automatically

## 📖 Documentation

- **Full deployment guide:** [PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md)
- **Docker quickstart:** [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md)
- **Database info:** [DATABASE_README.md](DATABASE_README.md)

## 🔧 Common Tasks

### View Logs
```bash
docker logs -f beat-ampacimon-crew
```

### Restart Container
In Portainer: Containers → beat-ampacimon-crew → Restart

### Access Database
```bash
docker exec -it beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db
```

### Update Application
1. Make your changes
2. Run `./build-for-portainer.sh`
3. Transfer new image to NAS
4. In Portainer: Pull and redeploy stack

## 🌐 Port Configuration

Default: Port 5000

To change (e.g., to 8080):
- Edit `docker-compose.portainer.yml`
- Change `"5000:5000"` to `"8080:5000"`
- Redeploy in Portainer

## 💾 Data Persistence

Everything persists across container restarts:
- Database: `nba-fantasy-data` volume
- Logs: `nba-fantasy-logs` volume

## 🎯 Production Ready

- Gunicorn WSGI server (not Flask dev server)
- Health checks enabled
- Auto-restart on failure
- Structured logging
- Timezone support

## ⚠️ Important Notes

- **First startup:** Takes 2-5 minutes to initialize
- **Timezone:** Set to Europe/Madrid (adjust in docker-compose.portainer.yml)
- **Updates:** Run automatically at 6 AM ET
- **Security:** HTTP only, LAN use recommended

## 🆘 Troubleshooting

**Container won't start?**
- Check Portainer logs
- Verify port 5000 is available
- Ensure Docker has enough resources

**Can't access web interface?**
- Verify container is running
- Check NAS firewall
- Try IP instead of hostname

**Need help?**
See [PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md) for detailed troubleshooting

---

Ready to deploy? Run `./build-for-portainer.sh` to begin! 🚀
