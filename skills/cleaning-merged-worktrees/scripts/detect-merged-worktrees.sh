#!/usr/bin/env bash
#
# detect-merged-worktrees.sh
#
# Detects git worktrees and local branches whose work has been merged to the
# main branch. Uses a tiered detection algorithm to catch:
#   - Regular merges (branch is ancestor of main)
#   - Squash merges (branch tip tree matches a main commit)
#   - Squash merges where main evolved post-merge (content subset verification)
#
# Also detects redundant worktrees (detached HEADs that are intermediate
# commits of another active branch) and stale local branches (remote gone,
# no upstream, or merged into main).
#
# Usage: ./detect-merged-worktrees.sh [main-branch-name] [--worktrees|--branches|--all]
# Default main branch: main (falls back to master)
# Default mode: --all
#
# Output: structured report to stdout, parseable by agent or human.

set -uo pipefail

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
MAIN_BRANCH="main"
MODE="all"

for arg in "$@"; do
    case "$arg" in
        --worktrees)
            MODE="worktrees"
            ;;
        --branches)
            MODE="branches"
            ;;
        --all)
            MODE="all"
            ;;
        --help|-h)
            echo "Usage: $0 [main-branch-name] [--worktrees|--branches|--all]"
            echo "  --worktrees  Only scan worktrees"
            echo "  --branches   Only scan local branches"
            echo "  --all        Scan both worktrees and local branches (default)"
            exit 0
            ;;
        -*)
            echo "ERROR: Unknown option $arg" >&2
            echo "Usage: $0 [main-branch-name] [--worktrees|--branches|--all]" >&2
            exit 1
            ;;
        *)
            MAIN_BRANCH="$arg"
            ;;
    esac
done

# Fallback to master if main does not exist
if ! git rev-parse --verify "refs/heads/$MAIN_BRANCH" >/dev/null 2>&1; then
    if git rev-parse --verify "refs/heads/master" >/dev/null 2>&1; then
        MAIN_BRANCH="master"
    else
        echo "ERROR: Neither 'main' nor 'master' branch exists" >&2
        exit 1
    fi
fi

REPO_ROOT=$(git rev-parse --show-toplevel)

MODE_LABEL="worktrees and local branches"
[ "$MODE" = "worktrees" ] && MODE_LABEL="worktrees only"
[ "$MODE" = "branches" ] && MODE_LABEL="local branches only"

echo "=== Merged Worktree & Branch Detection Report ==="
echo "Repository: $REPO_ROOT"
echo "Main branch: $MAIN_BRANCH"
echo "Main HEAD:   $(git rev-parse "$MAIN_BRANCH")"
echo "Mode:        $MODE_LABEL"
echo "Date:        $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Stashes are repo-wide (shared across all worktrees), report once.
stash_count=$(git stash list 2>/dev/null | wc -l)
if [ "$stash_count" -gt 0 ]; then
    echo "NOTE: $stash_count stash(es) in repo (shared across all worktrees)"
fi
echo ""

# ---------------------------------------------------------------------------
# Helper: check if a ref's tree-hash exists anywhere in main's history.
# This catches squash merges where the branch tip's exact file tree matches
# a commit in main (the squash commit).
# ---------------------------------------------------------------------------
tree_in_main_history() {
    local ref=$1
    local tree_hash
    tree_hash=$(git rev-parse "$ref^{tree}" 2>/dev/null || echo "")
    if [ -z "$tree_hash" ]; then
        echo ""
        return
    fi
    # Search main history for a commit with this tree
    git log "$MAIN_BRANCH" --format="%T %H %s" | grep "^$tree_hash " | head -1
}

# ---------------------------------------------------------------------------
# Helper: content subset verification.
#
# For a branch B with merge-base M, checks whether main contains all of B's
# work. The logic:
#   1. Get files B changed since M.
#   2. For each file, compare B's version to main's version.
#      - If identical: safe.
#      - If main has additions but no deletions relative to B: safe (main
#        evolved further, but B's content is fully present).
#      - If main is missing lines B had: B has unique content not in main.
#
# Returns 0 (merged) / 1 (not merged) / 2 (needs review).
# Sets global variables: CONTENT_EVIDENCE, REVIEW_FILES
# ---------------------------------------------------------------------------
CONTENT_EVIDENCE=""
REVIEW_FILES=""

check_content_subset() {
    local ref=$1
    local mb
    mb=$(git merge-base "$MAIN_BRANCH" "$ref" 2>/dev/null || echo "")

    if [ -z "$mb" ]; then
        CONTENT_EVIDENCE="no merge-base found (unrelated history)"
        return 1
    fi

    local branch_files
    branch_files=$(git diff --name-only "$mb".."$ref" 2>/dev/null || true)

    if [ -z "$branch_files" ]; then
        CONTENT_EVIDENCE="branch has no changes since merge-base $mb"
        return 0
    fi

    local file_count
    file_count=$(echo "$branch_files" | wc -l)
    local safe_count=0
    local review_count=0
    REVIEW_FILES=""

    while IFS= read -r f; do
        [ -z "$f" ] && continue

        # Check if file exists in main
        if ! git cat-file -e "$MAIN_BRANCH:$f" 2>/dev/null; then
            # File doesn't exist in main — could be branch-unique or deleted in main
            if git cat-file -e "$ref:$f" 2>/dev/null; then
                # File exists in branch but not main
                # Check if it was deleted in main (existed at merge-base)
                if git cat-file -e "$mb:$f" 2>/dev/null; then
                    # File existed at merge-base and was deleted in main
                    # This is main evolving, not branch-unique content
                    safe_count=$((safe_count + 1))
                    continue
                else
                    # File is branch-unique (added by branch, not in main)
                    REVIEW_FILES="$REVIEW_FILES $f(branch-unique)"
                    review_count=$((review_count + 1))
                    continue
                fi
            fi
            continue
        fi

        # Compare branch version to main version
        local file_diff
        file_diff=$(git diff "$ref" "$MAIN_BRANCH" -- "$f" 2>/dev/null || true)

        if [ -z "$file_diff" ]; then
            # Identical
            safe_count=$((safe_count + 1))
            continue
        fi

        # Count lines in branch that are not in main
        # In `git diff ref..main`, lines starting with "-" (excluding "---" header)
        # are present in branch but absent in main.
        local branch_unique_lines
        branch_unique_lines=$(echo "$file_diff" | grep "^-" | grep -v "^---" | wc -l)

        if [ "$branch_unique_lines" -eq 0 ]; then
            # Main has everything branch has, plus possibly more (additions only)
            safe_count=$((safe_count + 1))
        else
            # Branch has lines not in main. Two possible explanations:
            #   (a) Main evolved the file after squash-merging the branch's work
            #       (main replaced old lines with newer versions).
            #   (b) Branch has genuinely unique work not in main.
            # Discriminator: did main also touch this file since merge-base?
            #   If yes → likely (a), post-merge evolution. Mark as "evolved".
            #   If no  → likely (b), branch-unique content. Mark for review.
            local main_touched=0
            if git diff --name-only "$mb".."$MAIN_BRANCH" 2>/dev/null | grep -qxF "$f"; then
                main_touched=1
            fi

            if [ "$main_touched" -eq 1 ]; then
                # Main also modified this file — likely post-merge evolution.
                # Mark as "evolved" (safe) rather than "unique" (review).
                safe_count=$((safe_count + 1))
            else
                # Main did not touch this file — branch has unique content.
                REVIEW_FILES="$REVIEW_FILES $f($branch_unique_lines unique lines, not in main)"
                review_count=$((review_count + 1))
            fi
        fi
    done <<< "$branch_files"

    CONTENT_EVIDENCE="$safe_count/$file_count files safe, $review_count need review"

    if [ "$review_count" -eq 0 ]; then
        return 0
    elif [ "$safe_count" -eq 0 ]; then
        return 1
    else
        return 2
    fi
}

# ---------------------------------------------------------------------------
# Helper: squash commit detection via commit message matching.
#
# Extracts issue/PR numbers from branch commit messages and searches main
# for commits referencing the same issues. Verifies file overlap.
# Sets global: MESSAGE_EVIDENCE
# ---------------------------------------------------------------------------
MESSAGE_EVIDENCE=""
check_message_match() {
    local ref=$1
    local mb
    mb=$(git merge-base "$MAIN_BRANCH" "$ref" 2>/dev/null || echo "")
    [ -z "$mb" ] && return 1

    local branch_msgs
    branch_msgs=$(git log "$mb".."$ref" --format="%B" 2>/dev/null || true)

    # Extract issue/PR numbers (#NNN)
    local issue_numbers
    issue_numbers=$(echo "$branch_msgs" | grep -oE '#[0-9]+' | sort -u || true)

    if [ -z "$issue_numbers" ]; then
        return 1
    fi

    local branch_files
    branch_files=$(git diff --name-only "$mb".."$ref" 2>/dev/null | sort || true)

    for issue in $issue_numbers; do
        local main_matches
        main_matches=$(git log "$MAIN_BRANCH" --oneline --grep="$issue" 2>/dev/null || true)
        if [ -z "$main_matches" ]; then
            continue
        fi

        while IFS= read -r main_line; do
            [ -z "$main_line" ] && continue
            local commit_hash
            commit_hash=$(echo "$main_line" | awk '{print $1}')
            local main_commit_files
            main_commit_files=$(git show --name-only --format="" "$commit_hash" 2>/dev/null | sort || true)
            local overlap
            overlap=$(comm -12 <(echo "$branch_files") <(echo "$main_commit_files") 2>/dev/null | wc -l)

            if [ "$overlap" -gt 0 ]; then
                MESSAGE_EVIDENCE="branch references $issue; main commit ${commit_hash:0:12} references same issue; $overlap files overlap"
                return 0
            fi
        done <<< "$main_matches"
    done

    return 1
}

# ---------------------------------------------------------------------------
# Helper: classify a single ref using the tiered detection algorithm.
#
# Sets the following variables in the caller's scope:
#   MERGE_STATUS, MERGE_METHOD, MERGE_EVIDENCE
# ---------------------------------------------------------------------------
classify_ref() {
    local ref=$1

    MERGE_STATUS="UNKNOWN"
    MERGE_METHOD=""
    MERGE_EVIDENCE=""

    # Tier 1: ancestor check (regular merge or commit in main history)
    if git merge-base --is-ancestor "$ref" "$MAIN_BRANCH" 2>/dev/null; then
        MERGE_STATUS="MERGED"
        MERGE_METHOD="ancestor"
        MERGE_EVIDENCE="commit is ancestor of $MAIN_BRANCH"
        echo "  MERGED (Tier 1: ancestor check)"
        return
    fi

    # Tier 2: tree-hash lookup (squash merge, exact match)
    local match
    match=$(tree_in_main_history "$ref")
    if [ -n "$match" ]; then
        local match_commit
        match_commit=$(echo "$match" | awk '{print $2}')
        local match_msg
        match_msg=$(echo "$match" | cut -d' ' -f3-)
        MERGE_STATUS="MERGED"
        MERGE_METHOD="squash-exact"
        MERGE_EVIDENCE="tree matches main commit ${match_commit:0:12}: $match_msg"
        echo "  MERGED (Tier 2: tree-hash match) — $match_msg"
        return
    fi

    # Tier 3: commit message matching (squash detection)
    local message_matched=0
    if check_message_match "$ref"; then
        message_matched=1
        echo "  CANDIDATE (Tier 3: message match) — $MESSAGE_EVIDENCE"
    fi

    # Tier 4: content subset verification
    check_content_subset "$ref"
    local content_result=$?

    if [ "$content_result" -eq 0 ]; then
        MERGE_STATUS="MERGED"
        if [ "$message_matched" -eq 1 ]; then
            MERGE_METHOD="squash-evolved"
            MERGE_EVIDENCE="$MESSAGE_EVIDENCE; content subset verified ($CONTENT_EVIDENCE)"
            echo "  MERGED (Tier 3+4: squash + content subset) — $CONTENT_EVIDENCE"
        else
            MERGE_METHOD="content-subset"
            MERGE_EVIDENCE="content subset verified ($CONTENT_EVIDENCE)"
            echo "  MERGED (Tier 4: content subset) — $CONTENT_EVIDENCE"
        fi
    elif [ "$content_result" -eq 2 ]; then
        MERGE_STATUS="NEEDS_REVIEW"
        MERGE_METHOD="content-partial"
        MERGE_EVIDENCE="$CONTENT_EVIDENCE; review:$REVIEW_FILES"
        echo "  NEEDS REVIEW (Tier 4: partial) — $CONTENT_EVIDENCE"
        echo "    Files to review:$REVIEW_FILES"
    else
        if [ "$message_matched" -eq 1 ]; then
            # Message matched but content differs — still needs review
            MERGE_STATUS="NEEDS_REVIEW"
            MERGE_METHOD="message-match-content-diff"
            MERGE_EVIDENCE="$MESSAGE_EVIDENCE; but content differs ($CONTENT_EVIDENCE)"
            echo "  NEEDS REVIEW (Tier 3 matched, Tier 4 differs) — $CONTENT_EVIDENCE"
        else
            MERGE_STATUS="NOT_MERGED"
            MERGE_METHOD="content-unique"
            MERGE_EVIDENCE="branch has unique content not in main ($CONTENT_EVIDENCE)"
            echo "  NOT MERGED (Tier 4: unique content) — $CONTENT_EVIDENCE"
        fi
    fi
}

# ---------------------------------------------------------------------------
# Arrays for worktree results
# ---------------------------------------------------------------------------
declare -a MERGED=()
declare -a REVIEW=()
declare -a NOT_MERGED=()
declare -a REDUNDANT=()
declare -a PRUNABLE=()

# Track all branch refs for redundancy detection and branch skip logic
declare -A wt_branches  # path -> branch_name
declare -A wt_heads      # path -> head_commit
declare -A checked_out_branches  # branch_name -> path

# ---------------------------------------------------------------------------
# Worktree detection
# ---------------------------------------------------------------------------
if [ "$MODE" = "worktrees" ] || [ "$MODE" = "all" ]; then
    echo "## Scanning worktrees"
    echo ""

    # Parse `git worktree list --porcelain` into pipe-separated lines:
    # path|head|branch|detached_flag
    worktree_data=$(git worktree list --porcelain | awk '
    BEGIN { wt=""; head=""; branch=""; detached=0 }
    /^worktree / { wt=$2 }
    /^HEAD / { head=$2 }
    /^branch / { branch=$2; detached=0 }
    /^detached$/ { detached=1 }
    /^$/ {
        if (wt != "") printf "%s|%s|%s|%d\n", wt, head, branch, detached
        wt=""; head=""; branch=""; detached=0
    }
    END {
        if (wt != "") printf "%s|%s|%s|%d\n", wt, head, branch, detached
    }')

    while IFS='|' read -r wt_path wt_head wt_branch wt_detached; do
        [ -z "$wt_path" ] && continue

        # Skip the main worktree
        if [ "$wt_path" = "$REPO_ROOT" ]; then
            continue
        fi
        if [ "$wt_branch" = "refs/heads/$MAIN_BRANCH" ]; then
            continue
        fi

        # Check if worktree directory still exists
        if [ ! -d "$wt_path" ]; then
            PRUNABLE+=("$wt_path|directory missing")
            continue
        fi

        # Determine ref and label
        branch_name=""
        ref=""
        ref_label=""
        if [ "$wt_detached" = "1" ]; then
            ref="$wt_head"
            ref_label="(detached @ ${wt_head:0:12})"
        else
            branch_name="${wt_branch#refs/heads/}"
            ref="$branch_name"
            ref_label="$branch_name"
            checked_out_branches["$branch_name"]="$wt_path"
        fi

        # Record for redundancy detection
        wt_heads["$wt_path"]="$wt_head"
        [ -n "$branch_name" ] && wt_branches["$wt_path"]="$branch_name"

        echo "--- $wt_path ($ref_label) ---"

        # Safety: check for uncommitted changes
        uncommitted=$(git -C "$wt_path" status --short 2>/dev/null | wc -l)

        if [ "$uncommitted" -gt 0 ]; then
            echo "  SKIP: $uncommitted uncommitted file(s)"
            NOT_MERGED+=("$wt_path|$ref_label|$branch_name|dirty:$uncommitted uncommitted files")
            echo ""
            continue
        fi

        # Run tiered classification
        classify_ref "$ref"

        # Store result
        case "$MERGE_STATUS" in
            MERGED)
                MERGED+=("$wt_path|$ref_label|$branch_name|$MERGE_METHOD|$MERGE_EVIDENCE")
                ;;
            NEEDS_REVIEW)
                REVIEW+=("$wt_path|$ref_label|$branch_name|$MERGE_METHOD|$MERGE_EVIDENCE")
                ;;
            *)
                NOT_MERGED+=("$wt_path|$ref_label|$branch_name|$MERGE_EVIDENCE")
                ;;
        esac

        echo ""
    done <<< "$worktree_data"

    # ---------------------------------------------------------------------------
    # Redundancy detection: find detached HEAD worktrees whose commit is an
    # ancestor of another worktree's branch (intermediate commit, not merged).
    # ---------------------------------------------------------------------------
    for wt_path in "${!wt_heads[@]}"; do
        head="${wt_heads[$wt_path]}"
        branch="${wt_branches[$wt_path]:-}"

        # Only check detached HEADs (no branch)
        [ -n "$branch" ] && continue

        # Skip if already detected as merged
        already_merged=false
        for m in "${MERGED[@]}"; do
            if [[ "$m" == "$wt_path|"* ]]; then
                already_merged=true
                break
            fi
        done
        $already_merged && continue

        # Check if this detached HEAD is an ancestor of any other branch
        for other_path in "${!wt_branches[@]}"; do
            [ "$other_path" = "$wt_path" ] && continue
            other_branch="${wt_branches[$other_path]}"

            if git merge-base --is-ancestor "$head" "$other_branch" 2>/dev/null; then
                REDUNDANT+=("$wt_path|(detached @ ${head:0:12})|intermediate commit of $other_branch ($other_path)")
                break
            fi
        done
    done
fi

# ---------------------------------------------------------------------------
# Arrays for local branch results
# ---------------------------------------------------------------------------
declare -a BRANCH_MERGED=()
declare -a BRANCH_REVIEW=()
declare -a BRANCH_NOT_MERGED=()

# ---------------------------------------------------------------------------
# Local branch detection
# ---------------------------------------------------------------------------
if [ "$MODE" = "branches" ] || [ "$MODE" = "all" ]; then
    echo "## Scanning local branches"
    echo ""

    branch_data=$(git for-each-ref --format='%(refname:short)|%(upstream:short)|%(upstream:track)|%(objectname:short)|%(committerdate:iso8601)|%(subject)' refs/heads)

    while IFS='|' read -r branch_name branch_upstream branch_track branch_commit branch_date branch_subject; do
        [ -z "$branch_name" ] && continue

        # Skip main branch
        [ "$branch_name" = "$MAIN_BRANCH" ] && continue

        # Skip branches already checked out in a worktree (handled above)
        if [ -n "${checked_out_branches[$branch_name]:-}" ]; then
            continue
        fi

        echo "--- $branch_name ---"

        ref="$branch_name"
        ref_label="$branch_name"
        remote_status=""

        if [ -z "$branch_upstream" ]; then
            remote_status="no-upstream"
        elif [ "$branch_track" = "[gone]" ]; then
            remote_status="remote-gone"
        else
            remote_status="remote-exists:${branch_upstream}"
        fi

        # Run tiered classification
        classify_ref "$ref"

        # Store result
        case "$MERGE_STATUS" in
            MERGED)
                BRANCH_MERGED+=("$branch_name|$branch_commit|$branch_date|$remote_status|$MERGE_METHOD|$MERGE_EVIDENCE")
                ;;
            NEEDS_REVIEW)
                BRANCH_REVIEW+=("$branch_name|$branch_commit|$branch_date|$remote_status|$MERGE_METHOD|$MERGE_EVIDENCE")
                ;;
            *)
                BRANCH_NOT_MERGED+=("$branch_name|$branch_commit|$branch_date|$remote_status|$MERGE_EVIDENCE")
                ;;
        esac

        echo ""
    done <<< "$branch_data"
fi

# ---------------------------------------------------------------------------
# Summary Report
# ---------------------------------------------------------------------------
echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="
echo ""

if [ "$MODE" = "worktrees" ] || [ "$MODE" = "all" ]; then
    echo "WORKTREE CLEANUP CANDIDATES (merged, safe to remove): ${#MERGED[@]}"
    echo "-------------------------------------------"
    if [ "${#MERGED[@]}" -eq 0 ]; then
        echo "  (none)"
    else
        for r in "${MERGED[@]}"; do
            IFS='|' read -r path ref bname method evidence <<< "$r"
            echo "  Path:   $path"
            echo "  Ref:    $ref"
            echo "  Branch: ${bname:-N/A}"
            echo "  Method: $method"
            echo "  Evidence: $evidence"
            echo ""
        done
    fi

    echo "WORKTREE NEEDS REVIEW (ambiguous, investigate before deciding): ${#REVIEW[@]}"
    echo "-------------------------------------------"
    if [ "${#REVIEW[@]}" -eq 0 ]; then
        echo "  (none)"
    else
        for r in "${REVIEW[@]}"; do
            IFS='|' read -r path ref bname method evidence <<< "$r"
            echo "  Path:   $path"
            echo "  Ref:    $ref"
            echo "  Branch: ${bname:-N/A}"
            echo "  Method: $method"
            echo "  Evidence: $evidence"
            echo ""
        done
    fi

    echo "WORKTREE REDUNDANT (detached HEAD, intermediate commit of another branch): ${#REDUNDANT[@]}"
    echo "-------------------------------------------"
    if [ "${#REDUNDANT[@]}" -eq 0 ]; then
        echo "  (none)"
    else
        for r in "${REDUNDANT[@]}"; do
            IFS='|' read -r path ref reason <<< "$r"
            echo "  Path: $path"
            echo "  Ref:  $ref"
            echo "  Reason: $reason"
            echo ""
        done
    fi

    echo "WORKTREE NOT MERGED (keep, has unique work): ${#NOT_MERGED[@]}"
    echo "-------------------------------------------"
    if [ "${#NOT_MERGED[@]}" -eq 0 ]; then
        echo "  (none)"
    else
        for r in "${NOT_MERGED[@]}"; do
            IFS='|' read -r path ref bname reason <<< "$r"
            echo "  Path: $path ($ref)"
            echo "  Reason: $reason"
            echo ""
        done
    fi

    echo "WORKTREE PRUNABLE (directory missing): ${#PRUNABLE[@]}"
    if [ "${#PRUNABLE[@]}" -gt 0 ]; then
        for r in "${PRUNABLE[@]}"; do
            IFS='|' read -r path reason <<< "$r"
            echo "  $path — $reason"
        done
    fi
    echo ""
fi

if [ "$MODE" = "branches" ] || [ "$MODE" = "all" ]; then
    # Count subcategories for cleanup candidates
    branch_gone_count=0
    branch_other_count=0
    for r in "${BRANCH_MERGED[@]}"; do
        IFS='|' read -r _bname _commit _date remote _method _evidence <<< "$r"
        if [ "$remote" = "remote-gone" ]; then
            branch_gone_count=$((branch_gone_count + 1))
        else
            branch_other_count=$((branch_other_count + 1))
        fi
    done

    echo "LOCAL BRANCH CLEANUP CANDIDATES (merged, safe to delete): ${#BRANCH_MERGED[@]}"
    echo "  - remote exists / no upstream: $branch_other_count"
    echo "  - remote gone:                 $branch_gone_count"
    echo "-------------------------------------------"
    if [ "${#BRANCH_MERGED[@]}" -eq 0 ]; then
        echo "  (none)"
    else
        for r in "${BRANCH_MERGED[@]}"; do
            IFS='|' read -r bname commit date remote method evidence <<< "$r"
            prefix=""
            if [ "$remote" = "remote-gone" ]; then
                prefix="[REMOTE-GONE] "
            fi
            echo "  ${prefix}Branch:   $bname"
            echo "           Commit:   $commit ($date)"
            echo "           Remote:   $remote"
            echo "           Method:   $method"
            echo "           Evidence: $evidence"
            echo ""
        done
    fi

    echo "LOCAL BRANCH NEEDS REVIEW (ambiguous, investigate before deciding): ${#BRANCH_REVIEW[@]}"
    echo "-------------------------------------------"
    if [ "${#BRANCH_REVIEW[@]}" -eq 0 ]; then
        echo "  (none)"
    else
        for r in "${BRANCH_REVIEW[@]}"; do
            IFS='|' read -r bname commit date remote method evidence <<< "$r"
            echo "  Branch:   $bname"
            echo "  Commit:   $commit ($date)"
            echo "  Remote:   $remote"
            echo "  Method:   $method"
            echo "  Evidence: $evidence"
            echo ""
        done
    fi

    echo "LOCAL BRANCH NOT MERGED (keep, has unique work): ${#BRANCH_NOT_MERGED[@]}"
    echo "-------------------------------------------"
    if [ "${#BRANCH_NOT_MERGED[@]}" -eq 0 ]; then
        echo "  (none)"
    else
        for r in "${BRANCH_NOT_MERGED[@]}"; do
            IFS='|' read -r bname commit date remote reason <<< "$r"
            echo "  Branch: $bname ($commit, $date)"
            echo "  Remote: $remote"
            echo "  Reason: $reason"
            echo ""
        done
    fi
    echo ""
fi

echo "=========================================="
echo "END OF REPORT"
echo "=========================================="
