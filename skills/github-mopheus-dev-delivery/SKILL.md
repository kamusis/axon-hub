---
name: github-mopheus-dev-delivery
description: "Deliver a completed enmotech/mopheus code change end-to-end: run verification, commit, push, create/reuse PR, wait for checks, squash-merge, safely clean feature worktree, and sync Mopheus ticket and GitHub issue when present."
---

# GitHub Mopheus Dev Delivery

Treat explicit invocation as authorization for every write in this workflow: commit, push, PR creation, squash merge, remote branch deletion, verified worktree cleanup, ticket comments, repo links, and ticket completion when the corresponding records exist. Do not create a missing GitHub issue or Mopheus ticket for this workflow. If either record cannot be found, mark the integration as `SKIPPED` and continue delivery without its writes. Do not ask for step-by-step approval. Stop only on a safety blocker.

## Invariants

- Rebuild state from Git, GitHub, and Mopheus on every run. Resume idempotently; never rely on a previous chat checklist.
- Use `gh-wrapper` when available, otherwise `gh`.
- The GitHub repository is fixed to `enmotech/mopheus`; its canonical repository URL is `https://github.com/enmotech/mopheus.git`. Pass `--repo enmotech/mopheus` to every GitHub CLI command. Never derive the operation target from the current directory, `origin`, an active GitHub repository, or conversation context.
- Never force-push, merge failing checks, guess an ambiguous ticket, clean a dirty worktree, or touch unrelated branches/worktrees.
- Never execute destructive git commands (such as `git reset --hard`, `git checkout -f`, or `git clean -fd`) on the main worktree or any workspace containing uncommitted changes. Always protect dirty files and uncommitted user edits.
- Keep GitHub content and commit messages in English. Match the Mopheus ticket's language in comments.
- Preserve partial success on failure. Verify whether an external write succeeded before retrying it.

## Formal Mopheus CLI boundary

Delivery updates durable records in `https://dev.mopheus.ai`. Never inherit disposable preview identities or execute unreleased repository CLI binaries:
- Require the installed host `mopheus` executable (`command -v mopheus`); never substitute `mop`, `go run ./cmd/mopheus`, `make mopheus`, or `server/bin/mopheus`.
- Exclusively use the formal `--profile default`; unset preview environment variables (`MOPHEUS_PROFILE`, `MOPHEUS_SERVER_URL`, `MOPHEUS_WORKSPACE_ID`, etc.).
- Ensure configured server URL is `https://dev.mopheus.ai` (via `mopheus --profile default connect --server_url https://dev.mopheus.ai` or `config set server-url https://dev.mopheus.ai`) and verify with `auth status`.
- Pass `--profile default --workspace-id <id>` explicitly to every Mopheus command.

## 1. Resolve delivery context

1. Resolve the git root, `origin`, current feature branch/worktree, default branch, and main worktree. Require `origin` to identify `enmotech/mopheus` through an accepted HTTPS or SSH URL before any Git or GitHub write; use it only as an identity and transport check, never to select the GitHub repository.
2. Read repository instructions and identify the required full verification command.
3. Attempt to resolve exactly one existing GitHub issue from explicit context, branch/PR data, or the Mopheus ticket's structured links. This workflow does not create a new issue. If none is found, record `github_issue=SKIPPED` and continue; stop only when multiple candidates are ambiguous.
4. If Mopheus lookup is available, resolve the workspace before ticket lookup: explicit task workspace first, then a workspace matching the repository name, then the current workspace only when it contains a matching project. If no required workspace or ticket is found, record `mopheus_ticket=SKIPPED` and continue. Stop if candidates are ambiguous or formal CLI authentication/configuration is unsafe.
5. Resolve the ticket in this order: explicit ticket ID, `MOPHEUS_TICKET_ID`, current task context, then `mopheus --profile default --workspace-id <id> repo links --repo https://github.com/enmotech/mopheus.git --type git_issue --number <n>`. Do not create a ticket when this lookup returns no matching ticket.
6. If the issue exists but no ticket is linked, record `mopheus_ticket=SKIPPED`; do not invoke a ticket-creation skill. If a ticket exists but no issue is found, record `github_issue=SKIPPED` and continue without issue-linking or issue-closing actions.
7. Once a ticket is resolved, pass its workspace ID explicitly to every subsequent `mopheus` command. If either `github_issue` or `mopheus_ticket` is `SKIPPED`, omit all dependent lookup, sync, link, comment, and completion writes.

Stop on multiple candidate issues/tickets, an `origin` that does not identify `enmotech/mopheus`, unsafe formal CLI authentication/configuration, or mismatched repository identity. A missing workspace or ticket record is `SKIPPED`, not a blocker.

## 2. Verify and commit

1. Fetch the default branch and inspect status, untracked files, diff, and diff check. Confirm every intended file belongs to this change.
2. Run the repository's complete required verification command (`make check`) fresh. On Windows hosts, execute `make check` in the WSL/Linux environment where the Linux toolchain, daemon, claimkey, and race detectors reside. Require exit code 0 and confirm zero failure markers in both frontend and Go test outputs. Never commit if `make check` fails, and never substitute partial subpackage tests (`go test ./...` without `make check-web`, single package test, etc.) for the full `make check` pipeline.
3. If the intended change is uncommitted, stage only its files, inspect the complete staged diff, and create one accurate Conventional Commit without a co-author trailer.
4. If a suitable commit already exists, reuse it. Never duplicate or amend an unrelated commit.
5. Push the feature branch without force and verify local and remote tips match.

## 3. Create or reuse the PR

1. Look up an existing PR by head branch before creating one.
2. If absent, create a ready-for-review PR against the default branch with a Conventional Commit title and an English body covering description, changes, and test evidence. Add `Closes #<issue>` only when `github_issue` was resolved; otherwise omit issue-closing language.
3. Verify PR number, URL, base/head branches, commit set, and merge-base diff. Use three-dot diff for the PR scope when the default branch advanced.
4. Treat an existing matching PR as success; never create a duplicate.

## 4. Wait and squash merge

1. Poll checks with bounded waits until terminal. Continue when no checks are configured. Stop on failed/cancelled checks, conflicts, missing required approval, draft state, or branch-protection denial.
2. Require the PR to be open and mergeable. Validate or fix its Conventional Commit title.
3. Generate a concise squash body with major changes and relevant minor improvements.
4. Prefer `gh pr merge --repo enmotech/mopheus --squash --delete-branch --subject <title> --body-file <file>` when supported.
5. If the merge command reports a local branch deletion error, query the PR before retrying; the remote merge may already have succeeded.
6. Verify `MERGED`, capture the merge SHA, and read the remote commit through the GitHub API to confirm its exact message.

## 5. Update main and clean only this worktree

1. Fast-forward the main worktree safely from `origin`:
   - Inspect the main worktree with `git status --porcelain`.
   - If dirty (uncommitted or untracked changes exist): safely stash first with `git stash push -u -m "mopheus-delivery-auto-stash"`.
   - Run safe fast-forward: `git fetch origin main && git merge --ff-only FETCH_HEAD` (or `git pull --ff-only origin main`).
   - If changes were stashed, restore them immediately with `git stash pop`.
   - **SAFETY RED LINE**: NEVER execute `git reset --hard` or `git checkout -f` on the main worktree. If fast-forward or stash pop encounters merge conflicts, preserve all user edits, STOP immediately, and report the state.
2. Delete the remote feature branch if the merge left it behind.
3. Read [cleaning-merged-worktrees](../cleaning-merged-worktrees/SKILL.md) and run its detector for the target worktree.
4. Remove only the target worktree when it is clean and classified merged with no review items.
5. Delete only its local feature branch; use `-D` solely for a detector-confirmed squash merge. Prune remote tracking and stale worktree metadata.
6. Verify the path, local branch, and remote branch are absent and `main` is clean and synchronized.
7. Check whether a standing preview harness worktree (`preview-test` or `.worktrees/preview-test`) exists. If present, update this disposable test harness to `origin/main` (in both Windows and WSL environments when applicable) so the standing preview test environment stays synchronized with the latest delivered commit.

## 6. Close the Mopheus ticket when both records exist

Perform this only after the merge is verified and both `github_issue` and `mopheus_ticket` were resolved. If either is `SKIPPED`, skip this entire section and continue to the final report.

1. Add one completion comment with clickable Markdown links to the GitHub issue, PR, and merge commit; summarize delivered behavior and fresh verification evidence.
2. Refresh and formally link the issue with `mopheus --profile default --workspace-id <workspace-id> repo issue sync --repo https://github.com/enmotech/mopheus.git` using its actual state.
3. Refresh and formally link the PR with `mopheus --profile default --workspace-id <workspace-id> repo pr sync --repo https://github.com/enmotech/mopheus.git`, including actual title, author, refs, additions, deletions, changed files, closed state, and merged flag.
4. Read `mopheus --profile default --workspace-id <workspace-id> repo links --ticket <id>` and require both the `git_issue` and merged `git_pull_request` entries.
5. Set the ticket to `done` only after the comment and both links succeed.
6. Re-read the ticket and links; confirm Done, correct URLs, closed issue state, and merged PR state.

## Failure and final report

On a blocker, leave completed external state intact and report the exact failed stage, evidence, and safe resume point. Do not mark the ticket Done. A missing issue or ticket is not a blocker: report the corresponding integration as `SKIPPED` and continue.

On success, report only verified identifiers and URLs: commit, PR, merge SHA, cleanup result, and verification command. Include issue, ticket, and link state when resolved; otherwise report the exact `SKIPPED` reason for each missing record.
