#!/bin/bash
# Quick start script for NBA Fantasy Database Docker container

set -e

echo "NBA Fantasy Database - Docker Setup"
echo "===================================="
echo ""

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first:"
    echo "   https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if docker-compose -f config/docker-compose.yml is installed
if ! command -v docker-compose -f config/docker-compose.yml &> /dev/null; then
    echo "❌ docker-compose -f config/docker-compose.yml is not installed. Please install docker-compose -f config/docker-compose.yml first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and docker-compose -f config/docker-compose.yml are installed"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs
echo "✅ Directories created"
echo ""

# Build the container
echo "🔨 Building Docker image..."
docker-compose -f config/docker-compose.yml build
echo "✅ Image built successfully"
echo ""

# Start the container
echo "🚀 Starting container..."
docker-compose -f config/docker-compose.yml up -d
echo "✅ Container started"
echo ""

# Wait a moment for initialization
echo "⏳ Waiting for initialization (30 seconds)..."
sleep 30

# Check status
echo ""
echo "📊 Container Status:"
docker-compose -f config/docker-compose.yml ps
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  • View logs:           docker-compose -f config/docker-compose.yml logs -f"
echo "  • Check database:      sqlite3 data/nba_fantasy.db"
echo "  • Run manual update:   docker-compose -f config/docker-compose.yml exec nba-fantasy python3 /app/daily_update.py"
echo "  • View update logs:    tail -f logs/updates.log"
echo ""
echo "The container will automatically update the database every day at 6 AM."
echo "See README_DOCKER.md for more information."
