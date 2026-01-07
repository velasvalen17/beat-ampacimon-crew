# Deploy Beat Ampacimon Crew to Portainer

## Prerequisites
- Portainer running at http://nas.local:9000/
- Docker installed on your NAS

## Deployment Steps

### Option 1: Deploy via Portainer UI (Recommended)

1. **Build the Docker image locally first:**
   ```bash
   cd /home/velasvalen17/myproject
   docker build -t beat-ampacimon-crew:latest .
   ```

2. **Save and transfer the image to your NAS:**
   ```bash
   # Save the image to a tar file
   docker save -o beat-ampacimon-crew.tar beat-ampacimon-crew:latest
   
   # Transfer to NAS (adjust the command based on your NAS setup)
   scp beat-ampacimon-crew.tar user@nas.local:/path/to/destination/
   ```

3. **Load the image on your NAS:**
   ```bash
   # SSH into your NAS
   ssh user@nas.local
   
   # Load the image
   docker load -i /path/to/destination/beat-ampacimon-crew.tar
   ```

4. **Deploy via Portainer UI:**
   - Open http://nas.local:9000/ in your browser
   - Log in to Portainer
   - Go to **Stacks** → **Add stack**
   - Name it: `beat-ampacimon-crew`
   - Choose **Web editor** tab
   - Copy and paste the contents of `docker-compose.portainer.yml`
   - Click **Deploy the stack**

### Option 2: Deploy via Git Repository

1. **In Portainer UI:**
   - Go to **Stacks** → **Add stack**
   - Name it: `beat-ampacimon-crew`
   - Choose **Repository** tab
   - Enter your repository URL (if using Git)
   - Set Compose path: `docker-compose.portainer.yml`
   - Click **Deploy the stack**

### Option 3: Build on NAS directly

1. **Transfer project files to NAS:**
   ```bash
   # From your development machine
   rsync -av --exclude='venv' --exclude='__pycache__' \
     /home/velasvalen17/myproject/ user@nas.local:/path/to/project/
   ```

2. **In Portainer UI:**
   - Go to **Stacks** → **Add stack**
   - Name it: `beat-ampacimon-crew`
   - Choose **Web editor** tab
   - Paste the content but change the `image:` line to `build: .`
   - Set the build context path to your project folder on NAS
   - Click **Deploy the stack**

## After Deployment

### Access the Application
Once deployed, the application will be available at:
- **Internal LAN:** http://nas.local:5000
- **Direct IP:** http://[NAS-IP]:5000

### Verify Deployment
1. In Portainer, go to **Containers**
2. Find `beat-ampacimon-crew`
3. Check status (should be "running" with green indicator)
4. Click on the container to view logs
5. Look for: "Starting Flask web application..." and successful gunicorn startup

### Monitor Logs
- In Portainer: Container → **Logs** tab (real-time)
- Or via command line:
  ```bash
  docker logs -f beat-ampacimon-crew
  ```

### Check Database Initialization
The first startup will:
1. Create the database
2. Populate teams
3. Fetch last 7 days of game data
4. This may take 2-5 minutes

Watch logs for: "Initial data populated!" and "Starting Flask web application..."

### Access the Database
If you need to inspect the database:
```bash
docker exec -it beat-ampacimon-crew sqlite3 /app/data/nba_fantasy.db
```

## Automated Updates
The container runs a cron job that automatically:
- Updates player statistics daily at 6 AM ET
- Fetches new game schedules
- Keeps salary data current

Check cron logs:
```bash
docker exec beat-ampacimon-crew cat /var/log/cron.log
```

## Troubleshooting

### Container won't start
- Check logs in Portainer
- Verify port 5000 is not already in use on NAS
- Ensure volumes are properly mounted

### Can't access web interface
- Verify container is running
- Check firewall rules on NAS
- Try accessing via IP instead of hostname
- Verify port mapping: `docker ps` should show `0.0.0.0:5000->5000/tcp`

### Database is empty
- Wait for initial data population (2-5 minutes on first start)
- Check logs for any API errors
- Database initializes automatically on first run

### Need to restart
In Portainer:
- Go to **Containers**
- Select `beat-ampacimon-crew`
- Click **Restart**

Or via CLI:
```bash
docker restart beat-ampacimon-crew
```

## Updating the Application

When you make changes:

1. **Rebuild the image:**
   ```bash
   cd /home/velasvalen17/myproject
   docker build -t beat-ampacimon-crew:latest .
   ```

2. **Transfer to NAS** (same as deployment)

3. **In Portainer:**
   - Go to **Stacks** → `beat-ampacimon-crew`
   - Click **Pull and redeploy**
   - Or delete the stack and redeploy with new image

## Port Configuration

To change the external port (e.g., to 8080):
- Edit the `docker-compose.portainer.yml` file
- Change `"5000:5000"` to `"8080:5000"`
- Redeploy the stack
- Access at http://nas.local:8080

## Data Persistence

All data is stored in Docker volumes:
- `nba-fantasy-data`: Database with all NBA statistics
- `nba-fantasy-logs`: Application and access logs

These volumes persist even if you delete the container/stack.

To backup:
```bash
docker run --rm -v nba-fantasy-data:/data -v $(pwd):/backup \
  alpine tar czf /backup/nba-fantasy-backup.tar.gz -C /data .
```

## Security Notes

- The application runs on HTTP (not HTTPS)
- No authentication is configured
- Suitable for internal LAN use only
- For external access, consider adding:
  - Reverse proxy with HTTPS (nginx, Traefik)
  - Authentication layer
  - Firewall rules
