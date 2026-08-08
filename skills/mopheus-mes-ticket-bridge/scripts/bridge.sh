#!/usr/bin/env bash
# bridge.sh — main entry point for the mopheus-mes-ticket-bridge skill (v14).
#
# v14 architecture: agent-owned ticket lifecycle. The MES Webhook Handler job
# uses `actionType=assign_agent`, so mes-leader receives the raw envelope
# directly in its trigger context — no transit-ticket placeholder. The bridge
# owns ticket creation / patching / closure itself.
#
# Usage:
#   cat payload.json | scripts/bridge.sh
#   scripts/bridge.sh payload.json
#
# The design does not cross workspaces: there is no --workspace-id flag and no
# WORKSPACE_ID export. The agent's currently active workspace is inherited by
# every `moclaw` call inside the bridge. This avoids bypassing the platform's
# permission scope via hand-typed workspace IDs.
#
# Dispatches by payload.event_type. v14 has no `--transit-ticket` flag.

set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat >&2 <<'USAGE'
Usage: bridge.sh [PAYLOAD_FILE]

Reads an MES webhook payload (event_type + mes_sr_id + payload object) from
PAYLOAD_FILE or stdin, and dispatches to the matching event_*.sh handler.

v14: no transit-ticket, no workspace flag. The bridge owns ticket creation /
patching / closure and uses the agent's active workspace via the moclaw CLI.
USAGE
}

PAYLOAD_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      usage; exit 0
      ;;
    -*)
      printf 'error: unknown flag: %s\n' "$1" >&2
      usage; exit 2
      ;;
    *)
      [[ -z "$PAYLOAD_FILE" ]] || { usage; exit 2; }
      PAYLOAD_FILE="$1"
      shift
      ;;
  esac
done

if [[ -n "$PAYLOAD_FILE" ]]; then
  [[ -f "$PAYLOAD_FILE" ]] || { printf 'error: payload file not found: %s\n' "$PAYLOAD_FILE" >&2; exit 2; }
  PAYLOAD_RAW="$(cat "$PAYLOAD_FILE")"
else
  PAYLOAD_RAW="$(cat)"
fi

printf '%s' "$PAYLOAD_RAW" | jq -e . >/dev/null 2>&1 || {
  printf 'error: payload is not valid JSON\n' >&2; exit 1; }
EVENT_TYPE="$(jq -r '.event_type // empty' <<<"$PAYLOAD_RAW")"
[[ -n "$EVENT_TYPE" ]] || { printf 'error: event_type is required\n' >&2; exit 1; }
MES_SR_ID="$(jq -r '.mes_sr_id // empty' <<<"$PAYLOAD_RAW")"
[[ "$MES_SR_ID" =~ ^[0-9]+$ ]] || { printf 'error: mes_sr_id must be numeric\n' >&2; exit 1; }

case "$EVENT_TYPE" in
  ticket.created)
    exec "$HERE/event_created.sh" "$PAYLOAD_RAW"
    ;;
  ticket.replied)
    exec "$HERE/event_replied.sh" "$PAYLOAD_RAW"
    ;;
  ticket.closed)
    exec "$HERE/event_closed.sh" "$PAYLOAD_RAW"
    ;;
  *)
    printf 'error: unsupported event_type: %s (supported: ticket.created, ticket.replied, ticket.closed)\n' "$EVENT_TYPE" >&2
    exit 2
    ;;
esac
