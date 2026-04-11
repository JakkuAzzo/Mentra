#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MODE="${1:-sqlite}"
PORT="${PORT:-8002}"

if [[ "$MODE" == "postgres" ]]; then
  export DATABASE_URL="${DATABASE_URL:-postgresql://mentra_user:mentra_password@localhost:5432/mentra_db}"
  export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
else
  export DATABASE_URL="${DATABASE_URL:-sqlite:///./backend/mentra.db}"
  export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
fi

export JWT_SECRET_KEY="${JWT_SECRET_KEY:-dev-secret-key}"

echo "[mentra] mode=$MODE port=$PORT"
echo "[mentra] DATABASE_URL=$DATABASE_URL"

echo "[mentra] starting backend..."
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port "$PORT" --reload
