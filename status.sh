#!/bin/bash
# Check NBA Fantasy Database Docker container status

echo "NBA Fantasy Database - Container Status"
echo "========================================"
echo ""

# Check if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Container is running"
else
    echo "❌ Container is not running"
    echo "   Start with: docker-compose up -d"
    exit 1
fi

echo ""
echo "📊 Database Statistics:"
echo "------------------------"
docker-compose exec -T nba-fantasy sqlite3 /app/data/nba_fantasy.db <<SQL
.mode column
.headers on
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
echo "📅 Recent Games (last 5):"
echo "-------------------------"
docker-compose exec -T nba-fantasy sqlite3 /app/data/nba_fantasy.db <<SQL
.mode column
.headers on
SELECT 
    game_date,
    (SELECT team_name FROM teams WHERE team_id = home_team_id) as home_team,
    home_score,
    (SELECT team_name FROM teams WHERE team_id = away_team_id) as away_team,
    away_score
FROM games
ORDER BY game_date DESC
LIMIT 5;
SQL

echo ""
echo "📝 Last Update Log Entry:"
echo "-------------------------"
tail -n 1 logs/updates.log 2>/dev/null || echo "No updates logged yet"

echo ""
echo "Commands:"
echo "  • View live logs:      docker-compose logs -f"
echo "  • Run update now:      docker-compose exec nba-fantasy python3 /app/daily_update.py"
echo "  • Restart container:   docker-compose restart"
echo "  • Stop container:      docker-compose stop"
