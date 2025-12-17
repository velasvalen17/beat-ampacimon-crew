"""
Database Population Script
Populates the local database with current season NBA data.
Supports incremental updates - only fetches new data on subsequent runs.
"""

import sqlite3
from database import init_database, get_connection, DB_PATH
from nba_data_fetcher import NBADataFetcher
from fantasy_calculator import FantasyCalculator
from datetime import datetime, timedelta
import time
from typing import Optional, List, Dict
import requests
import random


class DatabasePopulator:
    """Populate the NBA fantasy database with current season data."""
    
    SEASON_YEAR = 2025
    # 2025-26 season: Started October 21, 2025
    SEASON_START_DATE = datetime(2025, 10, 21)
    
    @staticmethod
    def get_last_update_date() -> datetime:
        """Get the date of the last data update."""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT MAX(game_date) FROM player_game_stats")
            result = cursor.fetchone()
            if result and result[0]:
                return datetime.strptime(result[0], '%Y-%m-%d')
            else:
                # No data yet, return season start
                return DatabasePopulator.SEASON_START_DATE
        except Exception as e:
            print(f"Error getting last update date: {e}")
            return DatabasePopulator.SEASON_START_DATE
        finally:
            conn.close()
    
    @staticmethod
    def get_today() -> str:
        """Get today's date in YYYY-MM-DD format."""
        return datetime.now().strftime('%Y-%m-%d')
    
    @staticmethod
    def populate_teams():
        """Fetch and store all NBA teams."""
        print("Populating teams...")
        conn = get_connection()
        cursor = conn.cursor()
        
        teams = NBADataFetcher.get_all_teams()
        
        for team in teams:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO teams (team_id, team_name, team_abbreviation, city, state)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    team.get('id'),
                    team.get('full_name'),
                    team.get('abbreviation'),
                    team.get('city'),
                    team.get('state')
                ))
            except Exception as e:
                print(f"  Error inserting team {team.get('full_name')}: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Teams populated: {len(teams)} teams")
    
    @staticmethod
    def populate_players():
        """Fetch and store all NBA players with their team assignments."""
        print("Populating players...")
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all players
        all_players = NBADataFetcher.get_all_players()
        
        for player in all_players:
            try:
                # Get team for this player
                team_id = player.get('team_id')
                
                cursor.execute("""
                    INSERT OR IGNORE INTO players 
                    (player_id, player_name, team_id, position, jersey_number, height, weight, college, country, draft_year)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    player.get('id'),
                    player.get('full_name'),
                    team_id,
                    player.get('position'),
                    player.get('jersey'),
                    player.get('height'),
                    player.get('weight'),
                    player.get('college'),
                    player.get('country'),
                    player.get('draft_year')
                ))
            except Exception as e:
                print(f"  Error inserting player {player.get('full_name')}: {e}")
        
        conn.commit()
        conn.close()
        print(f"✓ Players populated: {len(all_players)} players")
    
    @staticmethod
    def create_gameweeks():
        """Create gameweek structure for the season."""
        print("Creating gameweek calendar...")
        conn = get_connection()
        cursor = conn.cursor()
        
        # Define gameweeks for 2025-26 season (typically 20-21 weeks)
        # Season starts October 21, 2025
        start_date = DatabasePopulator.SEASON_START_DATE
        
        for week in range(1, 22):  # 21 weeks in the season
            week_start = start_date + timedelta(weeks=week-1)
            week_end = week_start + timedelta(days=6)
            
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO gameweeks (season_year, week_number, start_date, end_date)
                    VALUES (?, ?, ?, ?)
                """, (
                    DatabasePopulator.SEASON_YEAR,
                    week,
                    week_start.strftime('%Y-%m-%d'),
                    week_end.strftime('%Y-%m-%d')
                ))
            except Exception as e:
                print(f"  Error creating gameweek {week}: {e}")
        
        conn.commit()
        conn.close()
        print("✓ Gameweeks created: 21 gameweeks for season")

    @staticmethod
    def populate_games(from_date: datetime = None, to_date: datetime = None):
        """Fetch and store games (schedule + scores) into the `games` table.

        If no dates provided, uses season start → today.
        Uses direct HTTP requests to stats.nba.com to avoid intermittent parsing issues.
        """
        if from_date is None:
            from_date = DatabasePopulator.SEASON_START_DATE
        if to_date is None:
            to_date = datetime.now()

        conn = get_connection()
        cursor = conn.cursor()

        cur_date = from_date
        total = 0
        print(f"Populating games from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}...")

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nba.com/',
            'Origin': 'https://www.nba.com',
        }

        while cur_date <= to_date:
            game_date_str = cur_date.strftime('%Y-%m-%d')
            mmddyyyy = cur_date.strftime('%m/%d/%Y')
            url = f'https://stats.nba.com/stats/scoreboardv2?GameDate={mmddyyyy}&LeagueID=00'

            data = None
            for attempt in range(1, NBADataFetcher.MAX_RETRIES + 1):
                try:
                    r = requests.get(url, headers=headers, timeout=NBADataFetcher.TIMEOUT)
                    r.raise_for_status()
                    data = r.json()
                    break
                except Exception as e:
                    if attempt < NBADataFetcher.MAX_RETRIES:
                        backoff = NBADataFetcher.RETRY_DELAY * (2 ** (attempt - 1))
                        jitter = random.uniform(0, 0.5 * backoff)
                        wait = backoff + jitter
                        print(f"  Scoreboard fetch failed for {game_date_str} (attempt {attempt}), retrying in {wait:.1f}s...")
                        time.sleep(wait)
                        continue
                    else:
                        print(f"  Failed to fetch scoreboard for {game_date_str}: {e}")

            if not data:
                cur_date = cur_date + timedelta(days=1)
                continue

            rs = {rs['name']: rs for rs in data.get('resultSets', [])}
            gh_rows = rs.get('GameHeader', {}).get('rowSet', [])
            ls_rows = rs.get('LineScore', {}).get('rowSet', [])
            ls_headers = rs.get('LineScore', {}).get('headers', [])

            idx_team = idx_pts = None
            if ls_headers:
                try:
                    idx_team = ls_headers.index('TEAM_ID')
                    idx_pts = ls_headers.index('PTS')
                except ValueError:
                    idx_team = idx_pts = None

            score_lookup = {}
            if idx_team is not None and idx_pts is not None:
                for row in ls_rows:
                    try:
                        team_id = int(row[idx_team])
                        pts = row[idx_pts]
                        score_lookup[team_id] = int(pts) if pts is not None else None
                    except Exception:
                        continue

            inserted_this_day = 0
            for gh in gh_rows:
                try:
                    game_id = gh[2]
                    home_team = int(gh[6])
                    away_team = int(gh[7])
                    raw_date = gh[0]
                    try:
                        gdt = datetime.fromisoformat(raw_date)
                        game_date_iso = gdt.strftime('%Y-%m-%d')
                    except Exception:
                        game_date_iso = game_date_str
                    status_text = gh[4]
                    season_year = int(gh[8]) if gh[8] else DatabasePopulator.SEASON_YEAR

                    home_score = score_lookup.get(home_team)
                    away_score = score_lookup.get(away_team)

                    cursor.execute("SELECT gameweek_id FROM gameweeks WHERE start_date <= ? AND end_date >= ? LIMIT 1", (game_date_iso, game_date_iso))
                    gw = cursor.fetchone()
                    gameweek_id = gw[0] if gw else 0

                    cursor.execute("INSERT OR IGNORE INTO games (game_id, gameweek_id, game_date, season_year, home_team_id, away_team_id, home_team_score, away_team_score, game_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
                        game_id,
                        gameweek_id,
                        game_date_iso,
                        season_year,
                        home_team,
                        away_team,
                        home_score,
                        away_score,
                        status_text
                    ))
                    if cursor.rowcount:
                        inserted_this_day += 1
                        total += 1
                except Exception as e:
                    print(f"  Error inserting game {gh}: {e}")

            try:
                conn.commit()
                print(f"Committed {inserted_this_day} games for {game_date_str}")
            except Exception as e:
                print(f"  Commit error for {game_date_str}: {e}")

            cur_date = cur_date + timedelta(days=1)

        conn.close()
        print(f"✓ Games populated: {total} new games")
    
    @staticmethod
    def populate_player_stats(from_date: datetime = None, to_date: datetime = None, players_list: Optional[List[Dict]] = None):
        """
        Fetch and store player game statistics for fantasy points calculation.
        
        Args:
            from_date: Start date for fetching stats (defaults to last update or season start)
            to_date: End date for fetching stats (defaults to today)
        """
        if from_date is None:
            from_date = DatabasePopulator.get_last_update_date()
        
        if to_date is None:
            to_date = datetime.now().date()
        
        # Only fetch up to today, not future dates
        today = datetime.now().date()
        if to_date > today:
            to_date = today
        
        print(f"Populating player game statistics from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}...")
        print("This may take a while as we fetch game logs for all players...")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get all players (or use provided subset)
        if players_list is None:
            all_players = NBADataFetcher.get_all_players()
        else:
            all_players = players_list
        total_stats = 0
        
        def _parse_date(date_value):
            """Parse a variety of date string formats into a datetime."""
            if isinstance(date_value, datetime):
                return date_value
            s = str(date_value).strip()
            # Try common formats
            for fmt in ('%Y-%m-%d', '%b %d, %Y', '%B %d, %Y', '%m/%d/%Y'):
                try:
                    return datetime.strptime(s, fmt)
                except Exception:
                    pass
            # Try title-cased month (handles all-caps like 'NOV 11, 2025')
            try:
                return datetime.strptime(s.title(), '%b %d, %Y')
            except Exception:
                pass
            # Give a clear error for unexpected formats
            raise ValueError(f"Unknown date format: {s}")

        for idx, player in enumerate(all_players):
            if idx % 50 == 0:
                print(f"  Processing player {idx+1}/{len(all_players)}...")
            
            # Handle both dict and int formats
            player_id = player.get('id') if isinstance(player, dict) else player
            
            # Fetch game log for this player
            game_log = NBADataFetcher.get_player_game_log(player_id, DatabasePopulator.SEASON_YEAR)
            
            for game in game_log:
                try:
                    game_date_str = game.get('GAME_DATE', datetime.now().strftime('%Y-%m-%d'))
                    # Parse into datetime, then normalise to ISO string for DB
                    game_date_dt = _parse_date(game_date_str)
                    game_date = game_date_dt
                    game_date_iso = game_date_dt.strftime('%Y-%m-%d')
                    
                    # Only insert if game date is within our range and not in future
                    if from_date <= game_date <= to_date:
                        # Check if we already have this game data
                        game_id = f"{game.get('Game_ID', '')}_{player_id}"
                        cursor.execute("SELECT stat_id FROM player_game_stats WHERE player_id = ? AND game_date = ?", 
                                     (player_id, game_date_iso))
                        if cursor.fetchone():
                            continue  # Skip if already in database
                        
                        # Calculate fantasy points
                        points = game.get('PTS', 0) or 0
                        rebounds = game.get('REB', 0) or 0
                        assists = game.get('AST', 0) or 0
                        blocks = game.get('BLK', 0) or 0
                        steals = game.get('STL', 0) or 0
                        
                        fantasy_points = FantasyCalculator.calculate_fantasy_points(
                            points=int(points),
                            rebounds=int(rebounds),
                            assists=int(assists),
                            blocks=int(blocks),
                            steals=int(steals)
                        )
                        
                        cursor.execute("""
                            INSERT OR IGNORE INTO player_game_stats 
                            (player_id, game_id, game_date, points, rebounds, assists, blocks, steals, 
                             fantasy_points, minutes_played, field_goals_made, field_goals_attempted,
                             three_pointers_made, three_pointers_attempted, free_throws_made, 
                             free_throws_attempted, turnovers, personal_fouls, plus_minus)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            player_id,
                            game_id,
                            game_date_iso,
                            int(points),
                            int(rebounds),
                            int(assists),
                            int(blocks),
                            int(steals),
                            fantasy_points,
                            float(game.get('MIN', 0) or 0),
                            int(game.get('FGM', 0) or 0),
                            int(game.get('FGA', 0) or 0),
                            int(game.get('FG3M', 0) or 0),
                            int(game.get('FG3A', 0) or 0),
                            int(game.get('FTM', 0) or 0),
                            int(game.get('FTA', 0) or 0),
                            int(game.get('TOV', 0) or 0),
                            int(game.get('PF', 0) or 0),
                            int(game.get('PLUS_MINUS', 0) or 0)
                        ))
                        total_stats += 1
                    
                except Exception as e:
                    print(f"  Error inserting stats for player {player_id}: {e}")
            
            # Commit after processing this player's games so other tools/clients can see progress
            try:
                conn.commit()
                print(f"  Committed after player {player_id} (total new records: {total_stats})")
            except Exception as e:
                print(f"  Error committing after player {player_id}: {e}")

            # Add delay to avoid rate limiting
            time.sleep(0.5)
        
        conn.commit()
        conn.close()
        print(f"✓ Player stats populated: {total_stats} new game records")
    
    @staticmethod
    def populate_all(force_full: bool = False):
        """
        Run the complete database population.
        
        Args:
            force_full: If True, does a full refresh of all data. If False, only fetches new data since last update.
        """
        # Initialize database first
        if not DB_PATH.exists():
            print(f"Creating database at {DB_PATH}\n")
            init_database()
        
        print("="*60)
        print("NBA Fantasy Database Population")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60 + "\n")
        
        start_time = datetime.now()
        
        # Always populate teams and players (they don't change often)
        DatabasePopulator.populate_teams()
        print()
        
        DatabasePopulator.populate_players()
        print()
        
        DatabasePopulator.create_gameweeks()
        print()
        
        # For stats, we can do incremental updates
        # For stats, we can do incremental updates; optional limit or specific players can be passed
        if force_full:
            print("Full data refresh requested. Fetching all data since season start...\n")
            DatabasePopulator.populate_player_stats(
                from_date=DatabasePopulator.SEASON_START_DATE,
                to_date=datetime.now()
            )
        else:
            print("Running incremental update. Only fetching new data...\n")
            DatabasePopulator.populate_player_stats()
        
        print()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("="*60)
        print(f"✓ Database population completed in {duration:.2f} seconds")
        print(f"✓ Last update: {DatabasePopulator.get_today()}")
        print("="*60)


if __name__ == "__main__":
    import sys
    
    # Check if --full flag is passed for complete refresh
    force_full = '--full' in sys.argv

    # Optional: --limit N to process only N players, or --players id1,id2
    limit = None
    player_ids = None
    if '--limit' in sys.argv:
        try:
            i = sys.argv.index('--limit')
            limit = int(sys.argv[i+1])
        except Exception:
            print('Invalid --limit value; ignoring')

    if '--players' in sys.argv:
        try:
            i = sys.argv.index('--players')
            raw = sys.argv[i+1]
            player_ids = [int(x) for x in raw.split(',') if x.strip()]
        except Exception:
            print('Invalid --players value; ignoring')

    # If a subset was requested, build a players_list and pass it through
    players_list = None
    if limit is not None or player_ids is not None:
        all_players = NBADataFetcher.get_all_players()
        if player_ids:
            players_list = [p for p in all_players if int(p.get('id')) in player_ids]
        elif limit is not None:
            players_list = all_players[:limit]

    # If players_list is provided, call populate_player_stats with it
    if players_list is not None:
        # run setup steps first
        if not DB_PATH.exists():
            print(f"Creating database at {DB_PATH}\n")
            init_database()

        DatabasePopulator.populate_teams()
        print()
        DatabasePopulator.populate_players()
        print()
        DatabasePopulator.create_gameweeks()
        print()

        print("Running population on requested subset...\n")
        DatabasePopulator.populate_player_stats(from_date=None, to_date=None, players_list=players_list)
    else:
        DatabasePopulator.populate_all(force_full=force_full)
