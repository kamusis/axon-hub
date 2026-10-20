# Worktree and Branch Edge Cases Reference

This document covers edge cases handled by `scripts/detect-merged-worktrees.sh` during cleanup analysis.

### Detached HEAD Worktrees
Worktrees can be in a detached HEAD state (checked out at a specific commit, not on a branch):
- **Tier 1** checks if the detached commit is an ancestor of main.
- **Tier 2** checks if the detached commit tree matches any main commit.
- **Tiers 3–4** use the detached commit as the ref for message matching and content comparison.
- **Redundancy detection** checks if the detached commit is an ancestor of any other worktree branch (indicating it is an intermediate commit of ongoing work).

### Local Branches Checked Out in Worktrees
A branch can be associated with both a worktree and a local branch ref. The script tracks which branches are checked out in worktrees and skips them during local branch scan to avoid duplicate reporting.

### Worktrees with Stashes
Stashes are repo-wide (`.git/refs/stash`), not per-worktree. Stashes persist after worktree removal and are not a reason to skip cleaning a worktree.

### Prunable Worktrees
In standalone host repositories, if a worktree directory was deleted manually from disk without `git worktree remove`, git retains administrative metadata and the script flags these as `PRUNABLE`.

**Critical exception — Mopheus Daemon bare caches (`.repos/<workspace-id>/*`) and task `workDir` checkouts**:
In Mopheus Agent Task sandboxes, bubblewrap (`--tmpfs`) hides sibling tasks' `workDir` directories (`*/mopheus_workspace/<workspace-id>/<task-id>/workdir/*`). As a result, `git worktree list` inside a task sandbox falsely marks every sibling task's active worktree as `prunable` (`gitdir file points to non-existent location`). NEVER run `detect-merged-worktrees.sh`, `git worktree prune`, `git worktree remove`, or `mopheus repo worktree prune` against Mopheus `.repos/*` bare caches or agent task `workDir` worktrees — their lifecycle is managed exclusively by the Mopheus Daemon GC.

### Branch Checked Out in Main Worktree
The repository root (main worktree) is always skipped by the detection script. Only secondary worktrees and non-main local branches are evaluated.

### Remote-gone Branches
A branch whose upstream was deleted on the remote is flagged with `[REMOTE-GONE]`. When also classified as `MERGED`, these are the highest-priority cleanup candidates.
