---
name: github-mopheus-pr-delivery
description: "Squash-merge, verify, and close an existing approved enmotech/mopheus PR. Validates PR readiness, awaits checks, squash-merges, cleans local feature worktree/branch, safely fast-forwards main, and syncs Mopheus ticket. Never creates code, commits, or PRs."
---

# GitHub Mopheus PR Delivery

Deliver an existing reviewed PR from merge readiness through verified Mopheus ticket synchronization and closure when the corresponding ticket (and optional GitHub issue) exists.

Explicit invocation authorizes the writes in this workflow: squash merge, remote feature-branch deletion, verified local worktree and branch cleanup, main fast-forward, Mopheus ticket comments, repository-link synchronization, and ticket completion. It does not authorize implementation, commit creation, feature-branch pushes, PR creation or editing, review, test-environment setup, deployment, or version release.

## Operating contract

- Treat Team Leader delegation as the organizational review gate. Do not duplicate or reinterpret the team's reviewer-routing policy inside this skill.
- Independently verify every mechanical delivery fact from Git, GitHub, and Mopheus.
- Use `gh-wrapper` when available, otherwise `gh`. Use `mopheus` with an explicit workspace ID for all Mopheus operations.
- The GitHub repository is fixed to `enmotech/mopheus`; its canonical repository URL is `https://github.com/enmotech/mopheus.git`. Pass `--repo enmotech/mopheus` to every GitHub CLI command. Never derive or override the target from local Git state, PR input, an active GitHub repository, or conversation context.
- Resume idempotently from partial success. Query external state before retrying a write.
- Never force-push, bypass GitHub checks or branch protection, guess an ambiguous issue or ticket, clean a dirty worktree, or touch unrelated branches and worktrees.
- Never execute destructive git commands (such as `git reset --hard`, `git checkout -f`, or `git clean -fd`) on the main worktree or any workspace containing uncommitted changes. Always protect dirty files and uncommitted user edits.
- **Mopheus Agent Task sandbox boundary**: When running inside a Mopheus Agent Task (`$MOPHEUS_AGENT_TASK_ID` is set or the repository is backed by a `.repos/<workspace-id>` shared bare cache), sibling task `workDir` directories are hidden by bubblewrap `--tmpfs` isolation and appear as `prunable` in `git worktree list`. NEVER run `git worktree prune`, `git worktree remove`, or `mopheus repo worktree prune`, and NEVER attempt to inspect/clean another task's feature worktree or fast-forward a local `main` worktree (the Mopheus Daemon manages and GCs task worktrees automatically).
- Keep GitHub and commit content in English. Match the Mopheus ticket language in comments.

## 1. Resolve the delivery context

Resolve and verify the PR, and resolve the associated Issue/Mopheus records when they are available:

- the fixed `enmotech/mopheus` GitHub repository and its default branch;
- existing pull request, its base/head branches, current head SHA, state, draft status, author, title, and URL;
- existing GitHub issue associated through the PR body, branch context, or structured Mopheus links, when present;
- Mopheus workspace and ticket, when present;
- feature worktree and main worktree when local cleanup is possible (host local IDE/CLI environments only; skip when `$MOPHEUS_AGENT_TASK_ID` is set).

Prefer explicit task context, then PR metadata and structured Mopheus repository links. Require every supplied PR URL, issue URL, structured link, and local `origin` to identify `enmotech/mopheus`; stop on a mismatch. Pass the resolved workspace ID to every `mopheus` command and use `https://github.com/enmotech/mopheus.git` for repository-link operations.

Treat the PR, repository identity, and delegated head as mandatory. Treat the GitHub issue, Mopheus workspace, ticket, and Issue/ticket link as optional integration records. Record `github_issue=SKIPPED` or `mopheus_ticket=SKIPPED` when the corresponding record is not found, and continue with PR delivery. Do not create missing issues or tickets.

Stop when:

- the PR does not exist, is closed without being merged, is draft, or targets an unexpected base branch;
- repository or PR identity is missing or ambiguous;
- issue or ticket candidates are ambiguous, supplied identities mismatch, or the repository identity does not match;
- the PR head differs from the delegated head SHA when one was supplied;
- the PR includes unexpected commits or files outside the delegated change;
- local repository identity does not match the GitHub repository.

Return only genuine delivery blockers to Team Leader; continue when optional integration records are missing.

## 2. Validate merge readiness

Fetch the default and feature refs without modifying history. Verify:

- the local feature tip, remote feature tip, and PR head SHA agree when a local checkout exists;
- the PR is open, non-draft, and reports a mergeable state;
- the PR title already follows the repository's Conventional Commit policy;
- GitHub checks apply to the current head SHA;
- there are no failed, cancelled, timed-out, action-required, or pending required checks at merge time;
- branch protection and required approvals, when configured by GitHub, permit merge.

Wait for checks to complete using `gh pr checks <number> --repo enmotech/mopheus --watch` (or background watch + `TaskOutput` waiting until completion with `--watch`). Avoid manual shell sleep loops (`sleep 60 && gh pr checks`). If no checks are configured, record that fact and continue. If the PR head changes while waiting, restart readiness validation for the new SHA rather than merging with stale evidence.

Do not edit the PR title/body, push fixes, run implementation tests, manufacture review evidence, or override protection rules. Stop and return those prerequisites to their owning role.

## 3. Squash merge

Build a concise English squash message from the existing PR title and verified PR contents. Preserve the valid PR title as the squash subject and summarize the delivered behavior in the body.

Prefer:

```bash
gh pr merge <number> --repo enmotech/mopheus --squash --delete-branch --subject <title> --body-file <file>
```

If the merge command reports a local branch deletion problem, query the PR before retrying because the remote merge may already have succeeded. Never issue a second merge when GitHub already reports `MERGED`.

Afterward require:

- PR state is `MERGED`;
- a merge commit SHA is present;
- the merge commit is reachable from the remote default branch;
- the exact remote commit subject and body match the intended squash message;
- the merged PR head SHA is the SHA validated immediately before merge.

Stop ticket closure if merge verification is incomplete.

## 4. Update main and clean only the delivered branch

**Environment check (Mopheus Agent Task Sandbox vs. Host Local Development)**:

- **When `$MOPHEUS_AGENT_TASK_ID` is set (running inside a Mopheus Agent Task sandbox)**:
  1. Delete the remote feature branch via GitHub CLI/API if `gh pr merge --delete-branch` did not already remove it.
  2. **Skip all local `main` fast-forward, local feature worktree removal, local branch deletion, `cleaning-merged-worktrees`, `mopheus repo worktree prune`, and `git worktree prune` / `git worktree remove` steps.** In Mopheus Agent Tasks, each task's `workDir` is isolated in its own sandbox (sibling worktrees are invisible and falsely appear `prunable`), and worktree lifecycle is managed and GC'd automatically by the Mopheus Daemon. Record `local_cleanup=SKIPPED (managed by Mopheus Daemon GC)` and proceed directly to Stage 5.

- **When `$MOPHEUS_AGENT_TASK_ID` is unset (host local IDE/CLI development environment)**:
  Fast-forward the registered main worktree safely to the remote default branch:
  - Inspect the main worktree with `git status --porcelain`.
  - If dirty (uncommitted or untracked changes exist): safely stash first with `git stash push -u -m "mopheus-delivery-auto-stash"`.
  - Run safe fast-forward: `git fetch origin main && git merge --ff-only FETCH_HEAD` (or `git pull --ff-only origin main`).
  - If changes were stashed, restore them immediately with `git stash pop`.
  - **SAFETY RED LINE**: NEVER execute `git reset --hard` or `git checkout -f` on the main worktree. If fast-forward or stash pop encounters merge conflicts, preserve all user edits, STOP immediately, and report the state.

  Delete the remote feature branch if GitHub did not remove it. For local cleanup:

  1. Read and follow `cleaning-merged-worktrees`.
  2. Run its detector for the exact feature worktree.
  3. Remove only a clean worktree classified as merged with no review items.
  4. Delete only the corresponding local feature branch. Use forced local deletion solely when the detector confirms a squash merge.
  5. Prune stale remote tracking and worktree metadata.
  6. Check whether a standing preview harness worktree (`preview-test` or `.worktrees/preview-test`) exists. If present, update this disposable test harness to `origin/main` (in both Windows and WSL environments when applicable) so the standing preview test environment stays synchronized with the latest delivered commit.

  If no local worktree can be resolved, report cleanup as not applicable. If it is dirty or uncertain, preserve it and report the blocker; the verified remote merge remains successful.

  Verify the expected local/remote feature refs are absent and the main worktree is clean and synchronized when cleanup was performed.

## 5. Synchronize and close the Mopheus ticket when a ticket is resolved

Perform this stage after the remote merge is verified whenever `mopheus_ticket` was resolved (even when `github_issue` is `SKIPPED`). Skip this stage only when `mopheus_ticket` is `SKIPPED`.

1. Add one completion comment containing clickable links to the PR and merge commit (plus the GitHub issue link when `github_issue` was resolved); include the merged head SHA, check evidence, delivered behavior, and cleanup result.
2. When `github_issue` was resolved (not `SKIPPED`), refresh the issue through `mopheus repo issue sync --repo https://github.com/enmotech/mopheus.git --ticket <id>` using its actual GitHub state. When `github_issue=SKIPPED`, skip only this issue-sync step.
3. Refresh and link the PR through `mopheus repo pr sync --repo https://github.com/enmotech/mopheus.git --ticket <id>` using its actual title, author, refs, additions, deletions, changed-file count, closed state (`--state closed`), and merged flag (`--merged`).
4. Read `mopheus repo links --ticket <id>` and require the merged `git_pull_request` entry (and require the `git_issue` entry only when `github_issue` was resolved).
5. Set the ticket to `done` (if not already `done`) only after the completion comment and required structured link(s) succeed.
6. Re-read the ticket and links. Confirm the ticket is Done, the URLs are correct, the PR is recorded as merged, and the issue state is current when an issue exists.

Do not close the ticket when the PR is unmerged, required link synchronization fails, or the ticket identity is ambiguous. A missing GitHub issue (`github_issue=SKIPPED`) never skips Mopheus PR link synchronization, completion comment, or ticket closure.

## Failure and final report

Preserve every verified successful external change. Report the exact failed stage, evidence, and safe resume point. A cleanup failure after a verified merge must not trigger another merge or hide the successful remote state.

On success report only verified identifiers and evidence:

- repository and PR URL;
- merged PR head SHA and merge commit SHA;
- check result;
- main synchronization and cleanup result.
- GitHub issue URL, Mopheus workspace/ticket, and structured-link state when resolved;
- `SKIPPED` reason for each missing Issue or ticket integration.
