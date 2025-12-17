#!/bin/bash
# Quick deployment script for Portainer

set -e

echo "🏀 Beat Ampacimon Crew - Docker Deployment"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

echo "Step 1: Building Docker image..."
docker build -t beat-ampacimon-crew:latest .

echo ""
echo "Step 2: Saving image to tar file..."
docker save -o beat-ampacimon-crew.tar beat-ampacimon-crew:latest

echo ""
echo "✅ Image built and saved successfully!"
echo ""
echo "📦 Image file: beat-ampacimon-crew.tar"
echo "📊 File size: $(du -h beat-ampacimon-crew.tar | cut -f1)"
echo ""
echo "Next steps:"
echo "==========="
echo "1. Transfer the image to your NAS:"
echo "   scp beat-ampacimon-crew.tar user@nas.local:/path/to/destination/"
echo ""
echo "2. SSH into your NAS and load the image:"
echo "   ssh user@nas.local"
echo "   docker load -i /path/to/destination/beat-ampacimon-crew.tar"
echo ""
echo "3. Deploy via Portainer (http://nas.local:9000/):"
echo "   - Go to Stacks → Add stack"
echo "   - Name: beat-ampacimon-crew"
echo "   - Copy contents from: docker-compose.portainer.yml"
echo "   - Click 'Deploy the stack'"
echo ""
echo "4. Access your app at: http://nas.local:5000"
echo ""
echo "📖 For detailed instructions, see: PORTAINER_DEPLOYMENT.md"
