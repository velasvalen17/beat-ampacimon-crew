#!/usr/bin/env bash
set -euo pipefail
echo "Starting DB discovery and dump helper"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker not found. If this is not containerized, run sqlite/mysql/pg commands manually."
  exit 1
fi

# Try to auto-detect the container exposing port 5000
CONTAINER=$(docker ps --format '{{.ID}} {{.Names}} {{.Ports}}' | grep -E '0.0.0.0:5000|:5000->|:5000/tcp' | awk '{print $1}' | head -n1 || true)
if [ -z "$CONTAINER" ]; then
  CONTAINER=$(docker ps --format '{{.ID}} {{.Names}}' | grep -i ampacimon || true)
  CONTAINER=$(echo "$CONTAINER" | awk '{print $1}' | head -n1 || true)
fi

if [ -z "$CONTAINER" ]; then
  echo "Could not auto-detect container. Run 'docker ps' and re-run with CONTAINER=<id> environment variable."
  exit 2
fi

echo "Using container: $CONTAINER"
echo "Mounted volumes (host:container):"
docker inspect --format '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}' "$CONTAINER" || true

# Look for sqlite files inside container
echo "Searching for sqlite/db files inside container (may take a few seconds)..."
docker exec "$CONTAINER" bash -lc "find / -type f \( -iname '*.db' -o -iname '*.sqlite' -o -iname '*.sqlite3' \) 2>/dev/null" > /tmp/remote_db_paths.txt || true

if [ -s /tmp/remote_db_paths.txt ]; then
  echo "Found sqlite DB paths:"
  cat /tmp/remote_db_paths.txt
  while read -r P; do
    BASENAME=$(basename "$P")
    DEST="/tmp/${BASENAME}"
    echo "Copying $P -> $DEST (on host)"
    docker cp "${CONTAINER}:${P}" "$DEST" || echo "docker cp failed for $P"
    echo "File info:"
    ls -lh "$DEST"
    if command -v sqlite3 >/dev/null 2>&1; then
      echo "Running PRAGMA integrity_check on $DEST"
      sqlite3 "$DEST" "PRAGMA integrity_check;" || echo "integrity_check returned non-OK"
      echo "Tables in DB:"
      sqlite3 "$DEST" ".tables"
    else
      echo "sqlite3 not available on host to run checks. You can copy $DEST and run 'sqlite3 <file> \"PRAGMA integrity_check;\"' locally."
    fi
  done < /tmp/remote_db_paths.txt
  echo "Done with sqlite checks. Dump files are in /tmp on the host."
  exit 0
fi

echo "No sqlite files found. Checking for Postgres/MySQL environment variables in container..."
docker exec "$CONTAINER" env | egrep -i 'POSTGRES|PGUSER|PGPASSWORD|POSTGRES_USER|POSTGRES_DB|MYSQL|MYSQL_ROOT_PASSWORD' || true

# Try to run pg_dump inside container if present
if docker exec "$CONTAINER" bash -lc "command -v pg_dump >/dev/null 2>&1" ; then
  echo "pg_dump found inside container. Attempting logical dump to /tmp/db_dump.sql"
  docker exec "$CONTAINER" bash -lc "pg_dump -U \"\${POSTGRES_USER:-postgres}\" -d \"\${POSTGRES_DB:-postgres}\" -F p -f /tmp/db_dump.sql" || echo "pg_dump may have failed; check credentials"
  docker cp "${CONTAINER}:/tmp/db_dump.sql" /tmp/db_dump.sql || echo "Failed to copy pg dump"
  ls -lh /tmp/db_dump.sql
  echo "pg_dump copied to /tmp/db_dump.sql"
  exit 0
fi

# Try mysqldump
if docker exec "$CONTAINER" bash -lc "command -v mysqldump >/dev/null 2>&1" ; then
  echo "mysqldump found. Attempting dump to /tmp/db_dump.sql"
  docker exec "$CONTAINER" bash -lc "mysqldump --all-databases --single-transaction -u \"\${MYSQL_USER:-root}\" -p\"\${MYSQL_ROOT_PASSWORD:-}\" > /tmp/db_dump.sql" || echo "mysqldump may have failed; check credentials"
  docker cp "${CONTAINER}:/tmp/db_dump.sql" /tmp/db_dump.sql || echo "Failed to copy mysql dump"
  ls -lh /tmp/db_dump.sql
  echo "mysqldump copied to /tmp/db_dump.sql"
  exit 0
fi

echo "Automatic dump not created. Next steps:"
echo " - If DB is SQLite, run the sqlite search manually inside the container and docker cp the file to host."
echo " - If DB is Postgres/MySQL but pg_dump/mysqldump not present or require creds, obtain DB credentials or run dumps from inside the DB host."
echo "Useful manual commands:"
echo "docker ps"
echo "docker exec -it <container> bash"
echo "  find / -type f -iname '*.db' -o -iname '*.sqlite' -o -iname '*.sqlite3'"
echo "  sqlite3 /path/to/db 'PRAGMA integrity_check;' '.tables'"
echo "docker cp <container>:/path/to/db /tmp/"
echo "scp user@192.168.215.100:/tmp/<dumpfile> ./"
exit 3
