# 🏀 NBA Fantasy Database - Docker Container

Your NBA Fantasy database is now containerized and will run continuously with automatic daily updates!

## 🚀 Quick Start

```bash
# One command to start everything:
./start_docker.sh
```

This will:
- Build the Docker image
- Start the container in the background
- Initialize the database (if needed)
- Set up automatic daily updates at 6 AM

## 📊 Check Status

```bash
# View current database statistics and recent games:
./status.sh
```

## 🔧 Common Commands

### View Live Logs
```bash
docker-compose logs -f nba-fantasy
```

### Run Update Manually (anytime)
```bash
docker-compose exec nba-fantasy python3 /app/daily_update.py
```

### Access Database
```bash
# From host machine
sqlite3 data/nba_fantasy.db

# From inside container
docker-compose exec nba-fantasy sqlite3 /app/data/nba_fantasy.db
```

### Container Management
```bash
# Stop container
docker-compose stop

# Start container
docker-compose start

# Restart container
docker-compose restart

# View container status
docker-compose ps

# Stop and remove container
docker-compose down
```

## 📁 File Structure

```
myproject/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Container orchestration
├── crontab                 # Daily update schedule (6 AM)
├── docker-entrypoint.sh    # Container startup script
├── daily_update.py         # Daily update script
├── start_docker.sh         # Easy setup script ⭐
├── status.sh               # Check container status ⭐
├── data/                   # Database storage (persistent)
│   └── nba_fantasy.db
└── logs/                   # Update logs (persistent)
    └── updates.log
```

## ⚙️ How It Works

1. **Continuous Operation**: Container runs 24/7 in the background
2. **Daily Updates**: Cron job runs at 6 AM every day
3. **Automatic Updates**:
   - Fetches yesterday's and today's games
   - Updates team rosters for active teams
   - Fetches player statistics for new games
4. **Persistent Data**: Database and logs survive container restarts

## 🔄 Update Schedule

Default: **6 AM daily**

To change the schedule, edit `crontab`:

```bash
# Examples:
# Every 6 hours:        0 */6 * * *
# Twice daily (6,18):   0 6,18 * * *
# Every hour:           0 * * * *
```

Then rebuild:
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## 📦 What Gets Updated Daily

- ✅ New games (yesterday + today)
- ✅ Team rosters (for teams with recent games)
- ✅ Player statistics (for all new games)
- ✅ Automatic data consistency checks

## 🔐 Data Persistence

Your data is stored in:
- **Database**: `./data/nba_fantasy.db`
- **Logs**: `./logs/updates.log`

These directories persist even if you:
- Restart the container
- Rebuild the image
- Restart your system

## 🛟 Troubleshooting

### Container won't start
```bash
# Check logs for errors
docker-compose logs

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Updates not running
```bash
# Check cron status
docker-compose exec nba-fantasy ps aux | grep cron

# Run update manually to test
docker-compose exec nba-fantasy python3 /app/daily_update.py

# Check update logs
tail -f logs/updates.log
```

### Database issues
```bash
# Check database integrity
sqlite3 data/nba_fantasy.db "PRAGMA integrity_check;"

# View table counts
sqlite3 data/nba_fantasy.db "SELECT 'teams', COUNT(*) FROM teams UNION ALL SELECT 'games', COUNT(*) FROM games;"
```

## 💾 Backup

```bash
# Create backup
cp data/nba_fantasy.db "data/backup_$(date +%Y%m%d_%H%M%S).db"

# Or use SQLite backup
sqlite3 data/nba_fantasy.db ".backup 'data/backup_$(date +%Y%m%d).db'"
```

## 📈 Monitoring

### View Update Logs in Real-Time
```bash
tail -f logs/updates.log
```

### Check Last Update
```bash
tail -n 20 logs/updates.log
```

### Database Statistics
```bash
./status.sh
```

## 🌐 Production Deployment

For production servers:

1. **Set timezone** in `docker-compose.yml`:
   ```yaml
   environment:
     - TZ=America/New_York  # Your timezone
   ```

2. **Auto-restart on system boot**:
   ```yaml
   restart: unless-stopped  # Already configured
   ```

3. **Monitor with healthcheck**:
   ```bash
   docker-compose ps  # Shows health status
   ```

## 🎯 Next Steps

1. ✅ Container is running automatically
2. ✅ Daily updates scheduled for 6 AM
3. ✅ Data persists across restarts
4. 📊 Check `./status.sh` anytime to view stats
5. 📝 Monitor `./logs/updates.log` for update history

## 📚 Documentation

- **Full Docker guide**: [README_DOCKER.md](README_DOCKER.md)
- **Database schema**: [DATABASE_README.md](DATABASE_README.md)
- **Project README**: [README.md](README.md)

---

**Your NBA Fantasy database is now running in production mode! 🎉**

Check status: `./status.sh`  
View logs: `docker-compose logs -f`  
Manual update: `docker-compose exec nba-fantasy python3 /app/daily_update.py`
