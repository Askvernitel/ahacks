#!/usr/bin/env bash
# Serve the BeeBuzz Monitor locally and expose it publicly via ngrok.
#
# Usage:   ./serve.sh [port]
# Default port: 8000
#
# Requirements:
#   - python3 (for the static file server)
#   - ngrok    (https://ngrok.com/download, run `ngrok config add-authtoken <token>` once)
#
# Note: Web Serial (Connect Arduino) only works over https or localhost.
#       The ngrok https URL satisfies this, so the live tunnel can connect to
#       hardware on the machine running this script. Demo mode works anywhere.

set -e
PORT="${1:-8000}"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok not found. Install it from https://ngrok.com/download" >&2
  exit 1
fi

echo "Serving $DIR on http://localhost:$PORT"
python3 -m http.server "$PORT" --directory "$DIR" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT

sleep 1
echo "Opening public ngrok tunnel…"
ngrok http "$PORT"
