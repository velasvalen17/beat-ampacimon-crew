#!/usr/bin/env python3
"""
Parse ICS calendar file and update game times in database with UTC times
"""

import sqlite3
import re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ICS_FILE = '/home/velasvalen17/myproject/NBA_fef0d03794cfba3c7eea9c9503e4ab755cd015e32e9ca713d1911fde78b0d3cf@group.calendar.google.com.ics'
DB_PATH = '/home/velasvalen17/myproject/nba_fantasy.db'

def parse_ics_file():
    """Parse ICS file and extract game information"""
    games = []
    
    with open(ICS_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into events
    events = content.split('BEGIN:VEVENT')[1:]  # Skip first split before any event
    
    for event in events:
        # Extract DTSTART (game time in UTC)
        dtstart_match = re.search(r'DTSTART:(\d{8}T\d{6}Z)', event)
        if not dtstart_match:
            continue
        
        dtstart_str = dtstart_match.group(1)
        # Parse: 20251216T033000Z
        game_datetime_utc = datetime.strptime(dtstart_str, '%Y%m%dT%H%M%SZ')
        game_datetime_utc = game_datetime_utc.replace(tzinfo=ZoneInfo('UTC'))
        
        # Extract SUMMARY (game matchup)
        summary_match = re.search(r'SUMMARY:🏀 (.+?) @ (.+?)(?:\n|$)', event)
        if not summary_match:
            continue
        
        away_team = summary_match.group(1).strip()
        home_team = summary_match.group(2).strip()
        
        # Convert to Madrid time for display
        madrid_tz = ZoneInfo('Europe/Madrid')
        game_datetime_madrid = game_datetime_utc.astimezone(madrid_tz)
        
        games.append({
            'away_team': away_team,
            'home_team': home_team,
            'datetime_utc': game_datetime_utc,
            'datetime_madrid': game_datetime_madrid,
            'date': game_datetime_madrid.strftime('%Y-%m-%d'),
            'time': game_datetime_madrid.strftime('%H:%M')
        })
    
    return games

def get_team_id(cursor, team_name):
    """Get team ID from database by full name or abbreviation"""
    # Normalize team name (LA -> Los Angeles)
    team_name_normalized = team_name.replace('LA Clippers', 'Los Angeles Clippers')
    team_name_normalized = team_name_normalized.replace('LA Lakers', 'Los Angeles Lakers')
    
    # Try exact match on team_name
    cursor.execute("SELECT team_id FROM teams WHERE team_name = ?", (team_name_normalized,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # Try matching by abbreviation in the name
    cursor.execute("SELECT team_id, team_name, team_abbreviation FROM teams")
    all_teams = cursor.fetchall()
    
    for team_id, db_name, db_abbr in all_teams:
        if team_name_normalized in db_name or db_name in team_name_normalized or team_name_normalized == db_abbr:
            return team_id
    
    return None

def update_database(games):
    """Update database with parsed game times"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    
    updated_count = 0
    not_found_count = 0
    
    for game in games:
        away_id = get_team_id(cur, game['away_team'])
        home_id = get_team_id(cur, game['home_team'])
        
        if not away_id or not home_id:
            print(f"❌ Could not find teams: {game['away_team']} @ {game['home_team']}")
            not_found_count += 1
            continue
        
        # Update game in database
        # Search in a 2-day window around the Madrid date (in case DB has old date in different timezone)
        search_date = game['datetime_madrid'].date()
        date_start = (search_date - timedelta(days=1)).strftime('%Y-%m-%d')
        date_end = (search_date + timedelta(days=1)).strftime('%Y-%m-%d')
        
        cur.execute("""
            UPDATE games 
            SET game_date = ?, game_time = ?
            WHERE away_team_id = ? AND home_team_id = ?
              AND game_date BETWEEN ? AND ?
        """, (
            game['date'], 
            game['time'],
            away_id,
            home_id,
            date_start,
            date_end
        ))
        
        if cur.rowcount > 0:
            updated_count += 1
            print(f"✅ Updated: {game['away_team']} @ {game['home_team']} - {game['date']} {game['time']}")
        else:
            not_found_count += 1
            print(f"⚠️  No match: {game['away_team']} @ {game['home_team']} - {game['date']} {game['time']}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated_count} games")
    print(f"⚠️  {not_found_count} games not found or not updated")

if __name__ == '__main__':
    print("Parsing ICS calendar file...")
    games = parse_ics_file()
    print(f"Found {len(games)} games in calendar\n")
    
    print("Updating database...")
    update_database(games)
