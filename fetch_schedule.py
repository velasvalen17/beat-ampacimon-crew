#!/usr/bin/env python3
"""Fetch only the game schedule for a date range"""

from nba_data_fetcher import NBADataFetcher
from database import get_connection
from datetime import datetime, timedelta
import sys

def fetch_schedule(start_date, end_date):
    fetcher = NBADataFetcher()
    conn = get_connection()
    cur = conn.cursor()
    
    print(f"Fetching schedule for {start_date} to {end_date}...")
    
    # Parse dates
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    total_games = 0
    current_date = start
    
    while current_date <= end:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"  {date_str}...", end='')
        
        games = fetcher.get_scoreboard(date_str)
        
        if games:
            for game in games:
                cur.execute("""
                    INSERT OR REPLACE INTO games (game_id, game_date, home_team_id, away_team_id, season)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    game['GAME_ID'],
                    date_str,
                    game['HOME_TEAM_ID'],
                    game['VISITOR_TEAM_ID'],
                    2025
                ))
            print(f" {len(games)} games")
            total_games += len(games)
        else:
            print(" 0 games")
        
        current_date += timedelta(days=1)
    
    conn.commit()
    conn.close()
    print(f"\n✓ Added {total_games} games to database")

if __name__ == '__main__':
    start = sys.argv[1] if len(sys.argv) > 1 else '2025-12-16'
    end = sys.argv[2] if len(sys.argv) > 2 else '2025-12-22'
    fetch_schedule(start, end)
