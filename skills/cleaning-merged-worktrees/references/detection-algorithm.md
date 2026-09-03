# Worktree and Branch Detection Algorithm Reference

This document details the four-tier detection algorithm used by `scripts/detect-merged-worktrees.sh` to classify git worktrees and local branches without false positives or missed squash merges.

## The Detection Ladder

Each tier catches cases missed by previous tiers. A candidate is classified as MERGED as soon as any tier confirms it.

```
Candidate Branch / Worktree
       │
       ▼
[Tier 1: Ancestor Check] ───────────► MERGED (regular merge / fast-forward)
       │ (Misses squash merges)
       ▼
[Tier 2: Tree-hash Lookup] ──────────► MERGED (exact squash merge)
       │ (Misses main post-merge evolution)
       ▼
[Tier 3: Commit Message Matching] ──► MERGED (squash with issue/PR refs)
       │ (Misses merges without issue refs)
       ▼
[Tier 4: Content Subset Verification] ► MERGED (squash + post-merge evolution)
       │
       ▼
NOT MERGED / NEEDS REVIEW
```

---

### Tier 1: Ancestor Check (Regular Merges)

`git merge-base --is-ancestor <branch-tip> main`

If the branch tip commit is an ancestor of main, every commit on the branch is in main history. Also works for detached HEAD worktrees.
- **Catches**: Regular merges (`git merge --no-ff`), fast-forwards, any commit in main history.
- **Misses**: Squash merges (squash creates a new commit; original commits are not ancestors).

---

### Tier 2: Tree-hash Lookup (Exact Squash Merges)

```bash
tree_hash=$(git rev-parse <branch-tip>^{tree})
git log main --format="%T %H %s" | grep "^$tree_hash "
```

Every git commit points to a tree object representing the full directory state. If the branch tip tree matches any commit in main history, the exact file state of the branch exists in main.
- **Catches**: Squash merges where the branch tip file state matches the squash commit.
- **Misses**: Squash merges where main evolved after the squash (subsequent commits touched files, altering main tree).

---

### Tier 3: Commit Message Matching (Squash with References)

Extracts issue/PR numbers (`#NNN`) from the branch commit messages and searches main commit history for commits referencing the same issues. If a main commit references the same issue AND touches overlapping files, it is classified as the squash merge.
- **Catches**: Squash merges referencing issue/PR numbers in commit messages.
- **Misses**: Squash merges without issue/PR references or with different numbering.

---

### Tier 4: Content Subset Verification (Squash + Post-merge Evolution)

For branches not confirmed by Tiers 1–3, verifies that main contains all the branch work by comparing file contents:
1. Find the merge-base between branch and main.
2. Get the files changed by the branch since merge-base.
3. For each file, compare branch version to main version:
   - **Identical** -> Safe (file exists in main as-is).
   - **Main has additions only** -> Safe (main contains all branch additions plus more).
   - **Branch has lines not in main, but main also touched this file** -> Safe (main evolved the file after incorporating branch changes; unique lines are superseded versions).
   - **Branch has lines not in main, and main did NOT touch this file** -> NOT merged (unique work exists only on branch).

- **Catches**: Squash merges with subsequent changes on main; any merge where branch changes are a subset of main.
- **False positive risk**: Extremely low. Requires main to independently develop identical changes without merging.
