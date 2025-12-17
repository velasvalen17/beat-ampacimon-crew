#!/usr/bin/env python3
"""
Show current roster schedule in a table format - one player per row, one column per game day.
"""

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Database path
DB_PATH = '/home/velasvalen17/myproject/nba_fantasy.db'

# Current roster (from analyze_lineup.py)
CURRENT_ROSTER = {
    'backcourt': [
        'Nickeil Alexander-Walker',
        'Cedric Coward',
        'Ryan Rollins',
        'Ajay Mitchell',
        'Immanuel Quickley'
    ],
    'frontcourt': [
        'Jalen Johnson',
        'Nikola Jokić',
        'Julius Randle',
        'Derik Queen',
        'Kyshawn George'
    ]
}

def get_player_games_for_week():
    """Get all games for each player in the current roster for gameweek 9."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get all players in roster
    all_players = CURRENT_ROSTER['backcourt'] + CURRENT_ROSTER['frontcourt']
    
    # Build query to get games for these players
    placeholders = ','.join(['?'] * len(all_players))
    
    cur.execute(f"""
        SELECT 
            p.player_name,
            p.team_id,
            t.team_abbreviation as team_abbr,
            g.game_date,
            g.game_time,
            g.home_team_id,
            g.away_team_id,
            ht.team_abbreviation as home_team,
            at.team_abbreviation as away_team
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        JOIN games g ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams at ON g.away_team_id = at.team_id
        WHERE p.player_name IN ({placeholders})
            AND g.game_date >= '2025-12-16'
            AND g.game_date <= '2025-12-22'
        ORDER BY p.player_name, g.game_date, g.game_time
    """, all_players)
    
    games = cur.fetchall()
    conn.close()
    
    # Organize games by player and fantasy day
    player_games = {}
    for game in games:
        player_name, team_id, team_abbr, game_date, game_time, home_id, away_id, home_team, away_team = game
        
        # Apply fantasy day grouping (games before 12:00 noon count as previous day)
        if game_time:
            hour = int(game_time.split(':')[0])
            if hour < 12:
                date_obj = datetime.strptime(game_date, '%Y-%m-%d')
                prev_day = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
                fantasy_day = prev_day
            else:
                fantasy_day = game_date
        else:
            fantasy_day = game_date
        
        # Determine opponent
        if team_id == home_id:
            opponent = f"vs {away_team}"
        else:
            opponent = f"@ {home_team}"
        
        if player_name not in player_games:
            player_games[player_name] = {}
        
        if fantasy_day not in player_games[player_name]:
            player_games[player_name][fantasy_day] = []
        
        player_games[player_name][fantasy_day].append({
            'date': game_date,
            'time': game_time,
            'opponent': opponent
        })
    
    return player_games

def main():
    player_games = get_player_games_for_week()
    
    # Get all unique fantasy days and sort them
    all_days = set()
    for games in player_games.values():
        all_days.update(games.keys())
    
    sorted_days = sorted(all_days)
    
    # Calculate gameweek.day format
    madrid_tz = ZoneInfo('Europe/Madrid')
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    
    # Map fantasy days to gameweek.day format
    day_headers = []
    day_mapping = {}
    
    # Group days and merge day 7 with day 6
    # Use actual day_in_week for labeling, not sequential numbering
    day_headers = []
    day_mapping = {}
    
    i = 0
    while i < len(sorted_days):
        day = sorted_days[i]
        day_obj = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
        days_since_start = (day_obj - season_start).days
        day_in_week = (days_since_start % 7) + 1
        gameweek = (days_since_start // 7) + 1
        
        # Check if next day should merge with this one
        if i + 1 < len(sorted_days):
            next_day = sorted_days[i + 1]
            next_day_obj = datetime.strptime(next_day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
            next_days_since_start = (next_day_obj - season_start).days
            next_day_in_week = (next_days_since_start % 7) + 1
            
            # If next is day 7 and current is day 6, merge them - label as day 6
            if next_day_in_week == 7 and day_in_week == 6:
                day_label = f"{gameweek}.{day_in_week}"
                day_headers.append(day_label)
                day_mapping[day] = day_label
                day_mapping[next_day] = day_label
                i += 2
                continue
        
        # Use the actual day_in_week for the label
        day_label = f"{gameweek}.{day_in_week}"
        day_headers.append(day_label)
        day_mapping[day] = day_label
        i += 1
    
    # Print header
    print("\n" + "="*120)
    print(f"{'PLAYER':<25}", end="")
    for header in day_headers:
        print(f"{header:^15}", end="")
    print()
    print("="*120)
    
    # Print backcourt
    print(f"\n{'🔵 BACKCOURT':^120}")
    print("-"*120)
    for player in CURRENT_ROSTER['backcourt']:
        print(f"{player:<25}", end="")
        games = player_games.get(player, {})
        
        for day_header in day_headers:
            # Find all games for this day_header
            day_games = []
            for fantasy_day, label in day_mapping.items():
                if label == day_header and fantasy_day in games:
                    day_games.extend(games[fantasy_day])
            
            if day_games:
                # Show all opponents for this day
                opponents = [g['opponent'] for g in day_games]
                cell = ", ".join(opponents)
                print(f"{cell:^15}", end="")
            else:
                print(f"{'—':^15}", end="")
        print()
    
    # Print frontcourt
    print(f"\n{'🔴 FRONTCOURT':^120}")
    print("-"*120)
    for player in CURRENT_ROSTER['frontcourt']:
        print(f"{player:<25}", end="")
        games = player_games.get(player, {})
        
        for day_header in day_headers:
            # Find all games for this day_header
            day_games = []
            for fantasy_day, label in day_mapping.items():
                if label == day_header and fantasy_day in games:
                    day_games.extend(games[fantasy_day])
            
            if day_games:
                # Show all opponents for this day
                opponents = [g['opponent'] for g in day_games]
                cell = ", ".join(opponents)
                print(f"{cell:^15}", end="")
            else:
                print(f"{'—':^15}", end="")
        print()
    
    print("="*120)
    print()

if __name__ == '__main__':
    main()
