#!/bin/bash
# Monitor database population progress

echo "=== NBA Fantasy Database Status ==="
echo ""
sqlite3 ~/myproject/nba_fantasy.db <<'SQL'
.headers on
.mode column
SELECT 
    'teams' as table_name, 
    COUNT(*) as count 
FROM teams
UNION ALL
SELECT 'players', COUNT(*) FROM players
UNION ALL
SELECT 'games', COUNT(*) FROM games
UNION ALL
SELECT 'player_game_stats', COUNT(*) FROM player_game_stats;
SQL

echo ""
echo "Recent player stats (last 10):"
sqlite3 ~/myproject/nba_fantasy.db <<'SQL'
.headers on
.mode column
SELECT 
    p.player_name,
    g.game_date,
    pgs.points,
    pgs.assists,
    pgs.rebounds
FROM player_game_stats pgs
JOIN players p ON pgs.player_id = p.player_id
JOIN games g ON pgs.game_id = g.game_id
ORDER BY pgs.rowid DESC
LIMIT 10;
SQL
