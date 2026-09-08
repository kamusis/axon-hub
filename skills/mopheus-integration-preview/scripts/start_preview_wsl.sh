#!/bin/bash
set -eo pipefail

export PATH="/home/kamus/.local/bin:/home/kamus/.nvm/versions/node/v24.14.0/bin:/usr/local/go/bin:$HOME/go/bin:/home/kamus/.local/share/pnpm:$PATH"

PREVIEW_DIR="/home/kamus/CascadeProjects/mopheus/.worktrees/preview-test"
FIXED_DAEMON_ID="5864c916-5e33-4137-8244-d435fd451561"
cd "$PREVIEW_DIR"

echo "==> [1/6] Stopping stale preview processes & daemon..."
if [ -x "$PREVIEW_DIR/server/bin/mopheus" ]; then
    "$PREVIEW_DIR/server/bin/mopheus" --profile wt-preview-test daemon stop --force 2>/dev/null || true
fi
fuser -k 8230/tcp 2>/dev/null || true
fuser -k 3230/tcp 2>/dev/null || true
pkill -9 -f "next dev" 2>/dev/null || true
pkill -9 -f "next-server" 2>/dev/null || true
sleep 1

echo "==> [2/6] Starting PostgreSQL container..."
docker start mopheus-postgres-1 2>/dev/null || true

echo "==> [3/6] Loading environment and running migrations..."
if [ -f .env.worktree ]; then
    set -a
    source .env.worktree
    set +a
fi

(cd server && go run ./cmd/migrate up)

echo "==> [4/6] Enabling all features & pruning stale runtimes..."
psql postgres://mopheus:mopheus@localhost:5432/mopheus_wt_preview_test -c "
    INSERT INTO workspace_feature (workspace_id, feature_id, enabled)
    SELECT w.id, f.id, true
    FROM workspace w, feature f
    WHERE w.slug = 'dev-space'
    ON CONFLICT (workspace_id, feature_id) DO UPDATE SET enabled = true;

    DELETE FROM daemon_runtime WHERE daemon_id != '$FIXED_DAEMON_ID' OR status = 0;
" >/dev/null 2>&1 || true

echo "==> [5/6] Building backend & CLI binaries..."
(cd server && mkdir -p bin && go build -o bin/mopheusd ./cmd/mopheusd && go build -o bin/mopheus ./cmd/mopheus)

# Start backend first
setsid "$PREVIEW_DIR/server/bin/mopheusd" </dev/null > "$PREVIEW_DIR/backend.log" 2>&1 &

echo "==> Waiting for backend (:8230) to be ready..."
for i in $(seq 1 10); do
    if ss -tulpn | grep -q ':8230'; then
        echo "Backend is ready on :8230"
        break
    fi
    sleep 0.5
done

# Start daemon
echo "==> [6/6] Registering & launching mop daemon..."
"$PREVIEW_DIR/server/bin/mopheus" --profile wt-preview-test --server_url http://localhost:8230 login --email preview-admin@test.local --password "MopheusPreview123!" >/dev/null 2>&1 || true
"$PREVIEW_DIR/server/bin/mopheus" --profile wt-preview-test --server_url http://localhost:8230 daemon start --daemon-id "$FIXED_DAEMON_ID" --allow-root

# Start frontend
setsid pnpm --filter @mopheus/web dev -p 3230 </dev/null > "$PREVIEW_DIR/frontend.log" 2>&1 &

echo "==> Waiting for frontend (:3230) to be ready..."
for i in $(seq 1 15); do
    if ss -tulpn | grep -q ':3230'; then
        echo "Frontend is ready on :3230"
        break
    fi
    sleep 1
done

WSL_IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

echo ""
echo "=================================================="
echo " Mopheus WSL Preview is ready!"
echo " Frontend:  http://${WSL_IP}:3230 (or http://localhost:3230)"
echo " Backend:   http://${WSL_IP}:8230 (or http://localhost:8230)"
echo " Workspace: http://${WSL_IP}:3230/dev-space/dashboard"
echo " Skills:    http://${WSL_IP}:3230/dev-space/skills"
echo " Runtimes:  http://${WSL_IP}:3230/dev-space/settings/runtimes"
echo " Test User: preview-admin@test.local / MopheusPreview123!"
echo " Daemon:    Online (ID: ${FIXED_DAEMON_ID})"
echo "=================================================="
