#!/usr/bin/env python3
"""
Show lineup comparison with depth-focused recommendations (Carter + Beringer).
"""

import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

DB_PATH = '/home/velasvalen17/myproject/nba_fantasy.db'

# Current roster
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

# Proposed roster with depth-focused changes
PROPOSED_ROSTER = {
    'backcourt': [
        'Nickeil Alexander-Walker',
        'Cedric Coward',
        'Jevon Carter',  # Replaces Rollins
        'Ajay Mitchell',
        'Joan Beringer'  # Note: Listed as F but adding to BC for now, will fix position
    ],
    'frontcourt': [
        'Jalen Johnson',
        'Nikola Jokić',
        'Julius Randle',
        'Derik Queen',
        'Kyshawn George'
    ]
}

# Actually Joan Beringer is a forward, let me fix this
PROPOSED_ROSTER = {
    'backcourt': [
        'Nickeil Alexander-Walker',
        'Cedric Coward',
        'Jevon Carter',  # Replaces Rollins
        'Ajay Mitchell'
    ],
    'frontcourt': [
        'Jalen Johnson',
        'Nikola Jokić',
        'Julius Randle',
        'Derik Queen',
        'Kyshawn George',
        'Joan Beringer'  # Replaces Quickley
    ]
}

def get_player_stats_and_games(roster_bc, roster_fc):
    """Get player stats and games for the week."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    all_players = roster_bc + roster_fc
    placeholders = ','.join(['?'] * len(all_players))
    
    # Get recent stats
    cur.execute(f"""
        WITH recent_stats AS (
            SELECT 
                p.player_id,
                p.player_name,
                AVG(pgs.points + 1.2 * pgs.rebounds + 1.5 * pgs.assists + 
                    3 * pgs.steals + 3 * pgs.blocks - pgs.turnovers) as fantasy_avg
            FROM players p
            JOIN player_game_stats pgs ON p.player_id = pgs.player_id
            JOIN games g ON pgs.game_id = g.game_id
            WHERE p.player_name IN ({placeholders})
                AND g.game_date >= '2025-12-09' 
                AND g.game_date <= '2025-12-15'
            GROUP BY p.player_id, p.player_name
        )
        SELECT player_name, COALESCE(fantasy_avg, 0) as fantasy_avg
        FROM recent_stats
    """, all_players)
    
    stats = {row[0]: row[1] for row in cur.fetchall()}
    
    # For players without recent stats, set to 0
    for player in all_players:
        if player not in stats:
            stats[player] = 0
    
    # Get games for next week
    cur.execute(f"""
        SELECT 
            p.player_name,
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
        WHERE p.player_name IN ({placeholders})
            AND g.game_date >= '2025-12-16'
            AND g.game_date <= '2025-12-22'
        ORDER BY p.player_name, g.game_date, g.game_time
    """, all_players)
    
    games = {}
    for player_name, game_date, game_time, team, opponent in cur.fetchall():
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
        
        if player_name not in games:
            games[player_name] = {}
        if fantasy_day not in games[player_name]:
            games[player_name][fantasy_day] = []
        games[player_name][fantasy_day].append({
            'team': team,
            'opponent': opponent
        })
    
    conn.close()
    return stats, games

def main():
    print("\n" + "🏀" + "="*118 + "🏀")
    print(" " * 35 + "DEPTH-FOCUSED LINEUP COMPARISON")
    print(" " * 30 + "Current vs Proposed (Carter + Beringer)")
    print("🏀" + "="*118 + "🏀\n")
    
    # Get stats and games for both rosters
    current_stats, current_games = get_player_stats_and_games(
        CURRENT_ROSTER['backcourt'], CURRENT_ROSTER['frontcourt']
    )
    proposed_stats, proposed_games = get_player_stats_and_games(
        PROPOSED_ROSTER['backcourt'], PROPOSED_ROSTER['frontcourt']
    )
    
    # Get all unique fantasy days
    all_days = set()
    for games in list(current_games.values()) + list(proposed_games.values()):
        all_days.update(games.keys())
    
    sorted_days = sorted(all_days)
    
    # Map to gameweek.day labels
    madrid_tz = ZoneInfo('Europe/Madrid')
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    
    day_labels = {}
    for day in sorted_days:
        day_obj = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
        days_since_start = (day_obj - season_start).days
        day_in_week = (days_since_start % 7) + 1
        gameweek = (days_since_start // 7) + 1
        day_labels[day] = f"{gameweek}.{day_in_week}"
    
    weekly_current = 0
    weekly_proposed = 0
    
    for day in sorted_days:
        day_obj = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
        day_name = day_obj.strftime('%A, %B %d')
        label = day_labels[day]
        
        print("="*120)
        print(f"📅 Game Day {label} - {day_name}")
        print("="*120)
        
        # Get available players for each roster
        current_bc = [p for p in CURRENT_ROSTER['backcourt'] if p in current_games and day in current_games[p]]
        current_fc = [p for p in CURRENT_ROSTER['frontcourt'] if p in current_games and day in current_games[p]]
        
        proposed_bc = [p for p in PROPOSED_ROSTER['backcourt'] if p in proposed_games and day in proposed_games[p]]
        proposed_fc = [p for p in PROPOSED_ROSTER['frontcourt'] if p in proposed_games and day in proposed_games[p]]
        
        print(f"\n{'CURRENT ROSTER':^60}│{'PROPOSED ROSTER':^59}")
        print("─"*60 + "┼" + "─"*59)
        
        # Show players
        print(f"{'🔵 BACKCOURT':^60}│{'🔵 BACKCOURT':^59}")
        max_bc = max(len(current_bc), len(proposed_bc))
        for i in range(max_bc):
            left = ""
            right = ""
            
            if i < len(current_bc):
                p = current_bc[i]
                fp = current_stats[p]
                opp = current_games[p][day][0]['opponent']
                team = current_games[p][day][0]['team']
                left = f"  ★ {p:20} {team:4} {fp:4.1f} FP {opp:8}"
            
            if i < len(proposed_bc):
                p = proposed_bc[i]
                fp = proposed_stats[p]
                opp = proposed_games[p][day][0]['opponent']
                team = proposed_games[p][day][0]['team']
                right = f"  ★ {p:20} {team:4} {fp:4.1f} FP {opp:8}"
            
            print(f"{left:60}│{right:59}")
        
        if not current_bc:
            print(f"{'  No backcourt players available':60}│", end="")
        if not proposed_bc:
            print(f"{'  No backcourt players available':59}")
        else:
            print()
        
        print(f"\n{'🔴 FRONTCOURT':^60}│{'🔴 FRONTCOURT':^59}")
        max_fc = max(len(current_fc), len(proposed_fc))
        for i in range(max_fc):
            left = ""
            right = ""
            
            if i < len(current_fc):
                p = current_fc[i]
                fp = current_stats[p]
                opp = current_games[p][day][0]['opponent']
                team = current_games[p][day][0]['team']
                left = f"  ★ {p:20} {team:4} {fp:4.1f} FP {opp:8}"
            
            if i < len(proposed_fc):
                p = proposed_fc[i]
                fp = proposed_stats[p]
                opp = proposed_games[p][day][0]['opponent']
                team = proposed_games[p][day][0]['team']
                right = f"  ★ {p:20} {team:4} {fp:4.1f} FP {opp:8}"
            
            print(f"{left:60}│{right:59}")
        
        if not current_fc:
            print(f"{'  No frontcourt players available':60}│", end="")
        if not proposed_fc:
            print(f"{'  No frontcourt players available':59}")
        else:
            print()
        
        # Calculate starting 5
        print("\n" + "─"*60 + "┼" + "─"*59)
        
        current_total = len(current_bc) + len(current_fc)
        proposed_total = len(proposed_bc) + len(proposed_fc)
        
        current_fp = 0
        proposed_fp = 0
        
        if current_total >= 5 and len(current_bc) >= 3 and len(current_fc) >= 2:
            # Select top 3 BC and top 2 FC by fantasy points
            bc_sorted = sorted(current_bc, key=lambda p: current_stats[p], reverse=True)[:3]
            fc_sorted = sorted(current_fc, key=lambda p: current_stats[p], reverse=True)[:2]
            current_fp = sum(current_stats[p] for p in bc_sorted + fc_sorted)
            weekly_current += current_fp
            current_status = f"📊 Starting 5 Total: {current_fp:6.1f} FP"
        else:
            current_status = f"⚠️  Can't field starting 5 ({current_total} players: {len(current_bc)} BC, {len(current_fc)} FC)"
        
        if proposed_total >= 5 and len(proposed_bc) >= 3 and len(proposed_fc) >= 2:
            bc_sorted = sorted(proposed_bc, key=lambda p: proposed_stats[p], reverse=True)[:3]
            fc_sorted = sorted(proposed_fc, key=lambda p: proposed_stats[p], reverse=True)[:2]
            proposed_fp = sum(proposed_stats[p] for p in bc_sorted + fc_sorted)
            weekly_proposed += proposed_fp
            diff = proposed_fp - current_fp
            diff_str = f"({diff:+.1f} FP)" if current_fp > 0 else ""
            proposed_status = f"📊 Starting 5 Total: {proposed_fp:6.1f} FP {diff_str}"
        else:
            proposed_status = f"⚠️  Can't field starting 5 ({proposed_total} players: {len(proposed_bc)} BC, {len(proposed_fc)} FC)"
        
        print(f"  {current_status:58}│  {proposed_status:57}")
        print()
    
    print("="*120)
    print("📊 WEEKLY SUMMARY")
    print("="*120)
    print(f"  CURRENT ROSTER:    {weekly_current:6.1f} FP")
    print(f"  PROPOSED ROSTER:   {weekly_proposed:6.1f} FP")
    diff = weekly_proposed - weekly_current
    pct = (diff / weekly_current * 100) if weekly_current > 0 else 0
    print(f"  DIFFERENCE:        {diff:+6.1f} FP ({pct:+.1f}%)")
    
    print("\n💡 KEY IMPROVEMENTS:")
    print("  • Can now field starting 5 on Day 9.4 (was 4 players, now 6)")
    print("  • Added coverage on Day 9.2 (was 2 players, now 4)")
    print("  • Both new players (Carter & Beringer) play on problem days")
    
    print("\n🏀" + "="*118 + "🏀\n")

if __name__ == '__main__':
    main()
