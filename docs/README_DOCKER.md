# NBA Fantasy Database - Docker Setup

This Docker container runs the NBA Fantasy database with automatic daily updates.

## Quick Start

### 1. Build and Start the Container

```bash
# Build the Docker image
docker-compose build

# Start the container (runs in background)
docker-compose up -d
```

### 2. Check Container Status

```bash
# View logs
docker-compose logs -f nba-fantasy

# Check if container is running
docker-compose ps

# View update logs
tail -f logs/updates.log
```

### 3. Access the Database

The database file is stored in `./data/nba_fantasy.db` and can be accessed:

```bash
# From host machine
sqlite3 data/nba_fantasy.db "SELECT COUNT(*) FROM games;"

# From inside container
docker-compose exec nba-fantasy sqlite3 /app/data/nba_fantasy.db
```

## How It Works

1. **Automatic Updates**: The container runs a cron job every day at 6 AM that:
   - Fetches new games from yesterday and today
   - Updates team rosters for active teams
   - Fetches player statistics for new games

2. **Persistent Data**: 
   - Database stored in `./data/` directory (persists across container restarts)
   - Logs stored in `./logs/` directory

3. **Always Running**: Container restarts automatically if it crashes or after system reboot

## Manual Operations

### Run Update Manually

```bash
# Trigger an update right now
docker-compose exec nba-fantasy python3 /app/daily_update.py
```

### View Database Statistics

```bash
docker-compose exec nba-fantasy bash /app/check_progress.sh
```

### Access Python Shell

```bash
docker-compose exec nba-fantasy python3
```

### Populate Historical Data

```bash
# Populate all December data
docker-compose exec nba-fantasy python3 /app/populate_december.py
```

## Maintenance

### Stop Container

```bash
docker-compose stop
```

### Start Container

```bash
docker-compose start
```

### Restart Container

```bash
docker-compose restart
```

### View Live Logs

```bash
docker-compose logs -f
```

### Rebuild After Code Changes

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Configuration

Edit `docker-compose.yml` to customize:

- **Timezone**: Change `TZ` environment variable
- **Update Schedule**: Edit `crontab` file (currently 6 AM daily)
- **Season Year**: Change `SEASON_YEAR` environment variable

## Backup

The database is stored in `./data/nba_fantasy.db`. To backup:

```bash
# Create backup
cp data/nba_fantasy.db data/nba_fantasy_backup_$(date +%Y%m%d).db

# Or use SQLite backup
sqlite3 data/nba_fantasy.db ".backup data/backup_$(date +%Y%m%d).db"
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs

# Check if port conflicts exist
docker-compose ps
```

### Updates not running

```bash
# Check cron is running
docker-compose exec nba-fantasy ps aux | grep cron

# Check cron logs
docker-compose exec nba-fantasy cat /var/log/cron.log

# Manually test update
docker-compose exec nba-fantasy python3 /app/daily_update.py
```

### Database corruption

```bash
# Check database integrity
sqlite3 data/nba_fantasy.db "PRAGMA integrity_check;"

# Restore from backup if needed
cp data/nba_fantasy_backup_YYYYMMDD.db data/nba_fantasy.db
docker-compose restart
```

## Advanced Usage

### Custom Update Schedule

Edit `crontab`:
```
# Every 6 hours
0 */6 * * * cd /app && /usr/local/bin/python3 /app/daily_update.py >> /var/log/nba-fantasy/updates.log 2>&1

# Twice daily (6 AM and 6 PM)
0 6,18 * * * cd /app && /usr/local/bin/python3 /app/daily_update.py >> /var/log/nba-fantasy/updates.log 2>&1
```

Then rebuild: `docker-compose build && docker-compose up -d`

### Export Data on Schedule

Add to crontab:
```
0 7 * * * cd /app && /usr/local/bin/python3 -c "from query_utils import QueryUtils; QueryUtils.export_games_to_csv('games_daily.csv')" >> /var/log/nba-fantasy/exports.log 2>&1
```
