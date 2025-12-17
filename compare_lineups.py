#!/usr/bin/env python3
"""
Compare daily lineups between current roster and proposed roster
"""

from database import get_connection
from datetime import datetime
from zoneinfo import ZoneInfo

# Current user lineup
CURRENT_ROSTER = {
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

# Proposed roster (after transactions)
PROPOSED_ROSTER = {
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
        'Keyonte George',      # IN (replaces Rollins)
        'Ajay Mitchell',
        'Kon Knueppel'        # IN (replaces Quickley)
    ]
}

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

def get_daily_comparison():
    conn = get_connection()
    cur = conn.cursor()
    
    print("\n" + "🏀" + "="*118 + "🏀")
    print(" " * 30 + "DAILY LINEUP COMPARISON - CURRENT vs PROPOSED")
    print(" " * 40 + "Gameweek 9: Dec 16-22, 2025 (Madrid Time)")
    print("🏀" + "="*118 + "🏀\n")
    
    # Get all game dates and times for next week
    cur.execute("""
        SELECT game_date, game_time
        FROM games
        WHERE game_date >= '2025-12-16' AND game_date <= '2025-12-22'
        ORDER BY game_date, game_time
    """)
    
    # Group games into fantasy days
    # Fantasy day cutoff: Next day's games before 6 AM count as previous fantasy day
    from datetime import timedelta
    fantasy_days = {}
    for game_date, game_time in cur.fetchall():
        if game_time:
            hour = int(game_time.split(':')[0])
            # Games before noon (Madrid time) count as previous fantasy day (previous night)
            if hour < 12:
                # Shift to previous day
                date_obj = datetime.strptime(game_date, '%Y-%m-%d')
                prev_day = (date_obj - timedelta(days=1)).strftime('%Y-%m-%d')
                fantasy_day = prev_day
            else:
                fantasy_day = game_date
        else:
            fantasy_day = game_date
        
        if fantasy_day not in fantasy_days:
            fantasy_days[fantasy_day] = []
        fantasy_days[fantasy_day].append((game_date, game_time))
    
    days = sorted(fantasy_days.keys())
    
    if not days:
        print("❌ No games found for this week")
        return
    
    all_current = CURRENT_ROSTER['frontcourt'] + CURRENT_ROSTER['backcourt']
    all_proposed = PROPOSED_ROSTER['frontcourt'] + PROPOSED_ROSTER['backcourt']
    
    current_total_fp = 0
    proposed_total_fp = 0
    
    madrid_tz = ZoneInfo('Europe/Madrid')
    
    # Get gameweek and calculate day within week
    season_start = datetime(2025, 10, 21, tzinfo=madrid_tz)
    
    # Merge day 7 with day 6 for fantasy purposes (week ends on day 6)
    merged_days = []
    i = 0
    while i < len(days):
        day_obj = datetime.strptime(days[i], '%Y-%m-%d').replace(tzinfo=madrid_tz)
        days_since_start = (day_obj - season_start).days
        day_in_week = (days_since_start % 7) + 1
        
        # If this is day 7 of the week and we have a day 6, merge with previous day
        if day_in_week == 7 and merged_days and merged_days[-1]['day_in_week'] == 6:
            # Merge day 7 into day 6
            merged_days[-1]['calendar_days'].append(days[i])
            merged_days[-1]['games'].extend(fantasy_days[days[i]])
        else:
            merged_days.append({
                'fantasy_day': days[i],
                'calendar_days': [days[i]],
                'games': fantasy_days[days[i]],
                'day_in_week': day_in_week
            })
        i += 1
    
    fantasy_day_num = 1
    for merged_day in merged_days:
        day = merged_day['fantasy_day']
        day_obj = datetime.strptime(day, '%Y-%m-%d').replace(tzinfo=madrid_tz)
        day_name = day_obj.strftime('%A, %B %d')
        
        # Calculate gameweek
        days_since_start = (day_obj - season_start).days
        gameweek = (days_since_start // 7) + 1
        
        # Get all games for this fantasy day
        games_in_fantasy_day = merged_day['games']
        game_count = len(games_in_fantasy_day)
        
        # Get time range
        times = [t for d, t in games_in_fantasy_day if t]
        first_game = min(times) if times else None
        last_game = max(times) if times else None
        
        # Check if this fantasy day includes multiple calendar dates
        calendar_dates = sorted(set(d for d, t in games_in_fantasy_day))
        if len(calendar_dates) > 1:
            date_range = f"{calendar_dates[0][-5:]} - {calendar_dates[-1][-5:]}"
        else:
            date_range = ""
        
        print(f"\n{'='*120}")
        if date_range:
            print(f"📅 Game Day {gameweek}.{fantasy_day_num} - {day_name} ({date_range}) - {game_count} games ({first_game} - {last_game} CET)")
        else:
            print(f"📅 Game Day {gameweek}.{fantasy_day_num} - {day_name} - {game_count} games ({first_game} - {last_game} CET)")
        print(f"{'='*120}\n")
        
        fantasy_day_num += 1
        
        # Get players with games on this fantasy day for CURRENT roster
        # Fantasy day includes games from the calendar day + early morning games (before 12:00) from next day
        game_dates_in_fantasy_day = list(set(d for d, t in games_in_fantasy_day))
        placeholders = ','.join(['?'] * len(game_dates_in_fantasy_day))
        
        cur.execute(f"""
            SELECT DISTINCT
                p.player_name,
                p.position,
                t.team_abbreviation,
                (SELECT ROUND(AVG(pgs2.points + 1.2*pgs2.rebounds + 1.5*pgs2.assists + 3*pgs2.steals + 3*pgs2.blocks - pgs2.turnovers), 1)
                 FROM player_game_stats pgs2
                 JOIN games g2 ON pgs2.game_id LIKE g2.game_id || '_%'
                 WHERE pgs2.player_id = p.player_id
                 AND g2.game_date >= '2025-12-09' AND g2.game_date <= '2025-12-15'
                ) as fantasy_avg,
                CASE 
                    WHEN g.home_team_id = p.team_id THEN 'vs ' || away.team_abbreviation
                    ELSE '@ ' || home.team_abbreviation
                END as matchup
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN games g ON (g.home_team_id = p.team_id OR g.away_team_id = p.team_id)
                AND g.game_date IN ({placeholders})
            JOIN teams home ON g.home_team_id = home.team_id
            JOIN teams away ON g.away_team_id = away.team_id
            WHERE p.player_name IN ({','.join(['?'] * len(all_current))})
            ORDER BY fantasy_avg DESC
        """, game_dates_in_fantasy_day + all_current)
        
        current_day_players = cur.fetchall()
        
        # Get players with games on this fantasy day for PROPOSED roster
        cur.execute(f"""
            SELECT DISTINCT
                p.player_name,
                p.position,
                t.team_abbreviation,
                (SELECT ROUND(AVG(pgs2.points + 1.2*pgs2.rebounds + 1.5*pgs2.assists + 3*pgs2.steals + 3*pgs2.blocks - pgs2.turnovers), 1)
                 FROM player_game_stats pgs2
                 JOIN games g2 ON pgs2.game_id LIKE g2.game_id || '_%'
                 WHERE pgs2.player_id = p.player_id
                 AND g2.game_date >= '2025-12-09' AND g2.game_date <= '2025-12-15'
                ) as fantasy_avg,
                CASE 
                    WHEN g.home_team_id = p.team_id THEN 'vs ' || away.team_abbreviation
                    ELSE '@ ' || home.team_abbreviation
                END as matchup
            FROM players p
            JOIN teams t ON p.team_id = t.team_id
            JOIN games g ON (g.home_team_id = p.team_id OR g.away_team_id = p.team_id)
                AND g.game_date IN ({placeholders})
            JOIN teams home ON g.home_team_id = home.team_id
            JOIN teams away ON g.away_team_id = away.team_id
            WHERE p.player_name IN ({','.join(['?'] * len(all_proposed))})
            ORDER BY fantasy_avg DESC
        """, game_dates_in_fantasy_day + all_proposed)
        
        proposed_day_players = cur.fetchall()
        
        # Split by position
        current_bc = [p for p in current_day_players if is_backcourt(p[1])]
        current_fc = [p for p in current_day_players if is_frontcourt(p[1])]
        
        proposed_bc = [p for p in proposed_day_players if is_backcourt(p[1])]
        proposed_fc = [p for p in proposed_day_players if is_frontcourt(p[1])]
        
        # Display side by side
        print(f"{'CURRENT ROSTER':^58} │ {'PROPOSED ROSTER':^58}")
        print(f"{'─'*58}┼{'─'*58}")
        
        # Backcourt
        print(f"\n{'🔵 BACK COURT':<58} │ {'🔵 BACK COURT':<58}")
        max_bc = max(len(current_bc), len(proposed_bc))
        
        current_bc_fp = 0
        proposed_bc_fp = 0
        
        for i in range(max_bc):
            left = ""
            right = ""
            
            if i < len(current_bc):
                name, pos, team, fp, matchup = current_bc[i]
                marker = "★" if i < 3 else " "
                left = f"  {marker} {name[:20]:<20} {team:<4} {fp:>5.1f} FP {matchup}"
                if i < 3:
                    current_bc_fp += fp
            
            if i < len(proposed_bc):
                name, pos, team, fp, matchup = proposed_bc[i]
                marker = "★" if i < 3 else " "
                right = f"  {marker} {name[:20]:<20} {team:<4} {fp:>5.1f} FP {matchup}"
                if i < 3:
                    proposed_bc_fp += fp
            
            print(f"{left:<58} │ {right:<58}")
        
        if not current_bc:
            print(f"  {'No backcourt players available':<56} │", end="")
        if not proposed_bc:
            print(f" │   No backcourt players available")
        else:
            print()
        
        # Frontcourt
        print(f"\n{'🔴 FRONT COURT':<58} │ {'🔴 FRONT COURT':<58}")
        max_fc = max(len(current_fc), len(proposed_fc))
        
        current_fc_fp = 0
        proposed_fc_fp = 0
        
        for i in range(max_fc):
            left = ""
            right = ""
            
            if i < len(current_fc):
                name, pos, team, fp, matchup = current_fc[i]
                marker = "★" if i < 2 else " "
                left = f"  {marker} {name[:20]:<20} {team:<4} {fp:>5.1f} FP {matchup}"
                if i < 2:
                    current_fc_fp += fp
            
            if i < len(proposed_fc):
                name, pos, team, fp, matchup = proposed_fc[i]
                marker = "★" if i < 2 else " "
                right = f"  {marker} {name[:20]:<20} {team:<4} {fp:>5.1f} FP {matchup}"
                if i < 2:
                    proposed_fc_fp += fp
            
            print(f"{left:<58} │ {right:<58}")
        
        if not current_fc:
            print(f"  {'No frontcourt players available':<56} │", end="")
        if not proposed_fc:
            print(f" │   No frontcourt players available")
        else:
            print()
        
        # Daily totals
        current_day_total = current_bc_fp + current_fc_fp if (len(current_bc) >= 3 and len(current_fc) >= 2) else 0
        proposed_day_total = proposed_bc_fp + proposed_fc_fp if (len(proposed_bc) >= 3 and len(proposed_fc) >= 2) else 0
        
        current_total_fp += current_day_total
        proposed_total_fp += proposed_day_total
        
        diff = proposed_day_total - current_day_total
        diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
        
        print(f"\n{'─'*58}┼{'─'*58}")
        print(f"  📊 Starting 5 Total: {current_day_total:>5.1f} FP          │   📊 Starting 5 Total: {proposed_day_total:>5.1f} FP ({diff_str} FP)")
        
        if current_day_total == 0 and proposed_day_total == 0:
            print(f"  {'⚠️  Insufficient players for starting 5':<56} │   ⚠️  Insufficient players for starting 5")
    
    # Weekly summary
    print(f"\n\n{'='*120}")
    print(f"📊 WEEKLY SUMMARY (Dec 16-22, 2025 - Madrid Time)")
    print(f"{'='*120}\n")
    
    diff = proposed_total_fp - current_total_fp
    diff_str = f"+{diff:.1f}" if diff > 0 else f"{diff:.1f}"
    pct_improvement = (diff / current_total_fp * 100) if current_total_fp > 0 else 0
    
    print(f"  CURRENT ROSTER:   {current_total_fp:>6.1f} FP")
    print(f"  PROPOSED ROSTER:  {proposed_total_fp:>6.1f} FP")
    print(f"  DIFFERENCE:       {diff_str:>6} FP ({pct_improvement:+.1f}%)")
    
    print("\n" + "🏀" + "="*118 + "🏀\n")
    
    conn.close()

if __name__ == '__main__':
    get_daily_comparison()
