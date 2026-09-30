#!/usr/bin/env bash
# ==============================================================================
# sync-github-to-huawei.sh (Self-contained in mopheus-sync-release skill)
# 
# Deterministic synchronization script: copies multi-arch Docker images from GHCR
# to Huawei Cloud SWR, and downloads CLI release assets from GitHub Releases to
# upload them to Huawei Cloud OBS.
# ==============================================================================
set -euo pipefail

# Default settings
REPO="enmotech/mopheus"
TAG="nightly"
VERSION=""
COMMIT=""
SKIP_IMAGES=false
SKIP_CLI=false
DRY_RUN=false
FORCE=false

SWR_REGISTRY="${SWR_REGISTRY:-swr.cn-north-4.myhuaweicloud.com}"
SWR_NAMESPACE="${SWR_NAMESPACE:-mopheus}"
GHCR_REGISTRY="${GHCR_REGISTRY:-ghcr.io}"
GHCR_NAMESPACE="${GHCR_NAMESPACE:-enmotech}"

OBS_BUCKET="${OBS_BUCKET:-mopheus}"
OBS_REGION="${OBS_REGION:-cn-north-4}"
OBS_HTTP_BASE="${OBS_HTTP_BASE:-https://${OBS_BUCKET}.obs.${OBS_REGION}.myhuaweicloud.com}"
OBS_AK="${OBS_AK:-${OBS_ACCESS_KEY_ID:-${HUAWEI_OBS_AK:-}}}"
OBS_SK="${OBS_SK:-${OBS_SECRET_ACCESS_KEY:-${HUAWEI_OBS_SK:-}}}"

TMP_CLI_DIR=""
cleanup() {
  if [[ -n "${TMP_CLI_DIR:-}" && -d "${TMP_CLI_DIR}" ]]; then
    rm -rf "${TMP_CLI_DIR}"
  fi
}
trap cleanup EXIT

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --tag <tag>             Target tag to sync (default: nightly, e.g. v2.2.6 or nightly)
  --version <version>     Exact version string (default: same as --tag)
  --commit <sha>          Git commit SHA (optional)
  --repo <repo>           GitHub repository (default: enmotech/mopheus)
  --skip-images           Skip Docker image synchronization
  --skip-cli              Skip CLI release assets synchronization
  --force                 Force sync even if target version already exists on SWR/OBS
  --dry-run               Log actions without pushing or uploading
  -h, --help              Show this help message
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tag) TAG="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --commit) COMMIT="$2"; shift 2 ;;
    --repo) REPO="$2"; shift 2 ;;
    --skip-images) SKIP_IMAGES=true; shift ;;
    --skip-cli) SKIP_CLI=true; shift ;;
    --force) FORCE=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage ;;
    *) echo "[ERROR] Unknown option: $1" >&2; usage ;;
  esac
done

VERSION="${VERSION:-$TAG}"
COMMIT="${COMMIT:-unknown}"

echo "=================================================================="
echo " Starting Mopheus GitHub -> Huawei Cloud Synchronization"
echo " Target Tag:    ${TAG}"
echo " Version:       ${VERSION}"
echo " Commit:        ${COMMIT}"
echo " GitHub Repo:   ${REPO}"
echo " Dry Run:       ${DRY_RUN}"
echo "=================================================================="

# Determine release mode
IS_STABLE=false
if [[ "${TAG}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  IS_STABLE=true
  echo "[INFO] Detected STABLE release mode for ${TAG}."
else
  echo "[INFO] Detected PRE-RELEASE / NIGHTLY mode for ${TAG}."
fi

# ------------------------------------------------------------------------------
# 1. Synchronize Docker Images (GHCR -> SWR)
# ------------------------------------------------------------------------------
ensure_crane() {
  if command -v crane >/dev/null 2>&1; then
    return 0
  fi
  echo "[INFO] crane not found in PATH; attempting to download standalone crane to /tmp..."
  local arch="x86_64"
  if [[ "$(uname -m)" =~ (aarch64|arm64) ]]; then
    arch="arm64"
  fi
  curl -sSL "https://github.com/google/go-containerregistry/releases/download/v0.20.3/go-containerregistry_Linux_${arch}.tar.gz" | tar -xz -C /tmp crane 2>/dev/null || true
  if [[ -x /tmp/crane ]]; then
    export PATH="/tmp:${PATH}"
    echo "[INFO] crane successfully downloaded and available at /tmp/crane."
  fi
}

login_registries() {
  if [[ "${DRY_RUN}" == "true" ]]; then
    return 0
  fi

  local gh_token="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
  local swr_user="${HUAWEICLOUD_SWR_USER:-${SWR_USER:-}}"
  local swr_pwd="${HUAWEICLOUD_SWR_PASSWORD:-${SWR_PASSWORD:-}}"

  if command -v crane >/dev/null 2>&1; then
    if [[ -n "${swr_user}" && -n "${swr_pwd}" ]]; then
      echo "[INFO] Authenticating crane with Huawei Cloud SWR..."
      crane auth login "${SWR_REGISTRY}" -u "${swr_user}" -p "${swr_pwd}" 2>/dev/null || true
    fi
    if [[ -n "${gh_token}" ]]; then
      echo "[INFO] Authenticating crane with GitHub Packages (GHCR)..."
      echo "${gh_token}" | crane auth login "${GHCR_REGISTRY}" -u "${GHCR_USER:-token}" --password-stdin 2>/dev/null || true
    fi
  elif command -v docker >/dev/null 2>&1; then
    if [[ -n "${swr_user}" && -n "${swr_pwd}" ]]; then
      echo "${swr_pwd}" | docker login "${SWR_REGISTRY}" -u "${swr_user}" --password-stdin 2>/dev/null || true
    fi
    if [[ -n "${gh_token}" ]]; then
      echo "${gh_token}" | docker login "${GHCR_REGISTRY}" -u "${GHCR_USER:-token}" --password-stdin 2>/dev/null || true
    fi
  fi
}

sync_single_image() {
  local src="$1"
  local dst="$2"

  echo "[INFO] Copying image: ${src} -> ${dst}"
  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] Would copy ${src} to ${dst}"
    return 0
  fi

  if command -v crane >/dev/null 2>&1; then
    crane copy "${src}" "${dst}"
  elif command -v skopeo >/dev/null 2>&1; then
    skopeo copy --all "docker://${src}" "docker://${dst}"
  elif command -v docker >/dev/null 2>&1; then
    docker pull "${src}"
    docker tag "${src}" "${dst}"
    docker push "${dst}"
  else
    echo "[ERROR] No container copying tool found (crane, skopeo, or docker required)." >&2
    return 1
  fi
}

sync_images() {
  echo ""
  echo "--- Step 1: Syncing Container Images ---"

  ensure_crane
  login_registries

  local apps=("mopheus-backend" "mopheus-web")

  # Fast check: if destination images already match source digests on SWR, skip sync
  if [[ "${FORCE}" != "true" ]] && command -v crane >/dev/null 2>&1; then
    local all_synced=true
    for app in "${apps[@]}"; do
      local src_image="${GHCR_REGISTRY}/${GHCR_NAMESPACE}/${app}:${TAG}"
      local dst_image="${SWR_REGISTRY}/${SWR_NAMESPACE}/${app}:${VERSION}"
      
      local src_digest
      src_digest=$(crane digest "${src_image}" 2>/dev/null || true)
      local dst_digest
      dst_digest=$(crane digest "${dst_image}" 2>/dev/null || true)

      if [[ -z "${src_digest}" || -z "${dst_digest}" || "${src_digest}" != "${dst_digest}" ]]; then
        all_synced=false
        break
      fi
    done

    if [[ "${all_synced}" == "true" ]]; then
      echo "[INFO] Container images for version '${VERSION}' already match digests on SWR. Skipping image copy."
      return 0
    fi
  fi
  for app in "${apps[@]}"; do
    local src_image="${GHCR_REGISTRY}/${GHCR_NAMESPACE}/${app}:${TAG}"
    local dst_image="${SWR_REGISTRY}/${SWR_NAMESPACE}/${app}:${TAG}"

    sync_single_image "${src_image}" "${dst_image}"

    # Also push version tag if version != tag
    if [[ "${VERSION}" != "${TAG}" ]]; then
      local dst_version_image="${SWR_REGISTRY}/${SWR_NAMESPACE}/${app}:${VERSION}"
      sync_single_image "${src_image}" "${dst_version_image}"
    fi

    # For stable releases, also update :latest tag
    if [[ "${IS_STABLE}" == "true" ]]; then
      local dst_latest_image="${SWR_REGISTRY}/${SWR_NAMESPACE}/${app}:latest"
      sync_single_image "${src_image}" "${dst_latest_image}"
    fi
  done
  echo "[INFO] Container images successfully synced."
}

# ------------------------------------------------------------------------------
# 2. Synchronize CLI Binaries and Manifest (GitHub Releases -> OBS)
# ------------------------------------------------------------------------------
_require_obs_creds() {
  if [[ -z "${OBS_AK:-}" || -z "${OBS_SK:-}" ]]; then
    echo "[ERROR] OBS_AK and OBS_SK must be set for uploading to OBS." >&2
    return 1
  fi
}

_obs_sign() {
  local string_to_sign="$1

$2
$3
/${OBS_BUCKET}/$4"
  printf '%s' "$string_to_sign" \
    | openssl dgst -sha1 -hmac "${OBS_SK}" -binary | base64
}

obs_put() {
  local local_path="$1"
  local key="$2"
  local content_type="${3:-application/octet-stream}"
  local cache_control="${4:-}"

  if [[ "${DRY_RUN}" == "true" ]]; then
    echo "[DRY-RUN] Would upload ${local_path} to obs://${OBS_BUCKET}/${key}"
    return 0
  fi

  _require_obs_creds

  local date
  date=$(LC_ALL=C date -u +"%a, %d %b %Y %H:%M:%S GMT")
  local signature
  signature=$(_obs_sign PUT "${content_type}" "${date}" "${key}")

  local extra_headers=()
  if [[ -n "${cache_control}" ]]; then
    extra_headers+=(-H "Cache-Control: ${cache_control}")
  fi

  local http_code
  http_code=$(curl -sS -o /tmp/obs_resp.txt -w "%{http_code}" \
    --connect-timeout 30 \
    --max-time 600 \
    --retry 3 \
    --retry-delay 3 \
    -X PUT \
    -H "Date: ${date}" \
    -H "Content-Type: ${content_type}" \
    -H "Authorization: OBS ${OBS_AK}:${signature}" \
    "${extra_headers[@]}" \
    --data-binary "@${local_path}" \
    "${OBS_HTTP_BASE}/${key}")

  if [[ "${http_code}" != "200" ]]; then
    echo "[ERROR] OBS upload failed [${http_code}] for ${key}: $(cat /tmp/obs_resp.txt)" >&2
    return 1
  fi
  echo "  uploaded ${key} [${http_code}]"
}

sync_cli() {
  echo ""
  echo "--- Step 2: Syncing CLI Binaries & Manifest ---"

  # Fast check: if manifest and binaries already exist on OBS, skip downloading and uploading
  local manifest_name="version-dev.json"
  if [[ "${IS_STABLE}" == "true" ]]; then
    manifest_name="version.json"
  fi

  if [[ "${FORCE}" != "true" ]]; then
    local remote_manifest_url="${OBS_HTTP_BASE%/}/tools/mopheus/${manifest_name}"
    local current_remote_version
    current_remote_version=$(curl -sS --connect-timeout 10 --max-time 15 "${remote_manifest_url}" 2>/dev/null | jq -r '.version // empty' 2>/dev/null || true)

    if [[ -n "${current_remote_version}" && "${current_remote_version}" == "${VERSION}" ]]; then
      echo "[INFO] OBS manifest (${manifest_name}) already points to version '${VERSION}'."
      local sample_url="${OBS_HTTP_BASE%/}/tools/mopheus/${VERSION}/mopheus_${VERSION}_linux_amd64.tar.gz"
      local sample_code
      sample_code=$(curl -sS -I -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 "${sample_url}" 2>/dev/null || true)
      if [[ "${sample_code}" == "200" ]]; then
        echo "[INFO] Version '${VERSION}' binary assets and manifest already fully synced on OBS. Skipping CLI sync."
        return 0
      fi
    fi
  fi

  # Require OBS credentials (unless in dry-run mode)
  if [[ "${DRY_RUN}" != "true" ]]; then
    _require_obs_creds
  fi

  TMP_CLI_DIR=$(mktemp -d /tmp/mopheus-sync-cli-XXXXXX)

  echo "[INFO] Downloading release assets from GitHub Release '${TAG}'..."
  gh release download "${TAG}" --repo "${REPO}" --dir "${TMP_CLI_DIR}"

  echo "[INFO] Downloaded assets:"
  ls -lh "${TMP_CLI_DIR}"

  # 1. Upload only version-specific archives and checksums to version-scoped path
  local files_to_upload=()
  for f in "${TMP_CLI_DIR}"/mopheus_"${VERSION}"_*.tar.gz \
           "${TMP_CLI_DIR}"/mopheus_"${VERSION}"_*.zip \
           "${TMP_CLI_DIR}"/checksums*.txt; do
    [[ -f "$f" ]] && files_to_upload+=("$f")
  done

  # Fallback: if no files matched mopheus_${VERSION}_*, upload whatever archives exist
  if [[ ${#files_to_upload[@]} -eq 0 ]]; then
    for f in "${TMP_CLI_DIR}"/*.tar.gz "${TMP_CLI_DIR}"/*.zip "${TMP_CLI_DIR}"/checksums*.txt; do
      [[ -f "$f" ]] && files_to_upload+=("$f")
    done
  fi

  for f in "${files_to_upload[@]}"; do
    local fname
    fname="$(basename "$f")"
    local key="tools/mopheus/${VERSION}/${fname}"
    echo "[INFO] Uploading ${fname} to ${key}..."
    obs_put "$f" "$key"
  done

  # 2. Upload manifest JSON (rewrite download_base and download URLs to OBS endpoints)
  local obs_tools_base="${OBS_HTTP_BASE%/}/tools/mopheus"
  local manifest_name="version-dev.json"
  if [[ "${IS_STABLE}" == "true" ]]; then
    manifest_name="version.json"
  fi

  if [[ -f "${TMP_CLI_DIR}/${manifest_name}" ]]; then
    echo "[INFO] Rewriting and uploading ${manifest_name} to tools/mopheus/${manifest_name}..."
    local obs_manifest="${TMP_CLI_DIR}/manifest_for_obs.json"
    jq --arg base "${obs_tools_base}" --arg ver "${VERSION}" \
      '.download_base = $base | .downloads |= with_entries(.value = "\($base)/\($ver)/\(.value | split("/") | last)")' \
      "${TMP_CLI_DIR}/${manifest_name}" > "${obs_manifest}"
    obs_put "${obs_manifest}" "tools/mopheus/${manifest_name}" "application/json" "no-cache, no-store"
  fi

  echo "[INFO] CLI binaries and manifests successfully synced to OBS."
}

# ------------------------------------------------------------------------------
# Main Flow
# ------------------------------------------------------------------------------
main() {
  if [[ "${SKIP_IMAGES}" != "true" ]]; then
    sync_images
  else
    echo "[INFO] Skipping container images synchronization (--skip-images)."
  fi

  if [[ "${SKIP_CLI}" != "true" ]]; then
    sync_cli
  else
    echo "[INFO] Skipping CLI synchronization (--skip-cli)."
  fi

  echo ""
  echo "=================================================================="
  echo " Synchronization completed successfully for ${TAG} (${VERSION})"
  echo "=================================================================="
}

main "$@"
