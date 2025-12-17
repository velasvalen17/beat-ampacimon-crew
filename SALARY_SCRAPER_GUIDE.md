# NBA Fantasy Salary Scraper - Setup Guide

## Overview
The salary scraper automates fetching player salary data from nbafantasy.nba.com and stores it in your SQLite database. This enables budget-constrained team optimization with the $100M salary cap.

## Prerequisites

### 1. Install ChromeDriver (Required for Selenium)

#### Option A: Ubuntu/Debian (Recommended)
```bash
sudo apt update
sudo apt install chromium-browser chromium-chromedriver
```

#### Option B: Download Manually
1. Visit https://googlechromelabs.github.io/chrome-for-testing/
2. Download ChromeDriver matching your Chrome version
3. Extract and move to PATH:
```bash
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
```

#### Verify Installation
```bash
chromedriver --version
```

### 2. Create Credentials File
```bash
cd ~/myproject
cp .env.example .env
nano .env  # or use your preferred editor
```

Add your NBA Fantasy credentials:
```
NBA_FANTASY_EMAIL=your_email@example.com
NBA_FANTASY_PASSWORD=your_password
DB_PATH=/home/velasvalen17/myproject/nba_fantasy.db
```

**⚠️ Security Note**: Never commit `.env` to version control!

## Usage

### Basic Usage
```bash
cd ~/myproject
source venv/bin/activate
python3 salary_scraper.py
```

### First Run (with visible browser for debugging)
```bash
python3 salary_scraper.py --no-headless
```

This allows you to:
- Verify login works correctly
- Handle any CAPTCHA/2FA if present
- Confirm the page structure matches expected format

### Command Line Options
```bash
# Specify credentials directly (overrides .env)
python3 salary_scraper.py --email user@example.com --password mypass

# Use non-headless mode (see browser window)
python3 salary_scraper.py --no-headless

# Custom database path
python3 salary_scraper.py --db-path /path/to/database.db
```

## Expected Output

### Success
```
🏀 NBA Fantasy Salary Scraper
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 Email: your_email@example.com
🔐 Password: ******
🗄️  Database: /home/velasvalen17/myproject/nba_fantasy.db
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🌐 Opening browser...
🔑 Logging in to NBA Fantasy...
📊 Scraping salary data...
💾 Updating database...

✅ Successfully updated 487 players
📋 Could not match 12 players (saved to salary_mismatches.log)

Total time: 45.3s
```

### Troubleshooting

#### Login Issues
- **CAPTCHA/2FA**: Run with `--no-headless`, complete verification manually
- **Invalid credentials**: Verify email/password in `.env`
- **Timeout**: Increase wait time in salary_scraper.py (line 89)

#### Page Structure Changed
If the scraper fails to find salary data:
1. Run with `--no-headless` to see the page
2. Check the HTML table structure on statistics page
3. Update CSS selectors in `scrape_salaries()` method

#### Player Name Mismatches
Review `salary_mismatches.log` for players that couldn't be matched:
- Some names may differ between nba.com and nbafantasy.nba.com
- The scraper uses fuzzy matching (95% similarity threshold)
- Adjust threshold in salary_scraper.py if needed

## After Scraping

### Verify Data
```bash
sqlite3 nba_fantasy.db "SELECT player_name, salary FROM players WHERE salary IS NOT NULL LIMIT 10;"
```

### Run Team Optimizer with Salary Constraints
```bash
python3 team_optimizer.py
```

#### Custom Salary Cap
```bash
python3 team_optimizer.py 95  # Use $95M cap instead of $100M
```

#### Adjust Performance vs Value Weight
```bash
python3 team_optimizer.py 100 0.5  # 50% performance, 50% value
python3 team_optimizer.py 100 0.9  # 90% performance, 10% value
```

## Automation (Optional)

Add to daily cron job to keep salaries updated:
```bash
crontab -e
```

Add line:
```
0 7 * * * cd /home/velasvalen17/myproject && source venv/bin/activate && python3 salary_scraper.py >> /tmp/salary_scraper.log 2>&1
```

This runs daily at 7 AM, logging output to `/tmp/salary_scraper.log`.

## File Locations

- **Main Script**: `salary_scraper.py`
- **Credentials**: `.env` (gitignored)
- **Database**: `nba_fantasy.db`
- **Mismatch Log**: `salary_mismatches.log`
- **Error Screenshots**: `/tmp/nba_fantasy_error_*.png`

## Support

If you encounter issues:
1. Check ChromeDriver is installed: `chromedriver --version`
2. Verify credentials in `.env`
3. Run with `--no-headless` to debug visually
4. Check error screenshots in `/tmp/`
5. Review `salary_mismatches.log` for name matching issues

## Next Steps

Once salary data is populated:
1. Run `python3 team_optimizer.py` to see optimal team
2. Experiment with different salary caps and weights
3. Compare performance-focused vs value-focused teams
4. Use in Docker container for automated daily updates

---

**Note**: NBA Fantasy may update their website structure. If the scraper breaks after a site update, you may need to adjust the CSS selectors in the `scrape_salaries()` method.
