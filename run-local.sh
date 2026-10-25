#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -d "$ROOT/.venv" ]]; then python3 -m venv "$ROOT/.venv"; fi
source "$ROOT/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$ROOT/services/api/requirements.txt"
if [[ ! -d "$ROOT/apps/web/node_modules" ]]; then (cd "$ROOT/apps/web" && npm install); fi
mkdir -p "$ROOT/services/api/data"
echo "Starting API at http://localhost:8000 and web app at http://localhost:3000"
(cd "$ROOT/services/api" && uvicorn app.main:app --reload --app-dir .) &
API_PID=$!
trap 'kill "$API_PID" 2>/dev/null || true' EXIT
cd "$ROOT/apps/web"
npm run dev
