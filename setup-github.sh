#!/bin/bash
# Initialize Git repository and push to GitHub

set -e

echo "🏀 Beat Ampacimon Crew - GitHub Setup"
echo "======================================"
echo ""

# Check if we're in the right directory
if [ ! -f "web_app.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git initialized"
else
    echo "✅ Git repository already exists"
fi

echo ""
echo "Please provide your GitHub repository details:"
echo ""
read -p "GitHub username: " github_user
read -p "Repository name (default: beat-ampacimon-crew): " repo_name
repo_name=${repo_name:-beat-ampacimon-crew}

echo ""
echo "Configuration:"
echo "  User: $github_user"
echo "  Repo: $repo_name"
echo ""
read -p "Is this correct? (y/n): " confirm

if [ "$confirm" != "y" ]; then
    echo "Aborted."
    exit 0
fi

# Rename README for GitHub
if [ -f "README_GITHUB.md" ]; then
    echo ""
    echo "📝 Setting up README.md for GitHub..."
    if [ -f "README.md" ]; then
        mv README.md README_LOCAL.md
        echo "   Renamed existing README.md to README_LOCAL.md"
    fi
    mv README_GITHUB.md README.md
    echo "✅ README.md ready for GitHub"
fi

# Add all files
echo ""
echo "📂 Adding files to git..."
git add .

# Check if there's anything to commit
if git diff --staged --quiet; then
    echo "⚠️  No changes to commit (everything already committed)"
else
    echo "💾 Creating initial commit..."
    git commit -m "Initial commit - Beat Ampacimon Crew NBA Fantasy App

- Flask web application with Ampacimon branding
- Docker and docker-compose configuration
- Automated daily NBA data updates
- SQLite database with player statistics
- Real-time lineup optimization
- Ready for Portainer deployment"
    echo "✅ Committed"
fi

# Create main branch if needed
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo ""
    echo "🌿 Creating main branch..."
    git branch -M main
fi

# Add remote if not exists
remote_url="https://github.com/$github_user/$repo_name.git"
if git remote get-url origin &>/dev/null; then
    current_remote=$(git remote get-url origin)
    echo ""
    echo "⚠️  Remote 'origin' already exists: $current_remote"
    read -p "Do you want to update it to $remote_url? (y/n): " update_remote
    if [ "$update_remote" = "y" ]; then
        git remote set-url origin "$remote_url"
        echo "✅ Remote updated"
    fi
else
    echo ""
    echo "🔗 Adding remote..."
    git remote add origin "$remote_url"
    echo "✅ Remote added"
fi

echo ""
echo "📤 Ready to push!"
echo ""
echo "⚠️  Make sure you have created the repository on GitHub:"
echo "    1. Go to https://github.com/new"
echo "    2. Repository name: $repo_name"
echo "    3. Make it Public or Private"
echo "    4. Do NOT initialize with README, .gitignore, or license"
echo "    5. Click 'Create repository'"
echo ""
read -p "Have you created the GitHub repository? (y/n): " repo_created

if [ "$repo_created" != "y" ]; then
    echo ""
    echo "⏸️  Stopping here. Please create the repository on GitHub first."
    echo ""
    echo "When ready, push with:"
    echo "  git push -u origin main"
    exit 0
fi

echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin main

echo ""
echo "✅ Success! Repository pushed to GitHub!"
echo ""
echo "🌐 Repository URL: https://github.com/$github_user/$repo_name"
echo ""
echo "Next steps:"
echo "=========="
echo "1. Open Portainer: http://nas.local:9000/"
echo "2. Go to Stacks → Add stack"
echo "3. Name: beat-ampacimon-crew"
echo "4. Build method: Repository"
echo "5. Repository URL: $remote_url"
echo "6. Repository reference: refs/heads/main"
echo "7. Compose path: docker-compose.yml"
echo "8. Enable 'Automatic updates' (optional)"
echo "9. Deploy the stack!"
echo ""
echo "Your app will be available at: http://nas.local:5000"
echo ""
echo "📖 Full deployment guide: GITHUB_DEPLOY.md"
