#!/usr/bin/env bash
# event_created.sh — handle MES webhook `ticket.created` event (v14).
#
# Behavior (v14, agent-owned):
#   1. Parse payload; require dict.itemName for routing.
#   2. Idempotency: if a canonical ticket already exists for mes_sr_id, ack dup.
#   3. Otherwise, CREATE the canonical Mopheus ticket (no transit placeholder):
#        - title: "[MES SR#<id>] <payload.title>"
#        - description: structured Source / Extracted / Plain-text / Routing
#        - priority: mapped from typeLabel
#        - assignee: routed DBA agent
#        - status: todo (so the DBA agent's task fires immediately)
#        - metadata: mes_sr_id, mes_sr_company, mes_sr_db_type, etc.
#   4. Wait for the auto-enqueued DBA agent run (≤10 min) and capture its first
#      comment as the analysis body.
#   5. Send the analysis as the mes-cli internal reply (subject to 1h rate-limit).
#
# Exit codes: 0 = created or dup-acked, 1 = validation error.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib_common.sh
source "$HERE/lib_common.sh"

require_tools

PAYLOAD_RAW="$1"
parse_envelope "$PAYLOAD_RAW" || exit 1

# Idempotency: check for existing canonical ticket before creating.
if find_canonical_ticket "$MES_SR_ID" 2>/dev/null; then
  log "ticket.created: mes_sr_id=$MES_SR_ID already onboarded as $CANONICAL_TICKET_ID; ack dup"
  printf 'duplicate ticket.created for %s — already onboarded as %s. Skipped.\n' \
    "$(mes_sr_link "$MES_SR_ID")" "$CANONICAL_TICKET_ID"
  exit 0
fi

# Required: dict.itemName (db_type) for routing + metadata.
DB_TYPE="$(db_type_from_payload)"
if [[ -z "$DB_TYPE" ]]; then
  printf 'error: ticket.created requires payload.dict.itemName\n' >&2
  exit 1
fi

TITLE_RAW="$(jq -r '.payload.title // ""' <<<"$PAYLOAD_JSON")"
COMPANY="$(jq -r '.payload.companyName // ""' <<<"$PAYLOAD_JSON")"
TYPE_LABEL="$(jq -r '.payload.typeLabel // ""' <<<"$PAYLOAD_JSON")"
STATUS_DESC="$(jq -r '.payload.statusDesc // ""' <<<"$PAYLOAD_JSON")"
OCCURRED_AT="$(jq -r '.occurred_at // ""' <<<"$PAYLOAD_JSON")"
CONTENT_HTML="$(jq -r '.payload.content // ""' <<<"$PAYLOAD_JSON")"

PRIORITY="normal"
case "$TYPE_LABEL" in
  P0*|P1*) PRIORITY="urgent" ;;
  P2*)     PRIORITY="high" ;;
  P3*)     PRIORITY="normal" ;;
  P4*|P5*) PRIORITY="low" ;;
esac

ROUTING="$(route_dba_agent "$DB_TYPE")"
DBA_AGENT_ID="${ROUTING%%|*}"
DBA_LABEL="${ROUTING##*|}"

PLAIN_CONTENT="$(printf '%s' "$CONTENT_HTML" | sed -E 's/<[^>]+>//g' | sed -E 's/&lt;/</g;s/&gt;/>/g;s/&amp;/\&/g;s/&quot;/"/g;s/&#39;/'\''/g')"
IMAGE_URLS="$(printf '%s' "$CONTENT_HTML" | grep -oE 'https?://[^"'"'"' ]+\.(png|jpg|jpeg|webp|gif)' | sort -u || true)"

DESCRIPTION="$(cat <<EOF
# $(mes_sr_title "$MES_SR_ID") $TITLE_RAW

## Source

- **MES SR**: $(mes_sr_link "$MES_SR_ID")
- **mes_sr_id**: \`$MES_SR_ID\`
- **event_type**: \`ticket.created\`
- **occurred_at**: \`$OCCURRED_AT\`
- **company**: $COMPANY
- **db_type**: \`$DB_TYPE\`
- **type**: \`$TYPE_LABEL\` ($STATUS_DESC)

## Extracted fields

\`\`\`yaml
$(jq -r '.payload | to_entries | map("  " + (.key + ": " + (.value | tostring))) | .[]' <<<"$PAYLOAD_JSON")
\`\`\`

## Plain-text content

$PLAIN_CONTENT

## Sub-issues

Per sub-issue (numbered in plain-text content): phenomenon, evidence, MES-suggested remediation (verbatim), read-only investigation checklist.

## Routing

- engine: \`$DB_TYPE\`
- target agent: \`$DBA_LABEL\` ($DBA_AGENT_ID)
- rationale: matched on \`payload.dict.itemName\`

## Handover requirements

- scope, affected objects, lock/downtime risk
- replication/backup impact, exact rollback steps
- verification queries before/after any change
- read-only first
EOF
)"

TICKET_TITLE="$(mes_sr_title "$MES_SR_ID") $TITLE_RAW"

# v14: create canonical ticket (no transit placeholder).
CREATE_OUT="$(printf '%s' "$DESCRIPTION" | mopheus \
  ticket create \
  --title "$TICKET_TITLE" \
  --description-stdin \
  --priority "$PRIORITY" \
  --output json 2>/dev/null || true)"
TICKET_ID="$(jq -r '.id // empty' <<<"$CREATE_OUT" 2>/dev/null || true)"
if [[ -z "$TICKET_ID" ]]; then
  printf 'error: failed to create canonical ticket for mes_sr_id=%s\n' "$MES_SR_ID" >&2
  exit 1
fi
log "created canonical ticket $TICKET_ID (mes_sr_id=$MES_SR_ID)"

mopheus ticket assign "$TICKET_ID" \
  --agent-id "$DBA_AGENT_ID" >/dev/null
log "assigned $DBA_LABEL agent to ticket $TICKET_ID"

mopheus ticket status "$TICKET_ID" todo >/dev/null
log "moved ticket $TICKET_ID to todo"

md_set "$TICKET_ID" mes_sr_id "$MES_SR_ID" number
md_set "$TICKET_ID" mes_sr_company "$COMPANY"
md_set "$TICKET_ID" mes_sr_db_type "$DB_TYPE"
md_set "$TICKET_ID" mes_sr_type_label "$TYPE_LABEL"
md_set "$TICKET_ID" child_assignee_agent "$DBA_LABEL"
md_set "$TICKET_ID" child_ticket_id "$TICKET_ID"
md_set "$TICKET_ID" last_event_type "ticket.created"
md_set "$TICKET_ID" last_occurred_at "$OCCURRED_AT"

if [[ -n "$IMAGE_URLS" ]]; then
  md_set "$TICKET_ID" image_ocr "pending; URLs: $IMAGE_URLS"
fi

# Close the loop: wait for DBA agent, then mes-cli internal reply.
AGENT_ANALYSIS=""
AGENT_RUN_WAIT_RESULT="no-wait"
log "waiting for $DBA_LABEL agent run on ticket $TICKET_ID (timeout=1500s, auto-enqueued by platform)"
if wait_for_agent_by_id "$TICKET_ID" "$DBA_AGENT_ID" 1500; then
  AGENT_RUN_WAIT_RESULT="completed"
  AGENT_ANALYSIS="$(get_latest_agent_comment "$TICKET_ID" "$DBA_AGENT_ID")"
  if [[ -n "$AGENT_ANALYSIS" ]]; then
    log "captured $DBA_LABEL analysis ($(printf '%s' "$AGENT_ANALYSIS" | wc -c) bytes)"
  else
    log "no analysis comment authored by $DBA_LABEL after run completion"
  fi
else
  AGENT_RUN_WAIT_RESULT="timeout"
  log "$DBA_LABEL agent run did not complete within timeout; will NOT send placeholder to MES"
fi

MES_CLI_RESULT=""
if [[ -z "$AGENT_ANALYSIS" ]]; then
  # No agent analysis captured — refuse to send placeholder to MES.
  MES_CLI_RESULT="skipped_no_agent_analysis"
  md_append_csv "$TICKET_ID" pending_mes_cli_no_analysis "created:$(date +%s)"
  log "no $DBA_LABEL analysis captured (agent-wait=$AGENT_RUN_WAIT_RESULT); skipping mes-cli (placeholder forbidden)"
elif ! command -v mes >/dev/null 2>&1; then
  MES_CLI_RESULT="mes-cli-not-available"
  log "mes-cli not on PATH; cannot send $DBA_LABEL analysis to MES"
elif ! mes_cli_rate_decision "$TICKET_ID" >/dev/null; then
  mes_cli_record_defer "$TICKET_ID" "created:$(date +%s)"
  MES_CLI_RESULT="deferred"
  log "mes sr reply deferred (window not elapsed) for mes_sr_id=$MES_SR_ID"
elif mes sr reply "$MES_SR_ID" --internal --markdown "$AGENT_ANALYSIS" >/dev/null 2>&1; then
  mes_cli_record_send "$TICKET_ID" "$MES_SR_ID" "$AGENT_ANALYSIS" "created:$(date +%s)"
  MES_CLI_RESULT="sent"
  log "mes sr reply sent for mes_sr_id=$MES_SR_ID (body from $DBA_LABEL analysis, markdown)"
else
  MES_CLI_RESULT="send_failed"
  log "mes sr reply failed for mes_sr_id=$MES_SR_ID"
fi

printf 'created ticket %s (mes_sr_id=%s, db_type=%s, routed to %s, agent-wait=%s, mes-cli=%s)\n' \
  "$TICKET_ID" "$MES_SR_ID" "$DB_TYPE" "$DBA_LABEL" "$AGENT_RUN_WAIT_RESULT" "$MES_CLI_RESULT"

# Non-zero exit if mes-cli was meant to send analysis but couldn't.
if [[ "$MES_CLI_RESULT" == "skipped_no_agent_analysis" || "$MES_CLI_RESULT" == "send_failed" ]]; then
  exit 4
fi
