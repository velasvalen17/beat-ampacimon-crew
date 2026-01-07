# 🔧 Portainer Deployment - Troubleshooting

## Issue: "failed to read dockerfile: no such file or directory"

This error means Portainer couldn't access the Dockerfile from your Git repository. Here are the solutions:

## Solution 1: Verify Repository Settings in Portainer

Make sure you entered **exactly**:

### Repository Configuration:
- **Repository URL:** `https://github.com/velasvalen17/beat-ampacimon-crew.git`
- **Repository reference:** `refs/heads/main` (not just "main")
- **Compose path:** `docker-compose.yml` (or `stack.yml`)
- **Authentication:** None (if public repo)

### Common Mistakes:
- ❌ Missing `.git` at the end of URL
- ❌ Using `main` instead of `refs/heads/main`
- ❌ Typo in compose file name
- ❌ Repository is private but no credentials provided

## Solution 2: Make Repository Public

If your repo is private:

1. Go to https://github.com/velasvalen17/beat-ampacimon-crew/settings
2. Scroll to "Danger Zone"
3. Click "Change visibility" → "Make public"
4. Try deploying again in Portainer

## Solution 3: Add GitHub Authentication

If you want to keep it private:

1. **Generate a Personal Access Token:**
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Give it a name: "Portainer Access"
   - Select scope: `repo` (full control of private repositories)
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

2. **In Portainer Stack Configuration:**
   - Check "Authentication"
   - Username: `velasvalen17`
   - Password: `<paste your token here>`

## Solution 4: Use Web Editor Instead

This is the most reliable method:

1. **In Portainer:**
   - Stacks → Add stack
   - Name: `beat-ampacimon-crew`
   - Select **"Web editor"** tab (not Repository)

2. **Copy the entire content below:**

```yaml
version: '3.8'

services:
  nba-fantasy:
    build:
      context: https://github.com/velasvalen17/beat-ampacimon-crew.git
      dockerfile: Dockerfile
    container_name: beat-ampacimon-crew
    ports:
      - "5000:5000"
    volumes:
      - nba-fantasy-data:/app/data
      - nba-fantasy-logs:/var/log/nba-fantasy
    environment:
      - TZ=Europe/Madrid
      - SEASON_YEAR=2025-26
      - DB_PATH=/app/data/nba_fantasy.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  nba-fantasy-data:
    driver: local
  nba-fantasy-logs:
    driver: local
```

3. **Click "Deploy the stack"**

4. **Wait 3-5 minutes** for the build to complete

## Solution 5: Build on NAS, Use Image

Alternative approach - build the image manually on your NAS:

### Step 1: Clone on NAS
```bash
# SSH to your NAS
ssh user@nas.local

# Clone the repository
cd /tmp
git clone https://github.com/velasvalen17/beat-ampacimon-crew.git
cd beat-ampacimon-crew

# Build the image
docker build -t beat-ampacimon-crew:latest .
```

### Step 2: Deploy in Portainer with Web Editor
Use this compose file (replaces `build:` with `image:`):

```yaml
version: '3.8'

services:
  nba-fantasy:
    image: beat-ampacimon-crew:latest
    container_name: beat-ampacimon-crew
    ports:
      - "5000:5000"
    volumes:
      - nba-fantasy-data:/app/data
      - nba-fantasy-logs:/var/log/nba-fantasy
    environment:
      - TZ=Europe/Madrid
      - SEASON_YEAR=2025-26
      - DB_PATH=/app/data/nba_fantasy.db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

volumes:
  nba-fantasy-data:
    driver: local
  nba-fantasy-logs:
    driver: local
```

## Recommended: Use Solution 4 (Web Editor with build context)

This is the easiest and most reliable for your setup.

## After Successful Deployment

Check the logs:
1. In Portainer → Stacks → beat-ampacimon-crew
2. Click on the container name
3. Go to "Logs" tab
4. You should see:
   - "Database initialized."
   - "Starting Flask web application..."
   - "Booting worker with pid: ..."

## Verify It's Working

Open http://nas.local:5000 in your browser

You should see the "Beat Ampacimon Crew" interface.

## Still Having Issues?

### Check Docker Buildkit
Your NAS might need Docker Buildkit enabled. On your NAS:

```bash
# Check Docker version
docker version

# If version < 23.0, you might need to enable buildkit
export DOCKER_BUILDKIT=1
```

### Check Repository Access
```bash
# From any machine with git
git clone https://github.com/velasvalen17/beat-ampacimon-crew.git
cd beat-ampacimon-crew
ls -la Dockerfile
```

If this works, your repo is fine.

### Portainer Version
Make sure you're running Portainer CE 2.19+ or BE 2.19+

Check in Portainer → Settings → About

---

**Most users succeed with Solution 4 (Web Editor). Try that first!** ✅
