#!/bin/bash
set -e

echo "NBA Fantasy Database Container Starting..."

# Initialize database if it doesn't exist
if [ ! -f "/app/data/nba_fantasy.db" ]; then
    echo "Database not found. Initializing..."
    cd /app
    python3 -c "from database import init_database; init_database()"
    echo "Database initialized."
    
    # Populate initial data for the past 7 days
    echo "Populating initial data (last 7 days)..."
    python3 - <<'PYTHON'
from datetime import datetime, timedelta
from populate_database import DatabasePopulator

# Get dates
today = datetime.now().date()
week_ago = today - timedelta(days=7)

print(f"Fetching data from {week_ago} to {today}...")

# Populate teams
DatabasePopulator.populate_teams()

# Populate games
DatabasePopulator.populate_games(
    from_date=week_ago,
    to_date=today
)

print("Initial data populated!")
PYTHON
    
    echo "Running first player stats update..."
    python3 /app/daily_update.py
fi

echo "Starting cron daemon..."
# Start cron in foreground
exec "$@"
