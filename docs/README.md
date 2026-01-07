# 🏀 Beat Ampacimon Crew

NBA Fantasy Lineup Optimizer with Ampacimon branding - Optimizes your fantasy basketball roster using real-time NBA statistics and game schedules.

![Ampacimon](https://media.licdn.com/dms/image/v2/D4E0BAQF-NwcxYJyG7A/company-logo_200_200/company-logo_200_200/0/1692891594402/ampacimon_logo?e=2147483647&v=beta&t=qXAlftQweEpdeKDACCCWXdEeAv79_pBFR2INAzLMhlk)

## Features

- 🎨 **Ampacimon-branded UI** - Professional design matching Ampacimon corporate style
- 📊 **Real-time NBA data** - Automatically fetches player statistics and game schedules
- 💰 **Salary optimization** - Maximize value within budget constraints
- 📅 **Gameweek analysis** - Analyzes game coverage for optimal lineup selection
- 🤖 **AI-powered recommendations** - Suggests optimal transfers and lineup changes
- 🔄 **Automated updates** - Daily cron jobs keep data fresh

## Tech Stack

- **Backend:** Python 3.12, Flask, SQLite
- **Frontend:** Vanilla JavaScript, HTML5, CSS3
- **Data Source:** NBA API
- **Deployment:** Docker, Docker Compose
- **Server:** Gunicorn (production WSGI)

## Quick Start

### Deploy to Portainer (Recommended)

1. **In Portainer UI:**
   - Navigate to **Stacks** → **Add stack**
   - Name: `beat-ampacimon-crew`
   - Build method: **Repository**
   - Repository URL: `https://github.com/YOUR_USERNAME/beat-ampacimon-crew`
   - Compose path: `docker-compose.yml`
   - Click **Deploy the stack**

2. **Access the app:**
   - http://nas.local:5000

See [GITHUB_DEPLOY.md](GITHUB_DEPLOY.md) for detailed instructions.

### Local Development

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/beat-ampacimon-crew.git
cd beat-ampacimon-crew

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python3 -c "from database import init_database; init_database()"

# Run the web app
python3 web_app.py

# Access at http://localhost:5000
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://localhost:5000

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Project Structure

```
.
├── web_app.py              # Flask web application
├── database.py             # Database schema and initialization
├── nba_data_fetcher.py     # NBA API data fetching
├── daily_update.py         # Automated daily updates
├── team_optimizer.py       # Lineup optimization logic
├── templates/              # HTML templates
│   └── index.html
├── static/                 # CSS and JavaScript
│   ├── style.css
│   └── app.js
├── Dockerfile              # Container definition
├── docker-compose.yml      # Docker orchestration
└── requirements.txt        # Python dependencies
```

## Configuration

### Timezone

Edit `docker-compose.yml`:
```yaml
environment:
  - TZ=Europe/Madrid  # Change to your timezone
```

### Port

Edit `docker-compose.yml`:
```yaml
ports:
  - "5000:5000"  # Change first number for external port
```

### Database Path

Set via environment variable:
```yaml
environment:
  - DB_PATH=/app/data/nba_fantasy.db
```

## Automated Updates

The application runs daily cron jobs at 6 AM ET to:
- Fetch new player statistics
- Update game schedules
- Refresh salary data

View cron logs:
```bash
docker exec beat-ampacimon-crew cat /var/log/cron.log
```

## API Endpoints

- `GET /` - Main web interface
- `GET /api/players` - Get all players with salaries
- `GET /api/gameweeks` - Get available gameweeks
- `POST /api/analyze` - Analyze lineup and get recommendations

## Database Schema

- **teams** - NBA team information
- **players** - Player profiles and salaries
- **games** - Game schedules
- **player_statistics** - Player performance data

See [DATABASE_README.md](DATABASE_README.md) for details.

## Development

### Adding Features

```bash
# Create a feature branch
git checkout -b feature/new-feature

# Make changes and test
python3 web_app.py

# Commit and push
git add .
git commit -m "Add new feature"
git push -u origin feature/new-feature

# Create pull request on GitHub
```

### Testing

```bash
# Run specific tests
python3 test_jokic_salary.py

# Test database queries
python3 -c "from database import get_db_connection; print(get_db_connection())"
```

## Troubleshooting

### Container won't start
```bash
# Check logs
docker logs beat-ampacimon-crew

# Verify database initialization
docker exec beat-ampacimon-crew ls -la /app/data/
```

### No data showing
```bash
# Check if database is populated
docker exec beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db "SELECT COUNT(*) FROM players;"

# Manually run update
docker exec beat-ampacimon-crew python3 /app/daily_update.py
```

### Port already in use
```bash
# Find what's using the port
lsof -i :5000

# Change port in docker-compose.yml
```

## Documentation

- [DEPLOY.md](DEPLOY.md) - Quick deployment guide
- [GITHUB_DEPLOY.md](GITHUB_DEPLOY.md) - GitHub + Portainer deployment
- [PORTAINER_DEPLOYMENT.md](PORTAINER_DEPLOYMENT.md) - Detailed Portainer instructions
- [DOCKER_QUICKSTART.md](DOCKER_QUICKSTART.md) - Docker setup guide
- [DATABASE_README.md](DATABASE_README.md) - Database documentation

## License

This project is for internal use within Ampacimon.

## Support

For issues or questions, contact the development team or create an issue on GitHub.

---

**Built with ❤️ for Ampacimon**
