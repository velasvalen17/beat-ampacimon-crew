#!/usr/bin/env python3
"""Daily update script for NBA Fantasy Database."""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from app.database import init_database, get_connection
from scripts.populate_database import DatabasePopulator

def log(message):
    """Log message with timestamp."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def update_database():
    """Run daily database updates."""
    log("="*60)
    log("Starting daily NBA Fantasy database update")
    
    try:
        # Initialize database if needed
        log("Checking database initialization...")
        init_database()
        
        # Get yesterday and today's dates
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        log(f"Updating data for {yesterday} to {today}")
        
        # Update teams (in case of changes)
        log("Updating teams...")
        DatabasePopulator.populate_teams()
        
        # Update games for yesterday and today
        log(f"Fetching games from {yesterday} to {today}...")
        DatabasePopulator.populate_games(
            from_date=yesterday,
            to_date=today
        )
        
        # Get all unique teams from recent games
        log("Fetching rosters for teams with recent games...")
        conn = get_connection()
        cur = conn.cursor()
        
        # Get teams that played in the last 7 days
        week_ago = today - timedelta(days=7)
        cur.execute("""
            SELECT DISTINCT home_team_id FROM games WHERE game_date >= ?
            UNION
            SELECT DISTINCT away_team_id FROM games WHERE game_date >= ?
        """, (week_ago.strftime('%Y-%m-%d'), week_ago.strftime('%Y-%m-%d')))
        
        active_team_ids = [row[0] for row in cur.fetchall()]
        log(f"Found {len(active_team_ids)} active teams")
        
        # Update rosters for active teams
        from nba_data_fetcher import NBADataFetcher
        for team_id in active_team_ids:
            try:
                roster = NBADataFetcher.get_team_roster(team_id)
                for player in roster:
                    try:
                        cur.execute("""
                            INSERT OR REPLACE INTO players 
                            (player_id, player_name, team_id, position, jersey_number)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            player.get('PLAYER_ID'),
                            player.get('PLAYER'),
                            team_id,
                            player.get('POSITION'),
                            player.get('NUM')
                        ))
                    except Exception:
                        pass
                conn.commit()
            except Exception as e:
                log(f"Warning: Could not fetch roster for team {team_id}: {e}")
        
        # Get all player IDs from database
        cur.execute("SELECT player_id FROM players ORDER BY player_id")
        player_ids = [row[0] for row in cur.fetchall()]
        conn.close()
        
        log(f"Updating stats for {len(player_ids)} players...")
        
        # Update player stats for yesterday and today
        DatabasePopulator.populate_player_stats(
            from_date=yesterday,
            to_date=today,
            players_list=player_ids
        )
        
        # Get final counts
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM teams")
        teams_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM players")
        players_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM games")
        games_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM player_game_stats")
        stats_count = cur.fetchone()[0]
        conn.close()
        
        log("Update completed successfully!")
        log(f"Database totals: {teams_count} teams, {players_count} players, "
            f"{games_count} games, {stats_count} player stats")
        log("="*60)
        
        return 0
        
    except Exception as e:
        log(f"ERROR during update: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(update_database())
