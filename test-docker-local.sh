#!/bin/bash
# Test the Docker build locally before deploying to Portainer

set -e

echo "🏀 Testing Beat Ampacimon Crew locally with Docker"
echo "=================================================="
echo ""

# Build the image
echo "Building Docker image..."
docker build -t beat-ampacimon-crew:latest .

echo ""
echo "Starting container..."
docker-compose up -d

echo ""
echo "Container started! Waiting for initialization..."
sleep 5

echo ""
echo "Container status:"
docker-compose ps

echo ""
echo "Checking logs..."
docker-compose logs --tail=20

echo ""
echo "✅ Local test deployment complete!"
echo ""
echo "📱 Access the app at: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  View logs:     docker-compose logs -f"
echo "  Stop:          docker-compose down"
echo "  Restart:       docker-compose restart"
echo "  Shell access:  docker-compose exec nba-fantasy /bin/bash"
echo ""
echo "When ready to deploy to Portainer, run:"
echo "  ./build-for-portainer.sh"
