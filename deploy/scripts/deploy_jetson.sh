#!/bin/bash
set -euo pipefail

COMMIT="${COMMIT:-main}"
APP_DIR="/opt/ha-meem"
COMPOSE="docker compose -f $APP_DIR/deploy/jetson/docker-compose.yml --env-file $APP_DIR/.env"

# ── Working hours guard ──────────────────────────────────────────────
# Prevent deployments during active warehouse hours unless FORCE=1 is set
HOUR=$(date +%H)
if [[ "$HOUR" -ge 6 && "$HOUR" -le 21 && "${FORCE:-0}" != "1" ]]; then
  echo "BLOCKED: Deploy during working hours (06:00–21:00). Use FORCE=1 to override."
  exit 1
fi

echo "═══════════════════════════════════════════════"
echo " Deploy: $COMMIT  |  Host: $(hostname)  |  $(date)"
echo "═══════════════════════════════════════════════"

# ── Record the current state BEFORE touching anything ───────────────
cd "$APP_DIR"
PREV_COMMIT=$(git rev-parse HEAD)   # what's running right now
PREV_IMAGE="ha-meem-jetson:${PREV_COMMIT::8}"

echo "[1/6] Preserving current image as rollback snapshot: $PREV_IMAGE"
# Tag current running image with its commit SHA so we can restore it instantly
docker tag ha-meem-jetson:latest "$PREV_IMAGE" 2>/dev/null || true

# ── Pull new code ────────────────────────────────────────────────────
echo "[2/6] Fetching commit $COMMIT"
git fetch origin
git checkout "$COMMIT"
NEW_COMMIT=$(git rev-parse HEAD)

# ── Build new image ──────────────────────────────────────────────────
echo "[3/6] Building new image (native ARM64)"
$COMPOSE build --pull pipeline api
docker tag ha-meem-jetson:latest "ha-meem-jetson:${NEW_COMMIT::8}"

# ── Migrate DB (Skipped or commented out since API is file-based) ────
echo "[4/6] Running DB migrations"
# $COMPOSE run --rm --no-deps api alembic upgrade head
echo "  → DB migrations skipped (FastAPI api_server currently uses JSONL logs)"

# ── Restart services ─────────────────────────────────────────────────
echo "[5/6] Restarting services (API first, then pipeline)"
$COMPOSE up -d --no-deps api
sleep 5
$COMPOSE up -d --no-deps pipeline   # 30s stop_grace_period drains active tracks

# ── Health check with auto-rollback ──────────────────────────────────
echo "[6/6] Health check (90s window)"
MAX=18; DELAY=5
for i in $(seq 1 $MAX); do
  # Query the API server's health check endpoint
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
  if [[ "$HTTP" == "200" ]]; then
    echo "✅ Healthy after $((i * DELAY))s — deploy complete"
    # Clean up old images (keep last 3 only)
    docker images ha-meem-jetson --format "{{.Tag}}" \
      | grep -v latest | sort -r | tail -n +4 \
      | xargs -I{} docker rmi "ha-meem-jetson:{}" 2>/dev/null || true
    exit 0
  fi
  echo "  [$i/$MAX] HTTP $HTTP — waiting ${DELAY}s"
  sleep "$DELAY"
done

# ── AUTOMATIC ROLLBACK ───────────────────────────────────────────────
echo ""
echo "❌ Health check failed — automatically reverting to $PREV_IMAGE"

# Restore previous code
git checkout "$PREV_COMMIT"

# Restore previous image — NO REBUILD NEEDED, it's already cached
docker tag "$PREV_IMAGE" ha-meem-jetson:latest
$COMPOSE up -d --no-deps api
sleep 5
$COMPOSE up -d --no-deps pipeline

# Verify rollback is healthy
sleep 15
HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null || echo "000")
if [[ "$HTTP" == "200" ]]; then
  echo "⚠️  Rolled back to ${PREV_COMMIT::8} — system restored and healthy"
  exit 2   # exit 2 = deploy failed but rollback succeeded (distinct from exit 1)
else
  echo "🚨 CRITICAL: Rollback also failed. Manual intervention required."
  exit 1
fi
