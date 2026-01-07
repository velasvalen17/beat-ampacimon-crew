#!/usr/bin/env python3
"""Import full season schedule from NBA API"""

from nba_api.stats.endpoints import scheduleleaguev2
from app.database import get_connection
import pandas as pd
from zoneinfo import ZoneInfo

def import_schedule():
    print("Fetching full 2025-26 season schedule...")
    schedule = scheduleleaguev2.ScheduleLeagueV2(season='2025-26')
    df = schedule.get_data_frames()[0]
    
    print(f"Found {len(df)} games in season")
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Convert date format
    df['gameDateEst'] = pd.to_datetime(df['gameDateEst'])
    
    games_added = 0
    madrid_tz = ZoneInfo('Europe/Madrid')
    
    for _, row in df.iterrows():
        # Convert UTC game time to Madrid timezone
        game_datetime_utc = pd.to_datetime(row['gameDateTimeEst'])
        game_datetime_madrid = game_datetime_utc.astimezone(madrid_tz)
        
        # Use Madrid date for game_date (a 1 AM EST game is 7 AM CET same day, but 11 PM PST game is 8 AM CET next day)
        game_date_madrid = game_datetime_madrid.strftime('%Y-%m-%d')
        game_time_madrid = game_datetime_madrid.strftime('%H:%M')
        
        # Determine gameweek based on Madrid timezone date
        season_start = pd.Timestamp('2025-10-21', tz=madrid_tz)
        week_num = ((game_datetime_madrid - season_start).days // 7) + 1
        
        cur.execute("""
            INSERT OR REPLACE INTO games (game_id, gameweek_id, game_date, game_time, home_team_id, away_team_id, season_year)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['gameId'],
            week_num,
            game_date_madrid,
            game_time_madrid,
            row['homeTeam_teamId'],
            row['awayTeam_teamId'],
            2025
        ))
        games_added += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ Imported {games_added} games into database")
    
    # Show summary for next week
    dec_games = df[(df['gameDateEst'] >= '2025-12-16') & (df['gameDateEst'] <= '2025-12-22')]
    print(f"\nGames scheduled Dec 16-22: {len(dec_games)}")
    
    # Count games per team for next week
    team_game_counts = {}
    for _, row in dec_games.iterrows():
        home_team = row['homeTeam_teamName']
        away_team = row['awayTeam_teamName']
        team_game_counts[home_team] = team_game_counts.get(home_team, 0) + 1
        team_game_counts[away_team] = team_game_counts.get(away_team, 0) + 1
    
    print("\nGames per team (Dec 16-22):")
    for team, count in sorted(team_game_counts.items(), key=lambda x: (-x[1], x[0])):
        print(f"  {team:20} {count} games")

if __name__ == '__main__':
    import_schedule()
