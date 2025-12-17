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

app = Flask(__name__)
DB_PATH = os.environ.get('DB_PATH', '/home/velasvalen17/myproject/nba_fantasy.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
    """Get all players with salaries"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            p.player_id,
            p.player_name,
            p.position,
            p.salary,
            t.team_abbreviation as team
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
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

@app.route('/api/analyze', methods=['POST'])
def analyze_lineup():
    """Analyze current lineup and provide recommendations"""
    data = request.json
    current_roster = data.get('current_roster', [])
    available_budget = float(data.get('available_budget', 0))
    gameweek = int(data.get('gameweek', 9))  # Default to gameweek 9
    
    # Calculate date range for selected gameweek
    madrid_tz = ZoneInfo('Europe/Madrid')
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    week_start = season_start + timedelta(days=(gameweek - 1) * 7)
    week_end = week_start + timedelta(days=6)
    
    start_date = week_start.strftime('%Y-%m-%d')
    end_date = week_end.strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get current roster details
    if not current_roster:
        return jsonify({'error': 'No roster provided'}), 400
    
    placeholders = ','.join(['?'] * len(current_roster))
    
    # Get roster with stats and games
    cur.execute(f"""
        SELECT 
            p.player_id,
            p.player_name,
            p.position,
            p.salary,
            t.team_abbreviation as team
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        WHERE p.player_id IN ({placeholders})
    """, current_roster)
    
    roster_details = [dict(row) for row in cur.fetchall()]
    
    # Get games for selected gameweek for current roster
    cur.execute(f"""
        SELECT 
            p.player_id,
            p.player_name,
            g.game_date,
            g.game_time
        FROM players p
        JOIN games g ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
        WHERE p.player_id IN ({placeholders})
            AND g.game_date >= ?
            AND g.game_date <= ?
        ORDER BY g.game_date, g.game_time
    """, current_roster + [start_date, end_date])
    
    # Group by fantasy days
    player_days = {}
    madrid_tz = ZoneInfo('Europe/Madrid')
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    
    for row in cur.fetchall():
        player_id = row['player_id']
        player_name = row['player_name']
        game_date = row['game_date']
        game_time = row['game_time']
        
        # Apply fantasy day grouping
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
        
        if player_id not in player_days:
            player_days[player_id] = set()
        player_days[player_id].add(fantasy_day)
    
    # Calculate coverage by day
    day_coverage = {}
    for player in roster_details:
        player_id = player['player_id']
        position = player['position']
        
        if player_id in player_days:
            for day in player_days[player_id]:
                if day not in day_coverage:
                    day_coverage[day] = {'bc': 0, 'fc': 0, 'total': 0, 'players': []}
                
                day_coverage[day]['total'] += 1
                day_coverage[day]['players'].append(player['player_name'])
                
                if 'G' in position:
                    day_coverage[day]['bc'] += 1
                else:
                    day_coverage[day]['fc'] += 1
    
    # Map to gameweek.day labels
    day_labels = {}
    insufficient_days = []
    
    for day in sorted(day_coverage.keys()):
        day_obj = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
        days_since_start = (day_obj - season_start).days
        day_in_week = (days_since_start % 7) + 1
        gameweek = (days_since_start // 7) + 1
        label = f"{gameweek}.{day_in_week}"
        day_labels[day] = label
        
        if day_coverage[day]['total'] < 5:
            insufficient_days.append({
                'date': day,
                'label': label,
                'total': day_coverage[day]['total'],
                'needed': 5 - day_coverage[day]['total']
            })
    
    # Find recommendations - players who play on insufficient days
    recommendations = []
    
    if insufficient_days:
        problem_dates = [d['date'] for d in insufficient_days]
        placeholders_dates = ','.join(['?'] * len(problem_dates))
        
        # Find players who play on problem days with their recent fantasy stats
        cur.execute(f"""
            WITH player_games AS (
                SELECT 
                    p.player_id,
                    p.player_name,
                    p.position,
                    p.salary,
                    t.team_abbreviation as team,
                    GROUP_CONCAT(DISTINCT g.game_date) as game_dates,
                    COUNT(DISTINCT g.game_date) as total_games
                FROM players p
                JOIN teams t ON p.team_id = t.team_id
                JOIN games g ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
                WHERE p.salary IS NOT NULL
                    AND p.player_id NOT IN ({placeholders})
                    AND g.game_date >= ?
                    AND g.game_date <= ?
                GROUP BY p.player_id
                HAVING COUNT(DISTINCT CASE WHEN g.game_date IN ({placeholders_dates}) THEN g.game_date END) >= 1
            ),
            recent_stats AS (
                SELECT 
                    pgs.player_id,
                    AVG(pgs.points + 1.2 * pgs.rebounds + 1.5 * pgs.assists + 
                        3 * pgs.steals + 3 * pgs.blocks - pgs.turnovers) as fantasy_avg,
                    COUNT(*) as games_played
                FROM player_game_stats pgs
                JOIN games g ON pgs.game_id = g.game_id
                WHERE g.game_date >= '2025-12-09' AND g.game_date <= '2025-12-15'
                GROUP BY pgs.player_id
                HAVING games_played >= 2
            )
            SELECT 
                pg.player_id,
                pg.player_name,
                pg.position,
                pg.salary,
                pg.team,
                pg.game_dates,
                pg.total_games,
                COALESCE(rs.fantasy_avg, 0) as fantasy_avg
            FROM player_games pg
            LEFT JOIN recent_stats rs ON pg.player_id = rs.player_id
            ORDER BY rs.fantasy_avg DESC NULLS LAST, pg.total_games DESC
            LIMIT 100
        """, current_roster + [start_date, end_date] + problem_dates)
        
        candidates = [dict(row) for row in cur.fetchall()]
        
        # Get recent stats for current roster
        cur.execute(f"""
            SELECT 
                pgs.player_id,
                AVG(pgs.points + 1.2 * pgs.rebounds + 1.5 * pgs.assists + 
                    3 * pgs.steals + 3 * pgs.blocks - pgs.turnovers) as fantasy_avg
            FROM player_game_stats pgs
            JOIN games g ON pgs.game_id = g.game_id
            WHERE pgs.player_id IN ({placeholders})
                AND g.game_date >= '2025-12-09' AND g.game_date <= '2025-12-15'
            GROUP BY pgs.player_id
        """, current_roster)
        
        roster_stats = {row['player_id']: row['fantasy_avg'] for row in cur.fetchall()}
        
        # Add fantasy stats to roster details
        for player in roster_details:
            player['fantasy_avg'] = roster_stats.get(player['player_id'], 0)
        
        # Find best 2 transaction pairs
        budget_with_drops = available_budget
        
        best_options = []
        
        # Try combinations of 2 drops and 2 adds
        for drops in itertools.combinations(roster_details, 2):
            drop_salary = sum(d['salary'] for d in drops)
            budget = budget_with_drops + drop_salary
            
            # Check position constraints
            drop_bc = sum(1 for d in drops if 'G' in d['position'])
            drop_fc = sum(1 for d in drops if 'F' in d['position'] or 'C' in d['position'])
            
            if drop_bc > 4 or drop_fc > 4:
                continue
            
            for adds in itertools.combinations(candidates[:30], 2):
                add_salary = sum(a['salary'] for a in adds)
                
                if add_salary > budget:
                    continue
                
                # Check position balance
                add_bc = sum(1 for a in adds if 'G' in a['position'])
                add_fc = sum(1 for a in adds if 'F' in a['position'] or 'C' in a['position'])
                
                new_bc_count = 5 - drop_bc + add_bc
                new_fc_count = 5 - drop_fc + add_fc
                
                if new_bc_count < 3 or new_bc_count > 5 or new_fc_count < 3 or new_fc_count > 5:
                    continue
                
                # Calculate comprehensive improvement score
                # Priority 1: Roster depth (covering problem days)
                # Priority 2: Fantasy points per game
                # Priority 3: Total games played
                
                depth_score = 0
                fp_improvement = 0
                games_improvement = 0
                
                # Calculate fantasy point impact
                drop_fp = sum(d['fantasy_avg'] for d in drops)
                add_fp = sum(a['fantasy_avg'] for a in adds)
                fp_improvement = add_fp - drop_fp
                
                # Calculate depth improvement
                for add in adds:
                    add_dates = add['game_dates'].split(',')
                    for date in add_dates:
                        if date in problem_dates:
                            depth_score += 100  # High weight for covering problem days
                    games_improvement += len(add_dates)
                
                for drop in drops:
                    if drop['player_id'] in player_days:
                        for date in player_days[drop['player_id']]:
                            if date in problem_dates:
                                depth_score -= 50  # Penalty for removing coverage
                
                # Combined score: Depth is most important, then FP, then games
                score = depth_score * 10 + fp_improvement * 5 + games_improvement
                
                best_options.append({
                    'drops': [{'id': d['player_id'], 'name': d['player_name'], 'salary': d['salary'], 'position': d['position'], 'fantasy_avg': d['fantasy_avg']} for d in drops],
                    'adds': [{'id': a['player_id'], 'name': a['player_name'], 'salary': a['salary'], 'position': a['position'], 'games': len(a['game_dates'].split(',')), 'fantasy_avg': a['fantasy_avg']} for a in adds],
                    'cost': add_salary - drop_salary,
                    'fp_improvement': fp_improvement,
                    'depth_score': depth_score,
                    'score': score
                })
        
        # Sort by score and get top 3
        best_options.sort(key=lambda x: x['score'], reverse=True)
        recommendations = best_options[:3]
    
    conn.close()
    
    return jsonify({
        'roster': roster_details,
        'day_coverage': {day_labels[day]: day_coverage[day] for day in day_coverage},
        'insufficient_days': insufficient_days,
        'recommendations': recommendations,
        'available_budget': available_budget,
        'gameweek': gameweek,
        'date_range': f"{start_date} to {end_date}"
    })

@app.route('/api/schedule/<int:player_id>')
def get_player_schedule(player_id):
    """Get schedule for a specific player"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            g.game_date,
            g.game_time,
            t.team_abbreviation as team,
            CASE 
                WHEN p.team_id = g.home_team_id THEN 'vs ' || at.team_abbreviation
                ELSE '@ ' || ht.team_abbreviation
            END as opponent
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        JOIN games g ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
        JOIN teams ht ON g.home_team_id = ht.team_id
        JOIN teams at ON g.away_team_id = at.team_id
        WHERE p.player_id = ?
            AND g.game_date >= '2025-12-16'
            AND g.game_date <= '2025-12-22'
        ORDER BY g.game_date, g.game_time
    """, (player_id,))
    
    schedule = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    return jsonify(schedule)

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
        
        # Get player info
        cur.execute(f"""
            SELECT p.player_id, p.player_name, p.team_id, t.team_abbreviation as team
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            WHERE p.player_id IN ({placeholders})
        """, player_ids)
        
        players_dict = {row['player_id']: dict(row) for row in cur.fetchall()}
        conn.close()
        
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
            # Parse game datetime (assume games table has date in YYYY-MM-DD)
            game_date_str = game['game_date']
            game_time_str = game['game_time'] or '00:00'
            
            # Combine date and time and make it timezone-aware
            try:
                game_dt = datetime.strptime(f"{game_date_str} {game_time_str}", '%Y-%m-%d %H:%M')
                game_dt = game_dt.replace(tzinfo=madrid_tz)
            except:
                game_dt = datetime.strptime(game_date_str, '%Y-%m-%d')
                game_dt = game_dt.replace(tzinfo=madrid_tz)
            
            # Find which fantasy gameday this game belongs to
            # Assign games to gamedays based on deadline windows
            fantasy_gameday_label = None
            
            for i, (gw, day_num, deadline) in enumerate(gameweek_gamedays):
                next_deadline = gameweek_gamedays[i+1][2] if i+1 < len(gameweek_gamedays) else None
                
                if i == 0:
                    # First gameday: include all games before next deadline (or before this deadline if last)
                    if next_deadline is None:
                        fantasy_gameday_label = f"GW{gw} Day {day_num}"
                        break
                    elif game_dt < next_deadline:
                        fantasy_gameday_label = f"GW{gw} Day {day_num}"
                        break
                else:
                    # Subsequent gamedays: games between previous and next deadline
                    prev_deadline = gameweek_gamedays[i-1][2]
                    if next_deadline is None:
                        # Last gameday
                        if game_dt >= prev_deadline:
                            fantasy_gameday_label = f"GW{gw} Day {day_num}"
                            break
                    elif game_dt >= prev_deadline and game_dt < next_deadline:
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
        
        return jsonify({'games_by_day': games_by_day})
    
    except Exception as e:
        print(f"Error in get_game_schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'games_by_day': {}}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
