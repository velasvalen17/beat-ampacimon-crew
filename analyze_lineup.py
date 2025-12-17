#!/usr/bin/env python3
"""
Analyze current lineup and recommend 2 transactions for next gameweek
"""

from database import get_connection
import sys
from zoneinfo import ZoneInfo

# Available salary budget (in millions)
AVAILABLE_BUDGET = 1.7

# Current user lineup
CURRENT_LINEUP = {
    'frontcourt': [
        'Jalen Johnson',
        'Nikola Jokić', 
        'Julius Randle',
        'Derik Queen',
        'Kyshawn George'
    ],
    'backcourt': [
        'Nickeil Alexander-Walker',
        'Cedric Coward',
        'Ryan Rollins',
        'Ajay Mitchell',
        'Immanuel Quickley'
    ]
}

# Our optimal roster recommendations
OPTIMAL_ROSTER = {
    'frontcourt': [
        'Nikola Jokić',
        'Alperen Sengun',
        'Lauri Markkanen',
        'Cooper Flagg',
        'Marvin Bagley III'
    ],
    'backcourt': [
        'Keyonte George',
        'Kon Knueppel',
        'Cam Spencer',
        'VJ Edgecombe'
    ]
}

def analyze_transactions():
    conn = get_connection()
    cur = conn.cursor()
    
    print("\n" + "🔄" + "="*118 + "🔄")
    print(" " * 40 + "LINEUP OPTIMIZATION - 2 FREE TRANSACTIONS")
    print(" " * 40 + "Based on Dec 9-15 Performance (Madrid Time)")
    print("🔄" + "="*118 + "🔄\n")
    
    all_current = CURRENT_LINEUP['frontcourt'] + CURRENT_LINEUP['backcourt']
    all_optimal = OPTIMAL_ROSTER['frontcourt'] + OPTIMAL_ROSTER['backcourt']
    
    # Get performance stats for current lineup (Dec 9-15)
    print("📊 YOUR CURRENT LINEUP PERFORMANCE:\n")
    
    cur.execute("""
        SELECT 
            p.player_name,
            p.position,
            t.team_name,
            p.salary,
            COUNT(DISTINCT pgs.game_id) as games_played,
            ROUND(AVG(pgs.points + pgs.rebounds + 2*pgs.assists + 3*pgs.blocks + 3*pgs.steals), 1) as fantasy_avg
        FROM players p
        LEFT JOIN teams t ON p.team_id = t.team_id
        LEFT JOIN player_game_stats pgs ON p.player_id = pgs.player_id
        LEFT JOIN games g ON pgs.game_id LIKE g.game_id || '_%'
        WHERE p.player_name IN ({})
        AND (g.game_date IS NULL OR (g.game_date >= '2025-12-09' AND g.game_date <= '2025-12-15'))
        GROUP BY p.player_id, p.player_name, p.position, t.team_name, p.salary
        ORDER BY fantasy_avg DESC NULLS LAST
    """.format(','.join(['?'] * len(all_current))), all_current)
    
    current_stats = cur.fetchall()
    
    print("🔵 BACK COURT:")
    bc_total = 0
    bc_players = []
    for row in current_stats:
        name = row[0]
        if name in CURRENT_LINEUP['backcourt']:
            pos, team, salary, games, fp = row[1:6]
            salary_str = f"${salary:.1f}M" if salary else "N/A"
            fp_str = f"{fp:.1f}" if fp else "0.0"
            games_str = f"{games}G" if games else "0G"
            print(f"   • {name:<30} {pos:<8} {fp_str:>6} FP/G  {salary_str:>8}  ({games_str})")
            bc_players.append((name, fp if fp else 0))
            bc_total += fp if fp else 0
    
    print(f"\n🔴 FRONT COURT:")
    fc_total = 0
    fc_players = []
    for row in current_stats:
        name = row[0]
        if name in CURRENT_LINEUP['frontcourt']:
            pos, team, salary, games, fp = row[1:6]
            salary_str = f"${salary:.1f}M" if salary else "N/A"
            fp_str = f"{fp:.1f}" if fp else "0.0"
            games_str = f"{games}G" if games else "0G"
            print(f"   • {name:<30} {pos:<8} {fp_str:>6} FP/G  {salary_str:>8}  ({games_str})")
            fc_players.append((name, fp if fp else 0))
            fc_total += fp if fp else 0
    
    total_fp = bc_total + fc_total
    print(f"\n   💰 TOTAL PROJECTED: {total_fp:.1f} FP/G")
    
    # Get performance for optimal roster players NOT in current lineup
    # Get games per team for NEXT week (Dec 16-22)
    print("\n\n" + "─"*120)
    print("\n📅 GAMES SCHEDULED NEXT WEEK (Dec 16-22):\n")
    
    cur.execute("""
        SELECT t.team_name, t.team_abbreviation, t.team_id, COUNT(DISTINCT g.game_id) as games
        FROM teams t
        LEFT JOIN games g ON (t.team_id = g.home_team_id OR t.team_id = g.away_team_id)
        AND g.game_date >= '2025-12-16' AND g.game_date <= '2025-12-22'
        GROUP BY t.team_id, t.team_name, t.team_abbreviation
        ORDER BY games DESC, t.team_name
    """)
    
    team_games_next_week = {}
    team_games_rows = cur.fetchall()
    for team_name, abbr, team_id, games in team_games_rows:
        team_games_next_week[team_id] = games
        if games > 0:
            print(f"   {abbr:>3}: {games} games - {team_name}")
    
    print("\n" + "─"*120)
    print("\n🎯 RECOMMENDED PLAYERS (Not Currently in Your Lineup):\n")
    
    players_to_add = [p for p in all_optimal if p not in all_current]
    
    if not players_to_add:
        print("   ✅ You already have all our recommended players!")
        return
    
    cur.execute("""
        SELECT 
            p.player_name,
            p.position,
            t.team_name,
            p.team_id,
            p.salary,
            COUNT(DISTINCT pgs.game_id) as games_played_last_week,
            ROUND(AVG(pgs.points + pgs.rebounds + 2*pgs.assists + 3*pgs.blocks + 3*pgs.steals), 1) as fantasy_avg,
            CASE 
                WHEN p.salary > 0 THEN ROUND(AVG(pgs.points + pgs.rebounds + 2*pgs.assists + 3*pgs.blocks + 3*pgs.steals) / p.salary, 2)
                ELSE 0
            END as value_per_mil
        FROM players p
        LEFT JOIN teams t ON p.team_id = t.team_id
        LEFT JOIN player_game_stats pgs ON p.player_id = pgs.player_id
        LEFT JOIN games g ON pgs.game_id LIKE g.game_id || '_%'
        WHERE p.player_name IN ({})
        AND (g.game_date >= '2025-12-09' AND g.game_date <= '2025-12-15')
        GROUP BY p.player_id, p.player_name, p.position, t.team_name, p.team_id, p.salary
        HAVING games_played_last_week >= 2
        ORDER BY fantasy_avg DESC
    """.format(','.join(['?'] * len(players_to_add))), players_to_add)
    
    available_stats = cur.fetchall()
    
    def is_backcourt(pos):
        if not pos:
            return False
        pos_upper = pos.upper()
        return any(x in pos_upper for x in ['PG', 'SG', 'G']) or pos_upper == 'G-F'
    
    print("🔵 BACK COURT OPTIONS:")
    bc_recommendations = []
    for row in available_stats:
        name, pos, team, team_id, salary, games_last_week, fp, value = row
        if is_backcourt(pos):
            games_next_week = team_games_next_week.get(team_id, 0)
            projected_fp = fp * games_next_week
            salary_str = f"${salary:.1f}M" if salary else "N/A"
            print(f"   ⭐ {name:<30} {pos:<8} {fp:>6.1f} FP/G × {games_next_week}G = {projected_fp:>6.1f} FP  {salary_str:>8}")
            bc_recommendations.append((name, fp, salary if salary else 999, value, games_next_week, projected_fp))
    
    print(f"\n🔴 FRONT COURT OPTIONS:")
    fc_recommendations = []
    for row in available_stats:
        name, pos, team, team_id, salary, games_last_week, fp, value = row
        if not is_backcourt(pos):
            games_next_week = team_games_next_week.get(team_id, 0)
            projected_fp = fp * games_next_week
            salary_str = f"${salary:.1f}M" if salary else "N/A"
            print(f"   ⭐ {name:<30} {pos:<8} {fp:>6.1f} FP/G × {games_next_week}G = {projected_fp:>6.1f} FP  {salary_str:>8}")
            fc_recommendations.append((name, fp, salary if salary else 999, value, games_next_week, projected_fp))
    
    # Get salaries for current players to calculate budget
    player_salary_map = {}
    for row in current_stats:
        player_salary_map[row[0]] = row[3] if row[3] else 0
    
    # Find weakest players in current lineup
    bc_players_sorted = sorted(bc_players, key=lambda x: x[1])
    fc_players_sorted = sorted(fc_players, key=lambda x: x[1])
    
    # Recommend 2 best transactions with salary constraints
    print("\n\n" + "="*120)
    print(f"\n💰 SALARY BUDGET: ${AVAILABLE_BUDGET:.1f}M available\n")
    print("💡 RECOMMENDED 2 TRANSACTIONS (considering salary constraints):\n")
    
    # Try to find the best 2 transactions that fit the budget
    best_transactions = []
    
    # Generate all possible transaction pairs
    all_bc_drops = [(name, fp, player_salary_map.get(name, 0)) for name, fp in bc_players_sorted]
    all_fc_drops = [(name, fp, player_salary_map.get(name, 0)) for name, fp in fc_players_sorted]
    
    # Try combinations of 2 transactions
    from itertools import combinations, product
    
    possible_pairs = []
    
    # Get current players' games next week for comparison
    current_player_games = {}
    for row in current_stats:
        name, pos, team, salary, games, fp = row
        team_id = None
        for t_name, t_abbr, t_id, t_games in team_games_rows:
            if t_name == team:
                team_id = t_id
                break
        if team_id:
            games_next = team_games_next_week.get(team_id, 0)
            current_player_games[name] = (fp, games_next, fp * games_next)
    
    # BC + BC transactions
    for (drop1, drop2) in combinations(all_bc_drops, 2):
        for (add1, add2) in combinations(bc_recommendations, 2):
            budget_available = AVAILABLE_BUDGET + drop1[2] + drop2[2]
            cost = add1[2] + add2[2]
            if cost <= budget_available:
                # Use projected total FP (FP/G × games next week)
                drop1_proj = current_player_games.get(drop1[0], (drop1[1], 0, 0))[2]
                drop2_proj = current_player_games.get(drop2[0], (drop2[1], 0, 0))[2]
                improvement = (add1[5] - drop1_proj) + (add2[5] - drop2_proj)
                if improvement > 0:
                    possible_pairs.append({
                        'drops': [drop1, drop2],
                        'adds': [add1, add2],
                        'improvement': improvement,
                        'budget_used': cost,
                        'budget_left': budget_available - cost
                    })
    
    # FC + FC transactions
    for (drop1, drop2) in combinations(all_fc_drops, 2):
        for (add1, add2) in combinations(fc_recommendations, 2):
            budget_available = AVAILABLE_BUDGET + drop1[2] + drop2[2]
            cost = add1[2] + add2[2]
            if cost <= budget_available:
                drop1_proj = current_player_games.get(drop1[0], (drop1[1], 0, 0))[2]
                drop2_proj = current_player_games.get(drop2[0], (drop2[1], 0, 0))[2]
                improvement = (add1[5] - drop1_proj) + (add2[5] - drop2_proj)
                if improvement > 0:
                    possible_pairs.append({
                        'drops': [drop1, drop2],
                        'adds': [add1, add2],
                        'improvement': improvement,
                        'budget_used': cost,
                        'budget_left': budget_available - cost
                    })
    
    # BC + FC transactions
    for drop_bc in all_bc_drops:
        for drop_fc in all_fc_drops:
            for add_bc in bc_recommendations:
                for add_fc in fc_recommendations:
                    budget_available = AVAILABLE_BUDGET + drop_bc[2] + drop_fc[2]
                    cost = add_bc[2] + add_fc[2]
                    if cost <= budget_available:
                        drop_bc_proj = current_player_games.get(drop_bc[0], (drop_bc[1], 0, 0))[2]
                        drop_fc_proj = current_player_games.get(drop_fc[0], (drop_fc[1], 0, 0))[2]
                        improvement = (add_bc[5] - drop_bc_proj) + (add_fc[5] - drop_fc_proj)
                        if improvement > 0:
                            possible_pairs.append({
                                'drops': [drop_bc, drop_fc],
                                'adds': [add_bc, add_fc],
                                'improvement': improvement,
                                'budget_used': cost,
                                'budget_left': budget_available - cost
                            })
    
    # Sort by improvement
    possible_pairs.sort(key=lambda x: x['improvement'], reverse=True)
    
    if possible_pairs:
        best = possible_pairs[0]
        
        drop1_games = current_player_games.get(best['drops'][0][0], (0, 0, 0))[1]
        drop2_games = current_player_games.get(best['drops'][1][0], (0, 0, 0))[1]
        drop1_proj = current_player_games.get(best['drops'][0][0], (0, 0, 0))[2]
        drop2_proj = current_player_games.get(best['drops'][1][0], (0, 0, 0))[2]
        
        print(f"   1️⃣  DROP: {best['drops'][0][0]:<30} ({best['drops'][0][1]:.1f} FP/G × {drop1_games}G = {drop1_proj:.1f} FP, ${best['drops'][0][2]:.1f}M)")
        print(f"      ADD:  {best['adds'][0][0]:<30} ({best['adds'][0][1]:.1f} FP/G × {best['adds'][0][4]}G = {best['adds'][0][5]:.1f} FP, ${best['adds'][0][2]:.1f}M)")
        print(f"      📈 IMPROVEMENT: +{best['adds'][0][5] - drop1_proj:.1f} FP for the week\n")
        
        print(f"   2️⃣  DROP: {best['drops'][1][0]:<30} ({best['drops'][1][1]:.1f} FP/G × {drop2_games}G = {drop2_proj:.1f} FP, ${best['drops'][1][2]:.1f}M)")
        print(f"      ADD:  {best['adds'][1][0]:<30} ({best['adds'][1][1]:.1f} FP/G × {best['adds'][1][4]}G = {best['adds'][1][5]:.1f} FP, ${best['adds'][1][2]:.1f}M)")
        print(f"      📈 IMPROVEMENT: +{best['adds'][1][5] - drop2_proj:.1f} FP for the week\n")
        
        print(f"   💰 BUDGET: ${AVAILABLE_BUDGET:.1f}M + ${best['drops'][0][2]:.1f}M + ${best['drops'][1][2]:.1f}M = ${AVAILABLE_BUDGET + best['drops'][0][2] + best['drops'][1][2]:.1f}M available")
        print(f"   💳 COST: ${best['adds'][0][2]:.1f}M + ${best['adds'][1][2]:.1f}M = ${best['budget_used']:.1f}M")
        print(f"   💵 REMAINING: ${best['budget_left']:.1f}M")
        print(f"   📊 TOTAL IMPROVEMENT: +{best['improvement']:.1f} FP for the week")
    else:
        print("   ⚠️  No affordable transactions found that improve your team!")
        print(f"   💡 You have ${AVAILABLE_BUDGET:.1f}M available. Consider saving for bigger moves.")
    
    print("🔄" + "="*118 + "🔄\n")
    conn.close()

if __name__ == '__main__':
    analyze_transactions()
