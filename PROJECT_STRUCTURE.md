# NBA Fantasy - Beat Ampacimon Crew

## Project Structure

```
.
├── app/                    # Core application modules
│   ├── web_app.py         # Flask web application
│   ├── database.py        # Database utilities
│   ├── fantasy_calculator.py
│   └── query_utils.py
│
├── scripts/               # Utility and maintenance scripts
│   ├── daily_update.py    # Automated daily data updates
│   ├── populate_database.py
│   ├── salary_scraper.py
│   └── *.sh               # Shell scripts for deployment
│
├── config/                # Configuration files
│   ├── docker-compose.yml
│   ├── docker-compose.portainer.yml
│   └── crontab
│
├── tests/                 # Test and debug scripts
│   ├── test_*.py
│   └── debug_*.py
│
├── docs/                  # Documentation
│   ├── README.md
│   ├── DEPLOY.md
│   ├── DATABASE_README.md
│   └── *.md               # Various documentation files
│
├── templates/             # Flask HTML templates
├── static/                # Static web assets (CSS, JS)
├── data/                  # Data files and CSV exports
├── logs/                  # Application logs
│
├── Dockerfile             # Docker image definition
├── requirements.txt       # Python dependencies
└── nba_fantasy.db        # SQLite database

```

## Quick Start

### Docker (Recommended)

```bash
# Build and run
docker-compose -f config/docker-compose.yml up -d

# Check status
./scripts/status.sh

# Manual update
./scripts/manual-update.sh
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run web app
python app/web_app.py
```

## Documentation

- [Deployment Guide](docs/DEPLOY.md)
- [Database Documentation](docs/DATABASE_README.md)
- [Docker Quick Start](docs/DOCKER_QUICKSTART.md)
- [Portainer Deployment](docs/PORTAINER_DEPLOYMENT.md)

For more information, see the [START_HERE.md](docs/START_HERE.md) guide.
