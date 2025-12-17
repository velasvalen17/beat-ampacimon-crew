#!/usr/bin/env python3
"""
NBA Fantasy Team Optimizer with Salary Cap Constraints
Builds optimal 10-player roster considering $100M salary cap
"""

from database import get_connection
from collections import defaultdict

def optimize_team_with_salary(max_salary=100.0, performance_weight=0.7):
    """
    Build optimal team with salary constraints.
    
    Args:
        max_salary: Maximum total salary in millions (default 100.0)
        performance_weight: Weight for performance vs value (0-1, default 0.7)
                          Higher = prioritize performance, Lower = prioritize value
    """
    conn = get_connection()
    cur = conn.cursor()
    
    print("🏀" + "="*118 + "🏀")
    print(" " * 25 + "NBA FANTASY - OPTIMAL TEAM WITH SALARY CAP")
    print(" " * 40 + "(Gameweek 9: Dec 16-22, 2025)")
    print("🏀" + "="*118 + "🏀")
    print(f"\n💰 Salary Cap: ${max_salary}M")
    print("📋 Requirements: 5 Backcourt, 5 Frontcourt, Max 2 per team")
    print(f"⚖️  Optimization: {int(performance_weight*100)}% performance, {int((1-performance_weight)*100)}% value\n")
    
    # Get all top performers with salaries
    cur.execute("""
        SELECT 
            p.player_name,
            p.position,
            t.team_name,
            p.team_id,
            p.salary,
            COUNT(DISTINCT SUBSTR(pgs.game_id, 1, 10)) as games_played,
            ROUND(AVG(pgs.points), 1) as avg_points,
            ROUND(AVG(pgs.rebounds), 1) as avg_rebounds,
            ROUND(AVG(pgs.assists), 1) as avg_assists,
            ROUND(AVG(pgs.steals), 1) as avg_steals,
            ROUND(AVG(pgs.blocks), 1) as avg_blocks,
            ROUND(AVG(pgs.turnovers), 1) as avg_turnovers,
            ROUND(AVG(pgs.points + pgs.rebounds + 2*pgs.assists + 3*pgs.blocks + 3*pgs.steals), 1) as fantasy_avg
        FROM player_game_stats pgs
        JOIN players p ON pgs.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
        JOIN games g ON pgs.game_id LIKE g.game_id || '_%'
        WHERE g.game_date >= '2025-12-09' AND g.game_date <= '2025-12-15'
        AND pgs.minutes_played > 0
        AND p.salary IS NOT NULL
        GROUP BY p.player_id, p.player_name, p.position, t.team_name, p.team_id, p.salary
        HAVING games_played >= 2
        ORDER BY fantasy_avg DESC
    """)
    
    all_players = cur.fetchall()
    
    if not all_players:
        print("❌ No salary data available. Run salary_scraper.py first!")
        conn.close()
        return
    
    # Calculate value score for each player
    players_with_value = []
    for p in all_players:
        fantasy_avg = p[12]
        salary = p[4]
        value = fantasy_avg / salary if salary > 0 else 0
        
        # Combined score: weighted average of performance and value
        score = (performance_weight * fantasy_avg) + ((1 - performance_weight) * value * 10)
        
        players_with_value.append(p + (value, score))
    
    # Sort by combined score
    players_with_value.sort(key=lambda x: x[14], reverse=True)
    
    # Position classification
    def is_backcourt(position):
        if not position:
            return False
        pos_upper = position.upper()
        return any(x in pos_upper for x in ['PG', 'SG', 'G']) or pos_upper == 'G-F'
    
    def is_frontcourt(position):
        if not position:
            return False
        pos_upper = position.upper()
        return any(x in pos_upper for x in ['SF', 'PF', 'F-C', 'C-F', 'C', 'F']) or pos_upper == 'F-G'
    
    # Build team with constraints
    selected_team = []
    team_counts = defaultdict(int)
    total_salary = 0.0
    
    backcourt_count = 0
    frontcourt_count = 0
    
    for player in players_with_value:
        if len(selected_team) >= 10:
            break
        
        pos = player[1]
        salary = player[4]
        team_id = player[3]
        
        # Check constraints
        if total_salary + salary > max_salary:
            continue
        
        if team_counts[team_id] >= 2:
            continue
        
        # Check position requirements
        if is_backcourt(pos) and backcourt_count < 5:
            selected_team.append(player)
            backcourt_count += 1
            team_counts[team_id] += 1
            total_salary += salary
        elif is_frontcourt(pos) and frontcourt_count < 5:
            selected_team.append(player)
            frontcourt_count += 1
            team_counts[team_id] += 1
            total_salary += salary
    
    # Display results
    print("─" * 120)
    print(f"{'Position':<12} {'Player':<26} {'Team':<22} {'FP/G':<8} {'Salary':<10} {'Value':<8}")
    print("─" * 120)
    
    backcourt_fp = 0
    frontcourt_fp = 0
    
    print("\n🔵 BACK COURT:")
    for player in selected_team:
        if is_backcourt(player[1]):
            print(f"{player[1]:<12} {player[0]:<26} {player[2]:<22} {player[12]:<8.1f} ${player[4]:<9.1f} {player[13]:<8.2f}")
            backcourt_fp += player[12]
    
    print("\n🔴 FRONT COURT:")
    for player in selected_team:
        if is_frontcourt(player[1]):
            print(f"{player[1]:<12} {player[0]:<26} {player[2]:<22} {player[12]:<8.1f} ${player[4]:<9.1f} {player[13]:<8.2f}")
            frontcourt_fp += player[12]
    
    total_fp = backcourt_fp + frontcourt_fp
    remaining_salary = max_salary - total_salary
    
    print("\n" + "─" * 120)
    print(f"💰 TOTAL SALARY: ${total_salary:.1f}M / ${max_salary}M (${remaining_salary:.1f}M remaining)")
    print(f"📊 TOTAL FANTASY POINTS: {total_fp:.1f} FP/G")
    print(f"   Back Court: {backcourt_fp:.1f} FP/G | Front Court: {frontcourt_fp:.1f} FP/G")
    print(f"⭐ AVERAGE VALUE: {total_fp/total_salary:.2f} FP per $1M")
    print("─" * 120)
    
    # Team distribution
    print("\n📋 TEAM DISTRIBUTION:")
    team_dist = defaultdict(list)
    for player in selected_team:
        team_dist[player[2]].append(player[0])
    
    for team, players in sorted(team_dist.items()):
        print(f"   • {team}: {', '.join(players)}")
    
    # Recommended starting 5
    print("\n💡 RECOMMENDED STARTING 5 (3 BC + 2 FC):")
    starting_bc = [p for p in selected_team if is_backcourt(p[1])][:3]
    starting_fc = [p for p in selected_team if is_frontcourt(p[1])][:2]
    
    print("   Back Court:")
    for p in starting_bc:
        print(f"   • {p[0]} ({p[12]:.1f} FP/G, ${p[4]}M)")
    print("   Front Court:")
    for p in starting_fc:
        print(f"   • {p[0]} ({p[12]:.1f} FP/G, ${p[4]}M)")
    
    starting_total = sum(p[12] for p in starting_bc + starting_fc)
    print(f"\n   Starting 5 Projected: {starting_total:.1f} FP/G")
    
    print("\n🏀" + "="*118 + "🏀\n")
    
    conn.close()


if __name__ == '__main__':
    import sys
    
    # Parse command line arguments
    max_salary = 100.0
    performance_weight = 0.7
    
    if len(sys.argv) > 1:
        try:
            max_salary = float(sys.argv[1])
        except:
            print("Usage: python3 team_optimizer.py [max_salary] [performance_weight]")
            print("Example: python3 team_optimizer.py 100 0.7")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        try:
            performance_weight = float(sys.argv[2])
            if not 0 <= performance_weight <= 1:
                raise ValueError()
        except:
            print("Performance weight must be between 0 and 1")
            sys.exit(1)
    
    optimize_team_with_salary(max_salary, performance_weight)
