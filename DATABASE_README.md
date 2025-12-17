# NBA Fantasy Database

A comprehensive local database system for storing and analyzing NBA player statistics with fantasy scoring calculations based on official NBA Fantasy rules.

## Features

- **Local SQLite Database**: Lightweight, self-contained database stored locally
- **Player Management**: Complete player profiles including team, position, college, etc.
- **Fantasy Scoring**: Automated calculation of fantasy points based on official NBA Fantasy rules
- **Gameweek Calendar**: Season schedule organized into gameweeks
- **Game Statistics**: Detailed player statistics for every game
- **Query Utilities**: Easy-to-use functions for querying player data and statistics

## Scoring Rules

Fantasy points are calculated as follows for each game:

| Stat | Points |
|------|--------|
| Points Scored | 1 point each |
| Rebounds | 1 point each |
| Assists | 2 points each |
| Blocks | 3 points each |
| Steals | 3 points each |

**Example**: A player with 25 points, 8 rebounds, 5 assists, 1 block, and 2 steals would earn:
- 25×1 + 8×1 + 5×2 + 1×3 + 2×3 = 25 + 8 + 10 + 3 + 6 = **52 fantasy points**

## Project Structure

```
myproject/
├── database.py                 # Database schema and initialization
├── fantasy_calculator.py       # Fantasy points calculation logic
├── nba_data_fetcher.py        # NBA API data fetching
├── populate_database.py        # Database population script
├── query_utils.py             # Query utilities for data retrieval
├── nba_fantasy.db             # SQLite database (created on first run)
└── README.md                  # This file
```

## Setup

### 1. Activate Virtual Environment

```bash
# On WSL/Linux
source ~/myproject/venv/bin/activate

# Or use explicit interpreter
~/myproject/venv/bin/python
```

### 2. Install Dependencies

Dependencies are already in `requirements.txt`:

```bash
pip install -r requirements.txt
```

The project requires:
- `nba_api`: For fetching official NBA data
- `sqlite3`: Built-in, no installation needed

### 3. Initialize and Populate Database

Run the population script to create and populate the database:

```bash
python populate_database.py
```

This will:
1. Create the SQLite database (`nba_fantasy.db`)
2. Fetch all NBA teams and store them
3. Fetch all NBA players and their current team assignments
4. Create gameweek calendar for the 2024-25 season
5. Fetch game statistics for all players and calculate fantasy points

**Note**: The initial population may take several minutes as it fetches data from the NBA API for every player.

## Usage Examples

### 1. Calculate Fantasy Points

```python
from fantasy_calculator import FantasyCalculator

# Calculate fantasy points
fantasy_points = FantasyCalculator.calculate_fantasy_points(
    points=25,
    rebounds=8,
    assists=5,
    blocks=1,
    steals=2
)
print(f"Fantasy Points: {fantasy_points}")  # Output: 52

# Get breakdown by category
breakdown = FantasyCalculator.breakdown_fantasy_points(
    points=25, rebounds=8, assists=5, blocks=1, steals=2
)
print(breakdown)
# Output: {'points': 25, 'rebounds': 8, 'assists': 10, 'blocks': 3, 'steals': 6, 'total': 52}
```

### 2. Query Player Information

```python
from query_utils import QueryUtils

# Get player by name
player = QueryUtils.get_player_by_name("LeBron James")
if player:
    print(f"Team: {player['team_abbreviation']}")
    print(f"Position: {player['position']}")

# Get team roster
roster = QueryUtils.get_team_roster(team_id=1610612738)  # Boston Celtics
for player in roster:
    print(f"{player['player_name']} - {player['position']}")

# Search for players
players = QueryUtils.search_players("Anthony Davis")
for p in players:
    print(f"{p['player_name']} - {p['team_abbreviation']}")
```

### 3. View Gameweek Calendar

```python
from query_utils import QueryUtils

# Get gameweek calendar for the season
calendar = QueryUtils.get_gameweek_calendar(season_year=2024)
for gw in calendar:
    print(f"Week {gw['week_number']}: {gw['start_date']} to {gw['end_date']}")

# Find gameweek for a specific date
gw = QueryUtils.get_gameweek_by_date("2024-11-15")
if gw:
    print(f"Date falls in Week {gw['week_number']}")
```

### 4. View Player Game Statistics

```python
from query_utils import QueryUtils

# Get recent games for a player (player_id for LeBron James is typically 2544)
games = QueryUtils.get_player_game_stats(player_id=2544, limit=5)
for game in games:
    print(f"Date: {game['game_date']}")
    print(f"  Points: {game['points']}, Rebounds: {game['rebounds']}, Assists: {game['assists']}")
    print(f"  Fantasy Points: {game['fantasy_points']}")

# Get aggregated gameweek stats
gw_stats = QueryUtils.get_player_gameweek_stats(player_id=2544, season_year=2024)
for week in gw_stats:
    print(f"Week {week['week_number']}: {week['total_fantasy_points']} FP ({week['games_played']} games)")
```

### 5. View Top Scorers

```python
from query_utils import QueryUtils

# Get top 10 fantasy scorers for the season
top_players = QueryUtils.get_top_scorers(season_year=2024, limit=10)
for idx, player in enumerate(top_players, 1):
    print(f"{idx}. {player['player_name']} ({player['team_abbreviation']}) - {player['total_fantasy_points']} FP")
```

## Database Schema

### Tables

#### Teams
- `team_id` (Primary Key)
- `team_name`
- `team_abbreviation`
- `city`
- `state`

#### Players
- `player_id` (Primary Key)
- `player_name`
- `team_id` (Foreign Key)
- `position`
- `jersey_number`
- `height`, `weight`
- `college`, `country`
- `draft_year`

#### Gameweeks
- `gameweek_id` (Primary Key)
- `season_year`
- `week_number`
- `start_date`, `end_date`

#### Games
- `game_id` (Primary Key)
- `gameweek_id` (Foreign Key)
- `game_date`
- `home_team_id`, `away_team_id` (Foreign Keys)
- `home_team_score`, `away_team_score`
- `game_status`

#### Player Game Stats
- `stat_id` (Primary Key)
- `player_id` (Foreign Key)
- `game_id` (Foreign Key)
- `game_date`
- `points`, `rebounds`, `assists`, `blocks`, `steals`
- `fantasy_points` (calculated)
- `minutes_played`
- Additional stats: FG%, 3P%, FT%, turnovers, fouls, +/-

#### Player Gameweek Stats
- `summary_id` (Primary Key)
- `player_id` (Foreign Key)
- `gameweek_id` (Foreign Key)
- `games_played`
- `total_points`, `total_rebounds`, `total_assists`, `total_blocks`, `total_steals`
- `total_fantasy_points`, `avg_fantasy_points`

## API Reference

### FantasyCalculator

#### `calculate_fantasy_points(points, rebounds, assists, blocks, steals)`
Calculate total fantasy points from individual statistics.

**Returns**: Integer fantasy points

#### `calculate_from_dict(stats)`
Calculate fantasy points from a dictionary of statistics.

**Parameters**: `stats` - Dictionary with keys: points, rebounds, assists, blocks, steals

#### `breakdown_fantasy_points(points, rebounds, assists, blocks, steals)`
Get breakdown of fantasy points by category.

**Returns**: Dictionary with points contribution from each stat

### QueryUtils

#### `get_player_info(player_id)`
Get complete player information including team.

#### `get_player_by_name(player_name)`
Get player info by name (case-insensitive).

#### `get_team_roster(team_id)`
Get all players on a team.

#### `get_gameweek_calendar(season_year)`
Get the gameweek calendar for a season.

#### `get_gameweek_by_date(game_date)`
Get gameweek information for a specific date.

#### `get_player_game_stats(player_id, limit=10)`
Get recent game statistics for a player.

#### `get_player_gameweek_stats(player_id, season_year)`
Get aggregated stats for a player by gameweek.

#### `search_players(name_pattern, team_id=None)`
Search for players by name pattern.

#### `get_top_scorers(season_year, limit=10)`
Get top players by total fantasy points for a season.

## Common Tasks

### Get a Specific Player's Fantasy Stats

```python
from query_utils import QueryUtils

player = QueryUtils.get_player_by_name("Luka Doncic")
if player:
    print(f"\n{player['player_name']} - {player['team_abbreviation']}")
    games = QueryUtils.get_player_game_stats(player['player_id'], limit=10)
    for game in games:
        print(f"  {game['game_date']}: {game['fantasy_points']} FP")
```

### Compare Two Players' Stats

```python
from query_utils import QueryUtils

player1 = QueryUtils.get_player_by_name("Kevin Durant")
player2 = QueryUtils.get_player_by_name("Giannis Antetokounmpo")

if player1 and player2:
    stats1 = QueryUtils.get_player_gameweek_stats(player1['player_id'], 2024)
    stats2 = QueryUtils.get_player_gameweek_stats(player2['player_id'], 2024)
    
    print(f"{player1['player_name']}: {sum(s['total_fantasy_points'] for s in stats1)} FP total")
    print(f"{player2['player_name']}: {sum(s['total_fantasy_points'] for s in stats2)} FP total")
```

### Find All Players from a Specific Team

```python
from query_utils import QueryUtils
from nba_data_fetcher import NBADataFetcher

# Get team ID first
teams = NBADataFetcher.get_all_teams()
lakers = [t for t in teams if t['abbreviation'] == 'LAL'][0]

# Get roster
roster = QueryUtils.get_team_roster(lakers['id'])
for player in roster:
    print(f"{player['player_name']} ({player['position']})")
```

## Tips

1. **First Run**: The first database population takes time. Subsequent queries are instant.
2. **Regular Updates**: Run `populate_database.py` periodically to update player stats.
3. **Performance**: The database can handle queries for thousands of players efficiently.
4. **Date Format**: Always use 'YYYY-MM-DD' format for dates in queries.
5. **Player IDs**: Use `get_player_by_name()` to find player IDs if you don't know them.

## Troubleshooting

### Database Already Exists
If you want to recreate the database, delete `nba_fantasy.db` and run `populate_database.py` again.

### API Rate Limiting
If you encounter rate limit errors while populating, the script includes small delays between requests. Try running again after a few minutes.

### No Results from Queries
Make sure the database has been populated by running `populate_database.py` first.

## Future Enhancements

- [ ] Automated daily stats updates
- [ ] Player injury/availability tracking
- [ ] Historical season data
- [ ] Trade and free agent transaction tracking
- [ ] League-based fantasy statistics
- [ ] REST API for web access

## License

This project uses the official NBA API for data. Ensure compliance with NBA's terms of service.

---

**Last Updated**: December 16, 2025
**NBA Season**: 2024-25
