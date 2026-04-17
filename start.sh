#!/usr/bin/env bash

# Allow invoking with `sh ./start.sh` by re-execing under bash.
if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

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

run_with_timeout() {
  local timeout_seconds="$1"
  shift

  "$@" &
  local pid=$!
  local elapsed=0

  while kill -0 "$pid" >/dev/null 2>&1; do
    if (( elapsed >= timeout_seconds )); then
      kill "$pid" >/dev/null 2>&1 || true
      wait "$pid" >/dev/null 2>&1 || true
      return 124
    fi
    sleep 1
    ((elapsed++))
  done

  wait "$pid"
}

if ! run_with_timeout 15 docker info >/dev/null 2>&1; then
  if [[ $? -eq 124 ]]; then
    echo "Error: Docker daemon check timed out. Restart Docker Desktop and try again."
    exit 1
  fi
  echo "Error: Docker daemon is not running. Start Docker Desktop and try again."
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
compose_up_with_fallback() {
  local log_file
  local status
  log_file="$(mktemp)"

  # First attempt: default Docker Compose behavior.
  if run_with_timeout 900 "${COMPOSE_CMD[@]}" up -d 2>&1 | tee "$log_file"; then
    rm -f "$log_file"
    return 0
  fi

  status=$?

  if [[ $status -eq 124 ]]; then
    echo "[mentra] Docker Compose startup timed out. Please restart Docker Desktop and rerun."
    rm -f "$log_file"
    return 1
  fi

  if grep -qi "input/output error" "$log_file"; then
    echo "[mentra] BuildKit reported an input/output error. Retrying with legacy builder..."
    if run_with_timeout 900 env COMPOSE_DOCKER_CLI_BUILD=0 DOCKER_BUILDKIT=0 "${COMPOSE_CMD[@]}" up -d; then
      rm -f "$log_file"
      return 0
    fi
  fi

  rm -f "$log_file"
  return 1
}

compose_up_with_fallback

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
