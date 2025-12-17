#!/usr/bin/env python3
"""
Generate optimal starting 5 for each day of the current gameweek
"""

from database import get_connection
from datetime import datetime, timedelta

# Optimal roster from team optimizer
OPTIMAL_ROSTER = {
    'backcourt': [
        ('Keyonte George', 1610612762),  # Utah Jazz
        ('Kon Knueppel', 1610612766),    # Charlotte Hornets (assuming)
        ('Cam Spencer', 1610612763),     # Memphis Grizzlies (assuming)
        ('VJ Edgecombe', 1610612755),    # Philadelphia 76ers (assuming)
    ],
    'frontcourt': [
        ('Nikola Jokić', 1610612743),    # Denver Nuggets
        ('Alperen Sengun', 1610612745),  # Houston Rockets
        ('Lauri Markkanen', 1610612762), # Utah Jazz
        ('Cooper Flagg', 1610612742),    # Dallas Mavericks (assuming)
        ('Marvin Bagley III', 1610612764), # Washington Wizards
    ]
}

def get_daily_lineups():
    """Get optimal starting 5 for each day of the week."""
    conn = get_connection()
    cur = conn.cursor()
    
    print("🏀" + "="*118 + "🏀")
    print(" " * 35 + "OPTIMAL STARTING 5 - DAILY LINEUPS")
    print(" " * 37 + "Recent Games (Dec 9-15, 2025)")
    print("🏀" + "="*118 + "🏀\n")
    
    # Get games for the most recent week we have data for (Dec 9-15)
    cur.execute("""
        SELECT DISTINCT date(game_date) as game_day
        FROM games
        WHERE game_date >= '2025-12-09' AND game_date <= '2025-12-15'
        ORDER BY game_day
    """)
    
    days = [row[0] for row in cur.fetchall()]
    
    if not days:
        print("❌ No games found in database")
        print("💡 Run populate_database.py to add game data")
        return
    
    # Get all roster player names
    all_roster_players = [p[0] for p in OPTIMAL_ROSTER['backcourt']] + [p[0] for p in OPTIMAL_ROSTER['frontcourt']]
    
    for day in days:
        # Parse date
        day_obj = datetime.strptime(day, '%Y-%m-%d')
        day_name = day_obj.strftime('%A, %B %d')
        
        print(f"\n📅 {day_name}")
        print("─" * 120)
        
        # Get our roster players who have games on this day
        cur.execute("""
            SELECT DISTINCT
                p.player_name,
                p.position,
                t.team_name,
                p.salary,
                ROUND(AVG(pgs.points + 1.2*pgs.rebounds + 1.5*pgs.assists + 3*pgs.steals + 3*pgs.blocks - pgs.turnovers), 1) as fantasy_avg,
                g.game_date,
                CASE 
                    WHEN g.home_team_id = p.team_id THEN 'vs ' || away.team_name
                    ELSE '@ ' || home.team_name
                END as matchup
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN player_game_stats pgs ON p.player_id = pgs.player_id
            JOIN games g ON pgs.game_id LIKE g.game_id || '_%'
            JOIN teams home ON g.home_team_id = home.team_id
            JOIN teams away ON g.away_team_id = away.team_id
            WHERE date(g.game_date) = ?
            AND p.player_name IN ({})
            AND g.game_date >= '2025-12-09' AND g.game_date <= '2025-12-15'
            GROUP BY p.player_id, p.player_name, p.position, t.team_name, p.salary, g.game_date, matchup
            ORDER BY fantasy_avg DESC
        """.format(','.join(['?'] * len(all_roster_players))), [day] + all_roster_players)
        
        players_today = cur.fetchall()
        
        if not players_today:
            print("   ⚠️  None of our roster players have games today")
            continue
        
        # Classify by position
        def is_backcourt(pos):
            if not pos:
                return False
            pos_upper = pos.upper()
            return any(x in pos_upper for x in ['PG', 'SG', 'G']) or pos_upper == 'G-F'
        
        def is_frontcourt(pos):
            if not pos:
                return False
            pos_upper = pos.upper()
            return any(x in pos_upper for x in ['SF', 'PF', 'F-C', 'C-F', 'C', 'F']) or pos_upper == 'F-G'
        
        backcourt_available = [p for p in players_today if is_backcourt(p[1])]
        frontcourt_available = [p for p in players_today if is_frontcourt(p[1])]
        
        # Select starting 5: top 3 backcourt + top 2 frontcourt
        starting_bc = backcourt_available[:3]
        starting_fc = frontcourt_available[:2]
        
        if len(starting_bc) < 3 or len(starting_fc) < 2:
            print(f"   ⚠️  Insufficient players available (BC: {len(backcourt_available)}, FC: {len(frontcourt_available)})")
            print(f"   Available players:")
            for p in players_today:
                pos_type = "BC" if is_backcourt(p[1]) else "FC"
                print(f"      [{pos_type}] {p[0]} - {p[4]} FP/G ({p[6]})")
            continue
        
        # Display starting 5
        print("\n   🔵 BACK COURT:")
        total_bc_fp = 0
        for name, pos, team, salary, fp, date, matchup in starting_bc:
            print(f"      • {name:<25} {pos:<8} {fp:>5.1f} FP/G  {matchup}")
            total_bc_fp += fp
        
        print("\n   🔴 FRONT COURT:")
        total_fc_fp = 0
        for name, pos, team, salary, fp, date, matchup in starting_fc:
            print(f"      • {name:<25} {pos:<8} {fp:>5.1f} FP/G  {matchup}")
            total_fc_fp += fp
        
        total_fp = total_bc_fp + total_fc_fp
        print(f"\n   📊 PROJECTED TOTAL: {total_fp:.1f} FP")
        
        # Show bench
        bench = backcourt_available[3:] + frontcourt_available[2:]
        if bench:
            print(f"\n   💺 BENCH ({len(bench)} players):")
            for name, pos, team, salary, fp, date, matchup in bench:
                pos_type = "BC" if is_backcourt(pos) else "FC"
                print(f"      [{pos_type}] {name:<25} {fp:>5.1f} FP/G  {matchup}")
    
    print("\n" + "🏀" + "="*118 + "🏀\n")
    conn.close()

if __name__ == '__main__':
    get_daily_lineups()
