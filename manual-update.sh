#!/bin/bash
# Run this on your NAS to manually trigger database update

echo "🔄 Manually triggering NBA data update..."
echo ""

# Option 1: Run the daily update script
echo "Running daily_update.py..."
docker exec beat-ampacimon-crew python3 /app/daily_update.py

echo ""
echo "✅ Update complete!"
echo ""
echo "Check logs:"
echo "  docker logs beat-ampacimon-crew --tail 50"
