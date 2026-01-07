# Scripts

This folder contains utility and maintenance scripts:

## Data Management
- **populate_database.py** - Populate database with NBA data
- **populate_december.py** - Specific December data population
- **daily_update.py** - Daily automated data updates
- **fetch_schedule.py** - Fetch game schedules
- **import_schedule.py** - Import schedule from CSV

## Salary Management
- **salary_scraper.py** - Scrape player salaries (Selenium)
- **scrape_salaries_simple.py** - Simplified salary scraper

## Analysis & Optimization
- **team_optimizer.py** - Team optimization algorithms
- **daily_lineups.py** - Generate daily lineup recommendations
- **show_*.py** - Various display scripts for schedules and lineups
- **simple_depth_recs.py** - Depth recommendation calculations

## Deployment & Monitoring
- **docker-entrypoint.sh** - Docker container initialization
- **start-services.sh** - Start cron and Flask services
- **manual-update.sh** - Manually trigger data updates
- **status.sh** - Check container and database status
- **check_progress.sh** - Monitor data population progress
- **build-for-portainer.sh** - Build Docker image for Portainer
- **deploy-on-nas.sh** - Deploy to NAS server
- **setup-github.sh** - GitHub deployment setup
- **start_docker.sh** - Start Docker containers
- **test-docker-local.sh** - Test Docker setup locally