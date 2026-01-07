# 🚀 Portainer Deployment - Working Configuration

## ✅ Repository Now Has Master Branch

Your repository now has both `main` and `master` branches. Portainer can deploy from either.

## Method 1: Repository Deployment (Direct from GitHub) ⭐

### In Portainer:

1. **Open:** http://nas.local:9000/
2. **Stacks** → **Add stack**
3. **Name:** `beat-ampacimon-crew`
4. **Build method:** Select **"Repository"** tab

5. **Repository Configuration:**
   ```
   Repository URL: https://github.com/velasvalen17/beat-ampacimon-crew
   Repository reference: refs/heads/master
   Compose path: docker-compose.yml
   ```
   
6. **Leave authentication empty** (public repo)

7. **Optional - Enable automatic updates:**
   - ✅ Check "Enable automatic updates"
   - Mechanism: Polling
   - Fetch interval: 5 minutes
   
8. **Click "Deploy the stack"**

9. **Wait 3-5 minutes** for the build

### Important Notes:
- Use `refs/heads/master` (NOT `master` or `refs/heads/main`)
- Leave "Relative path to compose file" empty
- Compose path should be just `docker-compose.yml`

## Method 2: Web Editor with Repository Build Context

If Method 1 doesn't work, try this:

1. **Stacks** → **Add stack**
2. **Name:** `beat-ampacimon-crew`
3. **Web editor** tab
4. **Paste this:**

```yaml
version: '3.8'

services:
  nba-fantasy:
    build:
      context: https://github.com/velasvalen17/beat-ampacimon-crew.git#master
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

Note the `#master` at the end of the context URL - this specifies the branch.

## Method 3: Set Master as Default on GitHub

To make `master` the default branch (helps with Portainer):

1. Go to: https://github.com/velasvalen17/beat-ampacimon-crew/settings/branches
2. Click the switch icon next to `master`
3. Confirm "Change default branch to master"
4. Now Portainer will use master by default

## Verify Repository Access

Test that Portainer can access your repo:

```bash
# From your NAS or any machine
git ls-remote https://github.com/velasvalen17/beat-ampacimon-crew.git
```

You should see both branches:
```
...refs/heads/main
...refs/heads/master
```

## Troubleshooting

### Still getting "repository does not contain ref master"?

Try Method 2 with the explicit `#master` in the build context.

### Docker build fails?

Check Portainer logs in the build output for specific errors.

### Want to sync main and master?

```bash
# On your dev machine
git checkout master
git merge main
git push origin master

git checkout main
git merge master
git push origin main
```

## After Successful Deployment

1. **Check logs:** Portainer → Stacks → beat-ampacimon-crew → Logs
2. **Access app:** http://nas.local:5000
3. **First startup:** Takes 2-5 minutes to initialize database

## Updating the App

After making changes:

```bash
# Commit and push to both branches
git checkout main
git add .
git commit -m "Your changes"
git push

git checkout master
git merge main
git push
```

If you enabled automatic updates in Portainer, it will redeploy within 5 minutes!

---

**Try Method 1 first!** It's the cleanest GitHub integration. ✨
