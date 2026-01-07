#!/usr/bin/env python3
"""
Fantasy NBA Lineup Optimizer - Web Application
"""

from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import itertools

import os

# Set template and static folders relative to project root
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
DB_PATH = os.environ.get('DB_PATH', '/home/velasvalen17/myproject/nba_fantasy.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_team_timezone(team_abbr):
    """Get the timezone for a team based on their city"""
    # Map team abbreviations to their home city timezones
    eastern_teams = ['BOS', 'BKN', 'NYK', 'PHI', 'TOR', 'CHI', 'CLE', 'DET', 'IND', 'MIL', 
                     'ATL', 'CHA', 'MIA', 'ORL', 'WAS']
    central_teams = ['DAL', 'HOU', 'MEM', 'NOP', 'SAS', 'MIN', 'OKC']
    mountain_teams = ['DEN', 'UTA']
    pacific_teams = ['GSW', 'LAC', 'LAL', 'PHX', 'SAC', 'POR']
    
    if team_abbr in eastern_teams:
        return ZoneInfo('America/New_York')
    elif team_abbr in central_teams:
        return ZoneInfo('America/Chicago')
    elif team_abbr in mountain_teams:
        return ZoneInfo('America/Denver')
    elif team_abbr in pacific_teams:
        return ZoneInfo('America/Los_Angeles')
    else:
        # Default to Eastern if unknown
        return ZoneInfo('America/New_York')

def get_fantasy_gamedays():
    """Return fantasy gameday schedule with deadlines in Madrid timezone"""
    madrid_tz = ZoneInfo('Europe/Madrid')
    
    # Parse gameday deadlines - lineup locks at these times, games before this belong to this gameday
    gamedays = [
        # Gameweek 9
        (9, 1, datetime(2025, 12, 16, 0, 30, tzinfo=madrid_tz)),
        (9, 2, datetime(2025, 12, 18, 1, 30, tzinfo=madrid_tz)),
        (9, 3, datetime(2025, 12, 19, 0, 30, tzinfo=madrid_tz)),
        (9, 4, datetime(2025, 12, 20, 0, 30, tzinfo=madrid_tz)),
        (9, 5, datetime(2025, 12, 20, 22, 30, tzinfo=madrid_tz)),
        (9, 6, datetime(2025, 12, 21, 21, 0, tzinfo=madrid_tz)),
        # Gameweek 10
        (10, 1, datetime(2025, 12, 23, 0, 30, tzinfo=madrid_tz)),
        (10, 2, datetime(2025, 12, 24, 0, 30, tzinfo=madrid_tz)),
        (10, 3, datetime(2025, 12, 25, 17, 30, tzinfo=madrid_tz)),
        (10, 4, datetime(2025, 12, 27, 0, 30, tzinfo=madrid_tz)),
        (10, 5, datetime(2025, 12, 27, 22, 30, tzinfo=madrid_tz)),
        (10, 6, datetime(2025, 12, 28, 21, 0, tzinfo=madrid_tz)),
        # Gameweek 11
        (11, 1, datetime(2025, 12, 30, 0, 30, tzinfo=madrid_tz)),
        (11, 2, datetime(2025, 12, 31, 1, 30, tzinfo=madrid_tz)),
        (11, 3, datetime(2025, 12, 31, 18, 30, tzinfo=madrid_tz)),
        (11, 4, datetime(2026, 1, 1, 23, 30, tzinfo=madrid_tz)),
        (11, 5, datetime(2026, 1, 3, 0, 30, tzinfo=madrid_tz)),
        (11, 6, datetime(2026, 1, 3, 22, 30, tzinfo=madrid_tz)),
        (11, 7, datetime(2026, 1, 4, 19, 30, tzinfo=madrid_tz)),
        # Gameweek 12
        (12, 1, datetime(2026, 1, 6, 0, 30, tzinfo=madrid_tz)),
        (12, 2, datetime(2026, 1, 7, 0, 30, tzinfo=madrid_tz)),
        (12, 3, datetime(2026, 1, 8, 0, 30, tzinfo=madrid_tz)),
        (12, 4, datetime(2026, 1, 9, 0, 30, tzinfo=madrid_tz)),
        (12, 5, datetime(2026, 1, 10, 0, 30, tzinfo=madrid_tz)),
        (12, 6, datetime(2026, 1, 10, 18, 30, tzinfo=madrid_tz)),
        (12, 7, datetime(2026, 1, 11, 20, 30, tzinfo=madrid_tz)),
    ]
    
    return gamedays

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/players')
def get_players():
    """Get all players with salaries and recent fantasy averages"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get players with fantasy averages calculated from all their game stats
    cur.execute("""
        WITH player_fantasy_stats AS (
            SELECT 
                pgs.player_id,
                COUNT(*) as games_played,
                AVG(pgs.points + pgs.rebounds + 2 * pgs.assists + 
                    3 * pgs.blocks + 3 * pgs.steals) as fantasy_avg
            FROM player_game_stats pgs
            GROUP BY pgs.player_id
            HAVING COUNT(*) >= 1
        )
        SELECT 
            p.player_id,
            p.player_name,
            p.position,
            p.salary,
            p.team_id,
            t.team_abbreviation as team,
            COALESCE(pfs.fantasy_avg, 0) as fantasy_avg,
            COALESCE(pfs.games_played, 0) as games_played
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        LEFT JOIN player_fantasy_stats pfs ON p.player_id = pfs.player_id
        WHERE p.salary IS NOT NULL
        ORDER BY p.salary DESC
    """)
    
    players = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return jsonify(players)

@app.route('/api/gameweeks')
def get_gameweeks():
    """Get all available gameweeks"""
    madrid_tz = ZoneInfo('Europe/Madrid')
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get min and max game dates
    cur.execute("SELECT MIN(game_date) as min_date, MAX(game_date) as max_date FROM games")
    row = cur.fetchone()
    conn.close()
    
    if not row or not row['min_date']:
        return jsonify([])
    
    min_date = datetime.strptime(row['min_date'], '%Y-%m-%d').replace(tzinfo=madrid_tz)
    max_date = datetime.strptime(row['max_date'], '%Y-%m-%d').replace(tzinfo=madrid_tz)
    
    # Calculate gameweeks
    gameweeks = []
    current_date = season_start
    gameweek_num = 1
    now = datetime.now(madrid_tz)
    
    while current_date <= max_date:
        week_end = current_date + timedelta(days=6)
        
        # Determine if gameweek is completed, active, or upcoming
        status = "upcoming"
        if now > week_end:
            status = "completed"
        elif now >= current_date:
            status = "active"
        
        status_label = ""
        if status == "completed":
            status_label = " ✓"
        elif status == "active":
            status_label = " (Current)"
        
        gameweeks.append({
            'gameweek': gameweek_num,
            'start_date': current_date.strftime('%Y-%m-%d'),
            'end_date': week_end.strftime('%Y-%m-%d'),
            'status': status,
            'label': f"Gameweek {gameweek_num}{status_label} ({current_date.strftime('%b %d')} - {week_end.strftime('%b %d')})"
        })
        current_date = week_end + timedelta(days=1)
        gameweek_num += 1
    
    return jsonify(gameweeks)

@app.route('/api/team_schedule/<int:gameweek>')
def get_team_schedule(gameweek):
    """Get top teams by number of games in a gameweek"""
    madrid_tz = ZoneInfo('Europe/Madrid')
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    
    # Calculate date range for selected gameweek
    week_start = season_start + timedelta(days=(gameweek - 1) * 7)
    week_end = week_start + timedelta(days=6)
    
    start_date = week_start.strftime('%Y-%m-%d')
    end_date = week_end.strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get teams with game counts and their games
    cur.execute("""
        SELECT 
            t.team_id,
            t.team_name,
            t.team_abbreviation,
            COUNT(DISTINCT g.game_date) as game_days,
            COUNT(*) as total_games,
            GROUP_CONCAT(
                CASE 
                    WHEN g.home_team_id = t.team_id 
                    THEN g.game_date || '|vs|' || away.team_abbreviation
                    ELSE g.game_date || '|@|' || home.team_abbreviation
                END, ':::'
            ) as games_detail
        FROM teams t
        JOIN games g ON (t.team_id = g.home_team_id OR t.team_id = g.away_team_id)
        LEFT JOIN teams home ON g.home_team_id = home.team_id
        LEFT JOIN teams away ON g.away_team_id = away.team_id
        WHERE g.game_date >= ? AND g.game_date <= ?
        GROUP BY t.team_id
        ORDER BY game_days DESC, total_games DESC
    """, [start_date, end_date])
    
    teams = []
    for row in cur.fetchall():
        team = dict(row)
        # Parse games detail
        games = []
        if team['games_detail']:
            for game_str in team['games_detail'].split(':::'):
                parts = game_str.split('|')
                if len(parts) == 3:
                    games.append({
                        'date': parts[0],
                        'type': parts[1],  # 'vs' or '@'
                        'opponent': parts[2]
                    })
        team['games'] = games
        del team['games_detail']
        teams.append(team)
    
    conn.close()
    
    return jsonify({
        'gameweek': gameweek,
        'date_range': f"{start_date} to {end_date}",
        'teams': teams
    })

@app.route('/api/game_schedule', methods=['POST'])
def get_game_schedule():
    """Get game schedule for selected players in a gameweek"""
    print("=== GAME SCHEDULE API CALLED - NEW CODE V2 ===")
    try:
        data = request.json
        print(f"Received data: {data}")
        
        if not data:
            return jsonify({'error': 'No data received', 'games_by_day': {}}), 400
        
        player_ids = data.get('player_ids', [])
        gameweek = data.get('gameweek', 9)
        if gameweek is None:
            gameweek = 9
        gameweek = int(gameweek)
        print(f"Player IDs: {player_ids}, Gameweek: {gameweek}")
        
        if not player_ids:
            return jsonify({'games_by_day': {}})
        
        # Calculate date range for gameweek
        madrid_tz = ZoneInfo('Europe/Madrid')
        season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
        week_start = season_start + timedelta(days=(gameweek - 1) * 7)
        week_end = week_start + timedelta(days=6)
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get teams for the selected players
        placeholders = ','.join('?' * len(player_ids))
        cur.execute(f"""
            SELECT DISTINCT team_id 
            FROM players 
            WHERE player_id IN ({placeholders})
        """, player_ids)
        
        team_ids = [row['team_id'] for row in cur.fetchall()]
        
        if not team_ids:
            conn.close()
            return jsonify({'games_by_day': {}})
        
        # Get all games for these teams in the gameweek
        team_placeholders = ','.join('?' * len(team_ids))
        cur.execute(f"""
            SELECT 
                g.game_id,
                g.game_date,
                g.game_time,
                home.team_name as home_team,
                home.team_abbreviation as home_abbr,
                away.team_name as away_team,
                away.team_abbreviation as away_abbr,
                g.home_team_id,
                g.away_team_id
            FROM games g
            JOIN teams home ON g.home_team_id = home.team_id
            JOIN teams away ON g.away_team_id = away.team_id
            WHERE g.game_date >= ? AND g.game_date <= ?
            AND (g.home_team_id IN ({team_placeholders}) OR g.away_team_id IN ({team_placeholders}))
            ORDER BY g.game_date, g.game_time
        """, [week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d')] + team_ids + team_ids)
        
        games = cur.fetchall()
        
        # Get player info including position
        cur.execute(f"""
            SELECT p.player_id, p.player_name, p.team_id, p.position, t.team_abbreviation as team
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            WHERE p.player_id IN ({placeholders})
        """, player_ids)
        
        players_dict = {row['player_id']: dict(row) for row in cur.fetchall()}
        
        # Get fantasy gameday schedule for this gameweek
        all_gamedays = get_fantasy_gamedays()
        gameweek_gamedays = [(gw, day, deadline) for gw, day, deadline in all_gamedays if gw == gameweek]
        
        # Initialize all gamedays for this gameweek (even if no games)
        games_by_day = {}
        for gw, day_num, deadline in gameweek_gamedays:
            label = f"GW{gw} Day {day_num}"
            games_by_day[label] = {
                'deadline': deadline.isoformat(),
                'games': []
            }
        
        # Organize games by fantasy gameday
        madrid_tz = ZoneInfo('Europe/Madrid')
        
        for game in games:
            # Parse game datetime from database (now stored in Madrid timezone after ICS import)
            game_date_str = game['game_date']
            game_time_str = game['game_time'] or '00:00'
            
            # Parse datetime and make it timezone-aware in Madrid timezone
            try:
                game_dt = datetime.strptime(f"{game_date_str} {game_time_str}", '%Y-%m-%d %H:%M')
                game_dt = game_dt.replace(tzinfo=madrid_tz)
            except:
                game_dt = datetime.strptime(game_date_str, '%Y-%m-%d')
                game_dt = game_dt.replace(tzinfo=madrid_tz)
            
            # Find which fantasy gameday this game belongs to
            # Rule: Deadline is ~30 min before first game. Games tip off AFTER deadline.
            # A game belongs to the gameday whose deadline it comes after.
            fantasy_gameday_label = None
            
            for i, (gw, day_num, deadline) in enumerate(gameweek_gamedays):
                next_deadline = gameweek_gamedays[i+1][2] if i+1 < len(gameweek_gamedays) else None
                
                # Games belong to this gameday if they occur between this deadline and next deadline
                if next_deadline is None:
                    # Last gameday: all games after this deadline
                    if game_dt >= deadline:
                        fantasy_gameday_label = f"GW{gw} Day {day_num}"
                        break
                else:
                    # Games from this deadline (inclusive) up to next deadline (exclusive)
                    if game_dt >= deadline and game_dt < next_deadline:
                        fantasy_gameday_label = f"GW{gw} Day {day_num}"
                        break
            
            # If no matching gameday found, assign to the last gameday in the list
            if not fantasy_gameday_label and gameweek_gamedays:
                gw, day_num, _ = gameweek_gamedays[-1]
                fantasy_gameday_label = f"GW{gw} Day {day_num}"
            
            # Fallback to date if still no match
            if not fantasy_gameday_label:
                fantasy_gameday_label = game_date_str
            
            # Create the gameday entry if it doesn't exist (for games outside gameweek)
            if fantasy_gameday_label not in games_by_day:
                games_by_day[fantasy_gameday_label] = {
                    'deadline': None,
                    'games': []
                }
            
            # Find which players are in this game
            game_players = []
            for player_id, player_info in players_dict.items():
                if player_info['team_id'] in [game['home_team_id'], game['away_team_id']]:
                    game_players.append({
                        'player_id': player_id,
                        'player_name': player_info['player_name'],
                        'team': player_info['team']
                    })
            
            if game_players:  # Only include games where our players are playing
                games_by_day[fantasy_gameday_label]['games'].append({
                    'game_id': game['game_id'],
                    'matchup': f"{game['home_abbr']} vs {game['away_abbr']}",
                    'time': game['game_time'],
                    'players': game_players
                })
        
        # Calculate projected fantasy points per day using last 7 games average
        for day_label, day_data in games_by_day.items():
            # Get unique player IDs playing on this day
            players_on_day = set()
            for game in day_data['games']:
                for player in game['players']:
                    players_on_day.add(player['player_id'])
            
            # Calculate projected FP for players on this day
            day_data['projected_fp'] = 0
            day_data['player_count'] = len(players_on_day)
            day_data['player_projections'] = []
            
            if players_on_day:
                # Get recent stats and total stats for these players
                player_ids_str = ','.join([str(pid) for pid in players_on_day])
                player_stats_query = f"""
                    WITH recent_stats AS (
                        SELECT 
                            player_id,
                            fantasy_points,
                            ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY game_date DESC) as rn
                        FROM player_game_stats
                        WHERE player_id IN ({player_ids_str})
                    ),
                    recent_avg AS (
                        SELECT 
                            player_id,
                            AVG(fantasy_points) as avg_last_5
                        FROM recent_stats
                        WHERE rn <= 5
                        GROUP BY player_id
                    ),
                    total_stats AS (
                        SELECT
                            player_id,
                            SUM(fantasy_points) as total_fp
                        FROM player_game_stats
                        WHERE player_id IN ({player_ids_str})
                        GROUP BY player_id
                    )
                    SELECT 
                        r.player_id,
                        COALESCE(r.avg_last_5, 0) as avg_last_5,
                        COALESCE(t.total_fp, 0) as total_fp
                    FROM recent_avg r
                    LEFT JOIN total_stats t ON r.player_id = t.player_id
                """
                
                player_stats = {}
                for row in conn.execute(player_stats_query).fetchall():
                    player_stats[row['player_id']] = {
                        'avg_last_5': row['avg_last_5'],
                        'total_fp': row['total_fp']
                    }
                
                # Calculate total projected FP and store individual projections with position info
                backcourt_players = []
                frontcourt_players = []
                
                for player_id in players_on_day:
                    stats = player_stats.get(player_id, {'avg_last_5': 0, 'total_fp': 0})
                    avg_fp = stats['avg_last_5']
                    total_fp = stats['total_fp']
                    day_data['projected_fp'] += avg_fp
                    
                    # Get player name and position from players_dict
                    if player_id in players_dict:
                        # Get position from players_dict
                        player_position = players_dict[player_id].get('position', '')
                        
                        projection = {
                            'player_id': player_id,
                            'player_name': players_dict[player_id]['player_name'],
                            'team': players_dict[player_id]['team'],
                            'position': player_position,
                            'projected_fp': round(avg_fp, 1),
                            'avg_last_5': round(avg_fp, 1),
                            'total_fp': round(total_fp, 1),
                            'is_starter': False
                        }
                        
                        # Categorize by position (G = Backcourt, F/C = Frontcourt)
                        if player_position and 'G' in player_position:
                            backcourt_players.append(projection)
                        else:
                            frontcourt_players.append(projection)
                        
                        day_data['player_projections'].append(projection)
                
                # Sort each position group by avg_last_5, then total_fp
                backcourt_players.sort(key=lambda x: (x['avg_last_5'], x['total_fp']), reverse=True)
                frontcourt_players.sort(key=lambda x: (x['avg_last_5'], x['total_fp']), reverse=True)
                
                # Only assign crowns if we have 5+ players total (otherwise there's no choice)
                total_players = len(backcourt_players) + len(frontcourt_players)
                
                if total_players >= 5:
                    # Select starters respecting position constraints (2-3 BC, 2-3 FC, total 5)
                    # Try 3 BC + 2 FC vs 2 BC + 3 FC and pick the combination with higher total FP
                    starters = []
                    
                    # Option 1: 3 BC + 2 FC (if we have enough players)
                    if len(backcourt_players) >= 3 and len(frontcourt_players) >= 2:
                        option1_bc = backcourt_players[:3]
                        option1_fc = frontcourt_players[:2]
                        option1_total = sum(p['avg_last_5'] for p in option1_bc) + sum(p['avg_last_5'] for p in option1_fc)
                    else:
                        option1_total = -1
                    
                    # Option 2: 2 BC + 3 FC (if we have enough players)
                    if len(backcourt_players) >= 2 and len(frontcourt_players) >= 3:
                        option2_bc = backcourt_players[:2]
                        option2_fc = frontcourt_players[:3]
                        option2_total = sum(p['avg_last_5'] for p in option2_bc) + sum(p['avg_last_5'] for p in option2_fc)
                    else:
                        option2_total = -1
                    
                    # Choose the valid option with higher total FP
                    if option1_total >= 0 and option1_total >= option2_total:
                        starters = backcourt_players[:3] + frontcourt_players[:2]
                    elif option2_total >= 0:
                        starters = backcourt_players[:2] + frontcourt_players[:3]
                    # else: Not enough players in proper positions, no starters assigned
                    
                    # Mark selected players as starters
                    starter_ids = {p['player_id'] for p in starters}
                    for proj in day_data['player_projections']:
                        proj['is_starter'] = proj['player_id'] in starter_ids
                
                # Sort all projections for display (starters first, then by FP)
                day_data['player_projections'].sort(key=lambda x: (not x['is_starter'], -x['avg_last_5'], -x['total_fp']))
                
                day_data['projected_fp'] = round(day_data['projected_fp'], 1)
        
        conn.close()
        return jsonify({'games_by_day': games_by_day})
    
    except Exception as e:
        print(f"Error in get_game_schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'games_by_day': {}}), 500

@app.route('/api/team_players/<int:team_id>', methods=['GET'])
def get_team_players(team_id):
    """Get all players from a specific team with their fantasy stats"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get team info
        cur.execute("""
            SELECT team_name, team_abbreviation 
            FROM teams 
            WHERE team_id = ?
        """, (team_id,))
        
        team_row = cur.fetchone()
        if not team_row:
            conn.close()
            return jsonify({'error': 'Team not found'}), 404
        
        team_info = dict(team_row)
        
        # Get players with fantasy averages from last 30 games (or all games if less)
        cur.execute("""
            WITH player_recent_games AS (
                SELECT 
                    pgs.player_id,
                    pgs.points,
                    pgs.rebounds,
                    pgs.assists,
                    pgs.blocks,
                    pgs.steals,
                    pgs.minutes_played,
                    pgs.game_date,
                    ROW_NUMBER() OVER (PARTITION BY pgs.player_id ORDER BY pgs.game_date DESC) as rn
                FROM player_game_stats pgs
            ),
            player_stats AS (
                SELECT 
                    player_id,
                    COUNT(*) as games_played,
                    AVG(points + rebounds + 2 * assists + 3 * blocks + 3 * steals) as fantasy_avg,
                    AVG(minutes_played) as avg_minutes
                FROM player_recent_games
                WHERE rn <= 30
                GROUP BY player_id
            )
            SELECT 
                p.player_id,
                p.player_name,
                p.position,
                p.salary,
                COALESCE(ps.fantasy_avg, 0) as fantasy_avg,
                COALESCE(ps.avg_minutes, 0) as avg_minutes,
                COALESCE(ps.games_played, 0) as games_played
            FROM players p
            LEFT JOIN player_stats ps ON p.player_id = ps.player_id
            WHERE p.team_id = ?
            ORDER BY 
                CASE 
                    WHEN p.position LIKE '%G%' THEN 0 
                    ELSE 1 
                END,
                ps.fantasy_avg DESC NULLS LAST
        """, (team_id,))
        
        players = [dict(row) for row in cur.fetchall()]
        conn.close()
        
        # Separate into BC and FC
        backcourt = [p for p in players if 'G' in p['position']]
        frontcourt = [p for p in players if 'G' not in p['position']]
        
        return jsonify({
            'team_id': team_id,
            'team_name': team_info['team_name'],
            'team_abbreviation': team_info['team_abbreviation'],
            'backcourt': backcourt,
            'frontcourt': frontcourt
        })
    
    except Exception as e:
        print(f"Error in get_team_players: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
