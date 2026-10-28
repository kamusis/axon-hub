#!/usr/bin/env bash
set -eo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    \. "$NVM_DIR/nvm.sh"
fi
# Include standard tool paths for both Linux and macOS (Homebrew, local bin, Go, pnpm)
for node_bin in "$HOME"/.nvm/versions/node/*/bin; do
    if [ -d "$node_bin" ]; then
        export PATH="$node_bin:$PATH"
    fi
done
export PATH="$HOME/.local/bin:$HOME/.local/share/pnpm:$HOME/Library/pnpm:/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/go/bin:/usr/local/bin:$HOME/go/bin:$PATH"

FIXED_DAEMON_ID="5864c916-5e33-4137-8244-d435fd451561"
DEV_SPACE_ID="bb08a9c4-9f3f-414d-8632-d23909bada79"

SOURCE_DIR="${1:-$PWD}"
if [ ! -d "$SOURCE_DIR" ]; then
    echo "ERROR: Source directory does not exist: $SOURCE_DIR" >&2
    exit 1
fi
SOURCE_REAL="$(cd "$SOURCE_DIR" && pwd -P)"

# Resolve the primary repository root via git-common-dir
if git -C "$SOURCE_REAL" rev-parse --git-common-dir >/dev/null 2>&1; then
    COMMON_DIR="$(git -C "$SOURCE_REAL" rev-parse --path-format=absolute --git-common-dir)"
    PRIMARY_REPO="$(cd "$COMMON_DIR/.." && pwd -P)"
elif [ -d "$HOME/CascadeProjects/mopheus" ]; then
    PRIMARY_REPO="$(cd "$HOME/CascadeProjects/mopheus" && pwd -P)"
else
    PRIMARY_REPO="$SOURCE_REAL"
fi

# Prefer dedicated .worktrees/preview-test if present; otherwise run directly in SOURCE_REAL
if [ -d "$PRIMARY_REPO/.worktrees/preview-test" ]; then
    PREVIEW_DIR="$(cd "$PRIMARY_REPO/.worktrees/preview-test" && pwd -P)"
else
    PREVIEW_DIR="$SOURCE_REAL"
fi

# Warn (never silently fix) if the host CLI was repointed at a repo/worktree build.
# The host CLI is the production tool for https://dev.mopheus.ai and must stay independent.
for host_cli in "$HOME/.local/bin/mopheus" "$HOME/.local/bin/mop"; do
    [ -e "$host_cli" ] || continue
    resolved="$(readlink -f "$host_cli" 2>/dev/null || true)"
    case "$resolved" in
        "$PRIMARY_REPO"/*)
            echo "WARNING: $host_cli resolves to $resolved (inside the repository)." >&2
            echo "WARNING: the host CLI must not point at a preview build; restore the installed binary." >&2
            ;;
    esac
done

kill_port() {
    local port="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -k "${port}/tcp" >/dev/null 2>&1 || true
    fi
    local pids
    pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$pids" ]; then
        # shellcheck disable=SC2086
        kill -9 $pids 2>/dev/null || true
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

if [ "$SOURCE_REAL" != "$PREVIEW_DIR" ]; then
    echo "==> [0/6] Syncing code from $SOURCE_REAL to $PREVIEW_DIR..."
    if [ ! -d "$SOURCE_REAL/apps/docs" ] && [ -d "$PREVIEW_DIR/apps/docs" ]; then
        rm -rf "$PREVIEW_DIR/apps/docs"
    fi
    rsync -a --delete \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='.next' \
        --exclude='.turbo' \
        --exclude='.worktrees' \
        --exclude='uploads' \
        --exclude='dist' \
        --exclude='bin' \
        --exclude='__pycache__' \
        --exclude='.env.worktree' \
        --exclude='.env.local' \
        --exclude='*.log' \
        --exclude='*.pid' \
        --exclude='*.tmp' \
        "$SOURCE_REAL/" "$PREVIEW_DIR/"
fi

cd "$PREVIEW_DIR"

echo "==> [1/6] Stopping stale preview processes & daemon..."
if [ -x "$PREVIEW_DIR/server/bin/mopheus" ]; then
    "$PREVIEW_DIR/server/bin/mopheus" daemon stop --profile wt-preview-test --force 2>/dev/null || true
fi
kill_port 8230
kill_port 3230
sleep 1

echo "==> [2/6] Initializing .env.worktree & ensuring PostgreSQL..."
if [ "$(uname -s)" = "Darwin" ] && ! docker info >/dev/null 2>&1; then
    if command -v colima >/dev/null 2>&1; then
        echo "Starting Colima on macOS..."
        colima start
    fi
fi

if [ ! -f .env.worktree ]; then
    bash scripts/init-worktree-env.sh .env.worktree
fi
set -a
source .env.worktree
set +a

BACKEND_PORT="${BACKEND_PORT:-8230}"
FRONTEND_PORT="${FRONTEND_PORT:-3230}"
POSTGRES_DB="${POSTGRES_DB:-mopheus_wt_preview_test}"
MOPHEUS_PROFILE="${MOPHEUS_PROFILE:-wt-preview-test}"

bash scripts/ensure-postgres.sh .env.worktree

echo "==> [3/6] Running database migrations..."
(cd server && go run ./cmd/migrate up)

echo "==> [4/6] Building backend & CLI binaries..."
(cd server && mkdir -p bin && go build -o bin/mopheusd ./cmd/mopheusd && go build -o bin/mopheus ./cmd/mopheus)

# Start backend detached using cross-platform Python helper
rm -f "$PREVIEW_DIR/backend.log"
python3 "$SCRIPT_DIR/start_detached.py" \
    --cwd "$PREVIEW_DIR" \
    --log "$PREVIEW_DIR/backend.log" \
    --pid-file "$PREVIEW_DIR/backend.pid" \
    "$PREVIEW_DIR/server/bin/mopheusd"

echo "==> Waiting for backend (:${BACKEND_PORT}) to be ready..."
for _ in $(seq 1 40); do
    if is_port_listening "$BACKEND_PORT"; then
        echo "Backend is ready on :${BACKEND_PORT}"
        break
    fi
    sleep 0.5
done
if ! is_port_listening "$BACKEND_PORT"; then
    echo "ERROR: Backend failed to listen on :${BACKEND_PORT}. Check $PREVIEW_DIR/backend.log" >&2
    tail -n 30 "$PREVIEW_DIR/backend.log" >&2 || true
    exit 1
fi

echo "==> [5/6] Seeding test accounts, dev-space workspace, features & pruning stale runtimes..."
docker exec mopheus-postgres-1 psql -U mopheus -d "$POSTGRES_DB" -c "
    UPDATE \"user\"
    SET password_hash = '\$2a\$10\$KP.r4.CLRCMwuFgC3gqKZeimIno.2poYeXTBxhZnLd01T3VWTd15O',
        must_change_password = false,
        email_verified = true,
        onboarded_at = COALESCE(onboarded_at, now())
    WHERE email IN ('alice@mopheus.dev', 'admin@mopheus.dev');

    INSERT INTO workspace (id, name, slug, description, identifier_prefix)
    VALUES ('$DEV_SPACE_ID', 'Dev Space', 'dev-space', 'Development Workspace', 'DEV')
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO workspace_member (workspace_id, user_id, role)
    SELECT '$DEV_SPACE_ID', u.id, CASE WHEN u.email = 'alice@mopheus.dev' THEN 0 ELSE 1 END
    FROM \"user\" u
    WHERE u.email IN ('alice@mopheus.dev', 'admin@mopheus.dev')
    ON CONFLICT (workspace_id, user_id) DO UPDATE SET role = EXCLUDED.role;

    INSERT INTO workspace_actor_role (workspace_id, actor_id, actor_type, role_id)
    SELECT '$DEV_SPACE_ID', u.id, 0, 'f47ac10b-58cc-4372-a567-0e02b2c3d400'
    FROM \"user\" u
    WHERE u.email IN ('alice@mopheus.dev', 'admin@mopheus.dev')
    ON CONFLICT DO NOTHING;

    INSERT INTO workspace_feature (workspace_id, feature_id, enabled)
    SELECT '$DEV_SPACE_ID', f.id, true
    FROM feature f
    ON CONFLICT (workspace_id, feature_id) DO UPDATE SET enabled = true;

    DELETE FROM daemon_runtime WHERE daemon_id != '$FIXED_DAEMON_ID' OR status = 0;
" >/dev/null

echo "==> [6/6] Logging in as alice@mopheus.dev, switching workspace & launching daemon + frontend..."
echo y | "$PREVIEW_DIR/server/bin/mopheus" --profile "$MOPHEUS_PROFILE" --server_url "http://localhost:${BACKEND_PORT}" login --email alice@mopheus.dev --password "Mopheus@123" >/dev/null
"$PREVIEW_DIR/server/bin/mopheus" --profile "$MOPHEUS_PROFILE" --server_url "http://localhost:${BACKEND_PORT}" workspace switch "$DEV_SPACE_ID" >/dev/null
"$PREVIEW_DIR/server/bin/mopheus" --profile "$MOPHEUS_PROFILE" --server_url "http://localhost:${BACKEND_PORT}" daemon start --daemon-id "$FIXED_DAEMON_ID" --sandbox-enabled=false --allow-root

rm -f "$PREVIEW_DIR/frontend.log"
python3 "$SCRIPT_DIR/start_detached.py" \
    --cwd "$PREVIEW_DIR" \
    --log "$PREVIEW_DIR/frontend.log" \
    --pid-file "$PREVIEW_DIR/frontend.pid" \
    pnpm --filter @mopheus/web dev -p "$FRONTEND_PORT"

echo "==> Waiting for frontend (:${FRONTEND_PORT}) to be ready..."
for _ in $(seq 1 45); do
    if is_port_listening "$FRONTEND_PORT"; then
        echo "Frontend is ready on :${FRONTEND_PORT}"
        break
    fi
    sleep 1
done
if ! is_port_listening "$FRONTEND_PORT"; then
    echo "ERROR: Frontend failed to listen on :${FRONTEND_PORT}. Check $PREVIEW_DIR/frontend.log" >&2
    tail -n 30 "$PREVIEW_DIR/frontend.log" >&2 || true
    exit 1
fi

echo ""
echo "=================================================="
echo " Mopheus Preview is ready!"
echo " Worktree:    ${PREVIEW_DIR}"
echo " Frontend:    http://localhost:${FRONTEND_PORT}"
echo " Backend:     http://localhost:${BACKEND_PORT}"
echo " Workspace:   http://localhost:${FRONTEND_PORT}/dev-space/dashboard"
echo " Skills:      http://localhost:${FRONTEND_PORT}/dev-space/skills"
echo " Runtimes:    http://localhost:${FRONTEND_PORT}/dev-space/settings/runtimes"
echo " Profile:     ${MOPHEUS_PROFILE}"
echo " Database:    ${POSTGRES_DB}"
echo " Test Member: alice@mopheus.dev / Mopheus@123 (Daemon owner & regular workspace testing)"
echo " Admin User:  admin@mopheus.dev / Mopheus@123 (System settings)"
echo " Daemon:      Online (ID: ${FIXED_DAEMON_ID})"
echo "=================================================="
