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

if ! command -v docker >/dev/null 2>&1; then
    echo "ERROR: Docker is not installed or not in PATH." >&2
    exit 1
fi

echo "=== Docker Environment Image Scan ==="
echo "Mode: $MODE | Keep historical versions per repo: $KEEP_VERSIONS"
echo ""

# 1. Collect in-use image IDs and names
IN_USE_IMAGES=$(docker ps -a --format '{{.Image}}' 2>/dev/null | sort -u)
IN_USE_IMAGE_IDS=$(docker ps -a --format '{{.ImageID}}' 2>/dev/null | sort -u)

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

# Protected base image patterns (never delete unless dangling)
is_protected_base() {
    local repo="$1"
    case "$repo" in
        alpine|golang|nginx|minio/minio|*pgvector*|*swissql-core*)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# 2. Parse all images (Repository, Tag, ImageID, Size, CreatedAt)
# Format: Repo\tTag\tImageID\tSize\tCreatedAt
RAW_IMAGES=$(docker images --format '{{.Repository}}\t{{.Tag}}\t{{.ID}}\t{{.Size}}\t{{.CreatedAt}}' 2>/dev/null | grep -v '<none>')

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
DANGLING_COUNT=$(docker images -f "dangling=true" -q 2>/dev/null | wc -l)
echo "Dangling (<none>:<none>) images count: $DANGLING_COUNT"

if [ "$MODE" = "apply" ]; then
    echo ""
    echo "=== Executing Deletion ==="
    if [ -n "$CANDIDATES_TO_REMOVE" ]; then
        echo -e "$CANDIDATES_TO_REMOVE" | while IFS=$'\t' read -r img id size reason; do
            [ -n "$img" ] || continue
            echo -n "Removing $img ($id)... "
            if docker rmi "$img" >/dev/null 2>&1; then
                echo "SUCCESS"
            else
                echo "FAILED / In-use child layer, skipping safely"
            fi
        done
    fi

    if [ "$DANGLING_COUNT" -gt 0 ]; then
        echo "Pruning dangling images..."
        docker image prune -f
    fi

    echo "Pruning build cache older than 7 days..."
    docker builder prune -f --filter "until=168h" 2>/dev/null || true
    echo "=== Cleanup Execution Finished ==="
fi
