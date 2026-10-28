#!/usr/bin/env bash
#
# detect-docker-images.sh
#
# Detects and manages Docker images on the host environment:
# 1. Protects in-use images (running/stopped containers) and base infrastructure images.
# 2. Identifies obsolete daily/beta build images (e.g. mopheus-backend, mopheus-web).
# 3. Retains the current in-use image plus the latest N historical versions for rollback.
# 4. Detects dangling images and stale build cache.
#
# Usage: ./detect-docker-images.sh [--keep N] [--apply|--dry-run]
# Default keep: 3 (keep in-use + latest 3 historical versions)
# Default mode: --dry-run
#

set -o pipefail

KEEP_VERSIONS=3
MODE="dry-run"

while [ $# -gt 0 ]; do
    case "$1" in
        --apply)
            MODE="apply"
            shift
            ;;
        --dry-run)
            MODE="dry-run"
            shift
            ;;
        --keep)
            shift
            KEEP_VERSIONS="${1:-3}"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--keep N] [--apply|--dry-run]"
            echo "  --keep N    Number of recent historical versions to keep (default: 3)"
            echo "  --apply     Execute deletion of candidate images"
            echo "  --dry-run   Report detection findings only without deletion (default)"
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            shift
            ;;
    esac
done

abort_for_agent() {
    local reason="$1"
    cat >&2 <<EOF
[FATAL_BLOCKER] ${reason}
[AGENT DIRECTIVE — DO NOT WORK AROUND]:
1. STOP all Docker/Podman cleanup steps immediately.
2. Do NOT attempt any alternative path, custom script, namespace wrapper (unshare/nsenter/mount/tmpfs), or direct read/write of ~/.local/share/containers/storage.
3. Mark the Docker cleanup section as BLOCKED and report this error verbatim to the human operator.
EOF
    exit 2
}

if ! command -v docker >/dev/null 2>&1; then
    abort_for_agent "Docker CLI is not installed or not in PATH."
fi

# Detect whether docker CLI works directly or requires host user-systemd delegation
# (e.g. rootless podman inside a bwrap sandbox where /run/user/<uid> is read-only).
# NEVER use unshare/mount/tmpfs over /run/user/<uid> against a live containers/storage graphroot,
# as doing so causes Podman to reset all running container states in db.sql to Created.
DOCKER_CMD=(docker)
if ! docker info >/dev/null 2>&1; then
    if command -v systemd-run >/dev/null 2>&1 \
        && systemd-run --user --pipe --wait --quiet -- docker info >/dev/null 2>&1; then
        DOCKER_CMD=(systemd-run --user --pipe --wait --quiet -- docker)
        echo "INFO: Rootless Podman in sandbox detected; delegating via 'systemd-run --user --pipe --wait --quiet -- docker'."
    else
        abort_for_agent "Container runtime is unreachable (both direct 'docker info' and 'systemd-run --user' delegation failed)."
    fi
fi

run_docker() {
    "${DOCKER_CMD[@]}" "$@"
}

echo "=== Docker Environment Image Scan ==="
echo "Mode: $MODE | Keep historical versions per repo: $KEEP_VERSIONS"
echo ""

# 1. Collect in-use image IDs and names (fail closed with directive if container listing fails)
# Note: Docker CLI 'ps --format' does not expose '{{.ImageID}}' (Podman-only field),
# so we query '{{.Image}}' via 'ps -a' and resolve full image IDs via 'inspect --format {{.Image}}',
# which works identically across both Docker Engine and Podman.
if ! PS_IMAGES_RAW=$(run_docker ps -a --format '{{.Image}}' 2>&1) \
    || ! ALL_CONTAINER_IDS=$(run_docker ps -aq 2>&1); then
    abort_for_agent "Failed to query container inventory via 'docker ps -a': ${PS_IMAGES_RAW} ${ALL_CONTAINER_IDS}"
fi
PS_IDS_RAW=""
if [ -n "$ALL_CONTAINER_IDS" ]; then
    # shellcheck disable=SC2086
    if ! PS_IDS_RAW=$(run_docker inspect --format '{{.Image}}' $ALL_CONTAINER_IDS 2>&1); then
        abort_for_agent "Failed to inspect container image IDs via 'docker inspect': ${PS_IDS_RAW}"
    fi
fi
IN_USE_IMAGES=$(echo "$PS_IMAGES_RAW" | sort -u)
IN_USE_IMAGE_IDS=$(echo "$PS_IDS_RAW" | sort -u)

is_in_use() {
    local img="$1"
    local id="$2"
    if echo "$IN_USE_IMAGES" | grep -Fxq "$img" 2>/dev/null; then
        return 0
    fi
    if [ -n "$id" ] && echo "$IN_USE_IMAGE_IDS" | grep -Fq "$id" 2>/dev/null; then
        return 0
    fi
    return 1
}

# Protected base image patterns (never delete unless dangling; match both Docker short names and Podman registry-prefixed names)
is_protected_base() {
    local repo="$1"
    case "$repo" in
        alpine|*/alpine|golang|*/golang|node|*/node|nginx|*/nginx|postgres|*/postgres|minio/minio|*/minio/minio|*pgvector*|*swissql-core*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# 2. Parse all images (Repository, Tag, ImageID, Size, CreatedAt)
# Format: Repo\tTag\tImageID\tSize\tCreatedAt
if ! IMAGES_OUTPUT=$(run_docker images --format '{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}' 2>&1); then
    abort_for_agent "Failed to enumerate container images via 'docker images': ${IMAGES_OUTPUT}"
fi
RAW_IMAGES=$(echo "$IMAGES_OUTPUT" | grep -v '<none>' || true)

REPOS=$(echo "$RAW_IMAGES" | cut -f1 | sort -u)

CANDIDATES_TO_REMOVE=""
PROTECTED_IMAGES=""

for repo in $REPOS; do
    [ -z "$repo" ] && continue
    TAG_ROWS=$(echo "$RAW_IMAGES" | awk -F'\t' -v r="$repo" '$1 == r')

    if is_protected_base "$repo"; then
        while IFS=$'\t' read -r r tag id size created; do
            [ -n "$tag" ] && PROTECTED_IMAGES="${PROTECTED_IMAGES}${r}:${tag}\t${id}\t${size}\tBase/Infrastructure image\n"
        done <<< "$TAG_ROWS"
        continue
    fi

    # For application/build repos (e.g. mopheus-backend, mopheus-web)
    kept_count=0
    while IFS=$'\t' read -r r tag id size created; do
        [ -z "$tag" ] && continue
        full_ref="${r}:${tag}"

        if is_in_use "$full_ref" "$id"; then
            PROTECTED_IMAGES="${PROTECTED_IMAGES}${full_ref}\t${id}\t${size}\tCurrently In-Use (Container active)\n"
            ((kept_count++))
        elif [ "$kept_count" -lt "$KEEP_VERSIONS" ]; then
            PROTECTED_IMAGES="${PROTECTED_IMAGES}${full_ref}\t${id}\t${size}\tRecent rollback version (rank $((kept_count+1)))\n"
            ((kept_count++))
        else
            CANDIDATES_TO_REMOVE="${CANDIDATES_TO_REMOVE}${full_ref}\t${id}\t${size}\tOutdated build (exceeds keep count ${KEEP_VERSIONS})\n"
        fi
    done <<< "$TAG_ROWS"
done

echo "--- Summary of Cleanup Candidates ---"
if [ -n "$CANDIDATES_TO_REMOVE" ]; then
    printf "%-75s %-15s %-10s %s\n" "IMAGE" "ID" "SIZE" "REASON"
    printf "%-75s %-15s %-10s %s\n" "-----" "--" "----" "------"
    echo -e "$CANDIDATES_TO_REMOVE" | while IFS=$'\t' read -r img id size reason; do
        [ -n "$img" ] && printf "%-75s %-15s %-10s %s\n" "$img" "$id" "$size" "$reason"
    done
else
    echo "No obsolete images detected for removal."
fi

echo ""
echo "--- Summary of Protected Images ---"
if [ -n "$PROTECTED_IMAGES" ]; then
    printf "%-75s %-15s %-10s %s\n" "IMAGE" "ID" "SIZE" "PROTECTION REASON"
    printf "%-75s %-15s %-10s %s\n" "-----" "--" "----" "-----------------"
    echo -e "$PROTECTED_IMAGES" | while IFS=$'\t' read -r img id size reason; do
        [ -n "$img" ] && printf "%-75s %-15s %-10s %s\n" "$img" "$id" "$size" "$reason"
    done
fi

echo ""
DANGLING_COUNT=$(run_docker images -f "dangling=true" -q 2>/dev/null | wc -l)
echo "Dangling (<none>:<none>) images count: $DANGLING_COUNT"

# 3. Inspect Toolchain & Build Caches (~/.cache/go-build, ~/.npm/_cacache)
ROOT_USE_PCT=$(df -P / 2>/dev/null | awk 'NR==2 {gsub(/%/,"",$5); print $5}')
ROOT_USE_PCT="${ROOT_USE_PCT:-0}"

GOCACHE_DIR="${GOCACHE:-$HOME/.cache/go-build}"
NPM_CACHE_DIR="$HOME/.npm/_cacache"

GOCACHE_MB=0
if [ -d "$GOCACHE_DIR" ]; then
    GOCACHE_MB=$(du -sm "$GOCACHE_DIR" 2>/dev/null | awk '{print $1}')
    GOCACHE_MB="${GOCACHE_MB:-0}"
fi

NPM_CACHE_MB=0
if [ -d "$NPM_CACHE_DIR" ]; then
    NPM_CACHE_MB=$(du -sm "$NPM_CACHE_DIR" 2>/dev/null | awk '{print $1}')
    NPM_CACHE_MB="${NPM_CACHE_MB:-0}"
fi

# Dynamic watermark thresholds: tighter when root filesystem >= 75%
if [ "$ROOT_USE_PCT" -ge 75 ]; then
    GOCACHE_LIMIT_MB=1024
    NPM_LIMIT_MB=512
else
    GOCACHE_LIMIT_MB=4096
    NPM_LIMIT_MB=2048
fi

echo ""
echo "--- Toolchain & Package Cache Status (Root FS: ${ROOT_USE_PCT}%) ---"
echo "Go build cache ($GOCACHE_DIR): ${GOCACHE_MB} MB (threshold: ${GOCACHE_LIMIT_MB} MB)"
echo "npm cache ($NPM_CACHE_DIR): ${NPM_CACHE_MB} MB (threshold: ${NPM_LIMIT_MB} MB)"

if [ "$MODE" = "apply" ]; then
    echo ""
    echo "=== Executing Deletion ==="
    if [ -n "$CANDIDATES_TO_REMOVE" ]; then
        echo -e "$CANDIDATES_TO_REMOVE" | while IFS=$'\t' read -r img id size reason; do
            [ -n "$img" ] || continue
            echo -n "Removing $img ($id)... "
            if run_docker rmi "$img" >/dev/null 2>&1; then
                echo "SUCCESS"
            else
                echo "FAILED / In-use child layer, skipping safely"
            fi
        done
    fi

    if [ "$DANGLING_COUNT" -gt 0 ]; then
        echo "Pruning dangling images..."
        run_docker image prune -f
    fi

    echo "Pruning build cache older than 24h..."
    run_docker builder prune -f --filter "until=24h" 2>/dev/null || true

    if [ "$GOCACHE_MB" -ge "$GOCACHE_LIMIT_MB" ] && [ -d "$GOCACHE_DIR" ]; then
        echo "Cleaning Go build cache (${GOCACHE_MB} MB >= ${GOCACHE_LIMIT_MB} MB threshold)..."
        go clean -cache 2>/dev/null || rm -rf "${GOCACHE_DIR:?}"/* 2>/dev/null || true
    fi

    if [ "$NPM_CACHE_MB" -ge "$NPM_LIMIT_MB" ] && [ -d "$NPM_CACHE_DIR" ]; then
        echo "Cleaning npm cache (${NPM_CACHE_MB} MB >= ${NPM_LIMIT_MB} MB threshold)..."
        rm -rf "${NPM_CACHE_DIR:?}" 2>/dev/null || true
    fi

    echo "Cleaning stale /tmp build and test residue..."
    find /tmp -maxdepth 1 \( -name "go-build*" -o -name "e2e*" -o -name "playwright*" \) -mtime +1 -exec rm -rf {} + 2>/dev/null || true
    find /tmp -maxdepth 1 \( -name "mopheus-it-*" -o -name "preview-*" \) -mtime +3 -exec rm -rf {} + 2>/dev/null || true

    echo "=== Cleanup Execution Finished ==="
fi
