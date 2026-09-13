#!/usr/bin/env bash
# Refresh MES CLI token by logging into support.enmotech.com with stored credentials
# and writing the returned Bearer token into the mes-cli target profile (default: kamus).
#
# Credentials lookup order:
#   1. Environment variables MES_USER (or MES_PHONE) and MES_PASSWORD
#   2. File specified by MES_ENV_FILE
#   3. ~/.mes/token.env
#
# Exit codes:
#   0 — token refreshed and verified
#   1 — login API did not return 200
#   2 — no Bearer token in Authorization header
#   3 — mes-cli verification failed after write
#   4 — dependency or required credential missing

set -euo pipefail

# Auto-source credentials file if credentials not yet in environment
if [[ -z "${MES_USER:-}" && -z "${MES_USERNAME:-}" && -z "${MES_PHONE:-}" ]] || [[ -z "${MES_PASSWORD:-}" ]]; then
  if [[ -n "${MES_ENV_FILE:-}" && -f "${MES_ENV_FILE}" ]]; then
    set -a; . "${MES_ENV_FILE}"; set +a
  elif [[ -f "${HOME}/.mes/token.env" ]]; then
    set -a; . "${HOME}/.mes/token.env"; set +a
  fi
fi

USER_ID="${MES_USER:-${MES_USERNAME:-${MES_PHONE:-}}}"
if [[ -z "$USER_ID" ]]; then
  echo "ERROR: MES_USER is required (set via env var, MES_ENV_FILE, or ~/.mes/token.env)" >&2
  exit 4
fi

PASSWORD="${MES_PASSWORD:?MES_PASSWORD is required (set via env var, MES_ENV_FILE, or ~/.mes/token.env)}"
PROFILE="${MES_PROFILE:-kamus}"
HOST="${MES_HOST_BASE:-https://support.enmotech.com}"

# Pre-flight: verify required binaries exist on PATH
command -v mes >/dev/null 2>&1 || { echo "ERROR: mes binary not found on PATH"; exit 4; }
command -v curl >/dev/null 2>&1 || { echo "ERROR: curl missing"; exit 4; }
command -v awk >/dev/null 2>&1 || { echo "ERROR: awk missing"; exit 4; }

# Step 1: login → capture Authorization header
TMP_HEADERS="$(mktemp)"
TMP_BODY="$(mktemp)"
trap 'rm -f "$TMP_HEADERS" "$TMP_BODY"' EXIT

# Build JSON body via printf %s to safely handle password special chars (#, $, \, ", etc.)
LOGIN_BODY=$(printf '%s' "{\"bizType\":\"mes\",\"phoneNum\":\"$USER_ID\",\"password\":\"$PASSWORD\",\"smsCode\":\"\"}")
HTTP_CODE=$(printf '%s' "$LOGIN_BODY" | curl -s -D "$TMP_HEADERS" -o "$TMP_BODY" -w "%{http_code}" \
  -X POST \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/plain, */*' \
  --data-binary @- \
  "${HOST}/api/login")
unset LOGIN_BODY

if [[ "$HTTP_CODE" != "200" ]]; then
  echo "ERROR: login API returned HTTP $HTTP_CODE; body:"
  cat "$TMP_BODY"
  exit 1
fi

# Step 2: extract Bearer token (case-insensitive header lookup)
TOKEN=$(awk 'BEGIN{IGNORECASE=1} /^authorization:/ {sub(/^authorization:[[:space:]]*/,""); sub(/[\r\n]/,""); print; exit}' "$TMP_HEADERS")

if [[ -z "$TOKEN" || "$TOKEN" != "Bearer "* ]]; then
  echo "ERROR: no Bearer token in Authorization header"
  cat "$TMP_HEADERS"
  exit 2
fi

# Step 3: write token to target profile via mes-cli
mes auth switch --profile "$PROFILE" >/dev/null 2>&1 || true
MES_HOST="${HOST}/esapi" mes auth login --with-token "$TOKEN" --profile "$PROFILE" >/dev/null

# Step 4: verify the new token is accepted by mes-cli itself
STATUS_JSON=$(MES_HOST="${HOST}/esapi" mes -o json auth status 2>&1) || true
if echo "$STATUS_JSON" | grep -q '"tokenValid": true'; then
  echo "OK: token refreshed and verified for profile=$PROFILE"
  exit 0
else
  echo "ERROR: token written but verification failed"
  echo "$STATUS_JSON"
  exit 3
fi
