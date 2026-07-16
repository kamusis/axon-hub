#!/usr/bin/env bash
set -euo pipefail

usage() {
  printf 'Usage: %s --workspace-id WORKSPACE_ID [PAYLOAD_FILE]\n' "$0" >&2
}

workspace_id=''
payload_file=''

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace-id)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      workspace_id="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      usage
      exit 2
      ;;
    *)
      [[ -z "$payload_file" ]] || { usage; exit 2; }
      payload_file="$1"
      shift
      ;;
  esac
done

[[ -n "$workspace_id" ]] || { printf 'error: --workspace-id is required\n' >&2; exit 2; }
command -v moclaw >/dev/null || { printf 'error: moclaw is required\n' >&2; exit 127; }
command -v jq >/dev/null || { printf 'error: jq is required\n' >&2; exit 127; }

if [[ -n "$payload_file" ]]; then
  [[ -f "$payload_file" ]] || { printf 'error: payload file not found: %s\n' "$payload_file" >&2; exit 2; }
  payload_json="$(cat "$payload_file")"
else
  payload_json="$(cat)"
fi

printf '%s' "$payload_json" | jq -e . >/dev/null || {
  printf 'error: payload is not valid JSON\n' >&2
  exit 1
}

event_type="$(jq -r '.event_type // empty' <<<"$payload_json")"
mes_sr_id="$(jq -r '.mes_sr_id // empty' <<<"$payload_json")"
db_type="$(jq -r '.payload.dict.itemName // empty' <<<"$payload_json")"
sr_title="$(jq -r '.payload.title // "MES service request"' <<<"$payload_json")"

[[ -n "$event_type" ]] || {
  printf 'error: event_type is required\n' >&2
  exit 1
}
[[ "$mes_sr_id" =~ ^[0-9]+$ ]] || {
  printf 'error: mes_sr_id must be numeric\n' >&2
  exit 1
}
metadata_filter="$(jq -cn --argjson id "$mes_sr_id" '{mes_sr_id: $id}')"
ticket_json="$(moclaw --workspace-id "$workspace_id" ticket list --metadata-json "$metadata_filter" --limit 100 --output json)"
ticket_count="$(jq 'length' <<<"$ticket_json")"

if (( ticket_count > 1 )); then
  printf '%s\n' "$ticket_json" | jq -r '.[].id' >&2
  printf 'error: multiple tickets match mes_sr_id=%s\n' "$mes_sr_id" >&2
  exit 1
fi

if (( ticket_count == 1 )); then
  ticket_id="$(jq -r '.[0].id' <<<"$ticket_json")"
  database_line=''
  if [[ -n "$db_type" ]]; then
    database_line="- Database: $db_type"
  fi
  comment_content="$(printf '# MES webhook update\n\n- Event: `%s`\n- MES SR: `%s`\n%s\n## Raw payload\n\n```json\n%s\n```\n' "$event_type" "$mes_sr_id" "$database_line" "$(jq . <<<"$payload_json")")"
  printf '%s' "$comment_content" | moclaw --workspace-id "$workspace_id" ticket comment add "$ticket_id" --content-stdin >/dev/null
  printf 'commented ticket %s (mes_sr_id=%s)\n' "$ticket_id" "$mes_sr_id"
  exit 0
fi

[[ -n "$db_type" ]] || {
  printf 'error: payload.dict.itemName is required when creating a new ticket\n' >&2
  exit 1
}

description="$(printf '# MES service request\n\n- MES SR: `%s`\n- Database: `%s`\n\n## Raw payload\n\n```json\n%s\n```\n' "$mes_sr_id" "$db_type" "$(jq . <<<"$payload_json")")"
ticket_id="$(printf '%s' "$description" | moclaw --workspace-id "$workspace_id" ticket create --title "[MES SR#$mes_sr_id] $sr_title" --description-stdin --status todo --output json | jq -r '.id')"
[[ -n "$ticket_id" && "$ticket_id" != 'null' ]] || {
  printf 'error: ticket creation returned no ticket ID\n' >&2
  exit 1
}

moclaw --workspace-id "$workspace_id" ticket metadata set "$ticket_id" --key mes_sr_id --value "$mes_sr_id" --type number
moclaw --workspace-id "$workspace_id" ticket metadata set "$ticket_id" --key db_type --value "$db_type" --type string
printf 'created ticket %s (mes_sr_id=%s, db_type=%s)\n' "$ticket_id" "$mes_sr_id" "$db_type"
