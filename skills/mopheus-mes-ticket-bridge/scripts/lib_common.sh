#!/usr/bin/env bash
# lib_common.sh — shared helpers for MES event handlers (v14).
# v14: removed cancel_transit_ticket (no transit concept).
# v14: removed WORKSPACE_ID guard — the bridge does not accept --workspace-id;
# every `mopheus` call here inherits the agent's active workspace.

set -euo pipefail

# ---------------- Constants ----------------

# Static agent ID table.
AGENT_MYSQL="a9b888e9-ea13-4189-890b-55eae1194cbc"
AGENT_POSTGRESQL="fce4983b-e771-46a4-bb59-3c22a695aeda"
AGENT_ORACLE="35c3940d-077b-44eb-b152-c4a80d827375"

MES_SR_URL_FMT="https://support.enmotech.com/service/request/%d"

# ---------------- Tooling guards ----------------

require_tools() {
  command -v mopheus >/dev/null || { printf 'error: mopheus is required\n' >&2; exit 127; }
  command -v jq >/dev/null     || { printf 'error: jq is required\n' >&2; exit 127; }
  command -v mes >/dev/null 2>&1 || printf 'warn: mes (mes-cli) not in PATH; outbound replies will be skipped\n' >&2 || true
}

# ---------------- Payload parsing ----------------

parse_envelope() {
  local input_json="$1"
  printf '%s' "$input_json" | jq -e . >/dev/null 2>&1 || {
    printf 'error: payload is not valid JSON\n' >&2; return 1
  }
  EVENT_TYPE="$(printf '%s' "$input_json" | jq -r '.event_type // empty')"
  MES_SR_ID="$(printf '%s' "$input_json" | jq -r '.mes_sr_id // empty')"
  [[ -n "$EVENT_TYPE" ]] || { printf 'error: event_type is required\n' >&2; return 1; }
  [[ "$MES_SR_ID" =~ ^[0-9]+$ ]] || { printf 'error: mes_sr_id must be numeric\n' >&2; return 1; }
  PAYLOAD_JSON="$input_json"
}

db_type_from_payload() {
  jq -r '.payload.dict.itemName // empty' <<<"$PAYLOAD_JSON"
}

mes_sr_link() {
  local id="$1"
  printf '[MES SR#%s](%s)' "$id" "$(printf "$MES_SR_URL_FMT" "$id")"
}

mes_sr_title() {
  printf '[MES SR#%s]' "$1"
}

# ---------------- Ticket lookup ----------------

find_canonical_ticket() {
  local sr_id="$1"
  local filter
  filter="$(jq -cn --argjson id "$sr_id" '{mes_sr_id: $id}')"
  local ticket_json
  ticket_json="$(mopheus ticket list --metadata-json "$filter" --limit 10 --output json)"
  local count
  count="$(jq 'length' <<<"$ticket_json")"
  if (( count > 1 )); then
    printf 'error: multiple tickets match mes_sr_id=%s — refusing to guess\n' "$sr_id" >&2
    printf '%s\n' "$ticket_json" | jq -r '.[].id' >&2
    return 2
  fi
  if (( count == 0 )); then
    CANONICAL_TICKET_ID=""
    return 1
  fi
  CANONICAL_TICKET_ID="$(jq -r '.[0].id' <<<"$ticket_json")"
}

# ---------------- Metadata ----------------

md_get() {
  local ticket="$1" key="$2"
  local out
  out="$(mopheus ticket metadata list "$ticket" --output json 2>/dev/null || true)"
  jq -r --arg k "$key" '.[$k] // empty' <<<"$out"
}

md_set() {
  local ticket="$1" key="$2" value="$3" type="${4:-string}"
  mopheus ticket metadata set "$ticket" \
    --key "$key" --value "$value" --type "$type" >/dev/null
}

md_append_csv() {
  local ticket="$1" key="$2" value="$3"
  local current
  current="$(md_get "$ticket" "$key")"
  if [[ ",$current," == *",$value,"* ]]; then
    return 0
  fi
  if [[ -z "$current" ]]; then
    md_set "$ticket" "$key" "$value" string
  else
    md_set "$ticket" "$key" "${current},${value}" string
  fi
}

# ---------------- Idempotency ----------------

idempotency_seen() {
  local ticket="$1" event="$2" key="$3"
  local seen
  seen="$(md_get "$ticket" "seen_${event}_ids")"
  [[ ",$seen," == *",$key,"* ]] && echo yes || echo no
}

idempotency_record() {
  local ticket="$1" event="$2" key="$3"
  md_append_csv "$ticket" "seen_${event}_ids" "$key"
}

# ---------------- Agent run polling ----------------

# Wait for the agent run triggered by a specific dispatch comment.
wait_for_agent_run() {
  local ticket="$1" trigger_comment_id="$2" timeout="${3:-1500}"
  local deadline=$(( $(date +%s) + timeout ))
  while (( $(date +%s) < deadline )); do
    local runs_json
    runs_json="$(mopheus ticket runs "$ticket" --output json 2>/dev/null || echo '[]')"
    local status
    status="$(jq -r --arg c "$trigger_comment_id" \
      'map(select(.triggerCommentId == $c)) | (.[0].status // empty)' <<<"$runs_json" 2>/dev/null || true)"
    if [[ "$status" == "3" ]]; then
      return 0
    fi
    sleep 5
  done
  return 1
}

# Wait for the latest agent run by a specific agent ID.
wait_for_agent_by_id() {
  local ticket="$1" agent_id="$2" timeout="${3:-1500}"
  local deadline=$(( $(date +%s) + timeout ))
  while (( $(date +%s) < deadline )); do
    local runs_json
    runs_json="$(mopheus ticket runs "$ticket" --output json 2>/dev/null || echo '[]')"
    local status
    status="$(jq -r --arg a "$agent_id" '
      map(select(.agentId == $a)) | sort_by(.startedAt) | .[-1].status // empty
    ' <<<"$runs_json" 2>/dev/null || true)"
    if [[ "$status" == "3" ]]; then
      return 0
    fi
    sleep 5
  done
  return 1
}

# Read the most recent comment authored by a specific agent.
get_latest_agent_comment() {
  local ticket="$1" agent_id="$2"
  local comments_json
  comments_json="$(mopheus ticket comment list "$ticket" --output json 2>/dev/null || echo '')"
  tail -n +2 <<<"$comments_json" | jq -r --arg a "$agent_id" '
    map(select(.authorType == 1 and .authorId == $a))
    | sort_by(.createdAt)
    | if length == 0 then "" else .[-1].content end
  ' 2>/dev/null
}

# ---------------- Routing ----------------

route_dba_agent() {
  local db_type="$1"
  local lc
  lc="$(printf '%s' "$db_type" | tr '[:upper:]' '[:lower:]')"
  case "$lc" in
    mysql|mysql8|aurora|txsql|rds)
      printf '%s|%s' "$AGENT_MYSQL" "MySQL"
      ;;
    postgresql|pg|greenplum)
      printf '%s|%s' "$AGENT_POSTGRESQL" "PostgreSQL"
      ;;
    oracle|oraclerac|ogg)
      printf '%s|%s' "$AGENT_ORACLE" "Oracle"
      ;;
    *)
      printf '%s|%s' "$AGENT_MYSQL" "unknown→MySQL" >&2
      printf '%s|%s|fallback' "$AGENT_MYSQL" "MySQL"
      ;;
  esac
}

# ---------------- Reply-time DBA resolver ----------------
#
# resolve_dba_agent_for_reply <ticket_id>
#
# 3-tier fallback to pick the DBA agent id for a `ticket.replied` event. We
# prefer the agent that `ticket.created` already chose (so create-time and
# reply-time routing agree), and only widen the search if that label is
# unrecognized.
#
#   1. `child_assignee_agent` metadata → mapped to AGENT_MYSQL /
#      AGENT_POSTGRESQL / AGENT_ORACLE by name (case-insensitive). Labels
#      written by event_created.sh: "MySQL", "PostgreSQL", "Oracle", and
#      "fallback" (the default branch of route_dba_agent for unknown db_type).
#      "fallback" is NOT trusted here — it never carries an agent id, so it
#      falls through to tier 2 (which re-runs route_dba_agent and resolves
#      it to AGENT_MYSQL).
#   2. `route_dba_agent($mes_sr_db_type)` → already has its own unknown→
#      MySQL fallback, so this tier also handles db_types the label table
#      doesn't list (zDBM, TiDB, MariaDB, …).
#   3. The ticket's current `assigneeId` from `mopheus ticket get` — last
#      resort. This is whatever the ticket was last assigned to, even if it
#      is no DBA agent (we still log a warning).
#
# Output: "<agent_id>|<label>|<source>" — three pipe-separated fields, where
# source ∈ {child_assignee_agent, route_dba_agent, assignee_id}.
# Returns 0 on success, 1 if all three tiers fail (caller should skip dispatch
# and write `last_dispatch_status=no_route`).
resolve_dba_agent_for_reply() {
  local ticket="$1"
  local child_label
  child_label="$(md_get "$ticket" child_assignee_agent)"
  case "${child_label,,}" in
    mysql)
      printf '%s|%s|child_assignee_agent' "$AGENT_MYSQL" "$child_label"
      return 0
      ;;
    postgresql|postgres|pg)
      printf '%s|%s|child_assignee_agent' "$AGENT_POSTGRESQL" "$child_label"
      return 0
      ;;
    oracle)
      printf '%s|%s|child_assignee_agent' "$AGENT_ORACLE" "$child_label"
      return 0
      ;;
  esac

  local db_type routed rid rlabel
  db_type="$(md_get "$ticket" mes_sr_db_type)"
  if [[ -n "$db_type" ]]; then
    routed="$(route_dba_agent "$db_type" 2>/dev/null || true)"
    rid="${routed%%|*}"
    rlabel="${routed##*|}"
    if [[ -n "$rid" && "$rid" =~ ^[0-9a-fA-F-]{36}$ ]]; then
      printf '%s|%s|route_dba_agent' "$rid" "$rlabel"
      return 0
    fi
  fi

  local current_assignee
  current_assignee="$(mopheus ticket get "$ticket" --output json 2>/dev/null \
    | jq -r '.assigneeId // empty' 2>/dev/null || true)"
  if [[ -n "$current_assignee" && "$current_assignee" =~ ^[0-9a-fA-F-]{36}$ ]]; then
    printf '%s|%s|assignee_id' "$current_assignee" "current-assignee"
    return 0
  fi

  return 1
}

# ---------------- mes-cli rate-limit ----------------

mes_cli_rate_decision() {
  local ticket="$1"
  local last_at pending_count
  last_at="$(md_get "$ticket" last_internal_reply_at)"
  pending_count="$(md_get "$ticket" pending_mes_replies_count)"
  pending_count="${pending_count:-0}"
  if [[ -z "$last_at" ]]; then
    echo "send (no prior)"
    return 0
  fi
  local last_epoch now_epoch
  last_epoch="$(date -d "$last_at" +%s 2>/dev/null || echo 0)"
  now_epoch="$(date +%s)"
  if (( now_epoch - last_epoch >= 3600 )); then
    echo "send (window elapsed)"
    return 0
  fi
  echo "defer (window not elapsed, ${pending_count} pending)"
  return 1
}

mes_cli_record_send() {
  local ticket="$1" target_sr_id="$2" body="$3" reply_ids_csv="$4"
  local now sha
  now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  sha="$(printf '%s' "$body" | sha256sum | cut -c1-16)"
  md_set "$ticket" last_internal_reply_at "$now"
  md_set "$ticket" last_internal_reply_target_id "$target_sr_id"
  md_set "$ticket" last_internal_reply_text_sha "$sha"
  md_set "$ticket" last_internal_reply_covers_replyids "$reply_ids_csv"
  md_set "$ticket" pending_mes_replies_count "0" number
  md_set "$ticket" pending_mes_replies_window_collect ""
}

mes_cli_record_defer() {
  local ticket="$1" new_reply_id="$2"
  local current count_str count_num
  current="$(md_get "$ticket" pending_mes_replies_window_collect)"
  if [[ -z "$current" ]]; then
    md_set "$ticket" pending_mes_replies_window_collect "$new_reply_id"
  else
    md_set "$ticket" pending_mes_replies_window_collect "${current},${new_reply_id}"
  fi
  count_str="$(md_get "$ticket" pending_mes_replies_count || true)"
  count_num="${count_str:-0}"
  count_num=$((count_num + 1))
  md_set "$ticket" pending_mes_replies_count "$count_num" number
}

# ---------------- Logging ----------------

log() { printf '[bridge] %s\n' "$*" >&2; }