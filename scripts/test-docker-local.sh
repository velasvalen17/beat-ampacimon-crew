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
docker-compose -f config/docker-compose.yml up -d

echo ""
echo "Container started! Waiting for initialization..."
sleep 5

echo ""
echo "Container status:"
docker-compose -f config/docker-compose.yml ps

echo ""
echo "Checking logs..."
docker-compose -f config/docker-compose.yml logs --tail=20

echo ""
echo "✅ Local test deployment complete!"
echo ""
echo "📱 Access the app at: http://localhost:5000"
echo ""
echo "Useful commands:"
echo "  View logs:     docker-compose -f config/docker-compose.yml logs -f"
echo "  Stop:          docker-compose -f config/docker-compose.yml down"
echo "  Restart:       docker-compose -f config/docker-compose.yml restart"
echo "  Shell access:  docker-compose -f config/docker-compose.yml exec nba-fantasy /bin/bash"
echo ""
echo "When ready to deploy to Portainer, run:"
echo "  ./build-for-portainer.sh"
