#!/usr/bin/env python3
"""
Analyze current lineup and recommend 2 transactions prioritizing:
1. FIRST: Roster depth (ensuring 5 players per game day)
2. SECOND: Fantasy point average
"""

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import itertools

# Database path
DB_PATH = '/home/velasvalen17/myproject/nba_fantasy.db'

# Available budget for transactions
AVAILABLE_BUDGET = 1.7  # in millions

# Current roster (from user's image)
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

def get_player_games_by_day():
    """Get games for each player organized by fantasy day."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    all_players = CURRENT_ROSTER['backcourt'] + CURRENT_ROSTER['frontcourt']
    placeholders = ','.join(['?'] * len(all_players))
    
    cur.execute(f"""
        SELECT 
            p.player_name,
            p.position,
            g.game_date,
            g.game_time
        FROM players p
        JOIN games g ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
        WHERE p.player_name IN ({placeholders})
            AND g.game_date >= '2025-12-16'
            AND g.game_date <= '2025-12-22'
        ORDER BY p.player_name, g.game_date, g.game_time
    """, all_players)
    
    games = cur.fetchall()
    conn.close()
    
    # Apply fantasy day grouping
    player_days = {}
    for player_name, position, game_date, game_time in games:
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
        
        if player_name not in player_days:
            player_days[player_name] = {'position': position, 'days': set()}
        player_days[player_name]['days'].add(fantasy_day)
    
    return player_days

def calculate_day_coverage(roster_bc, roster_fc, player_days):
    """Calculate how many players are available on each game day."""
    all_roster = roster_bc + roster_fc
    day_coverage = {}
    
    for player in all_roster:
        if player in player_days:
            for day in player_days[player]['days']:
                if day not in day_coverage:
                    day_coverage[day] = {'bc': 0, 'fc': 0, 'total': 0, 'players': []}
                day_coverage[day]['total'] += 1
                day_coverage[day]['players'].append(player)
                if player in roster_bc:
                    day_coverage[day]['bc'] += 1
                else:
                    day_coverage[day]['fc'] += 1
    
    return day_coverage

def get_available_players():
    """Get all available players with their stats, salaries, and game schedule."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Get players with recent stats and games next week
    cur.execute("""
        WITH recent_stats AS (
            SELECT 
                pgs.player_id,
                AVG(pgs.points + pgs.rebounds + 2 * pgs.assists + 
                    3 * pgs.blocks + 3 * pgs.steals) as fantasy_avg,
                COUNT(*) as games_played
            FROM player_game_stats pgs
            JOIN games g ON pgs.game_id = g.game_id
            WHERE g.game_date >= '2025-12-09' AND g.game_date <= '2025-12-15'
            GROUP BY pgs.player_id
            HAVING games_played >= 3
        ),
        next_week_games AS (
            SELECT 
                p.player_id,
                p.player_name,
                g.game_date,
                g.game_time
            FROM players p
            JOIN games g ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
            WHERE g.game_date >= '2025-12-16' AND g.game_date <= '2025-12-22'
        )
        SELECT DISTINCT
            p.player_id,
            p.player_name,
            p.position,
            p.salary,
            rs.fantasy_avg,
            rs.games_played
        FROM players p
        JOIN recent_stats rs ON p.player_id = rs.player_id
        JOIN next_week_games nwg ON p.player_id = nwg.player_id
        WHERE p.salary IS NOT NULL
        ORDER BY rs.fantasy_avg DESC
    """)
    
    players = cur.fetchall()
    
    # Get game days for each player
    result = []
    for player_id, player_name, position, salary, fantasy_avg, games_played in players:
        cur.execute("""
            SELECT game_date, game_time
            FROM games g
            JOIN players p ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
            WHERE p.player_id = ?
                AND g.game_date >= '2025-12-16' 
                AND g.game_date <= '2025-12-22'
        """, (player_id,))
        
        game_dates = cur.fetchall()
        
        # Apply fantasy day grouping
        fantasy_days = set()
        for game_date, game_time in game_dates:
            if game_time:
                hour = int(game_time.split(':')[0])
                if hour < 12:
                    date_obj = datetime.strptime(game_date, '%Y-%m-%d')
                    prev_day = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
                    fantasy_days.add(prev_day)
                else:
                    fantasy_days.add(game_date)
            else:
                fantasy_days.add(game_date)
        
        result.append({
            'player_id': player_id,
            'player_name': player_name,
            'position': position,
            'salary': salary,
            'fantasy_avg': fantasy_avg,
            'games_played': games_played,
            'fantasy_days': fantasy_days
        })
    
    conn.close()
    return result

def main():
    print("\n" + "="*80)
    print("TRANSACTION RECOMMENDATIONS - PRIORITIZING ROSTER DEPTH")
    print("="*80 + "\n")
    
    # Get current roster coverage
    player_days = get_player_games_by_day()
    current_coverage = calculate_day_coverage(
        CURRENT_ROSTER['backcourt'], 
        CURRENT_ROSTER['frontcourt'], 
        player_days
    )
    
    # Map calendar dates to gameweek.day format
    madrid_tz = ZoneInfo('Europe/Madrid')
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    
    sorted_days = sorted(current_coverage.keys())
    day_labels = {}
    for day in sorted_days:
        day_obj = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
        days_since_start = (day_obj - season_start).days
        day_in_week = (days_since_start % 7) + 1
        gameweek = (days_since_start // 7) + 1
        day_labels[day] = f"{gameweek}.{day_in_week}"
    
    print("Current Roster Coverage by Game Day:")
    print("-" * 80)
    insufficient_days = []
    for day in sorted_days:
        coverage = current_coverage[day]
        label = day_labels[day]
        status = "✓" if coverage['total'] >= 5 else "⚠️ INSUFFICIENT"
        print(f"  {label} ({day}): {coverage['total']} players ({coverage['bc']} BC, {coverage['fc']} FC) {status}")
        if coverage['total'] < 5:
            insufficient_days.append(day)
    
    print(f"\n⚠️  Days with insufficient players: {len(insufficient_days)}")
    for day in insufficient_days:
        print(f"    - {day_labels[day]} ({day}): Need {5 - current_coverage[day]['total']} more players")
    
    # Get available players
    print("\n" + "-" * 80)
    print("Finding best transactions to improve roster depth...")
    print("-" * 80 + "\n")
    
    available_players = get_available_players()
    
    # Filter out current roster
    current_roster_names = CURRENT_ROSTER['backcourt'] + CURRENT_ROSTER['frontcourt']
    available_players = [p for p in available_players if p['player_name'] not in current_roster_names]
    
    # Get current roster with stats
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    current_roster_details = []
    for player_name in current_roster_names:
        cur.execute("""
            WITH recent_stats AS (
                SELECT 
                    AVG(pgs.points + pgs.rebounds + 2 * pgs.assists + 
                        3 * pgs.blocks + 3 * pgs.steals) as fantasy_avg
                FROM player_game_stats pgs
                JOIN games g ON pgs.game_id = g.game_id
                JOIN players p ON pgs.player_id = p.player_id
                WHERE p.player_name = ?
                    AND g.game_date >= '2025-12-09' 
                    AND g.game_date <= '2025-12-15'
            )
            SELECT 
                p.player_id,
                p.player_name,
                p.position,
                p.salary,
                rs.fantasy_avg
            FROM players p
            LEFT JOIN recent_stats rs
            WHERE p.player_name = ?
        """, (player_name, player_name))
        
        row = cur.fetchone()
        if row:
            player_id, name, position, salary, fantasy_avg = row
            current_roster_details.append({
                'player_id': player_id,
                'player_name': name,
                'position': position,
                'salary': salary or 0,
                'fantasy_avg': fantasy_avg or 0,
                'fantasy_days': player_days.get(name, {}).get('days', set())
            })
    
    conn.close()
    
    # Try all combinations of 2 transactions
    best_transactions = None
    best_score = float('-inf')
    best_coverage = None
    
    for drops in itertools.combinations(current_roster_details, 2):
        # Calculate budget after drops
        drop_salary = sum(d['salary'] for d in drops)
        budget = AVAILABLE_BUDGET + drop_salary
        
        # Check position constraints (can't drop all of one position)
        drop_bc = sum(1 for d in drops if d['player_name'] in CURRENT_ROSTER['backcourt'])
        drop_fc = sum(1 for d in drops if d['player_name'] in CURRENT_ROSTER['frontcourt'])
        
        if drop_bc > 4 or drop_fc > 4:  # Would leave us with < 1 in a position
            continue
        
        # Try pairs of adds that fit position and budget constraints
        for adds in itertools.combinations(available_players, 2):
            add_salary = sum(a['salary'] for a in adds)
            
            if add_salary > budget:
                continue
            
            # Check position constraints
            add_bc = sum(1 for a in adds if 'G' in a['position'] or a['position'] == 'G-F')
            add_fc = sum(1 for a in adds if 'F' in a['position'] or 'C' in a['position'])
            
            # After drops and adds, check if we maintain roster balance
            new_bc_count = 5 - drop_bc + add_bc
            new_fc_count = 5 - drop_fc + add_fc
            
            if new_bc_count < 3 or new_bc_count > 5 or new_fc_count < 3 or new_fc_count > 5:
                continue
            
            # Calculate new roster
            new_roster_bc = [p for p in CURRENT_ROSTER['backcourt'] if p not in [d['player_name'] for d in drops]]
            new_roster_fc = [p for p in CURRENT_ROSTER['frontcourt'] if p not in [d['player_name'] for d in drops]]
            
            for add in adds:
                if 'G' in add['position'] or add['position'] == 'G-F':
                    new_roster_bc.append(add['player_name'])
                else:
                    new_roster_fc.append(add['player_name'])
            
            # Calculate new coverage
            new_player_days = player_days.copy()
            for drop in drops:
                if drop['player_name'] in new_player_days:
                    del new_player_days[drop['player_name']]
            
            for add in adds:
                new_player_days[add['player_name']] = {
                    'position': add['position'],
                    'days': add['fantasy_days']
                }
            
            new_coverage = calculate_day_coverage(new_roster_bc, new_roster_fc, new_player_days)
            
            # Calculate score:
            # Priority 1: Number of days with >= 5 players
            # Priority 2: Total player-days available
            # Priority 3: Fantasy points
            days_with_5plus = sum(1 for cov in new_coverage.values() if cov['total'] >= 5)
            total_player_days = sum(cov['total'] for cov in new_coverage.values())
            total_fp = sum(a['fantasy_avg'] * len(a['fantasy_days']) for a in adds) - sum(d['fantasy_avg'] * len(d['fantasy_days']) for d in drops)
            
            # Weight: days with 5+ is most important (weight 1000), then player-days (weight 100), then FP
            score = days_with_5plus * 1000 + total_player_days * 100 + total_fp
            
            if score > best_score:
                best_score = score
                best_transactions = (drops, adds)
                best_coverage = new_coverage
    
    if best_transactions:
        drops, adds = best_transactions
        
        print("RECOMMENDED TRANSACTIONS:")
        print("=" * 80)
        
        for i, (drop, add) in enumerate(zip(drops, adds), 1):
            drop_days_str = ", ".join(sorted([day_labels.get(d, d) for d in drop['fantasy_days']]))
            add_days_str = ", ".join(sorted([day_labels.get(d, d) for d in add['fantasy_days']]))
            
            print(f"\nTransaction #{i}:")
            print(f"  DROP: {drop['player_name']}")
            print(f"        ${drop['salary']:.1f}M, {drop['fantasy_avg']:.1f} FP/G")
            print(f"        Plays on: {drop_days_str}")
            print(f"  ADD:  {add['player_name']}")
            print(f"        ${add['salary']:.1f}M, {add['fantasy_avg']:.1f} FP/G")
            print(f"        Plays on: {add_days_str}")
        
        # Calculate cost
        drop_salary = sum(d['salary'] for d in drops)
        add_salary = sum(a['salary'] for a in adds)
        net_cost = add_salary - drop_salary
        
        print(f"\n" + "-" * 80)
        print(f"Budget Impact:")
        print(f"  Available: ${AVAILABLE_BUDGET:.1f}M")
        print(f"  Freed from drops: ${drop_salary:.1f}M")
        print(f"  Cost of adds: ${add_salary:.1f}M")
        print(f"  Net cost: ${net_cost:.1f}M")
        print(f"  Remaining: ${AVAILABLE_BUDGET - net_cost:.1f}M")
        
        print(f"\n" + "=" * 80)
        print("NEW ROSTER COVERAGE:")
        print("-" * 80)
        
        for day in sorted(best_coverage.keys()):
            coverage = best_coverage[day]
            label = day_labels.get(day, day)
            old_total = current_coverage.get(day, {}).get('total', 0)
            change = coverage['total'] - old_total
            change_str = f"(+{change})" if change > 0 else f"({change})" if change < 0 else ""
            status = "✓" if coverage['total'] >= 5 else "⚠️"
            print(f"  {label} ({day}): {coverage['total']} players {change_str} ({coverage['bc']} BC, {coverage['fc']} FC) {status}")
        
        days_fixed = sum(1 for day, cov in best_coverage.items() 
                        if cov['total'] >= 5 and current_coverage.get(day, {}).get('total', 0) < 5)
        if days_fixed > 0:
            print(f"\n✓ Fixed {days_fixed} day(s) that had insufficient players")
        
    else:
        print("❌ Could not find transactions that fit budget and position constraints")
    
    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    main()
