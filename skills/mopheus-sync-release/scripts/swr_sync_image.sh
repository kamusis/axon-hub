#!/usr/bin/env bash
# ==============================================================================
# swr_sync_image.sh — copy one multi-arch image from GHCR to Huawei Cloud SWR.
#
# `crane copy` cannot be used on this link: it streams each layer over a
# single connection, and SWR aborts long-lived upload connections, so the
# 17-24 MiB binary layers always fail with "PROTOCOL_ERROR / unexpected EOF".
#
# This script instead walks the manifest list itself:
#   1. read the source manifest list and every per-arch manifest,
#   2. HEAD each layer on SWR and skip the ones already present,
#   3. download the missing layers from GHCR and upload them with
#      swr_push_blob.sh (chunked for small blobs, monolithic for large ones),
#   4. push the per-arch manifests and finally the manifest list.
#
# Because blobs are content-addressed, re-running after a failure only pushes
# what is still missing.
#
# Usage: swr_sync_image.sh <src-image> <dst-image>
# ==============================================================================
set -uo pipefail

SRC="${1:?source image required}"
DST="${2:?destination image required}"

SWR_REGISTRY="${SWR_REGISTRY:-swr.cn-north-4.myhuaweicloud.com}"
SWR_BASE="${SWR_BASE:-https://${SWR_REGISTRY}}"
GHCR_REGISTRY="${GHCR_REGISTRY:-ghcr.io}"
GHCR_NAMESPACE="${GHCR_NAMESPACE:-enmotech}"

SWR_USER="${HUAWEICLOUD_SWR_USER:-${SWR_USER:-}}"
SWR_PASSWORD="${HUAWEICLOUD_SWR_PASSWORD:-${SWR_PASSWORD:-}}"
GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

UPLOAD_JOBS="${SWR_UPLOAD_JOBS:-4}"
WORK_DIR="${SWR_WORK_DIR:-/tmp/swr-sync-$$}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PUSH_BLOB="${SCRIPT_DIR}/swr_push_blob.sh"

[[ -x "$PUSH_BLOB" || -f "$PUSH_BLOB" ]] || {
  echo "[ERROR] swr_push_blob.sh not found next to this script (${SCRIPT_DIR})" >&2
  exit 1
}

# The destination repository is "namespace/app" on SWR. Drop the scheme and
# the registry host, whatever they look like (the host may carry a port).
DST_NO_SCHEME="${DST#*://}"
DST_REPO="${DST_NO_SCHEME#*/}"        # strip the registry host
DST_REPO="${DST_REPO%%:*}"            # the tag is after the last colon
DST_TAG="${DST##*:}"

cleanup() { rm -rf "$WORK_DIR"; }
trap cleanup EXIT
mkdir -p "$WORK_DIR"

# --- source image handling ---------------------------------------------------

# Strip the registry so crane talks to ghcr.io explicitly.
SRC_SHORT="${SRC#${GHCR_REGISTRY}/}"
SRC_SHORT="${SRC_SHORT#*/}"   # drop "enmotech/" -> "mopheus-backend:nightly"

crane_cmd() {
  if command -v crane >/dev/null 2>&1; then
    crane "$@"
  elif [[ -x /tmp/crane ]]; then
    /tmp/crane "$@"
  else
    echo "[ERROR] crane not available" >&2
    return 1
  fi
}

auth_ghcr() {
  [[ -n "$GH_TOKEN" ]] || return 0
  if command -v crane >/dev/null 2>&1; then
    printf '%s' "$GH_TOKEN" | crane auth login "${GHCR_REGISTRY}" -u "${GH_USER:-token}" --password-stdin >/dev/null 2>&1 || true
  fi
}

# Fetch the raw manifest JSON for a reference.
_manifest_json() {
  local ref="$1" out="$2"
  crane_cmd manifest "$ref" > "$out" 2>/dev/null
}

# Print "arch digest" for each child manifest of a manifest list.
_child_manifests() {
  local json="$1"
  jq -r 'if .manifests then (.manifests[] | "\(.platform.os)/\(.platform.architecture) \(.digest)") else empty end' "$json"
}

# Print each layer digest of an image manifest.
_layer_digests() {
  local json="$1"
  jq -r '.layers[]?.digest' "$json"
}

# --- SWR auth ----------------------------------------------------------------

SWR_TOKEN=""
_get_swr_token() {
  [[ -n "$SWR_TOKEN" ]] && { echo "$SWR_TOKEN"; return 0; }
  local scope="repository:${DST_REPO}:push,pull"
  SWR_TOKEN=$(curl -sS --retry 3 --retry-all-errors \
    -u "${SWR_USER}:${SWR_PASSWORD}" \
    "${SWR_BASE}/swr/auth/v2/registry/auth/?service=dockyard&scope=${scope}" \
    | jq -r '.token // empty')
  [[ -n "$SWR_TOKEN" ]] || return 1
  echo "$SWR_TOKEN"
}

# HEAD on SWR returns 200 when the blob exists. GET would answer 302 and make
# existing layers look missing, which would re-upload everything.
_blob_present() {
  local digest="$1" code
  code=$(curl -sS -I -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${SWR_TOKEN}" \
    "${SWR_BASE}/v2/${DST_REPO}/blobs/${digest}")
  [[ "$code" == "200" ]]
}

_manifest_present() {
  local ref="$1" code
  code=$(curl -sS -I -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer ${SWR_TOKEN}" \
    "${SWR_BASE}/v2/${DST_REPO}/manifests/${ref}")
  [[ "$code" == "200" ]]
}

# --- main --------------------------------------------------------------------

echo "[swr] syncing ${SRC} -> ${DST}"

auth_ghcr

SRC_MANIFEST="${WORK_DIR}/src-index.json"
if ! _manifest_json "${GHCR_REGISTRY}/${SRC_SHORT}" "$SRC_MANIFEST"; then
  echo "[ERROR] could not read source manifest for ${SRC}" >&2
  exit 1
fi

_get_swr_token >/dev/null || {
  echo "[ERROR] could not obtain SWR registry token" >&2
  exit 1
}

# Collect every layer of every architecture.
LAYER_LIST="${WORK_DIR}/layers.txt"
: > "$LAYER_LIST"
CHILD_LIST="${WORK_DIR}/children.txt"
: > "$CHILD_LIST"

if jq -e '.manifests' "$SRC_MANIFEST" >/dev/null 2>&1; then
  _child_manifests "$SRC_MANIFEST" > "$CHILD_LIST"
  while read -r platform digest; do
    [[ -z "$digest" ]] && continue
    child_json="${WORK_DIR}/child-${digest:7:16}.json"
    crane_cmd manifest "${GHCR_REGISTRY}/${SRC_SHORT}@${digest}" > "$child_json" 2>/dev/null || {
      echo "[ERROR] could not read child manifest ${digest}" >&2
      exit 1
    }
    _layer_digests "$child_json" >> "$LAYER_LIST"
  done < "$CHILD_LIST"
else
  # Single-arch image: the manifest itself carries the layers.
  _layer_digests "$SRC_MANIFEST" >> "$LAYER_LIST"
fi

TOTAL_LAYERS=$(sort -u "$LAYER_LIST" | grep -c . || true)
echo "[swr] ${TOTAL_LAYERS} unique layers in source"

# --- upload missing layers ---------------------------------------------------

MISSING="${WORK_DIR}/missing.txt"
: > "$MISSING"
while read -r digest; do
  [[ -z "$digest" ]] && continue
  if _blob_present "$digest"; then
    echo "[swr] [skip] ${digest} already on SWR"
  else
    echo "${digest}" >> "$MISSING"
  fi
done < <(sort -u "$LAYER_LIST")

MISSING_COUNT=$(grep -c . "$MISSING" || true)
echo "[swr] ${MISSING_COUNT} layers missing on SWR"

if [[ "$MISSING_COUNT" -gt 0 ]]; then
  BLOBS_DIR="${WORK_DIR}/blobs"
  mkdir -p "$BLOBS_DIR"

  # Download from GHCR first, so a failed download never eats upload time.
  echo "[swr] downloading ${MISSING_COUNT} layers from GHCR"
  while read -r digest; do
    [[ -z "$digest" ]] && continue
    file="${BLOBS_DIR}/${digest#sha256:}"
    if [[ ! -s "$file" ]]; then
      if ! crane_cmd blob "${GHCR_REGISTRY}/${SRC_SHORT}@${digest}" > "$file"; then
        echo "[ERROR] download failed for ${digest}" >&2
        rm -f "$file"
      fi
    fi
  done < "$MISSING"

  export BLOBS_DIR PUSH_BLOB SWR_REGISTRY SWR_BASE SWR_USER SWR_PASSWORD SWR_TOKEN
  export HUAWEICLOUD_SWR_USER="$SWR_USER" HUAWEICLOUD_SWR_PASSWORD="$SWR_PASSWORD"
  export DST_REPO

  _upload_one() {
    local digest="$1"
    local file="${BLOBS_DIR}/${digest#sha256:}"
    if [[ ! -s "$file" ]]; then
      echo "[SKIP] ${digest} (download failed)"
      return 1
    fi
    bash "$PUSH_BLOB" "$file" "$DST_REPO" "${digest#sha256:}"
  }
  export -f _upload_one

  echo "[swr] uploading ${MISSING_COUNT} layers (${UPLOAD_JOBS} parallel)"
  xargs -P "$UPLOAD_JOBS" -I{} bash -c '_upload_one "$1"' _ {} < "$MISSING"
  UPLOAD_RC=$?
  if [[ "$UPLOAD_RC" -ne 0 ]]; then
    echo "[ERROR] one or more layer uploads failed" >&2
    exit 1
  fi
fi

# --- push manifests ----------------------------------------------------------

# Refresh SWR token before pushing manifests to ensure token has not expired
# during long-running multi-layer blob transfers.
SWR_TOKEN=""
_get_swr_token >/dev/null || {
  echo "[ERROR] could not refresh SWR registry token before pushing manifests" >&2
  exit 1
}

# The manifest list plus each per-arch manifest are small JSON documents, so a
# single PUT is enough. Pushing the manifest list last makes the tag resolve
# only once every layer is in place.
push_manifest() {
  local ref="$1" json="$2"
  local type
  type=$(jq -r '.mediaType // empty' "$json" 2>/dev/null || true)
  if [[ -z "$type" ]]; then
    if jq -e '.manifests' "$json" >/dev/null 2>&1; then
      type="application/vnd.docker.distribution.manifest.list.v2+json"
    else
      type="application/vnd.docker.distribution.manifest.v2+json"
    fi
  fi
  local resp_tmp
  resp_tmp="$(mktemp /tmp/swr_manifest_resp_XXXXXX.txt)"
  local code
  code=$(curl -sS --http1.1 --max-time 120 \
    -H "Authorization: Bearer ${SWR_TOKEN}" \
    -H "Content-Type: ${type}" \
    -X PUT --data-binary "@${json}" \
    -o "$resp_tmp" -w "%{http_code}" \
    "${SWR_BASE}/v2/${DST_REPO}/manifests/${ref}")
  if [[ "$code" == "201" || "$code" == "200" || "$code" == "202" ]]; then
    echo "[swr] manifest ${ref} pushed (HTTP ${code})"
    rm -f "$resp_tmp"
    return 0
  fi
  echo "[ERROR] manifest ${ref} push failed [${code}]: $(head -c 200 "$resp_tmp")" >&2
  rm -f "$resp_tmp"
  return 1
}

if jq -e '.manifests' "$SRC_MANIFEST" >/dev/null 2>&1; then
  while read -r platform digest; do
    [[ -z "$digest" ]] && continue
    child_json="${WORK_DIR}/child-${digest:7:16}.json"
    push_manifest "$digest" "$child_json" || exit 1
  done < "$CHILD_LIST"
fi

push_manifest "$DST_TAG" "$SRC_MANIFEST" || exit 1

# --- verify ------------------------------------------------------------------

SRC_DIGEST=$(crane_cmd digest "${GHCR_REGISTRY}/${SRC_SHORT}" 2>/dev/null || echo "")
DST_DIGEST=$(crane_cmd digest "${SWR_BASE}/${DST_REPO}:${DST_TAG}" 2>/dev/null || echo "")

if [[ -n "$SRC_DIGEST" && -n "$DST_DIGEST" && "$SRC_DIGEST" == "$DST_DIGEST" ]]; then
  echo "[swr] OK ${DST} digest matches source: ${DST_DIGEST}"
else
  echo "[ERROR] digest mismatch for ${DST}: src=${SRC_DIGEST:-EMPTY} dst=${DST_DIGEST:-EMPTY}" >&2
  exit 1
fi
