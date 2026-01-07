# 🔄 Beat Ampacimon Crew - Maintenance Workflow

This guide explains how to maintain your NBA Fantasy app running 24/7 on your Raspberry Pi.

## 📋 Overview

Your app runs on your Pi and automatically updates most data daily. You only need to manually update salaries weekly since Selenium doesn't run well on Raspberry Pi.

---

## 🤖 Daily Updates (Automatic)

**Your Pi handles this automatically - no action needed!**

### What Updates Automatically:
- ✅ New games and schedules
- ✅ Player rosters
- ✅ Player statistics
- ✅ Team information

### When:
- Runs daily at **6:00 AM ET** via cron job
- Triggered automatically by the Docker container

### Verify It's Working:
```bash
# Check the update logs
ssh user@nas.local
docker exec beat-ampacimon-crew cat /var/log/nba-fantasy/updates.log | tail -20

# Check latest game data
docker exec beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db \
  "SELECT MAX(game_date) FROM games;"

# Check latest player stats
docker exec beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db \
  "SELECT COUNT(*) FROM player_game_stats WHERE game_date >= date('now', '-1 day');"
```

---

## 💰 Weekly Salary Updates (Manual)

**Do this once per week (recommended: Sunday before the new week starts)**

### Step 1: Update Salaries on Your Dev Machine

```bash
# On your development machine (not the Pi)
cd /home/velasvalen17/myproject
source venv/bin/activate
python3 salary_scraper.py
```

This will:
- Open a browser with Selenium
- Scrape latest salaries from Sorare NBA
- Update the local database (takes 5-10 minutes)

### Step 2: Transfer Database to Pi

```bash
# Copy the updated database to your Pi
scp nba_fantasy.db user@nas.local:/tmp/
```

### Step 3: Update Container Database

```bash
# SSH to your Pi
ssh user@nas.local

# Copy database into container
docker cp /tmp/nba_fantasy.db beat-ampacimon-crew:/app/data/

# Restart container to ensure clean state
docker restart beat-ampacimon-crew

# Clean up temp file
rm /tmp/nba_fantasy.db
```

### Step 4: Verify Update

```bash
# Check salary data is fresh
docker exec beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db \
  "SELECT COUNT(*) FROM players WHERE salary IS NOT NULL;"
```

---

## 🔧 On-Demand Manual Updates

If you need to manually trigger a data update (e.g., after fixing a bug):

```bash
# SSH to your Pi
ssh user@nas.local

# Run the update script manually
docker exec beat-ampacimon-crew python3 /app/daily_update.py

# Watch the output for completion
```

---

## 📊 Monitoring & Troubleshooting

### View Real-Time Logs
```bash
# Live logs (Ctrl+C to exit)
docker logs -f beat-ampacimon-crew

# Last 50 lines
docker logs beat-ampacimon-crew --tail 50
```

### Check Container Status
```bash
# Is it running?
docker ps | grep beat-ampacimon-crew

# Health check status
docker inspect beat-ampacimon-crew | grep -A 10 Health
```

### Access Database Directly
```bash
# Open SQLite console
docker exec -it beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db

# Useful queries:
sqlite> SELECT COUNT(*) FROM players;
sqlite> SELECT COUNT(*) FROM games;
sqlite> SELECT COUNT(*) FROM player_game_stats;
sqlite> SELECT * FROM teams;
sqlite> .exit
```

### Restart Container
```bash
# Via Docker command
docker restart beat-ampacimon-crew

# Or in Portainer UI:
# Containers → beat-ampacimon-crew → Restart
```

### Check Cron Jobs
```bash
# View cron log
docker exec beat-ampacimon-crew cat /var/log/cron.log

# View scheduled cron jobs
docker exec beat-ampacimon-crew crontab -l
```

---

## 🚀 Updating the Application Code

When you make changes to the app code:

### Step 1: Commit and Push Changes
```bash
# On your dev machine
cd /home/velasvalen17/myproject
git add .
git commit -m "Your changes"
git push
```

### Step 2: Update on Pi

**Option A: Rebuild from GitHub (if stack deployed from repo)**
```bash
# In Portainer UI:
# Stacks → beat-ampacimon-crew → Pull and redeploy
```

**Option B: Manual rebuild on Pi**
```bash
# SSH to Pi
ssh user@nas.local

# Pull latest code
cd /tmp/beat-ampacimon-crew
git pull

# Rebuild image
docker build -t beat-ampacimon-crew:latest .

# Restart in Portainer or:
docker stop beat-ampacimon-crew
docker rm beat-ampacimon-crew
# Then redeploy stack in Portainer
```

---

## 🗓️ Recommended Schedule

### Daily (Automatic ✅)
- **6:00 AM ET:** Automatic data update runs

### Weekly (Manual - 5 minutes) 📅
- **Sunday evening:** Update salaries and sync to Pi
  1. Run `salary_scraper.py` locally
  2. SCP database to Pi
  3. Copy into container

### Monthly (Optional) 🔍
- Check logs for any errors
- Verify disk space on Pi
- Review database size

---

## 💾 Backup Strategy

### Backup Your Database

**From your Pi:**
```bash
# Backup to your dev machine
scp user@nas.local:/var/lib/docker/volumes/beat-ampacimon-crew_nba-fantasy-data/_data/nba_fantasy.db \
  ~/backups/nba_fantasy_$(date +%Y%m%d).db
```

**Or use Docker:**
```bash
# Create compressed backup
docker run --rm \
  -v beat-ampacimon-crew_nba-fantasy-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/nba-fantasy-backup-$(date +%Y%m%d).tar.gz -C /data .
```

### Restore from Backup
```bash
# Copy backup to Pi
scp nba_fantasy_backup.db user@nas.local:/tmp/

# Restore to container
ssh user@nas.local
docker cp /tmp/nba_fantasy_backup.db beat-ampacimon-crew:/app/data/nba_fantasy.db
docker restart beat-ampacimon-crew
```

---

## 🆘 Common Issues

### Salary Scraper Fails
- **Issue:** Sorare website changed layout
- **Solution:** Update `salary_scraper.py` selectors and push changes

### Daily Update Not Running
- **Check:** `docker exec beat-ampacimon-crew crontab -l`
- **Fix:** Ensure cron daemon is running: `docker exec beat-ampacimon-crew ps aux | grep cron`

### Database Locked Error
- **Issue:** Multiple processes accessing database
- **Solution:** `docker restart beat-ampacimon-crew`

### Container Won't Start
- **Check logs:** `docker logs beat-ampacimon-crew`
- **Common cause:** Database file corrupted
- **Solution:** Restore from backup

### Web App Not Accessible
- **Check:** Is container running? `docker ps`
- **Check:** Port mapping: `docker ps | grep 5000`
- **Check:** Health status: `docker inspect beat-ampacimon-crew | grep Health -A 5`

---

## 📱 Quick Reference Commands

```bash
# === MONITORING ===
docker logs -f beat-ampacimon-crew              # Live logs
docker ps | grep beat-ampacimon-crew            # Is it running?
docker exec beat-ampacimon-crew ps aux          # Processes inside

# === DATABASE ===
docker exec -it beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db
docker cp beat-ampacimon-crew:/app/data/nba_fantasy.db ./backup.db

# === UPDATES ===
docker exec beat-ampacimon-crew python3 /app/daily_update.py  # Manual update
docker restart beat-ampacimon-crew                            # Restart

# === LOGS ===
docker exec beat-ampacimon-crew cat /var/log/nba-fantasy/updates.log
docker exec beat-ampacimon-crew cat /var/log/cron.log

# === ACCESS ===
docker exec -it beat-ampacimon-crew /bin/bash  # Shell access
```

---

## 📞 Support

- **App URL:** http://nas.local:5000
- **Portainer:** http://nas.local:9000
- **GitHub:** https://github.com/velasvalen17/beat-ampacimon-crew
- **Documentation:**
  - [DEPLOY.md](DEPLOY.md) - Initial deployment
  - [GITHUB_DEPLOY.md](GITHUB_DEPLOY.md) - Git deployment
  - [DATABASE_README.md](DATABASE_README.md) - Database schema

---

**Remember:** Your Pi handles everything automatically except weekly salary updates! 🎯
