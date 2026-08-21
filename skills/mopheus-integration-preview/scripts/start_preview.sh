#!/usr/bin/env bash
set -euo pipefail

readonly PREVIEW_EMAIL_DEFAULT="pr484-web-admin@test.local"
readonly PREVIEW_PASSWORD_DEFAULT="MopheusPR484!"
readonly PREVIEW_WORKSPACE_SLUG_DEFAULT="dev-space"
readonly PREVIEW_WORKSPACE_NAME_DEFAULT="Dev Space"
readonly POSTGRES_CONTAINER_NAME="mopheus-postgres-1"

usage() {
  printf 'Usage: %s [--allow-existing-previews | --reuse-db-from <absolute-source-worktree>] <absolute-target-worktree>\n' "$0"
}

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  local command_name="$1"
  command -v "$command_name" >/dev/null 2>&1 || fail "required command not found: $command_name"
}

json_success() {
  jq -e '.success == true' >/dev/null
}

api_call() {
  local method="$1"
  local url="$2"
  local token="${3:-}"
  local workspace_slug="${4:-}"
  local payload="${5:-}"
  local response_file
  local http_code
  local -a curl_args

  response_file="$(mktemp)"
  curl_args=(-sS -o "$response_file" -w '%{http_code}' -X "$method" "$url" -H 'Content-Type: application/json')
  if [ -n "$token" ]; then
    curl_args+=(-H "Authorization: Bearer $token")
  fi
  if [ -n "$workspace_slug" ]; then
    curl_args+=(-H "X-Workspace-Slug: $workspace_slug")
  fi
  if [ -n "$payload" ]; then
    curl_args+=(--data "$payload")
  fi
  http_code="$(curl "${curl_args[@]}")"

  if [[ "$http_code" != 2* ]]; then
    printf 'API request failed: %s %s -> HTTP %s\n' "$method" "$url" "$http_code" >&2
    jq '{success, error, code}' "$response_file" 2>/dev/null >&2 || sed -n '1,20p' "$response_file" >&2
    rm -f "$response_file"
    return 1
  fi

  cat "$response_file"
  rm -f "$response_file"
}

login() {
  local api_base="$1"
  local email="$2"
  local password="$3"
  local payload

  payload="$(jq -n --arg email "$email" --arg password "$password" '{email:$email,password:$password}')"
  api_call POST "$api_base/auth/login" "" "" "$payload"
}

is_http_ready() {
  local url="$1"
  curl -fsS --max-time 3 "$url" >/dev/null 2>&1
}

wait_for_http() {
  local url="$1"
  local timeout_seconds="$2"
  local started_at

  started_at="$(date +%s)"
  until is_http_ready "$url"; do
    if (( $(date +%s) - started_at >= timeout_seconds )); then
      return 1
    fi
    sleep 1
  done
}

is_daemon_running() {
  local target_worktree="$1"
  local profile="$2"
  local status_output

  status_output="$(cd "$target_worktree/server" && go run ./cmd/mopheus --profile "$profile" daemon status 2>/dev/null || true)"
  grep -Eq ':[[:space:]]+running([[:space:]]|$)' <<<"$status_output"
}

wait_for_runtimes() {
  local api_base="$1"
  local token="$2"
  local workspace_slug="$3"
  local timeout_seconds="$4"
  local started_at
  local response

  started_at="$(date +%s)"
  while true; do
    response="$(api_call GET "$api_base/runtimes" "$token" "$workspace_slug" 2>/dev/null || true)"
    if json_success <<<"$response" && jq -e '(.data // []) | length > 0' <<<"$response" >/dev/null; then
      return 0
    fi
    if (( $(date +%s) - started_at >= timeout_seconds )); then
      return 1
    fi
    sleep 1
  done
}

read_env_value() {
  local env_path="$1"
  local key="$2"
  awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$env_path"
}

allow_existing_previews=0
reuse_db_from=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --allow-existing-previews)
      allow_existing_previews=1
      shift
      ;;
    --reuse-db-from)
      [ "$#" -ge 2 ] || fail "--reuse-db-from requires an absolute linked worktree path"
      reuse_db_from="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*)
      fail "unknown option: $1"
      ;;
    *)
      break
      ;;
  esac
done

if [ "$#" -ne 1 ]; then
  usage >&2
  exit 2
fi

if [ "$allow_existing_previews" = "1" ] && [ -n "$reuse_db_from" ]; then
  fail "--allow-existing-previews and --reuse-db-from are mutually exclusive"
fi

for required_command in bash curl docker git go jq lsof make node pnpm python3; do
  require_command "$required_command"
done

input_path="$1"
[[ "$input_path" = /* ]] || fail "worktree path must be absolute: $input_path"
[ -d "$input_path" ] || fail "worktree path does not exist: $input_path"

worktree_path="$(cd "$input_path" && pwd -P)"
script_dir="$(cd "$(dirname "$0")" && pwd -P)"
git -C "$worktree_path" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a Git worktree: $worktree_path"

git_dir="$(git -C "$worktree_path" rev-parse --absolute-git-dir)"
common_dir="$(git -C "$worktree_path" rev-parse --path-format=absolute --git-common-dir)"
[ "$git_dir" != "$common_dir" ] || fail "primary checkout is not accepted; provide an existing linked Mopheus worktree"

[ -f "$worktree_path/server/go.mod" ] || fail "missing server/go.mod; not a Mopheus worktree"
grep -Eq '^module[[:space:]]+mopheus$' "$worktree_path/server/go.mod" || fail "server/go.mod is not the Mopheus module"
[ -x "$worktree_path/scripts/init-worktree-env.sh" ] || fail "missing executable scripts/init-worktree-env.sh"
[ -f "$worktree_path/scripts/ensure-postgres.sh" ] || fail "missing scripts/ensure-postgres.sh"

existing_previews="$($script_dir/discover_previews.sh "$worktree_path")"
if [ -n "$existing_previews" ] && [ "$allow_existing_previews" != "1" ] && [ -z "$reuse_db_from" ]; then
  printf 'Existing Mopheus previews are running:\n' >&2
  printf 'WORKTREE\tFRONTEND_PORT\tFRONTEND_PID\tBACKEND_PORT\tBACKEND_PID\tDATABASE\n' >&2
  printf '%s\n' "$existing_previews" >&2
  fail "existing preview confirmation required; ask whether to stop one and reuse its database, or rerun with --allow-existing-previews after explicit approval"
fi

env_file="$worktree_path/.env.worktree"
if [ ! -f "$env_file" ]; then
  (cd "$worktree_path" && bash scripts/init-worktree-env.sh .env.worktree)
fi

if [ -n "$reuse_db_from" ]; then
  [[ "$reuse_db_from" = /* ]] || fail "reuse source path must be absolute: $reuse_db_from"
  [ -d "$reuse_db_from" ] || fail "reuse source path does not exist: $reuse_db_from"
  reuse_db_from="$(cd "$reuse_db_from" && pwd -P)"
  [ "$reuse_db_from" != "$worktree_path" ] || fail "reuse source and target worktrees must differ"

  unexpected_previews="$(awk -F '\t' -v approved_source="$reuse_db_from" '$1 != approved_source' <<<"$existing_previews")"
  if [ -n "$unexpected_previews" ]; then
    printf 'Additional unconfirmed Mopheus previews are running:\n' >&2
    printf 'WORKTREE\tFRONTEND_PORT\tFRONTEND_PID\tBACKEND_PORT\tBACKEND_PID\tDATABASE\n' >&2
    printf '%s\n' "$unexpected_previews" >&2
    fail "database reuse approval covers only $reuse_db_from; ask what to do with the additional previews"
  fi

  reuse_git_dir="$(git -C "$reuse_db_from" rev-parse --absolute-git-dir 2>/dev/null || true)"
  reuse_common_dir="$(git -C "$reuse_db_from" rev-parse --path-format=absolute --git-common-dir 2>/dev/null || true)"
  [ -n "$reuse_git_dir" ] && [ "$reuse_git_dir" != "$reuse_common_dir" ] || fail "reuse source is not a linked Git worktree: $reuse_db_from"

  reuse_env_file="$reuse_db_from/.env.worktree"
  [ -f "$reuse_env_file" ] || fail "reuse source is missing .env.worktree: $reuse_db_from"
  reuse_frontend_port="$(read_env_value "$reuse_env_file" FRONTEND_PORT)"
  reuse_backend_port="$(read_env_value "$reuse_env_file" BACKEND_PORT)"
  reuse_postgres_db="$(read_env_value "$reuse_env_file" POSTGRES_DB)"
  reuse_database_url="$(read_env_value "$reuse_env_file" DATABASE_URL)"
  reuse_mopheus_profile="$(read_env_value "$reuse_env_file" MOPHEUS_PROFILE)"
  [ -n "$reuse_postgres_db" ] && [ -n "$reuse_database_url" ] || fail "reuse source database settings are incomplete"

  reuse_frontend_pid="$(lsof -nP -tiTCP:"$reuse_frontend_port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  reuse_backend_pid="$(lsof -nP -tiTCP:"$reuse_backend_port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [ -n "$reuse_frontend_pid" ] || [ -n "$reuse_backend_pid" ]; then
    fail "reuse source services are still running (frontend PID: ${reuse_frontend_pid:-none}, backend PID: ${reuse_backend_pid:-none}); stop them only after explicit user approval"
  fi
  if [ -n "$reuse_mopheus_profile" ] && is_daemon_running "$reuse_db_from" "$reuse_mopheus_profile"; then
    fail "reuse source daemon profile '$reuse_mopheus_profile' is still running; stop it only after explicit user approval"
  fi

  target_frontend_port="$(read_env_value "$env_file" FRONTEND_PORT)"
  target_backend_port="$(read_env_value "$env_file" BACKEND_PORT)"
  target_mopheus_profile="$(read_env_value "$env_file" MOPHEUS_PROFILE)"
  target_frontend_pid="$(lsof -nP -tiTCP:"$target_frontend_port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  target_backend_pid="$(lsof -nP -tiTCP:"$target_backend_port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [ -n "$target_frontend_pid" ] || [ -n "$target_backend_pid" ]; then
    fail "target services are still running (frontend PID: ${target_frontend_pid:-none}, backend PID: ${target_backend_pid:-none}); stop them before changing the target database"
  fi
  if [ -n "$target_mopheus_profile" ] && is_daemon_running "$worktree_path" "$target_mopheus_profile"; then
    fail "target daemon profile '$target_mopheus_profile' is still running; stop it before changing the target database"
  fi

  reuse_tmp_file="$(mktemp)"
  awk -v postgres_db="$reuse_postgres_db" -v database_url="$reuse_database_url" '
    /^POSTGRES_DB=/ {print "POSTGRES_DB=" postgres_db; next}
    /^DATABASE_URL=/ {print "DATABASE_URL=" database_url; next}
    {print}
  ' "$env_file" >"$reuse_tmp_file"
  mv "$reuse_tmp_file" "$env_file"
  printf '==> Reusing database %s from %s while retaining target application ports.\n' "$reuse_postgres_db" "$reuse_db_from"
fi

set -a
# shellcheck disable=SC1090
. "$env_file"
set +a

: "${POSTGRES_DB:?POSTGRES_DB is required in .env.worktree}"
: "${POSTGRES_PORT:?POSTGRES_PORT is required in .env.worktree}"
: "${BACKEND_PORT:?BACKEND_PORT is required in .env.worktree}"
: "${FRONTEND_PORT:?FRONTEND_PORT is required in .env.worktree}"
: "${DATABASE_URL:?DATABASE_URL is required in .env.worktree}"
: "${ADMIN_EMAIL:?ADMIN_EMAIL is required in .env.worktree}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD is required in .env.worktree}"
: "${MOPHEUS_PROFILE:?MOPHEUS_PROFILE is required in .env.worktree}"

case "$DATABASE_URL" in
  *"@localhost:"*|*"@127.0.0.1:"*) ;;
  *) fail "preview requires a local DATABASE_URL; refusing remote database: $DATABASE_URL" ;;
esac

postgres_container_id="$(docker ps -aq --filter "name=^/${POSTGRES_CONTAINER_NAME}$" | head -n 1)"
[ -n "$postgres_container_id" ] || fail "shared PostgreSQL container '$POSTGRES_CONTAINER_NAME' does not exist"

port_owner="$(docker ps --filter "publish=$POSTGRES_PORT" --format '{{.Names}}' | head -n 1)"
if [ -n "$port_owner" ] && [ "$port_owner" != "$POSTGRES_CONTAINER_NAME" ]; then
  fail "PostgreSQL port $POSTGRES_PORT is occupied by Docker container '$port_owner'; explicit user authorization is required before stopping it"
fi

non_docker_port_pid="$(lsof -nP -tiTCP:"$POSTGRES_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
if [ -n "$non_docker_port_pid" ] && [ -z "$port_owner" ]; then
  port_command="$(ps -p "$non_docker_port_pid" -o command= 2>/dev/null || true)"
  fail "PostgreSQL port $POSTGRES_PORT is occupied by PID $non_docker_port_pid ($port_command)"
fi

docker start "$POSTGRES_CONTAINER_NAME" >/dev/null

printf '==> Preparing worktree dependencies, database, and migrations...\n'
make -C "$worktree_path" setup-worktree

backend_url="http://localhost:$BACKEND_PORT"
frontend_url="http://localhost:$FRONTEND_PORT"
api_base="$backend_url/api/v1"
auth_ready_url="$api_base/config/auth"
login_url="$frontend_url/login"

runtime_hash="$(printf '%s' "$worktree_path" | cksum | awk '{print $1}')"
runtime_dir="${TMPDIR:-/tmp}/mopheus-preview-$runtime_hash"
mkdir -p "$runtime_dir"
backend_log_file="$runtime_dir/backend.log"
frontend_log_file="$runtime_dir/frontend.log"
backend_pid_file="$runtime_dir/backend.pid"
frontend_pid_file="$runtime_dir/frontend.pid"
daemon_log_file="$runtime_dir/daemon.log"
daemon_pid_file="$runtime_dir/daemon.pid"
services_state="reused"
log_display="existing processes; no logs were created by this run"
daemon_state="reused"
daemon_log_display="existing process; no daemon log was created by this run"

if ! is_http_ready "$auth_ready_url" || ! is_http_ready "$login_url"; then
  backend_pid="$(lsof -nP -tiTCP:"$BACKEND_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  frontend_pid="$(lsof -nP -tiTCP:"$FRONTEND_PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [ -n "$backend_pid" ] || [ -n "$frontend_pid" ]; then
    fail "configured application port is occupied but preview health checks fail (backend PID: ${backend_pid:-none}, frontend PID: ${frontend_pid:-none})"
  fi

  # Next.js can retain a failed remote-font/Turbopack compilation in this ignored cache.
  # Remove only this worktree's generated cache before a cold start so readiness is reproducible.
  rm -rf "$worktree_path/apps/web/.next"

  printf '==> Starting backend and frontend...\n'
  python3 "$script_dir/start_detached.py" \
    --cwd "$worktree_path/server" \
    --log "$backend_log_file" \
    --pid-file "$backend_pid_file" \
    go run ./cmd/mopheusd
  python3 "$script_dir/start_detached.py" \
    --cwd "$worktree_path" \
    --log "$frontend_log_file" \
    --pid-file "$frontend_pid_file" \
    pnpm dev:web
  services_state="started"
  log_display="backend: $backend_log_file; frontend: $frontend_log_file"

  timeout_seconds="${MOPHEUS_PREVIEW_START_TIMEOUT:-180}"
  if ! wait_for_http "$auth_ready_url" "$timeout_seconds"; then
    tail -n 80 "$backend_log_file" >&2 || true
    fail "backend did not become ready within ${timeout_seconds}s"
  fi
  if ! wait_for_http "$login_url" "$timeout_seconds"; then
    tail -n 80 "$frontend_log_file" >&2 || true
    fail "frontend did not become ready within ${timeout_seconds}s"
  fi
fi

printf '==> Enabling every registered system feature...\n'
admin_response="$(login "$api_base" "$ADMIN_EMAIL" "$ADMIN_PASSWORD")" || fail "bootstrap Admin login failed"
admin_token="$(jq -er '.data.accessToken' <<<"$admin_response")"
features_response="$(api_call GET "$api_base/admin/features" "$admin_token")"
feature_keys_file="$(mktemp)"
jq -er '.data[].key' <<<"$features_response" >"$feature_keys_file"
[ -s "$feature_keys_file" ] || fail "admin feature list is empty"

while IFS= read -r feature_key; do
  encoded_key="$(printf '%s' "$feature_key" | jq -sRr @uri)"
  api_call PUT "$api_base/admin/features/$encoded_key" "$admin_token" "" '{"systemState":2}' >/dev/null
done <"$feature_keys_file"

preview_email="${MOPHEUS_PREVIEW_EMAIL:-$PREVIEW_EMAIL_DEFAULT}"
preview_password="${MOPHEUS_PREVIEW_PASSWORD:-$PREVIEW_PASSWORD_DEFAULT}"
workspace_slug="${MOPHEUS_PREVIEW_WORKSPACE_SLUG:-$PREVIEW_WORKSPACE_SLUG_DEFAULT}"
workspace_name="${MOPHEUS_PREVIEW_WORKSPACE_NAME:-$PREVIEW_WORKSPACE_NAME_DEFAULT}"

printf '==> Creating or reusing the regular preview user and workspace...\n'
preview_auth_response="$(login "$api_base" "$preview_email" "$preview_password" 2>/dev/null || true)"
if ! json_success <<<"$preview_auth_response"; then
  register_payload="$(jq -n --arg name "Mopheus Preview" --arg email "$preview_email" --arg password "$preview_password" '{name:$name,email:$email,password:$password}')"
  preview_auth_response="$(api_call POST "$api_base/auth/register" "" "" "$register_payload")" || fail "preview user login failed and registration did not succeed; persistent account password may differ"
fi

preview_token="$(jq -er '.data.accessToken' <<<"$preview_auth_response")"
preview_role="$(jq -er '.data.user.role' <<<"$preview_auth_response")"
[ "$preview_role" = "0" ] || fail "preview user has system role $preview_role; expected regular user role 0"

workspaces_response="$(api_call GET "$api_base/workspaces" "$preview_token")"
workspace_id="$(jq -r --arg slug "$workspace_slug" '.data[] | select(.slug == $slug) | .id' <<<"$workspaces_response" | head -n 1)"
if [ -z "$workspace_id" ]; then
  workspace_payload="$(jq -n --arg name "$workspace_name" --arg slug "$workspace_slug" '{name:$name,slug:$slug,description:"Local integration preview workspace",identifierPrefix:"DEV"}')"
  workspace_response="$(api_call POST "$api_base/workspaces" "$preview_token" "" "$workspace_payload")" || fail "failed to create preview workspace '$workspace_slug'"
  workspace_id="$(jq -er '.data.id' <<<"$workspace_response")"
fi

onboarding_payload="$(jq -n --arg workspaceName "$workspace_name" --arg displayName "Mopheus Preview" '{workspaceName:$workspaceName,displayName:$displayName}')"
api_call POST "$api_base/auth/onboarding/complete" "$preview_token" "" "$onboarding_payload" >/dev/null

printf '==> Enabling every feature for workspace %s...\n' "$workspace_slug"
while IFS= read -r feature_key; do
  encoded_key="$(printf '%s' "$feature_key" | jq -sRr @uri)"
  api_call PUT "$api_base/workspaces/$workspace_id/features/$encoded_key" "$preview_token" "" '{"enabled":true}' >/dev/null
done <"$feature_keys_file"

effective_response="$(api_call GET "$api_base/features/effective" "$preview_token" "$workspace_slug")"
disabled_features="$(jq -r '(.data // {}) | to_entries[] | select(.value != true) | .key' <<<"$effective_response")"
if [ -n "$disabled_features" ]; then
  printf 'Features still disabled:\n%s\n' "$disabled_features" >&2
  fail "effective feature verification failed"
fi

enabled_features="$(jq -r '(.data // {}) | to_entries | sort_by(.key) | map(.key) | join(", ")' <<<"$effective_response")"
rm -f "$feature_keys_file"

if ! is_daemon_running "$worktree_path" "$MOPHEUS_PROFILE"; then
  printf '==> Starting daemon and registering runtimes...\n'
  if command -v make >/dev/null 2>&1; then
    python3 "$script_dir/start_detached.py" \
      --cwd "$worktree_path" \
      --log "$daemon_log_file" \
      --pid-file "$daemon_pid_file" \
      make daemon-worktree "DEFAULT_EMAIL=$preview_email" "DEFAULT_PASSWORD=$preview_password"
  else
    printf '==> make not found; using direct daemon login and foreground startup...\n'
    printf 'y\n' | (cd "$worktree_path/server" && go run ./cmd/mopheus --profile "$MOPHEUS_PROFILE" login --email "$preview_email" --password "$preview_password")
    python3 "$script_dir/start_detached.py" \
      --cwd "$worktree_path/server" \
      --log "$daemon_log_file" \
      --pid-file "$daemon_pid_file" \
      go run ./cmd/mopheus --profile "$MOPHEUS_PROFILE" daemon start --foreground --allow-root
  fi
  daemon_state="started"
  daemon_log_display="$daemon_log_file"
fi

daemon_timeout_seconds="${MOPHEUS_PREVIEW_DAEMON_TIMEOUT:-120}"
if ! wait_for_runtimes "$api_base" "$preview_token" "$workspace_slug" "$daemon_timeout_seconds"; then
  if [ -f "$daemon_log_file" ]; then
    tail -n 80 "$daemon_log_file" >&2 || true
  fi
  fail "daemon did not register any runtime for workspace '$workspace_slug' within ${daemon_timeout_seconds}s"
fi

printf '\n'
printf 'Mopheus integration preview is ready.\n'
printf 'Application services: %s\n' "$services_state"
printf 'Daemon: %s (profile: %s)\n' "$daemon_state" "$MOPHEUS_PROFILE"
printf 'Frontend login: %s\n' "$login_url"
printf 'Workspace: %s/%s/dashboard\n' "$frontend_url" "$workspace_slug"
printf 'Backend: %s\n' "$backend_url"
printf 'PostgreSQL: %s on localhost:%s\n' "$POSTGRES_CONTAINER_NAME" "$POSTGRES_PORT"
printf 'Database: %s\n' "$POSTGRES_DB"
printf 'Enabled features: %s\n' "$enabled_features"
printf 'Test email: %s\n' "$preview_email"
printf 'Test password: %s\n' "$preview_password"
printf 'Service logs: %s\n' "$log_display"
printf 'Daemon log: %s\n' "$daemon_log_display"
