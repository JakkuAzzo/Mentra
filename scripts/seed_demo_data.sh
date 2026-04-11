#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export DATABASE_URL="${DATABASE_URL:-sqlite:///./backend/mentra.db}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export JWT_SECRET_KEY="${JWT_SECRET_KEY:-dev-secret-key}"

python backend/seed.py
