#!/usr/bin/env python3
"""
Find best transactions prioritizing roster depth on problem days (9.2 and 9.4).
"""

import sqlite3

DB_PATH = '/home/velasvalen17/myproject/nba_fantasy.db'
AVAILABLE_BUDGET = 1.7

# Current roster
CURRENT_ROSTER_NAMES = [
    'Nickeil Alexander-Walker', 'Cedric Coward', 'Ryan Rollins', 
    'Ajay Mitchell', 'Immanuel Quickley',  # Backcourt
    'Jalen Johnson', 'Nikola Jokić', 'Julius Randle', 
    'Derik Queen', 'Kyshawn George'  # Frontcourt
]

print("\n" + "="*90)
print("RECOMMENDATIONS PRIORITIZING ROSTER DEPTH")
print("="*90)
print("\nProblem: Days 9.2 (Dec 17) and 9.4 (Dec 19) have insufficient players (< 5)")
print("Strategy: Find players who play on BOTH problem days\n")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Get current roster with salaries
print("Current Roster:")
print("-" * 90)
cur.execute("""
    SELECT player_name, position, salary
    FROM players
    WHERE player_name IN ({})
    ORDER BY salary DESC
""".format(','.join(['?'] * len(CURRENT_ROSTER_NAMES))), CURRENT_ROSTER_NAMES)

current_roster_details = []
for name, pos, salary in cur.fetchall():
    current_roster_details.append({'name': name, 'position': pos, 'salary': salary or 0})
    print(f"  {name:30} {pos:5} ${salary:.1f}M" if salary else f"  {name:30} {pos:5} No salary data")

# Find players who play on BOTH problem days and are affordable
print("\n" + "-" * 90)
print("Top Affordable Players Playing on BOTH Dec 17 and Dec 19:")
print("-" * 90)

cur.execute("""
    SELECT 
        p.player_name,
        p.position,
        p.salary,
        t.team_abbreviation,
        COUNT(DISTINCT CASE WHEN g.game_date IN ('2025-12-17', '2025-12-19') THEN g.game_date END) as problem_days,
        COUNT(DISTINCT g.game_date) as total_games_week
    FROM players p
    JOIN teams t ON p.team_id = t.team_id
    JOIN games g ON (p.team_id = g.home_team_id OR p.team_id = g.away_team_id)
    WHERE p.salary IS NOT NULL
      AND p.salary <= 15.0
      AND p.player_name NOT IN ({})
      AND g.game_date >= '2025-12-16' AND g.game_date <= '2025-12-22'
    GROUP BY p.player_id
    HAVING problem_days = 2
    ORDER BY p.salary ASC
    LIMIT 30
""".format(','.join(['?'] * len(CURRENT_ROSTER_NAMES))), CURRENT_ROSTER_NAMES)

candidates = []
for name, pos, salary, team, problem_days, total_games in cur.fetchall():
    candidates.append({
        'name': name,
        'position': pos,
        'salary': salary,
        'team': team,
        'problem_days': problem_days,
        'total_games': total_games
    })
    if len(candidates) <= 15:  # Print top 15
        print(f"  {name:30} {pos:8} {team:4} ${salary:5.1f}M  (plays {total_games} games this week)")

# Now suggest specific transactions
print("\n" + "="*90)
print("RECOMMENDED TRANSACTIONS:")
print("="*90)

# Strategy: Drop lowest performers who don't play on problem days, add players who do
# Rollins and Quickley don't play on 9.2 or 9.4, so they're good drop candidates

drop_candidates = ['Ryan Rollins', 'Immanuel Quickley']
print("\nDrop candidates (don't play on problem days):")
for name in drop_candidates:
    player = next((p for p in current_roster_details if p['name'] == name), None)
    if player:
        print(f"  ❌ {name:30} ${player['salary']:.1f}M")

budget_after_drops = AVAILABLE_BUDGET
for name in drop_candidates:
    player = next((p for p in current_roster_details if p['name'] == name), None)
    if player:
        budget_after_drops += player['salary']

print(f"\nBudget after drops: ${budget_after_drops:.1f}M")

# Find best 2 adds within budget
print("\nBest additions within budget:")
best_pair = None
best_score = 0

for i, cand1 in enumerate(candidates):
    for cand2 in candidates[i+1:]:
        total_cost = cand1['salary'] + cand2['salary']
        if total_cost <= budget_after_drops:
            # Check position balance
            bc1 = 'G' in cand1['position']
            bc2 = 'G' in cand2['position']
            
            # We're dropping 2 BC (Rollins, Quickley), so we need at least 1 BC back
            if not (bc1 or bc2):
                continue
            
            # Score: prefer pairs with different positions and more total games
            score = cand1['total_games'] + cand2['total_games']
            if bc1 != bc2:  # Different positions
                score += 10
            
            if score > best_score:
                best_score = score
                best_pair = (cand1, cand2, total_cost)

if best_pair:
    cand1, cand2, total_cost = best_pair
    print(f"\n  ✅ ADD: {cand1['name']:30} {cand1['position']:8} {cand1['team']:4} ${cand1['salary']:5.1f}M")
    print(f"          Plays {cand1['total_games']} games including BOTH problem days")
    print(f"\n  ✅ ADD: {cand2['name']:30} {cand2['position']:8} {cand2['team']:4} ${cand2['salary']:5.1f}M")
    print(f"          Plays {cand2['total_games']} games including BOTH problem days")
    print(f"\n  💰 Total cost: ${total_cost:.1f}M (${budget_after_drops - total_cost:.1f}M remaining)")
    
    print("\n" + "-" * 90)
    print("IMPACT:")
    print("-" * 90)
    print(f"  • Day 9.2 (Dec 17): +2 players → {2 + 2} total (still need 1 more for starting 5)")
    print(f"  • Day 9.4 (Dec 19): +2 players → {4 + 2} total (can now field starting 5!) ✓")
else:
    print("\n  ❌ Could not find affordable pair within budget")
    print(f"     Cheapest pair costs ${candidates[0]['salary'] + candidates[1]['salary']:.1f}M")
    print(f"     Available: ${budget_after_drops:.1f}M")

conn.close()

print("\n" + "="*90 + "\n")
