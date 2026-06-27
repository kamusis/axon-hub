---
name: cleaning-merged-worktrees
description: >-
  Detect and clean up git worktrees and local branches whose work has been
  merged to the main branch, including squash merges and squash merges where
  main evolved post-merge. Use this skill whenever the user mentions cleaning
  worktrees, pruning worktrees, worktree maintenance, checking merged branches,
  cleaning up local branches, stale branch cleanup, pruning branches, or any
  periodic git hygiene task. Also triggers on phrases like "clean up worktrees",
  "which worktrees are merged", "remove old worktrees", "worktree cleanup",
  "prune worktrees", "list merged worktrees", "clean up branches",
  "prune local branches", "which branches are merged", "remove stale branches",
  "delete old branches", or when the user wants to know which worktrees or
  branches are safe to delete. Handles regular merges, squash merges, squash
  merges with post-merge evolution, detached HEAD worktrees, redundant
  worktree detection, remote-gone branches, local-only branches, and abandoned
  verification branches.
---

# Cleaning Merged Git Worktrees and Local Branches

## Overview

Over time, git worktrees and local branches accumulate. Feature branches get
merged (regularly or via squash merge), but the worktree directories and local
branches remain. This skill detects which worktrees and local branches are safe
to remove and cleans them up after explicit user confirmation.

**Core challenge:** Squash merges are invisible to `git branch --merged`. The
branch's commits are not ancestors of main, and the branch tip's tree may not
exactly match any main commit (if main evolved after the squash). A naive
`--merged` check misses squash-merged worktrees and branches, leaving them to
accumulate forever. This skill uses a tiered detection algorithm that catches all
merge types without false positives.

## Safety Principles

1. **Never auto-clean.** Always present candidates with evidence, get explicit
   user confirmation, then clean.
2. **Never clean a dirty worktree.** If a worktree has uncommitted changes, skip
   it entirely and report it as "not safe".
3. **Conservative classification.** When the detection algorithm is uncertain,
   classify as NEEDS_REVIEW rather than MERGED. The agent investigates
   NEEDS_REVIEW items before presenting them to the user.
4. **No data loss.** Cleaning a worktree removes the directory and optionally the
   branch. The detection algorithm ensures the branch's work is fully in main
   before classifying as MERGED — removing the worktree and branch loses nothing.
5. **One-by-one confirmation.** The user can confirm all candidates at once or
   selectively exclude specific ones.

## Detection Algorithm

The script `scripts/detect-merged-worktrees.sh` implements a four-tier
detection algorithm. Each tier is more expensive but catches cases the previous
tier missed. A worktree or local branch is classified as MERGED if any tier
confirms it.

### Tier 1: Ancestor check (regular merge)

```
git merge-base --is-ancestor <branch-tip> main
```

If the branch tip commit is an ancestor of main, every commit on the branch is
in main's history. This catches regular merges (`git merge --no-ff`) and
fast-forward merges. Also works for detached HEAD worktrees — if the detached
commit is in main's history, it's merged.

**Catches:** regular merges, fast-forwards, any commit in main history.
**Misses:** squash merges (squash creates a new commit, original commits are not ancestors).

### Tier 2: Tree-hash lookup (squash merge, exact match)

```
tree_hash=$(git rev-parse <branch-tip>^{tree})
git log main --format="%T %H %s" | grep "^$tree_hash "
```

Every git commit points to a tree object representing the full directory state.
If the branch tip's tree object matches any commit in main's history, the exact
file state of the branch tip exists in main. This is the squash commit.

**Catches:** squash merges where the branch tip's file state exactly matches the
squash commit in main.
**Misses:** squash merges where main evolved after the squash (additional commits
changed files, so main's tree no longer matches the branch tip's tree).

### Tier 3: Commit message matching (squash detection)

Extracts issue/PR numbers (`#NNN`) from the branch's commit messages and
searches main's commit history for commits referencing the same issues. If a
main commit references the same issue AND touches overlapping files, it's likely
the squash merge of this branch.

**Catches:** squash merges that reference issue/PR numbers in commit messages.
**Misses:** squash merges without issue/PR references, or with different
numbering.

### Tier 4: Content subset verification (squash + post-merge evolution)

For branches not confirmed by Tiers 1-3, verifies that main contains all the
branch's work by comparing file contents:

1. Find the merge-base between the branch and main.
2. Get the files the branch changed since merge-base.
3. For each file, compare the branch's version to main's version:
   - **Identical** → safe (file is in main as-is).
   - **Main has additions only** (no lines from branch are missing) → safe
     (main has everything the branch has, plus more).
   - **Branch has lines not in main, but main also touched this file** → safe
     (main evolved the file after incorporating the branch's changes; the
     branch's "unique" lines are old versions that main replaced with newer
     content).
   - **Branch has lines not in main, and main did NOT touch this file** →
     NOT merged (the branch has genuinely unique work).

This tier is the catch-all. It correctly handles the case where a squash merge
brought the branch's work into main, and then main evolved further (additional
commits modified the same files). The branch's version is older, but its work is
fully represented in main's newer version.

**Catches:** squash merges with post-merge evolution, any merge where the
branch's changes are a subset of main's changes.
**False positive risk:** extremely low. For a false positive, main would need to
independently develop the exact same changes as the branch without any merge.
This is rare and the result is the same (the work is in main).

## Local Branch Detection

In addition to worktrees, the script scans all local branches. This catches the
common case where a branch was created for a PR, the PR was merged, but the local
branch was never deleted. It also catches:

- **Remote-gone branches**: Branches whose upstream has been deleted on the
  remote (e.g., after a PR was merged and the remote branch was cleaned up).
- **Local-only branches**: Branches with no upstream, such as temporary
  verification branches (`pr-NNN-verify`, `pr-NNN-reverify`) that are no longer
  needed after the PR lands.
- **Squash-merged branches**: Branches that `git branch --merged` misses because
  they were squash-merged.

Branches that are currently checked out in a worktree are skipped by the local
branch scan because they are already handled by the worktree scan.

## Execution Workflow

### Step 1: Run the detection script

```bash
bash <skill-dir>/scripts/detect-merged-worktrees.sh [main-branch-name] [--worktrees|--branches|--all]
```

The script defaults to `--all` (both worktrees and local branches). Use
`--worktrees` or `--branches` to scan only one category.

The script outputs a structured report with these categories:

#### For worktrees

- **CLEANUP CANDIDATES** — merged, safe to remove
- **NEEDS REVIEW** — ambiguous, investigate before deciding
- **REDUNDANT** — detached HEAD worktrees that are intermediate commits of
  another active branch (safe to remove without losing work, but not merged)
- **NOT MERGED** — has unique work not in main, keep
- **PRUNABLE** — worktree directory missing, metadata only

#### For local branches

- **LOCAL BRANCH CLEANUP CANDIDATES** — merged, safe to delete. The total count is
  shown first, followed by sub-counts:
  - `remote exists / no upstream` — normal merged branches
  - `remote gone` — merged branches whose upstream was deleted on the remote
    (these are the highest-priority cleanup targets)
- **LOCAL BRANCH NEEDS REVIEW** — ambiguous, investigate before deciding
- **LOCAL BRANCH NOT MERGED** — has unique work not in main, keep

### Step 2: Investigate NEEDS REVIEW items

For each NEEDS_REVIEW item, the script reports which files have potential
branch-unique content. Investigate by examining the actual diff:

```bash
git diff <branch-tip>..main -- <file>
```

Determine whether the differences are:
- **Post-merge evolution** (main has newer content in the same files) → promote
  to MERGED
- **Genuinely unique work** (branch has content main doesn't have) → keep as
  NOT_MERGED

### Step 3: Present report to user

Present the findings in a clear table format:

```
## Worktree Cleanup Candidates (merged, safe to remove)

| Worktree | Branch | Method | Evidence |
|---|---|---|---|
| path | branch | squash-exact | tree matches main commit abc123 |
| ...

## Worktree Redundant (safe to remove, work preserved in another worktree)

| Worktree | Reason |
|---|---|
| path | intermediate commit of branch X (worktree Y) |

## Worktree Keep (not merged, has unique work)

| Worktree | Branch | Reason |
|---|---|---|
| path | branch | unique content in N files |

## Local Branch Cleanup Candidates (merged, safe to delete): N

| Branch | Commit | Remote | Method | Evidence |
|---|---|---|---|---|
| issue-123 | abc1234 | remote-gone | squash-exact | tree matches main commit def5678 |
| pr-456-verify | abc1234 | no-upstream | content-subset | 5/5 files safe |
| ...

## Local Branch Keep (not merged, has unique work)

| Branch | Commit | Reason |
|---|---|---|
| feature/wip | abc1234 | unique content in N files |
```

Ask the user: "Which of these should I clean up? You can confirm all, or
exclude specific ones."

### Step 4: Execute cleanup (after confirmation)

#### 4a: Remove worktrees

For each confirmed worktree, execute in order:

```bash
git worktree remove <path>
```

If the worktree has been manually modified (files not tracked by git), use:
```bash
git worktree remove --force <path>
```

Only use `--force` if the detection script confirmed the work is in main. The
`--force` flag overrides the "dirty worktree" safety check, but since we already
verified the work is merged, this is safe.

#### 4b: Delete local branches

```bash
git branch -d <branch-name>
```

`git branch -d` (lowercase d) refuses to delete branches that haven't been
merged, providing a safety net. For squash-merged branches where `-d` refuses
(because git doesn't know about the squash), use:

```bash
git branch -D <branch-name>
```

Only use `-D` after the detection script confirmed the branch's work is in main.

For local branches that are currently checked out in a worktree, delete the
worktree first (Step 4a), then delete the branch.

#### 4c: Prune remote tracking branches (optional)

```bash
git remote prune origin
```

This cleans up remote-tracking branches that no longer exist on the remote
(e.g., after a PR was merged and the remote branch was deleted).

#### 4d: Prune stale worktree metadata

```bash
git worktree prune
```

This cleans up any leftover worktree administrative files.

### Step 5: Report results

After cleanup, report what was removed:

```
Removed:
  - worktree: /path/to/worktree (branch: feature/foo)
  - worktree: /path/to/another (branch: fix/bar)
  - branch: feature/foo (deleted)
  - branch: fix/bar (deleted)
  - branch: issue-123 (deleted, remote gone)
  - pruned: 2 stale worktree entries
  - pruned: 3 stale remote-tracking branches
Kept:
  - worktree: /path/to/active (branch: feature/wip) — not merged
  - branch: feature/wip — not merged
```

## Edge Cases

### Detached HEAD worktrees

Worktrees can be in a detached HEAD state (checked out at a specific commit,
not on a branch). The detection script handles these:

- **Tier 1** checks if the detached commit is an ancestor of main.
- **Tier 2** checks if the detached commit's tree matches any main commit.
- **Tier 3-4** use the detached commit as the ref for message matching and
  content comparison.
- **Redundancy detection** checks if the detached commit is an ancestor of any
  other worktree's branch (indicating it's an intermediate commit of work
  continuing in another worktree).

### Local branches checked out in worktrees

A branch can be associated with both a worktree and a local branch ref. The
script avoids double-reporting by tracking which branches are checked out in
worktrees and skipping them during the local branch scan.

### Worktrees with stashes

Stashes are repo-wide (shared across all worktrees), not per-worktree. The
script reports stash count once at the top. Stashes are not a reason to skip a
worktree — they persist in the repo after worktree removal.

### Prunable worktrees

If a worktree directory was deleted manually (without `git worktree remove`),
git still tracks its metadata. The script detects these as "PRUNABLE" and
recommends `git worktree prune` to clean up.

### Branch checked out in main worktree

The main worktree (the repository root) is always skipped by the detection
script. Only secondary worktrees and non-main local branches are evaluated.

### Remote-gone branches

A branch whose upstream no longer exists on the remote is flagged in the
"LOCAL BRANCH WITH GONE REMOTE" section. These are often leftover PR branches
that were deleted on the remote after merging. If the detection algorithm also
classifies the branch as MERGED, the branch is safe to delete.

## Common Mistakes

### Relying solely on `git branch --merged`

`git branch --merged main` only catches regular merges where the branch is an
ancestor of main. It misses all squash merges. This is the most common mistake
and the primary reason this skill exists.

### Using `git cherry` for squash merge detection

`git cherry` compares patch-ids, but squash merges create new commits with
different patch-ids. `git cherry` marks squash-merged commits as `+` (not
merged), giving false negatives.

### Assuming tree-hash match is sufficient

Tree-hash lookup (Tier 2) catches exact squash matches, but misses cases where
main evolved after the squash. A branch can be fully merged but have a different
tree than any main commit because main has additional commits on top.

### Cleaning without checking for uncommitted changes

A worktree might have uncommitted changes even if its branch is merged. The
detection script checks `git status --short` and skips dirty worktrees. Never
bypass this check.

### Forgetting to delete the branch after removing the worktree

`git worktree remove` removes the directory but leaves the branch. Over time,
branches accumulate. Always delete the branch after removing the worktree
(unless the user wants to keep the branch for reference).

### Ignoring remote-gone branches

After a PR is merged and the remote branch is deleted, the local branch often
remains. These branches are not in `git branch --merged` if they were
squash-merged, so they are easily missed. The local branch scan explicitly
surfaces them.

## Quick Reference

| Detection method | Catches | Misses |
|---|---|---|
| `git branch --merged` (Tier 1) | Regular merges | Squash merges |
| Tree-hash lookup (Tier 2) | Squash merges (exact) | Squash + evolution |
| Message matching (Tier 3) | Squash with issue refs | No issue refs |
| Content subset (Tier 4) | All of the above | (catch-all) |

| Classification | Action |
|---|---|
| MERGED | Present as cleanup candidate |
| NEEDS_REVIEW | Investigate diff, then classify |
| REDUNDANT | Present as redundant (safe if work is in another worktree) |
| NOT_MERGED | Keep, do not clean |
| PRUNABLE | `git worktree prune` |

Within the MERGED local-branch candidates, the remote status is shown as a
sub-category: `remote exists / no upstream` and `remote gone`. Remote-gone
branches are marked with `[REMOTE-GONE]` in the detailed list and are the
highest-priority cleanup targets.
