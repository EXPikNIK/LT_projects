#!/usr/bin/env bash
set -euo pipefail

# TODO: change SSH target
SSH_TARGET="ubuntu@1.2.3.4"
REMOTE_DIR="/opt/rest_stub"
PORT="8000"

# Local path (this script's directory)
LOCAL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 1) Upload project
rsync -az --delete \
  --exclude ".venv" \
  --exclude "__pycache__" \
  --exclude ".pytest_cache" \
  "$LOCAL_DIR/" "$SSH_TARGET:$REMOTE_DIR/"

# 2) Prepare venv and install deps
ssh "$SSH_TARGET" "bash -s" <<'REMOTE'
set -euo pipefail
cd /opt/rest_stub

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required on the server" >&2
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3) Run in background (nohup)
# Kill existing instance if any
pkill -f "uvicorn app:app" || true

nohup .venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 > /opt/rest_stub/server.log 2>&1 &

echo "Started: http://0.0.0.0:8000"
REMOTE

echo "Deploy finished. Remote log: $REMOTE_DIR/server.log"
