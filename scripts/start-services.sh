#!/bin/bash
set -e

echo "Starting NBA Fantasy Services..."

# Start cron in the background
cron

echo "Cron daemon started."

# Wait a moment for cron to initialize
sleep 2

echo "Starting Flask web application..."

# Start Flask app with gunicorn (production-ready)
cd /app
exec gunicorn --bind 0.0.0.0:5000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile /var/log/nba-fantasy/access.log \
    --error-logfile /var/log/nba-fantasy/error.log \
    --log-level info \
    app.web_app:app
