#!/usr/bin/env bash
# restart_service.sh — Restart an individual preview service cleanly without full reprovisioning
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    \. "$NVM_DIR/nvm.sh"
fi
for node_bin in "$HOME"/.nvm/versions/node/*/bin; do
    if [ -d "$node_bin" ]; then
        export PATH="$node_bin:$PATH"
    fi
done
export PATH="$HOME/.local/bin:$HOME/.local/share/pnpm:$HOME/Library/pnpm:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/go/bin:/usr/local/bin:$HOME/go/bin:$PATH"

SERVICE="${1:-frontend}"
TARGET_DIR="${2:-$PWD}"

if git -C "$TARGET_DIR" rev-parse --git-common-dir >/dev/null 2>&1; then
    COMMON_DIR="$(git -C "$TARGET_DIR" rev-parse --path-format=absolute --git-common-dir)"
    PRIMARY_REPO="$(cd "$COMMON_DIR/.." && pwd -P)"
elif [ -d "$HOME/CascadeProjects/mopheus" ]; then
    PRIMARY_REPO="$(cd "$HOME/CascadeProjects/mopheus" && pwd -P)"
else
    PRIMARY_REPO="$TARGET_DIR"
fi

if [ -d "$PRIMARY_REPO/.worktrees/preview-test" ]; then
    PREVIEW_DIR="$(cd "$PRIMARY_REPO/.worktrees/preview-test" && pwd -P)"
else
    PREVIEW_DIR="$TARGET_DIR"
fi

cd "$PREVIEW_DIR"

if [ -f .env.worktree ]; then
    set -a
    source .env.worktree
    set +a
fi

BACKEND_PORT="${BACKEND_PORT:-8230}"
FRONTEND_PORT="${FRONTEND_PORT:-3230}"
MOPHEUS_PROFILE="${MOPHEUS_PROFILE:-wt-preview-test}"
FIXED_DAEMON_ID="5864c916-5e33-4137-8244-d435fd451561"

kill_port() {
    local port="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -k "${port}/tcp" 2>/dev/null || true
    elif command -v lsof >/dev/null 2>&1; then
        local pids
        pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
        fi
    fi
}

is_port_listening() {
    local port="$1"
    python3 - "$port" <<'PY' >/dev/null 2>&1
import socket, sys
port = int(sys.argv[1])
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(0.5)
    sys.exit(0 if s.connect_ex(("127.0.0.1", port)) == 0 else 1)
PY
}

case "$SERVICE" in
    frontend)
        echo "==> Restarting preview frontend on :${FRONTEND_PORT}..."
        if [ -f "$PREVIEW_DIR/frontend.pid" ]; then
            kill -9 "$(cat "$PREVIEW_DIR/frontend.pid" 2>/dev/null)" 2>/dev/null || true
        fi
        kill_port "$FRONTEND_PORT"
        sleep 0.5
        rm -f "$PREVIEW_DIR/frontend.log"
        echo "==> Cleaning stale Next.js cache to avoid Turbopack chunk reuse..."
        rm -rf "$PREVIEW_DIR/apps/web/.next"
        bash "$SCRIPT_DIR/start_detached.sh" \
            --cwd "$PREVIEW_DIR" \
            --log "$PREVIEW_DIR/frontend.log" \
            --pid-file "$PREVIEW_DIR/frontend.pid" \
            pnpm --filter @mopheus/web dev -p "$FRONTEND_PORT"
        echo "==> Waiting for frontend (:${FRONTEND_PORT}) to be ready..."
        for _ in $(seq 1 45); do
            if is_port_listening "$FRONTEND_PORT"; then
                echo "Frontend is ready on :${FRONTEND_PORT}"
                exit 0
            fi
            sleep 1
        done
        echo "ERROR: Frontend failed to listen on :${FRONTEND_PORT}" >&2
        exit 1
        ;;
    backend)
        echo "==> Rebuilding and restarting preview backend on :${BACKEND_PORT}..."
        if [ -f "$PREVIEW_DIR/backend.pid" ]; then
            kill -9 "$(cat "$PREVIEW_DIR/backend.pid" 2>/dev/null)" 2>/dev/null || true
        fi
        kill_port "$BACKEND_PORT"
        sleep 0.5
        (cd server && mkdir -p bin && go build -o bin/mopheusd ./cmd/mopheusd && go build -o bin/mopheus ./cmd/mopheus)
        rm -f "$PREVIEW_DIR/backend.log"
        bash "$SCRIPT_DIR/start_detached.sh" \
            --cwd "$PREVIEW_DIR" \
            --log "$PREVIEW_DIR/backend.log" \
            --pid-file "$PREVIEW_DIR/backend.pid" \
            "$PREVIEW_DIR/server/bin/mopheusd"
        echo "==> Waiting for backend (:${BACKEND_PORT}) to be ready..."
        for _ in $(seq 1 40); do
            if is_port_listening "$BACKEND_PORT"; then
                echo "Backend is ready on :${BACKEND_PORT}"
                exit 0
            fi
            sleep 0.5
        done
        echo "ERROR: Backend failed to listen on :${BACKEND_PORT}" >&2
        exit 1
        ;;
    daemon)
        echo "==> Restarting preview daemon..."
        if [ -x "$PREVIEW_DIR/server/bin/mopheus" ]; then
            "$PREVIEW_DIR/server/bin/mopheus" daemon stop --profile "$MOPHEUS_PROFILE" --force 2>/dev/null || true
            sleep 1
            "$PREVIEW_DIR/server/bin/mopheus" --profile "$MOPHEUS_PROFILE" --server_url "http://localhost:${BACKEND_PORT}" daemon start --daemon-id "$FIXED_DAEMON_ID" --sandbox-enabled=false --allow-root
            echo "Daemon restarted."
        else
            echo "ERROR: mopheus CLI not found in $PREVIEW_DIR/server/bin/" >&2
            exit 1
        fi
        ;;
    *)
        echo "Usage: $0 [frontend|backend|daemon] [target-dir]" >&2
        exit 1
        ;;
esac
