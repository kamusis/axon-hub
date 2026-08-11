#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s <absolute-target-worktree-path>\n' "$0"
}

read_env_value() {
  local env_file="$1"
  local key="$2"
  awk -F= -v key="$key" '$1 == key {sub(/^[^=]*=/, ""); print; exit}' "$env_file"
}

if [ "$#" -ne 1 ]; then
  usage >&2
  exit 2
fi

target_path="$1"
[[ "$target_path" = /* ]] || { printf 'ERROR: target path must be absolute: %s\n' "$target_path" >&2; exit 1; }
[ -d "$target_path" ] || { printf 'ERROR: target path does not exist: %s\n' "$target_path" >&2; exit 1; }

target_path="$(cd "$target_path" && pwd -P)"
common_dir="$(git -C "$target_path" rev-parse --path-format=absolute --git-common-dir)"
primary_checkout="$(cd "$common_dir/.." && pwd -P)"

while IFS= read -r candidate_path; do
  [ -n "$candidate_path" ] || continue
  candidate_path="$(cd "$candidate_path" && pwd -P)"
  [ "$candidate_path" != "$target_path" ] || continue

  env_file="$candidate_path/.env.worktree"
  [ -f "$env_file" ] || continue

  frontend_port="$(read_env_value "$env_file" FRONTEND_PORT)"
  backend_port="$(read_env_value "$env_file" BACKEND_PORT)"
  database_name="$(read_env_value "$env_file" POSTGRES_DB)"
  [ -n "$frontend_port" ] || continue
  [ -n "$backend_port" ] || continue
  [ -n "$database_name" ] || continue

  frontend_pid="$(lsof -nP -tiTCP:"$frontend_port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  backend_pid="$(lsof -nP -tiTCP:"$backend_port" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
  if [ -n "$frontend_pid" ] || [ -n "$backend_pid" ]; then
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
      "$candidate_path" "$frontend_port" "${frontend_pid:-none}" \
      "$backend_port" "${backend_pid:-none}" "$database_name"
  fi
done < <(git -C "$primary_checkout" worktree list --porcelain | awk '/^worktree / {sub(/^worktree /, ""); print}')
