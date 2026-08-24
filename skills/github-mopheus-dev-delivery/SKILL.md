---
name: github-mopheus-dev-delivery
description: "Deliver a completed enmotech/mopheus code change end to end in one authorized run: verify, commit, push, create or reuse a GitHub PR, wait for checks, squash merge, clean the feature worktree, and update the available Mopheus ticket and GitHub issue/PR links when they exist. If no corresponding GitHub issue or Mopheus ticket can be found, skip that integration and continue delivery. Use after implementation is finished when the user wants the entire delivery workflow without repeated approvals. Always target the fixed enmotech/mopheus GitHub repository."
---

# GitHub Mopheus Dev Delivery

Treat explicit invocation as authorization for every write in this workflow: commit, push, PR creation, squash merge, remote branch deletion, verified worktree cleanup, ticket comments, repo links, and ticket completion when the corresponding records exist. Do not create a missing GitHub issue or Mopheus ticket for this workflow. If either record cannot be found, mark the integration as `SKIPPED` and continue delivery without its writes. Do not ask for step-by-step approval. Stop only on a safety blocker.

## Invariants

- Rebuild state from Git, GitHub, and Mopheus on every run. Resume idempotently; never rely on a previous chat checklist.
- Use `gh-wrapper` when available, otherwise `gh`.
- The GitHub repository is fixed to `enmotech/mopheus`; its canonical repository URL is `https://github.com/enmotech/mopheus.git`. Pass `--repo enmotech/mopheus` to every GitHub CLI command. Never derive the operation target from the current directory, `origin`, an active GitHub repository, or conversation context.
- Never force-push, merge failing checks, guess an ambiguous ticket, clean a dirty worktree, or touch unrelated branches/worktrees.
- Keep GitHub content and commit messages in English. Match the Mopheus ticket's language in comments.
- Preserve partial success on failure. Verify whether an external write succeeded before retrying it.

## Formal Mopheus CLI boundary

Delivery updates durable records in the formal Mopheus deployment, so it must never inherit a disposable preview identity or execute CLI code from the branch being delivered.

1. Resolve `mopheus` with the host PATH before any Mopheus lookup. Require the installed executable returned by `command -v mopheus` (or the platform equivalent). Stop if it is missing.
2. Never substitute `mop`, `go run ./cmd/mopheus`, `make mopheus`, a repository/worktree `server/bin/mopheus`, or a temporarily compiled binary. Those paths are valid for local development or previews, not formal delivery.
3. Use the formal `default` profile exclusively. Never use or repoint `local`, `wt-*`, or any other preview/test profile.
4. Do not source `.env.worktree`. Remove preview overrides such as `MOPHEUS_PROFILE`, `MOPHEUS_SERVER_URL`, `MOPHEUS_WORKSPACE_ID`, `MOPHEUS_TOKEN`, `MOPHEUS_AGENT_ID`, and `MOPHEUS_DAEMON_ID` from the formal CLI command environment; pass `--profile default` explicitly on every command.
5. Before resolving a workspace or ticket, bind the installed CLI's default profile to the formal deployment. Use `connect` when the installed version supports it:
   ```bash
   mopheus --profile default connect --server_url https://dev.mopheus.ai
   ```
   Current releases without `connect` must use the supported configuration command instead:
   ```bash
   mopheus --profile default config set server-url https://dev.mopheus.ai
   ```
   Then validate the existing login with `auth status`; if authentication cannot complete, run the installed CLI's formal `login --server_url https://dev.mopheus.ai` flow. Stop rather than falling back to a preview profile or repository-built CLI.
6. Verify the resulting profile with `mopheus --profile default config show --output json`, `mopheus --profile default auth status`, and `mopheus --profile default workspace list --output json`. Require the configured server URL to be exactly `https://dev.mopheus.ai` before any Mopheus write.
7. After resolving the workspace, pass both `--profile default` and `--workspace-id <id>` to every workspace-scoped Mopheus command.

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
2. Run the repository's complete required verification command fresh. Do not commit if it fails.
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

1. Fast-forward the main worktree from `origin`.
2. Delete the remote feature branch if the merge left it behind.
3. Read [cleaning-merged-worktrees](../cleaning-merged-worktrees/SKILL.md) and run its detector for the target worktree.
4. Remove only the target worktree when it is clean and classified merged with no review items.
5. Delete only its local feature branch; use `-D` solely for a detector-confirmed squash merge. Prune remote tracking and stale worktree metadata.
6. Verify the path, local branch, and remote branch are absent and `main` is clean and synchronized.
7. Check whether a standing preview harness worktree (`preview-test` or `.worktrees/preview-test`) exists. If present, update and reset it to `origin/main` (in both Windows and WSL environments when applicable) so the standing preview test environment stays synchronized with the latest delivered commit.

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
