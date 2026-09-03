---
name: cleaning-merged-worktrees
description: Detect and clean up merged git worktrees and local branches. Identifies regular and squash merges (including evolved main branches and remote-gone branches), presents evidence for review, and safely removes directories and branches after confirmation.
---

# Cleaning Merged Git Worktrees and Local Branches

## Overview

Over time, git worktrees and local branches accumulate after features merge. This skill detects which worktrees and local branches are safe to remove and cleans them up after explicit user confirmation.

**Core challenge:** Squash merges create new commits, making them invisible to naive `git branch --merged`. This skill uses a tiered detection algorithm that catches regular merges, exact squash merges, and squash merges with post-merge main evolution without false positives.

## Safety Principles

1. **Never auto-clean without review**: Always present candidates with evidence and obtain user confirmation before executing deletion.
2. **Never clean a dirty worktree**: If uncommitted or untracked changes exist, skip the worktree and report it as unsafe to remove.
3. **Conservative classification**: Ambiguous items are classified as `NEEDS_REVIEW` and investigated before presenting to the user.
4. **Zero data loss**: A worktree or branch is removed only when all its changes are verified to exist within main.
5. **Selective execution**: Support confirming all safe candidates or selectively excluding specific ones.

## Detection Algorithm Summary

The detection script (`scripts/detect-merged-worktrees.sh`) uses a 4-tier ladder. For in-depth mechanics and proof, see [`references/detection-algorithm.md`](references/detection-algorithm.md).

| Tier | Method | Catches | Misses |
|---|---|---|---|
| **Tier 1** | `git merge-base --is-ancestor` | Regular merges (`--no-ff`), fast-forwards | Squash merges |
| **Tier 2** | Tree-hash lookup | Exact squash merges | Squash + subsequent main commits |
| **Tier 3** | Commit message matching (`#NNN`) | Squash merges referencing issues/PRs | Merges without issue refs |
| **Tier 4** | Content subset verification | Squash merges with post-merge evolution | (Comprehensive catch-all) |

For detached HEADs, stashes, prunable worktrees, or remote-gone branches, see [`references/edge-cases.md`](references/edge-cases.md).

## Execution Workflow

### Step 1: Run detection script

```bash
bash <skill-dir>/scripts/detect-merged-worktrees.sh [main-branch-name] [--worktrees|--branches|--all]
```

Defaults to `--all`. Scans secondary worktrees and non-main local branches. Outputs structured categories:
- `CLEANUP CANDIDATES` (merged, safe to remove)
- `NEEDS REVIEW` (ambiguous, requires diff check)
- `REDUNDANT` (intermediate commits preserved in another worktree)
- `NOT MERGED` (contains unique work, keep)
- `PRUNABLE` (worktree directory missing, metadata-only)

### Step 2: Investigate NEEDS REVIEW items

Check diffs for files reported with potential unique content:

```bash
git diff <branch-tip>..main -- <file>
```
- If differences are post-merge evolution (main has newer edits) -> promote to `MERGED`.
- If differences are unique branch work not in main -> keep as `NOT_MERGED`.

### Step 3: Present report to user

Present candidates in a clean tabular summary:

```markdown
## Worktree Cleanup Candidates (merged, safe to remove)
| Worktree | Branch | Method | Evidence |
|---|---|---|---|
| path | branch | squash-exact | tree matches main commit abc123 |

## Local Branch Cleanup Candidates (merged, safe to delete)
| Branch | Commit | Remote | Method | Evidence |
|---|---|---|---|---|
| feature/login | abc1234 | remote-gone | squash-exact | tree matches main commit def5678 |
```

Ask: *"Which of these should I clean up? You can confirm all, or exclude specific ones."*

### Step 4: Execute cleanup (after user confirmation)

#### 4a: Remove confirmed worktrees
```bash
git worktree remove <path>
# Use --force only if directory has untracked build artifacts and changes are verified in main
```

#### 4b: Delete local branches
```bash
git branch -d <branch-name>
# For squash-merged branches where git refuses -d, use -D only after merge verification
git branch -D <branch-name>
```

#### 4c: Prune remote-tracking and metadata
```bash
git remote prune origin
git worktree prune
```

### Step 5: Report results

Report removed worktrees, deleted branches, pruned metadata, and preserved active worktrees.

## Common Mistakes

- **Relying solely on `git branch --merged`**: Misses all squash merges. Always run the multi-tier script.
- **Cleaning without checking dirty state**: Always verify `git status --short` before removing any worktree.
- **Forgetting local branch deletion**: `git worktree remove` leaves the local branch ref behind. Delete the branch after removing the worktree.
