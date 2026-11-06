#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="/opt/adex"
CONTAINER_NAME="adex"
IMAGE_NAME="adex-test:latest"
ROLLBACK_IMAGE="adex-rollback:previous"
LOCK_FILE="/var/lock/adex-deploy.lock"
HEALTH_URL="http://127.0.0.1:10000/health"
BACKUP_DIR="$APP_DIR/backups"
BACKUP_FILE="$BACKUP_DIR/neon-predeploy-$(date -u +%Y%m%dT%H%M%SZ).dump"

exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "Another ADEX deployment is already running."
  exit 1
fi

if [[ ! -f "$APP_DIR/.env" ]]; then
  echo "Missing $APP_DIR/.env; refusing to deploy."
  exit 1
fi

if ! docker inspect "$CONTAINER_NAME" >/dev/null 2>&1; then
  echo "Current container '$CONTAINER_NAME' was not found; refusing first-time deployment."
  exit 1
fi

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
echo "Creating a pre-deployment Neon PostgreSQL backup..."
docker run --rm \
  --env-file "$APP_DIR/.env" \
  -e BACKUP_FILE="/backups/$(basename "$BACKUP_FILE")" \
  -v "$BACKUP_DIR:/backups" \
  postgres:18-alpine \
  sh -ec 'test -n "$DATABASE_URL"; pg_dump "$DATABASE_URL" --format=custom --no-owner --no-acl -f "$BACKUP_FILE"; pg_restore --list "$BACKUP_FILE" >/dev/null'
chmod 600 "$BACKUP_FILE"
test -s "$BACKUP_FILE"
echo "Database backup created: $BACKUP_FILE"

OLD_IMAGE_ID="$(docker inspect --format '{{.Image}}' "$CONTAINER_NAME")"
docker image tag "$OLD_IMAGE_ID" "$ROLLBACK_IMAGE"

echo "Pulling latest main branch as opc..."
sudo -u opc env HOME=/home/opc GIT_SSH_COMMAND="ssh -i /home/opc/.ssh/adex_github -o IdentitiesOnly=yes -o UserKnownHostsFile=/home/opc/.ssh/known_hosts" \
  git -C "$APP_DIR" pull --ff-only origin main

echo "Building new ARM64 image..."
docker build --platform linux/arm64 -t "$IMAGE_NAME" "$APP_DIR"

echo "Replacing application container..."
docker rm -f "$CONTAINER_NAME" >/dev/null

start_container() {
  local image="$1"
  docker run -d \
    --name "$CONTAINER_NAME" \
    --restart unless-stopped \
    --env-file "$APP_DIR/.env" \
    -p 127.0.0.1:10000:10000 \
    "$image"
}

if ! start_container "$IMAGE_NAME"; then
  echo "New container failed to start; restoring previous image."
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  start_container "$ROLLBACK_IMAGE"
  exit 1
fi

echo "Checking application health..."
healthy=0
for attempt in $(seq 1 40); do
  if curl --fail --silent --show-error "$HEALTH_URL" >/dev/null 2>&1; then
    healthy=1
    break
  fi
  if ! docker inspect "$CONTAINER_NAME" >/dev/null 2>&1 || [[ "$(docker inspect --format '{{.State.Running}}' "$CONTAINER_NAME")" != "true" ]]; then
    break
  fi
  sleep 3
done

if [[ "$healthy" != "1" ]]; then
  echo "Health check failed. Recent container logs:"
  docker logs --tail 100 "$CONTAINER_NAME" || true
  echo "Rolling back to previous image..."
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true
  start_container "$ROLLBACK_IMAGE"
  for attempt in $(seq 1 20); do
    if curl --fail --silent "$HEALTH_URL" >/dev/null 2>&1; then
      echo "Previous application image restored and healthy."
      break
    fi
    sleep 3
  done
  exit 1
fi

echo "Deployment successful."
find "$BACKUP_DIR" -type f -name 'neon-predeploy-*.dump' -mtime +7 -delete
docker image prune -f >/dev/null
