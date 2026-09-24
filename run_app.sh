#!/usr/bin/env bash
# Starts LED Studio on Linux: backend (FastAPI) + frontend (Vite) and opens the browser.
# First run installs the Python venv and npm packages. Ctrl+C stops both servers.
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
backend="$root/backend"
frontend="$root/frontend"
python="$backend/.venv/bin/python"

for tool in python3 npm; do
    command -v "$tool" >/dev/null || { echo "'$tool' is not installed. Install Python 3.13+ and Node.js 24+ first." >&2; exit 1; }
done

# A previous run that did not shut down cleanly leaves a process holding a port; evict it.
free_port() {
    local pids
    pids="$(lsof -t -iTCP:"$1" -sTCP:LISTEN 2>/dev/null || fuser -n tcp "$1" 2>/dev/null || true)"
    if [ -n "$pids" ]; then
        echo "Port $1 is held by process(es) $pids - stopping them."
        kill -9 $pids 2>/dev/null || true
    fi
}
free_port 8765
free_port 5173

if [ ! -x "$python" ]; then
    echo "Creating Python environment..."
    python3 -m venv "$backend/.venv"
    "$python" -m pip install --quiet --upgrade pip
    "$python" -m pip install --quiet -e "$backend[dev]"
fi

if [ ! -d "$frontend/node_modules" ]; then
    echo "Installing frontend packages..."
    npm --prefix "$frontend" install --silent
fi

if ! ls /dev/hidraw* >/dev/null 2>&1 || [ ! -w "$(ls /dev/hidraw* | head -n1)" ]; then
    echo "Note: if the zones fail to open, add the udev rule from README.md (hidraw access)." >&2
fi

echo "Starting backend on http://127.0.0.1:8765 ..."
(cd "$backend" && exec "$python" -m led_studio.main) &
server=$!
trap 'kill "$server" 2>/dev/null || true' EXIT

sleep 2
kill -0 "$server" 2>/dev/null || { echo "Backend failed to start." >&2; exit 1; }
(xdg-open "http://localhost:5173" >/dev/null 2>&1 || true) &
echo "Frontend on http://localhost:5173 - press Ctrl+C to stop everything."
npm --prefix "$frontend" run dev
