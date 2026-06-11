#!/bin/bash
# Usage: health_check.sh [local|central|jetson-a|jetson-b]
set -euo pipefail

TARGET="${1:-local}"
MAX=18    # 18 × 5s = 90s max wait
DELAY=5

case "$TARGET" in
  local)     URL="http://localhost:8000/health" ;;
  jetson-a)  URL="http://jetson-a:8000/health" ;;
  jetson-b)  URL="http://jetson-b:8000/health" ;;
  central)   URL="http://localhost:8001/health" ;;
  *)         echo "Unknown target: $TARGET"; exit 1 ;;
esac

for i in $(seq 1 $MAX); do
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$URL" 2>/dev/null || echo "000")
  if [[ "$HTTP" == "200" ]]; then
    echo "✅ $TARGET healthy (attempt $i, ${HTTP})"
    exit 0
  fi
  echo "  [$i/$MAX] $TARGET returned $HTTP — waiting ${DELAY}s"
  sleep "$DELAY"
done

echo "❌ $TARGET did not become healthy after $((MAX * DELAY))s"
exit 1
