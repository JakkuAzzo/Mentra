#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

SEED_DEMO_DATA=false
TAIL_LOGS=false

for arg in "$@"; do
  case "$arg" in
    --seed)
      SEED_DEMO_DATA=true
      ;;
    --logs)
      TAIL_LOGS=true
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./start.sh [--seed] [--logs]

Starts all Mentra services with Docker Compose.

Options:
  --seed   Seed demo data after services are healthy
  --logs   Tail compose logs after startup
  -h       Show this help message
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Run ./start.sh --help for usage."
      exit 1
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker is required but not installed."
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Error: docker compose or docker-compose is required but not installed."
  exit 1
fi

wait_for_http() {
  local name="$1"
  local url="$2"
  local retries="${3:-60}"
  local delay="${4:-2}"

  echo "[mentra] waiting for ${name} at ${url}"
  for ((i=1; i<=retries; i++)); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[mentra] ${name} is ready"
      return 0
    fi
    sleep "$delay"
  done

  echo "[mentra] warning: ${name} did not become ready in time"
  return 1
}

echo "[mentra] starting services with Docker Compose..."
"${COMPOSE_CMD[@]}" up -d

# Backend and frontend are the minimum required for app usage.
wait_for_http "backend" "http://localhost:8000/docs" || true
wait_for_http "frontend" "http://localhost:3000" || true

if [[ "$SEED_DEMO_DATA" == "true" ]]; then
  echo "[mentra] seeding demo data..."
  "${COMPOSE_CMD[@]}" exec -T backend python seed.py
fi

echo ""
echo "[mentra] startup complete"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  ${COMPOSE_CMD[*]} ps"
echo "  ${COMPOSE_CMD[*]} logs -f backend"
echo "  ${COMPOSE_CMD[*]} down"

if [[ "$TAIL_LOGS" == "true" ]]; then
  echo ""
  echo "[mentra] tailing logs (Ctrl+C to stop)"
  "${COMPOSE_CMD[@]}" logs -f
fi
