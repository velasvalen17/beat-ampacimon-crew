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

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install docker-compose first:"
    echo "   https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and docker-compose are installed"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs
echo "✅ Directories created"
echo ""

# Build the container
echo "🔨 Building Docker image..."
docker-compose build
echo "✅ Image built successfully"
echo ""

# Start the container
echo "🚀 Starting container..."
docker-compose up -d
echo "✅ Container started"
echo ""

# Wait a moment for initialization
echo "⏳ Waiting for initialization (30 seconds)..."
sleep 30

# Check status
echo ""
echo "📊 Container Status:"
docker-compose ps
echo ""

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  • View logs:           docker-compose logs -f"
echo "  • Check database:      sqlite3 data/nba_fantasy.db"
echo "  • Run manual update:   docker-compose exec nba-fantasy python3 /app/daily_update.py"
echo "  • View update logs:    tail -f logs/updates.log"
echo ""
echo "The container will automatically update the database every day at 6 AM."
echo "See README_DOCKER.md for more information."
