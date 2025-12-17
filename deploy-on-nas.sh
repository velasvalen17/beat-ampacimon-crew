#!/bin/bash
# Run this script on your NAS

set -e

echo "🏀 Building Beat Ampacimon Crew on NAS"
echo "======================================"

# Clone or pull latest
if [ -d "beat-ampacimon-crew" ]; then
    echo "📥 Pulling latest changes..."
    cd beat-ampacimon-crew
    git pull
else
    echo "📥 Cloning repository..."
    git clone https://github.com/velasvalen17/beat-ampacimon-crew.git
    cd beat-ampacimon-crew
fi

echo ""
echo "🔨 Building Docker image..."
docker build -t beat-ampacimon-crew:latest .

echo ""
echo "✅ Image built successfully!"
echo ""
echo "Next: Deploy in Portainer with the compose file below"
