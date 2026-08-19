#!/usr/bin/env bash
# event_replied.sh — handle MES webhook `ticket.replied` event (v14).
#
# Behavior (v14):
#   1. Parse payload; require replyId for idempotency.
#   2. Find canonical ticket by mes_sr_id. Refuse to create one for a reply event.
#   3. Idempotency check by replyId; ack dup if seen.
#   4. Post a comment on the canonical ticket (hyperlink + author + plain-text).
#   5. Update metadata.
#   6. Dispatch the assigned DBA agent via @-mention.
#   7. Wait for the agent run to reach a terminal status (up to 10 minutes).
#   8. Read the latest agent-authored analysis comment.
#   9. Send the analysis as the mes-cli internal reply body (subject to 1h rate-limit).
#
# v14: NO transit-ticket concept; no cancel_transit_ticket call.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=lib_common.sh
source "$HERE/lib_common.sh"

require_tools

PAYLOAD_RAW="$1"
parse_envelope "$PAYLOAD_RAW" || exit 1

REPLY_ID="$(jq -r '.payload.replyId // empty' <<<"$PAYLOAD_JSON")"
[[ -n "$REPLY_ID" ]] || { printf 'error: ticket.replied requires payload.replyId\n' >&2; exit 1; }

if ! find_canonical_ticket "$MES_SR_ID"; then
  printf 'error: ticket.replied for %s but no canonical ticket exists; refusing to create one for a reply event\n' \
    "$(mes_sr_link "$MES_SR_ID")" >&2
  exit 1
fi
TARGET="$CANONICAL_TICKET_ID"

if [[ "$(idempotency_seen "$TARGET" reply "$REPLY_ID")" == "yes" ]]; then
  log "ticket.replied: replyId=$REPLY_ID already patched; ack dup"
  printf 'duplicate ticket.replied replyId=%s for %s — skipped\n' "$REPLY_ID" "$(mes_sr_link "$MES_SR_ID")"
  exit 0
fi

AUTHOR_NAME="$(jq -r '.payload.authorName // empty' <<<"$PAYLOAD_JSON")"
CREATED_AT="$(jq -r '.payload.createdAt // empty' <<<"$PAYLOAD_JSON")"
CONTENT_HTML="$(jq -r '.payload.content // ""' <<<"$PAYLOAD_JSON")"
ATTACHMENT_URLS="$(jq -r '.payload.attachments // [] | map(.url) | .[]' <<<"$PAYLOAD_JSON")"

PLAIN_CONTENT="$(printf '%s' "$CONTENT_HTML" | sed -E 's/<[^>]+>//g' | sed -E 's/&lt;/</g;s/&gt;/>/g;s/&amp;/\&/g;s/&quot;/"/g;s/&#39;/'\''/g')"

# Resolve the DBA agent FIRST so we can fold the @-mention into the same
# comment as the customer reply. Posting two separate comments per MES
# reply was the v14.0/14.1 behaviour — see MCS-68 ticket ca7e78ff.
DBA_AGENT_ID=""
DBA_AGENT_NAME=""
ROUTING_SOURCE=""
if RESOLVED="$(resolve_dba_agent_for_reply "$TARGET" 2>/dev/null)"; then
  DBA_AGENT_ID="${RESOLVED%%|*}"
  ROUTING_SOURCE="${RESOLVED##*|}"
  DBA_AGENT_NAME="${RESOLVED#*|}"
  DBA_AGENT_NAME="${DBA_AGENT_NAME%|*}"
  log "reply routing: source=$ROUTING_SOURCE agent=$DBA_AGENT_ID label=$DBA_AGENT_NAME"
else
  md_set "$TARGET" last_dispatch_status "no_route"
  log "no DBA agent resolvable for $TARGET (mes_sr_db_type=$(md_get "$TARGET" mes_sr_db_type), child_assignee_agent=$(md_get "$TARGET" child_assignee_agent))"
fi

ATTACHMENT_SECTION=""
if [[ -n "$ATTACHMENT_URLS" ]]; then
  ATTACHMENT_SECTION="

### Attachments

${ATTACHMENT_URLS}"
fi

DISPATCH_SECTION=""
if [[ -n "$DBA_AGENT_ID" ]]; then
  REPLY_PREVIEW="$(printf '%s' "$PLAIN_CONTENT" | head -c 200 | tr -d '\r')"
  DISPATCH_SECTION="$(cat <<EOF


---

**DBA dispatch**

客户已回复(replyId=${REPLY_ID}),@[@${DBA_AGENT_NAME}](mention://agent/${DBA_AGENT_ID}) 请基于新证据继续只读分析,并把结论/方案直接贴在本工单(mes-leader 会把这条结论原文回写到 MES):

> ${REPLY_PREVIEW}

如需更多信息(慢 SQL、计划、alert.log 等),在本工单追问或由 mes-leader 通过 mes-cli 内部回复。
EOF
)"
fi

# Build the single merged comment. The @-mention inside DISPATCH_SECTION
# enqueues the agent run, so this comment's ID is also the triggerCommentId
# we wait on below.
MERGED_COMMENT="$(cat <<EOF
$(mes_sr_link "$MES_SR_ID") — customer reply

- author: $AUTHOR_NAME
- createdAt: $CREATED_AT
- replyId: $REPLY_ID

### HTML (verbatim)

\`\`\`html
$CONTENT_HTML
\`\`\`

### Plain-text

$PLAIN_CONTENT${ATTACHMENT_SECTION}${DISPATCH_SECTION}
EOF
)"

DBA_DISPATCH_RESULT="no-dispatch"
DISPATCH_COMMENT_ID="$(printf '%s' "$MERGED_COMMENT" | mopheus \
  ticket comment add "$TARGET" --content-stdin --output json 2>/dev/null | jq -r '.id // empty')"
if [[ -n "$DBA_AGENT_ID" ]]; then
  if [[ -n "$DISPATCH_COMMENT_ID" ]]; then
    DBA_DISPATCH_RESULT="dispatched:${DBA_AGENT_NAME}"
    log "posted merged reply+dispatch comment to ticket $TARGET (id=$DISPATCH_COMMENT_ID, agent=$DBA_AGENT_NAME)"
  else
    DBA_DISPATCH_RESULT="dispatch_failed"
    log "posted merged comment to ticket $TARGET but failed to capture comment id (agent=$DBA_AGENT_NAME)"
  fi
elif [[ -n "$DISPATCH_COMMENT_ID" ]]; then
  log "posted customer reply comment to ticket $TARGET (no dispatch, id=$DISPATCH_COMMENT_ID)"
fi

md_set "$TARGET" last_reply_id "$REPLY_ID"
md_set "$TARGET" last_reply_at "$CREATED_AT"
md_set "$TARGET" last_reply_author "$AUTHOR_NAME"
md_set "$TARGET" last_event_type "ticket.replied"
md_set "$TARGET" last_occurred_at "$(jq -r '.occurred_at // empty' <<<"$PAYLOAD_JSON")"
idempotency_record "$TARGET" reply "$REPLY_ID"

AGENT_ANALYSIS=""
AGENT_RUN_WAIT_RESULT="no-wait"
if [[ -n "$DBA_AGENT_ID" && -n "$DISPATCH_COMMENT_ID" ]]; then
  log "waiting for DBA agent run triggered by $DISPATCH_COMMENT_ID (timeout=1500s)"
  if wait_for_agent_run "$TARGET" "$DISPATCH_COMMENT_ID" 1500; then
    AGENT_RUN_WAIT_RESULT="completed"
    AGENT_ANALYSIS="$(get_latest_agent_comment "$TARGET" "$DBA_AGENT_ID")"
    if [[ -n "$AGENT_ANALYSIS" ]]; then
      log "captured agent analysis ($(printf '%s' "$AGENT_ANALYSIS" | wc -c) bytes) from agent $DBA_AGENT_ID"
    else
      log "no analysis comment authored by $DBA_AGENT_ID found after run completion"
    fi
  else
    AGENT_RUN_WAIT_RESULT="timeout"
    log "agent run did not complete within timeout; will NOT send placeholder to MES"
  fi
fi

MES_CLI_RESULT=""
if [[ -z "$AGENT_ANALYSIS" ]]; then
  # No agent analysis captured — refuse to send placeholder to MES.
  MES_CLI_RESULT="skipped_no_agent_analysis"
  md_append_csv "$TARGET" pending_mes_cli_no_analysis "reply:${REPLY_ID}:$(date +%s)"
  log "no DBA analysis captured (agent-wait=$AGENT_RUN_WAIT_RESULT); skipping mes-cli (placeholder forbidden)"
elif ! command -v mes >/dev/null 2>&1; then
  MES_CLI_RESULT="mes-cli-not-available"
  log "mes-cli not on PATH; cannot send DBA analysis to MES"
elif mes sr reply "$MES_SR_ID" --internal --markdown "$AGENT_ANALYSIS" >/dev/null 2>&1; then
  # ticket.replied sends ALWAYS (no bridge-side rate-limit). Idempotency
  # on `seen_reply_ids` (above) already prevents duplicate sends; the
  # previous 1h rate-limit was wrong design — when a customer replied
  # twice within an hour, the second reply's analysis was silently
  # deferred and the deferred-list was never flushed (see
  # pending_mes_replies_window_collect on MCS-59 replyIds 751/752). The
  # only way to recover those today is manual mes-cli; once this code
  # lands in the canonical skill, future ticket.replied events send
  # each new analysis immediately.
  mes_cli_record_send "$TARGET" "$MES_SR_ID" "$AGENT_ANALYSIS" "$REPLY_ID"
  MES_CLI_RESULT="sent"
  log "mes sr reply sent for mes_sr_id=$MES_SR_ID (body from agent analysis, markdown)"
else
  MES_CLI_RESULT="send_failed"
  log "mes sr reply failed for mes_sr_id=$MES_SR_ID"
fi

printf 'patched ticket %s (mes_sr_id=%s, replyId=%s, agent-wait=%s, mes-cli=%s, dba=%s)\n' \
  "$TARGET" "$MES_SR_ID" "$REPLY_ID" "$AGENT_RUN_WAIT_RESULT" "$MES_CLI_RESULT" "$DBA_DISPATCH_RESULT"

# Non-zero exit if mes-cli was meant to send analysis but couldn't.
if [[ "$MES_CLI_RESULT" == "skipped_no_agent_analysis" || "$MES_CLI_RESULT" == "send_failed" ]]; then
  exit 4
fi