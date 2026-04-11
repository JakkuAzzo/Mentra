#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

API_BASE="${API_BASE:-http://127.0.0.1:8002}"
USER_ID="${USER_ID:-1}"
TOPIC_ID="${TOPIC_ID:-2}"

mkdir -p docs/artifacts

curl -s "$API_BASE/api/recommendations/due-for-review/$USER_ID" | python -m json.tool > docs/artifacts/due-for-review.json
curl -s "$API_BASE/api/recommendations/mastery-date/$USER_ID/$TOPIC_ID" | python -m json.tool > docs/artifacts/mastery-date.json
curl -s "$API_BASE/api/recommendations/session-stats/$USER_ID?days=7" | python -m json.tool > docs/artifacts/session-stats.json

echo "Saved:"
echo "  docs/artifacts/due-for-review.json"
echo "  docs/artifacts/mastery-date.json"
echo "  docs/artifacts/session-stats.json"
