#!/bin/bash
# Manually update Portainer stack from Git repository
# Run this on your NAS after pushing changes to GitHub

echo "🔄 Updating beat-ampacimon-crew stack in Portainer..."

# Your Portainer webhook URL - get this from Portainer stack settings
WEBHOOK_URL="YOUR_WEBHOOK_URL_HERE"

if [ "$WEBHOOK_URL" = "YOUR_WEBHOOK_URL_HERE" ]; then
    echo "⚠️  Please update WEBHOOK_URL in this script first"
    echo "Get it from: Portainer → Stacks → beat-ampacimon-crew → Webhook"
    exit 1
fi

curl -X POST "$WEBHOOK_URL"

echo "✅ Update triggered! Check Portainer for deployment status."
