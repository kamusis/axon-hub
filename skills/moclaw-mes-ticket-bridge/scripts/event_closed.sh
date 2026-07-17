#!/usr/bin/env bash
# event_closed.sh — handle MES webhook `ticket.closed` event (v14).
#
# v14: NO transit-ticket concept; no cancel_transit_ticket call.
# Idempotency key: (stateUpdateTime, status). Patches metadata, flips target
# ticket to `done`.
#
# Note on comments: mes-leader (the agent invoking this script) is required by
# its runtime to post a single concise summary on the triggering ticket per
# CLAUDE.md (operation + bridge outcome + hyperlink). Posting another
# "closure record" comment here would create a second comment per closure
# event (observed on MCS-66: bridge record + agent summary = 2). So this
# handler no longer posts a closure-record comment — all closure details are
# preserved in metadata fields (`mes_sr_status`, `mes_sr_status_desc`,
# `mes_sr_closed_at`, `mes_sr_closed_by`, `mes_sr_closure_reason`) and the
# mes-leader summary is the only visible record. If the agent-run ever
# bypasses its summary post, the metadata fields are still authoritative.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib_common.sh
source "$HERE/lib_common.sh"

require_tools

PAYLOAD_RAW="$1"
parse_envelope "$PAYLOAD_RAW" || exit 1

STATE_TIME="$(jq -r '.payload.stateUpdateTime // empty' <<<"$PAYLOAD_JSON")"
STATUS="$(jq -r '.payload.status // empty' <<<"$PAYLOAD_JSON")"
STATUS_DESC="$(jq -r '.payload.statusDesc // empty' <<<"$PAYLOAD_JSON")"
CLOSED_AT="$(jq -r '.payload.closedAt // empty' <<<"$PAYLOAD_JSON")"
CLOSED_BY_NAME="$(jq -r '.payload.closedByName // empty' <<<"$PAYLOAD_JSON")"
REASON_TYPE="$(jq -r '.payload.reasonType // empty' <<<"$PAYLOAD_JSON")"
OTHER_REASON="$(jq -r '.payload.otherReason // empty' <<<"$PAYLOAD_JSON")"

REASON="${REASON_TYPE:-${OTHER_REASON:-未提供}}"
[[ -n "$STATE_TIME" && -n "$STATUS" ]] || {
  printf 'error: ticket.closed requires stateUpdateTime and status\n' >&2; exit 1; }

if ! find_canonical_ticket "$MES_SR_ID"; then
  printf 'error: ticket.closed for %s but no canonical ticket\n' "$(mes_sr_link "$MES_SR_ID")" >&2
  exit 1
fi
TARGET="$CANONICAL_TICKET_ID"

ID_KEY="${STATE_TIME}|${STATUS}"
if [[ "$(idempotency_seen "$TARGET" state_transitions "$ID_KEY")" == "yes" ]]; then
  log "ticket.closed: key=$ID_KEY already recorded; ack dup"
  printf 'duplicate ticket.closed %s for %s — skipped\n' "$ID_KEY" "$(mes_sr_link "$MES_SR_ID")"
  exit 0
fi

# Bridge intentionally posts NO comment here. See file header — mes-leader's
# own summary is the only visible comment per closure event.

md_set "$TARGET" mes_sr_status "$STATUS" number
md_set "$TARGET" mes_sr_status_desc "$STATUS_DESC"
md_set "$TARGET" mes_sr_closed_at "$CLOSED_AT"
md_set "$TARGET" mes_sr_closed_by "$CLOSED_BY_NAME"
md_set "$TARGET" mes_sr_closure_reason "$REASON"
md_set "$TARGET" last_event_type "ticket.closed"
md_set "$TARGET" last_occurred_at "$(jq -r '.occurred_at // empty' <<<"$PAYLOAD_JSON")"
idempotency_record "$TARGET" state_transitions "$ID_KEY"

moclaw ticket status "$TARGET" done >/dev/null
log "flipped ticket $TARGET to done (no closure-record comment — mes-leader summary is the only visible record)"

printf 'closed ticket %s (mes_sr_id=%s, closed_by=%s, comments=no)\n' \
  "$TARGET" "$MES_SR_ID" "$CLOSED_BY_NAME"
