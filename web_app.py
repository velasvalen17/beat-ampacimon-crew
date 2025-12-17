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
        LIMIT 10
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
            p.team_id,
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
    
    # Map to gameweek.day labels (relative to the selected gameweek)
    day_labels = {}
    insufficient_days = []
    
    for day in sorted(day_coverage.keys()):
        day_obj = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
        # Calculate day number within THIS gameweek (1-7)
        days_from_week_start = (day_obj - week_start).days
        day_in_week = days_from_week_start + 1
        
        # Use the requested gameweek number, not calculated from season start
        label = f"{gameweek}.{day_in_week}"
        day_labels[day] = label
        
        if day_coverage[day]['total'] < 5:
            insufficient_days.append({
                'date': day,
                'label': label,
                'total': day_coverage[day]['total'],
                'needed': 5 - day_coverage[day]['total']
            })
    
    # Calculate how many unique days each team plays in this gameweek
    cur.execute("""
        SELECT 
            t.team_id,
            t.team_abbreviation,
            COUNT(DISTINCT g.game_date) as game_days
        FROM teams t
        JOIN games g ON (t.team_id = g.home_team_id OR t.team_id = g.away_team_id)
        WHERE g.game_date >= ? AND g.game_date <= ?
        GROUP BY t.team_id
    """, [start_date, end_date])
    
    team_game_days = {row['team_id']: row['game_days'] for row in cur.fetchall()}
    
    # Calculate average game days for current roster teams
    roster_team_ids = [p['team_id'] for p in roster_details]
    roster_team_game_days = [team_game_days.get(tid, 0) for tid in roster_team_ids]
    avg_roster_team_days = sum(roster_team_game_days) / len(roster_team_game_days) if roster_team_game_days else 0
    
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
                    p.team_id,
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
                    AVG(pgs.points + pgs.rebounds + 2 * pgs.assists + 
                        3 * pgs.blocks + 3 * pgs.steals) as fantasy_avg,
                    AVG(pgs.minutes_played) as avg_minutes,
                    COUNT(*) as games_played
                FROM (
                    SELECT 
                        pgs2.player_id,
                        pgs2.points,
                        pgs2.rebounds,
                        pgs2.assists,
                        pgs2.blocks,
                        pgs2.steals,
                        pgs2.minutes_played,
                        pgs2.game_date,
                        ROW_NUMBER() OVER (PARTITION BY pgs2.player_id ORDER BY pgs2.game_date DESC) as rn
                    FROM player_game_stats pgs2
                ) pgs
                WHERE pgs.rn <= 5
                GROUP BY pgs.player_id
                HAVING games_played >= 3 
                    AND AVG(pgs.minutes_played) >= 18 
                    AND AVG(pgs.points + pgs.rebounds + 2 * pgs.assists + 
                        3 * pgs.blocks + 3 * pgs.steals) > 0
            )
            SELECT 
                pg.player_id,
                pg.player_name,
                pg.position,
                pg.salary,
                pg.team_id,
                pg.team,
                pg.game_dates,
                pg.total_games,
                COALESCE(rs.fantasy_avg, 0) as fantasy_avg,
                COALESCE(rs.avg_minutes, 0) as avg_minutes
            FROM player_games pg
            INNER JOIN recent_stats rs ON pg.player_id = rs.player_id
            ORDER BY rs.fantasy_avg DESC, pg.total_games DESC
            LIMIT 200
        """, current_roster + [start_date, end_date] + problem_dates)
        
        candidates = [dict(row) for row in cur.fetchall()]
        
        # Add team game days to each candidate
        for candidate in candidates:
            candidate['team_game_days'] = team_game_days.get(candidate['team_id'], 0)
        
        # Get fantasy stats for current roster from ALL games (not date-filtered)
        cur.execute(f"""
            SELECT 
                pgs.player_id,
                COUNT(*) as games_played,
                AVG(pgs.points + pgs.rebounds + 2 * pgs.assists + 
                    3 * pgs.blocks + 3 * pgs.steals) as fantasy_avg
            FROM player_game_stats pgs
            WHERE pgs.player_id IN ({placeholders})
            GROUP BY pgs.player_id
        """, current_roster)
        
        roster_stats = {row['player_id']: {
            'fantasy_avg': row['fantasy_avg'],
            'games_played': row['games_played']
        } for row in cur.fetchall()}
        
        # Add fantasy stats to roster details
        for player in roster_details:
            stats = roster_stats.get(player['player_id'], {'fantasy_avg': 0, 'games_played': 0})
            player['fantasy_avg'] = stats['fantasy_avg']
            player['games_played'] = stats['games_played']
        
        # Find best 2 transaction pairs
        budget_with_drops = available_budget
        
        best_options = []
        
        # Calculate average fantasy points of current roster for comparison
        players_with_stats = [p for p in roster_details if p['fantasy_avg'] > 0]
        roster_avg_fp = sum(p['fantasy_avg'] for p in players_with_stats) / len(players_with_stats) if players_with_stats else 0
        roster_total_fp = sum(p['fantasy_avg'] for p in roster_details)
        
        # Try combinations of 2 drops and 2 adds
        for drops in itertools.combinations(roster_details, 2):
            drop_salary = sum(d['salary'] for d in drops)
            budget = budget_with_drops + drop_salary
            
            # Check position constraints
            drop_bc = sum(1 for d in drops if 'G' in d['position'])
            drop_fc = sum(1 for d in drops if 'F' in d['position'] or 'C' in d['position'])
            
            if drop_bc > 4 or drop_fc > 4:
                continue
            
            # Calculate average FP of players being dropped
            drop_avg_fp = sum(d['fantasy_avg'] for d in drops) / len(drops)
            
            for adds in itertools.combinations(candidates[:100], 2):
                add_salary = sum(a['salary'] for a in adds)
                
                # Hard budget constraint - can't exceed budget
                if add_salary > budget:
                    continue
                
                # Check position balance
                add_bc = sum(1 for a in adds if 'G' in a['position'])
                add_fc = sum(1 for a in adds if 'F' in a['position'] or 'C' in a['position'])
                
                new_bc_count = 5 - drop_bc + add_bc
                new_fc_count = 5 - drop_fc + add_fc
                
                # Position balance is a hard constraint
                if new_bc_count < 3 or new_bc_count > 5 or new_fc_count < 3 or new_fc_count > 5:
                    continue
                
                # Track warnings for suboptimal recommendations
                warnings = []
                
                # Calculate average FP of players being added
                add_avg_fp = sum(a['fantasy_avg'] for a in adds) / len(adds)
                
                # Check quality concerns (don't skip, just warn)
                fp_threshold_good = drop_avg_fp * 0.85
                fp_threshold_acceptable = drop_avg_fp * 0.70
                
                if add_avg_fp < fp_threshold_acceptable:
                    fp_loss_pct = ((drop_avg_fp - add_avg_fp) / drop_avg_fp * 100) if drop_avg_fp > 0 else 0
                    warnings.append(f"⚠️ Significant FP drop: New players avg {add_avg_fp:.1f} FP/G vs drops avg {drop_avg_fp:.1f} FP/G ({fp_loss_pct:.0f}% decrease)")
                elif add_avg_fp < fp_threshold_good:
                    warnings.append(f"⚡ Moderate FP impact: New players slightly lower quality ({add_avg_fp:.1f} vs {drop_avg_fp:.1f} FP/G)")
                
                # Check if players are below roster average
                weak_players = [a for a in adds if a['fantasy_avg'] < roster_avg_fp * 0.5 and a['fantasy_avg'] > 0]
                if weak_players:
                    player_names = ', '.join([p['name'] for p in weak_players])
                    warnings.append(f"⚠️ Below roster average: {player_names} significantly below team quality")
                
                # Check budget usage
                budget_usage_pct = (add_salary / budget * 100) if budget > 0 else 0
                if add_salary < budget * 0.3:
                    warnings.append(f"💰 Low budget usage: Only using ${add_salary:.1f}M of ${budget:.1f}M available ({budget_usage_pct:.0f}%)")
                
                # Calculate comprehensive improvement score
                # Priorities: Team game days > Games improvement > Fantasy Points > Depth
                
                depth_score = 0
                fp_improvement = 0
                games_improvement = 0
                team_days_improvement = 0
                
                # Calculate team game days improvement (KEY METRIC)
                drop_team_days = sum(team_game_days.get(d['team_id'], 0) for d in drops)
                add_team_days = sum(a['team_game_days'] for a in adds)
                team_days_improvement = add_team_days - drop_team_days
                
                # Prioritize teams that play MORE days than roster average
                teams_above_avg = sum(1 for a in adds if a['team_game_days'] > avg_roster_team_days)
                team_quality_bonus = teams_above_avg * 100
                
                # Calculate fantasy point impact
                drop_fp = sum(d['fantasy_avg'] for d in drops)
                add_fp = sum(a['fantasy_avg'] for a in adds)
                fp_improvement = add_fp - drop_fp
                
                # Bonus for similar or better fantasy points (minimize FP loss)
                fp_similarity_bonus = 0
                for i, add in enumerate(adds):
                    if i < len(drops):
                        fp_ratio = add['fantasy_avg'] / drops[i]['fantasy_avg'] if drops[i]['fantasy_avg'] > 0 else 1
                        if fp_ratio >= 0.9:  # Within 10% of dropped player
                            fp_similarity_bonus += 50
                        elif fp_ratio >= 0.8:  # Within 20%
                            fp_similarity_bonus += 30
                
                # Calculate games and depth improvement
                drop_total_games = sum(len(player_days.get(d['player_id'], [])) for d in drops)
                
                for add in adds:
                    add_dates = add['game_dates'].split(',')
                    games_improvement += len(add_dates)
                    
                    # Bonus for covering problem days
                    for date in add_dates:
                        if date in problem_dates:
                            depth_score += 50
                
                games_improvement -= drop_total_games
                
                # Penalty for removing coverage on problem days
                for drop in drops:
                    if drop['player_id'] in player_days:
                        for date in player_days[drop['player_id']]:
                            if date in problem_dates:
                                depth_score -= 30
                
                # Budget efficiency bonus: prefer using more of available budget
                budget_usage = add_salary / budget if budget > 0 else 0
                budget_bonus = budget_usage * 20
                
                # Add positive indicators
                if team_days_improvement > 0:
                    warnings.append(f"✅ Better schedule: Teams play {add_team_days} vs {drop_team_days} game days")
                if games_improvement > 0:
                    warnings.append(f"✅ More games: +{games_improvement} total games in gameweek")
                if fp_improvement > 0:
                    warnings.append(f"✅ Better quality: +{fp_improvement:.1f} FP/G improvement")
                
                # Combined score: Team days (most important) > Games > FP similarity > FP improvement > Depth
                score = (team_days_improvement * 200 + team_quality_bonus + 
                        games_improvement * 100 + fp_similarity_bonus + 
                        fp_improvement * 50 + depth_score + budget_bonus)
                
                best_options.append({
                    'drops': [{'player_id': d['player_id'], 'name': d['player_name'], 'salary': d['salary'], 'position': d['position'], 'fantasy_avg': d['fantasy_avg'], 'team': d.get('team', ''), 'team_game_days': team_game_days.get(d['team_id'], 0)} for d in drops],
                    'adds': [{'player_id': a['player_id'], 'name': a['player_name'], 'salary': a['salary'], 'position': a['position'], 'games': len(a['game_dates'].split(',')), 'fantasy_avg': a['fantasy_avg'], 'avg_minutes': a.get('avg_minutes', 0), 'team': a.get('team', ''), 'team_game_days': a['team_game_days']} for a in adds],
                    'cost': add_salary - drop_salary,
                    'fp_improvement': fp_improvement,
                    'depth_score': depth_score,
                    'games_improvement': games_improvement,
                    'team_days_improvement': team_days_improvement,
                    'score': score,
                    'warnings': warnings
                })
        
        # Sort by score and always get top 3 (or all if less than 3)
        best_options.sort(key=lambda x: x['score'], reverse=True)
        recommendations = best_options[:3]
        
        # If we have fewer than 3 recommendations, add a note
        if len(recommendations) < 3 and len(recommendations) > 0:
            pass  # Frontend will handle displaying available recommendations
    
    conn.close()
    
    return jsonify({
        'roster': roster_details,
        'roster_avg_fp': round(roster_avg_fp, 1),
        'roster_total_fp': round(roster_total_fp, 1),
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
        
        return jsonify({'games_by_day': games_by_day})
    
    except Exception as e:
        print(f"Error in get_game_schedule: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'games_by_day': {}}), 500

@app.route('/api/optimal_team/<int:gameweek>', methods=['GET'])
def get_optimal_team(gameweek):
    """Build the optimal 10-player team for a gameweek based on last 7 games performance"""
    try:
        conn = get_db_connection()
        
        # Get gameweek date range
        gameweek_query = """
            SELECT start_date, end_date 
            FROM gameweeks 
            WHERE week_number = ?
        """
        gw_row = conn.execute(gameweek_query, (gameweek,)).fetchone()
        if not gw_row:
            return jsonify({'error': 'Invalid gameweek'}), 400
        
        start_date = gw_row['start_date']
        end_date = gw_row['end_date']
        
        # Get all players with their last 7 games stats and games in this gameweek
        query = """
            WITH recent_stats AS (
                SELECT 
                    player_id,
                    fantasy_points,
                    minutes_played,
                    game_date,
                    ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY game_date DESC) as rn
                FROM player_game_stats
                WHERE minutes_played > 0
            ),
            player_averages AS (
                SELECT 
                    player_id,
                    AVG(fantasy_points) as avg_fp,
                    AVG(minutes_played) as avg_minutes,
                    COUNT(*) as games_played
                FROM recent_stats
                WHERE rn <= 7
                GROUP BY player_id
                HAVING COUNT(*) >= 3 AND AVG(minutes_played) >= 18
            ),
            gameweek_games AS (
                SELECT 
                    p.player_id,
                    COUNT(DISTINCT g.game_id) as games_in_gameweek
                FROM players p
                JOIN teams t ON p.team_id = t.team_id
                JOIN games g ON (g.home_team_id = t.team_id OR g.away_team_id = t.team_id)
                WHERE g.game_date >= ? AND g.game_date <= ?
                GROUP BY p.player_id
            )
            SELECT 
                p.player_id,
                p.player_name,
                p.position,
                p.salary,
                t.team_abbreviation as team,
                pa.avg_fp,
                pa.avg_minutes,
                pa.games_played as recent_games,
                COALESCE(gg.games_in_gameweek, 0) as games_in_gameweek,
                pa.avg_fp * COALESCE(gg.games_in_gameweek, 0) as projected_total_fp
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN player_averages pa ON p.player_id = pa.player_id
            LEFT JOIN gameweek_games gg ON p.player_id = gg.player_id
            WHERE COALESCE(gg.games_in_gameweek, 0) >= 2
            ORDER BY projected_total_fp DESC
        """
        
        cursor = conn.execute(query, (start_date, end_date))
        all_candidates = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        # Filter out players with null or zero salary
        all_candidates = [p for p in all_candidates if p.get('salary') and p['salary'] > 0]
        
        if not all_candidates:
            return jsonify({'error': 'No eligible players found', 'optimal_team': []})
        
        # Separate by position
        backcourt = [p for p in all_candidates if 'G' in p['position']]
        frontcourt = [p for p in all_candidates if 'F' in p['position'] or 'C' in p['position']]
        
        # Smart optimization: Use a mixed strategy
        # 1. Take top 2 from each position (best performers)
        # 2. Fill remaining slots with best value players that fit budget
        budget = 100.0
        selected_backcourt = []
        selected_frontcourt = []
        
        # Step 1: Take top 2 performers from each position group
        for i in range(min(2, len(backcourt))):
            selected_backcourt.append(backcourt[i])
        for i in range(min(2, len(frontcourt))):
            selected_frontcourt.append(frontcourt[i])
        
        # Step 2: Fill remaining slots, prioritizing by value (FP per $ spent)
        remaining_bc = backcourt[len(selected_backcourt):]
        remaining_fc = frontcourt[len(selected_frontcourt):]
        
        # Calculate value ratio for remaining players
        for p in remaining_bc:
            p['value_ratio'] = p['projected_total_fp'] / p['salary'] if p['salary'] > 0 else 0
        for p in remaining_fc:
            p['value_ratio'] = p['projected_total_fp'] / p['salary'] if p['salary'] > 0 else 0
        
        # Sort by value ratio
        remaining_bc.sort(key=lambda x: x['value_ratio'], reverse=True)
        remaining_fc.sort(key=lambda x: x['value_ratio'], reverse=True)
        
        # Fill remaining slots
        bc_idx = fc_idx = 0
        while len(selected_backcourt) < 5 or len(selected_frontcourt) < 5:
            current_total = sum(p['salary'] for p in selected_backcourt + selected_frontcourt)
            added_any = False
            
            # Try to add BC if needed
            if len(selected_backcourt) < 5 and bc_idx < len(remaining_bc):
                if current_total + remaining_bc[bc_idx]['salary'] <= budget:
                    selected_backcourt.append(remaining_bc[bc_idx])
                    added_any = True
                bc_idx += 1
            
            # Try to add FC if needed
            if len(selected_frontcourt) < 5 and fc_idx < len(remaining_fc):
                current_total = sum(p['salary'] for p in selected_backcourt + selected_frontcourt)
                if current_total + remaining_fc[fc_idx]['salary'] <= budget:
                    selected_frontcourt.append(remaining_fc[fc_idx])
                    added_any = True
                fc_idx += 1
            
            # Break if we can't add any more players
            if not added_any and bc_idx >= len(remaining_bc) and fc_idx >= len(remaining_fc):
                break
        
        optimal_team = selected_backcourt + selected_frontcourt
        total_salary = sum(p['salary'] for p in optimal_team)
        total_projected_fp = sum(p['projected_total_fp'] for p in optimal_team)
        
        return jsonify({
            'gameweek': gameweek,
            'date_range': f"{start_date} to {end_date}",
            'optimal_team': optimal_team,
            'total_salary': round(total_salary, 1),
            'total_projected_fp': round(total_projected_fp, 1),
            'backcourt_count': len(selected_backcourt),
            'frontcourt_count': len(selected_frontcourt)
        })
    
    except Exception as e:
        print(f"Error in get_optimal_team: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
