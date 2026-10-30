#!/usr/bin/env bash
# ==============================================================================
# swr_push_blob.sh — upload one blob to Huawei Cloud SWR.
#
# SWR's registry-v2 upload API is used with a Bearer token obtained from
# /swr/auth/v2/registry/auth/. Two upload paths are implemented because the
# chunked session path has a hard per-session byte cap on this network:
#
#   * chunked  — POST session -> PATCH Content-Range -> PUT ?digest=
#                Works for blobs up to ~6 MiB (the session rejects anything
#                beyond that with HTTP 400 DIGEST_INVALID).
#   * monolithic — POST session -> single PUT carrying the whole body.
#                Required for larger blobs; a 24 MiB layer completes in one
#                request.
#
# The path is chosen automatically from the blob size. Both paths retry with a
# fresh session, so a transient failure never leaves a half-used session behind.
#
# Usage: swr_push_blob.sh <local-file> <swr-repo> <sha256-digest>
# ==============================================================================
set -uo pipefail

FILE="${1:?local file required}"
REPO="${2:?swr repo required}"
DIGEST="${3:?sha256 digest required}"

SWR_REGISTRY="${SWR_REGISTRY:-swr.cn-north-4.myhuaweicloud.com}"
# SWR_BASE allows pointing at a plain-HTTP endpoint for testing.
SWR_BASE="${SWR_BASE:-https://${SWR_REGISTRY}}"
SWR_USER="${HUAWEICLOUD_SWR_USER:-${SWR_USER:-}}"
SWR_PASSWORD="${HUAWEICLOUD_SWR_PASSWORD:-${SWR_PASSWORD:-}}"

# Blobs larger than this are uploaded with a single PUT. Set to 0 to always use monolithic PUT.
MONOLITHIC_THRESHOLD="${SWR_MONOLITHIC_THRESHOLD:-0}"

# Chunk size for the chunked path. SWR caps a session at ~6 MiB regardless, so
# this only needs to stay well under that limit.
CHUNK_SIZE="${SWR_CHUNK_SIZE:-262144}"

UPLOAD_TIMEOUT="${SWR_UPLOAD_TIMEOUT:-3600}"
ATTEMPTS="${SWR_UPLOAD_ATTEMPTS:-4}"
SCOPE="repository:${REPO}:push,pull"

SIZE=$(stat -c %s "$FILE")

[[ -s "$FILE" ]] || { echo "[ERROR] missing or empty blob file: $FILE" >&2; exit 1; }
[[ -n "$SWR_USER" && -n "$SWR_PASSWORD" ]] || {
  echo "[ERROR] SWR credentials missing (HUAWEICLOUD_SWR_USER / HUAWEICLOUD_SWR_PASSWORD)" >&2
  exit 1
}

# --- helpers -----------------------------------------------------------------

_hdr_of() { grep -i "^$1:" | tr -d '\r' | sed "s/^[^:]*: //" | tail -1; }

_get_token() {
  curl -sS --retry 3 --retry-all-errors \
    -u "${SWR_USER}:${SWR_PASSWORD}" \
    "${SWR_BASE}/swr/auth/v2/registry/auth/?service=dockyard&scope=${SCOPE}" \
    | jq -r '.token // empty'
}

_start_session() {
  curl -sS --retry 3 --retry-all-errors \
    -H "Authorization: Bearer ${TOKEN}" \
    -X POST -D - -o /dev/null \
    "${SWR_BASE}/v2/${REPO}/blobs/uploads/" | _hdr_of "location"
}

# Bytes the current session already holds, e.g. "0-1048575"; empty on failure.
_session_range() {
  curl -sS --max-time 30 -H "Authorization: Bearer ${TOKEN}" \
    -X GET -D - -o /dev/null "$1" | _hdr_of "range"
}

TOKEN="${SWR_TOKEN:-}"
if [[ -z "$TOKEN" ]]; then
  TOKEN="$(_get_token)"
fi
[[ -n "$TOKEN" ]] || { echo "[ERROR] could not obtain SWR registry token" >&2; exit 1; }

# --- upload paths ------------------------------------------------------------

_upload_chunked() {
  local loc
  loc="$(_start_session)"
  [[ -n "$loc" ]] || { echo "  [warn] could not open upload session"; return 1; }

  local offset=0 chunk_file
  chunk_file="$(mktemp /tmp/swr-chunk-XXXXXX)"
  while [[ $offset -lt $SIZE ]]; do
    local end=$((offset + CHUNK_SIZE - 1))
    [[ $end -ge $SIZE ]] && end=$((SIZE - 1))
    local len=$((end - offset + 1))
    dd if="$FILE" of="$chunk_file" bs=1048576 iflag=skip_bytes,count_bytes \
      skip="$offset" count="$len" status=none

    local resp code next
    resp="$(curl -sS --max-time 120 \
      -H "Authorization: Bearer ${TOKEN}" \
      -H "Content-Type: application/octet-stream" \
      -H "Content-Range: ${offset}-${end}" \
      -X PATCH -D - -o /dev/null --data-binary "@${chunk_file}" "$loc")"
    code="$(printf '%s' "$resp" | head -1 | awk '{print $2}')"
    next="$(printf '%s' "$resp" | _hdr_of "location")"

    if [[ "$code" == "202" || "$code" == "201" || "$code" == "204" ]]; then
      [[ -n "$next" ]] && loc="$next"
      offset=$((end + 1))
      echo "  [chunk] uploaded 0-${end} / ${SIZE}"
      continue
    fi

    echo "  [warn] chunk ${offset}-${end} failed [${code}]"
    local range have=-1
    range="$(_session_range "$loc")"
    if [[ -n "$range" ]]; then
      have="${range##*-}"
      [[ "$have" =~ ^[0-9]+$ ]] || have=-1
    fi
    if [[ "$have" -ge 0 && $((have + 1)) -gt $offset ]]; then
      echo "  [info] session already holds 0-${have}, resuming at $((have + 1))"
      offset=$((have + 1))
      continue
    fi
    rm -f "$chunk_file"
    return 1
  done
  rm -f "$chunk_file"

  local code
  code="$(curl -sS --retry 5 --retry-all-errors --retry-delay 2 --max-time 120 \
    -H "Authorization: Bearer ${TOKEN}" \
    -X PUT -o /dev/null -w "%{http_code}" \
    "${loc}&digest=sha256:${DIGEST}")"
  if [[ "$code" != "201" && "$code" != "202" ]]; then
    echo "  [warn] commit failed [${code}]"
    return 1
  fi
  echo "  [commit] HTTP ${code}"
  return 0
}

_upload_monolithic() {
  local loc
  loc="$(_start_session)"
  [[ -n "$loc" ]] || { echo "  [warn] could not open upload session"; return 1; }

  local body start code rc elapsed body_head
  body="$(mktemp /tmp/swr-mono-XXXXXX)"
  start=$(date +%s)
  code=$(curl -sS --http1.1 --max-time "$UPLOAD_TIMEOUT" \
    --speed-time 300 --speed-limit 512 \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/octet-stream" \
    -X PUT -o "$body" -w "%{http_code}" \
    --data-binary "@${FILE}" \
    "${loc}&digest=sha256:${DIGEST}")
  rc=$?
  elapsed=$(( $(date +%s) - start ))
  body_head="$(head -c 200 "$body" | tr -d '\n')"
  rm -f "$body"

  if [[ "$code" == "201" || "$code" == "204" || "$code" == "200" ]]; then
    echo "  [monolithic] committed (HTTP ${code}, ${elapsed}s)"
    return 0
  fi
  echo "  [warn] monolithic PUT failed: curl_rc=${rc} http=${code} after ${elapsed}s body=${body_head}"
  return 1
}

# --- main --------------------------------------------------------------------

if [[ $MONOLITHIC_THRESHOLD -gt 0 && $SIZE -le $MONOLITHIC_THRESHOLD ]]; then
  PATH_NAME="chunked"
  UPLOAD_FN="_upload_chunked"
else
  PATH_NAME="monolithic"
  UPLOAD_FN="_upload_monolithic"
fi

for attempt in $(seq 1 "$ATTEMPTS"); do
  echo "[attempt ${attempt}] ${REPO} sha256:${DIGEST} (${SIZE} bytes, ${PATH_NAME})"
  if "$UPLOAD_FN"; then
    echo "[OK] ${REPO} blob sha256:${DIGEST} committed"
    exit 0
  fi
  echo "[warn] attempt ${attempt} failed, restarting" >&2
  sleep 3
done

echo "[ERROR] failed to upload blob sha256:${DIGEST}" >&2
exit 1
