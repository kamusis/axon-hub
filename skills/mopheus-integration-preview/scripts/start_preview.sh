#!/usr/bin/env bash
set -euo pipefail

readonly PREVIEW_EMAIL_DEFAULT="pr484-web-admin@test.local"
readonly PREVIEW_PASSWORD_DEFAULT="MopheusPR484!"
readonly PREVIEW_WORKSPACE_SLUG_DEFAULT="dev-space"
readonly PREVIEW_WORKSPACE_NAME_DEFAULT="Dev Space"
readonly POSTGRES_CONTAINER_NAME="mopheus-postgres-1"

usage() {
  printf 'Usage: %s <absolute-mopheus-worktree-path>\n' "$0"
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

if [ "$#" -ne 1 ]; then
  usage >&2
  exit 2
fi

for required_command in bash curl docker git go jq lsof make node pnpm; do
  require_command "$required_command"
done

input_path="$1"
[[ "$input_path" = /* ]] || fail "worktree path must be absolute: $input_path"
[ -d "$input_path" ] || fail "worktree path does not exist: $input_path"

worktree_path="$(cd "$input_path" && pwd -P)"
git -C "$worktree_path" rev-parse --is-inside-work-tree >/dev/null 2>&1 || fail "not a Git worktree: $worktree_path"

git_dir="$(git -C "$worktree_path" rev-parse --absolute-git-dir)"
common_dir="$(git -C "$worktree_path" rev-parse --path-format=absolute --git-common-dir)"
[ "$git_dir" != "$common_dir" ] || fail "primary checkout is not accepted; provide an existing linked Mopheus worktree"

[ -f "$worktree_path/server/go.mod" ] || fail "missing server/go.mod; not a Mopheus worktree"
grep -Eq '^module[[:space:]]+mopheus$' "$worktree_path/server/go.mod" || fail "server/go.mod is not the Mopheus module"
[ -x "$worktree_path/scripts/init-worktree-env.sh" ] || fail "missing executable scripts/init-worktree-env.sh"
[ -f "$worktree_path/scripts/ensure-postgres.sh" ] || fail "missing scripts/ensure-postgres.sh"

env_file="$worktree_path/.env.worktree"
if [ ! -f "$env_file" ]; then
  (cd "$worktree_path" && bash scripts/init-worktree-env.sh .env.worktree)
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
log_file="$runtime_dir/services.log"
pid_file="$runtime_dir/launcher.pid"
services_state="reused"
log_display="existing process; no log was created by this run"

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
  (
    cd "$worktree_path"
    nohup make start-worktree >"$log_file" 2>&1 </dev/null &
    printf '%s\n' "$!" >"$pid_file"
  )
  services_state="started"
  log_display="$log_file"

  timeout_seconds="${MOPHEUS_PREVIEW_START_TIMEOUT:-180}"
  if ! wait_for_http "$auth_ready_url" "$timeout_seconds"; then
    tail -n 80 "$log_file" >&2 || true
    fail "backend did not become ready within ${timeout_seconds}s"
  fi
  if ! wait_for_http "$login_url" "$timeout_seconds"; then
    tail -n 80 "$log_file" >&2 || true
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

printf '\n'
printf 'Mopheus integration preview is ready.\n'
printf 'Services: %s\n' "$services_state"
printf 'Frontend login: %s\n' "$login_url"
printf 'Workspace: %s/%s/dashboard\n' "$frontend_url" "$workspace_slug"
printf 'Backend: %s\n' "$backend_url"
printf 'PostgreSQL: %s on localhost:%s\n' "$POSTGRES_CONTAINER_NAME" "$POSTGRES_PORT"
printf 'Database: %s\n' "$POSTGRES_DB"
printf 'Enabled features: %s\n' "$enabled_features"
printf 'Test email: %s\n' "$preview_email"
printf 'Test password: %s\n' "$preview_password"
printf 'Service log: %s\n' "$log_display"
