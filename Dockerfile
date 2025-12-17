# NBA Fantasy Database Docker Container
FROM python:3.12-slim

# Install cron, SQLite, and wget
RUN apt-get update && apt-get install -y \
    cron \
    sqlite3 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py .
COPY *.sh .
RUN chmod +x *.sh

# Copy web application assets
COPY templates/ ./templates/
COPY static/ ./static/

# Create directory for database
RUN mkdir -p /app/data

# Set up environment variable for database path
ENV DB_PATH=/app/data/nba_fantasy.db

# Copy cron job configuration
COPY crontab /etc/cron.d/nba-updates
RUN chmod 0644 /etc/cron.d/nba-updates && \
    crontab /etc/cron.d/nba-updates

# Create log directory
RUN mkdir -p /var/log/nba-fantasy && \
    touch /var/log/nba-fantasy/updates.log && \
    touch /var/log/cron.log

# Initialize database on first run
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Expose Flask port
EXPOSE 5000

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["./start-services.sh"]
