#!/usr/bin/env python3
"""Efficiently populate December player stats for current roster players only."""

from datetime import datetime
from scripts.populate_database import DatabasePopulator
from nba_data_fetcher import NBADataFetcher
from app.database import get_connection

def populate_december_stats():
    """Fetch stats only for players in the current rosters (much faster)."""
    print('Efficiently populating December player stats...')
    print('Step 1: Get player list from database...')
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Get all player IDs from our rosters
    cur.execute("SELECT player_id FROM players ORDER BY player_id")
    player_ids = [row[0] for row in cur.fetchall()]
    print(f'Found {len(player_ids)} players in roster')
    
    # Close connection - populate_player_stats will open its own
    conn.close()
    
    print('\nStep 2: Fetching stats for roster players only (Dec 1-16)...')
    DatabasePopulator.populate_player_stats(
        from_date=datetime(2025, 12, 1),
        to_date=datetime(2025, 12, 16),
        players_list=player_ids  # Only fetch for our roster players
    )
    
    print('\n✓ December stats populated!')
    
    # Show final counts
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM player_game_stats")
    stats_count = cur.fetchone()[0]
    conn.close()
    
    print(f'\nFinal counts:')
    print(f'  Players: {len(player_ids)}')
    print(f'  Player game stats: {stats_count}')

if __name__ == '__main__':
    populate_december_stats()
