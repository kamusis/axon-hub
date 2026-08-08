---
name: github-mopheus-dev-delivery
description: "Deliver a completed Mopheus code change end to end in one authorized run: verify, commit, push, create or reuse a GitHub PR, wait for checks, squash merge, clean the feature worktree, update the Mopheus ticket, and formally link its GitHub issue and PR. Use after implementation is finished when the user wants the entire delivery and ticket-closure workflow without repeated approvals."
---

# GitHub Mopheus Dev Delivery

Treat explicit invocation as authorization for every write in this workflow: commit, push, PR creation, squash merge, remote branch deletion, verified worktree cleanup, ticket creation when required, ticket comments, repo links, and ticket completion. Do not ask for step-by-step approval. Stop only on a safety blocker.

## Invariants

- Rebuild state from Git, GitHub, and Mopheus on every run. Resume idempotently; never rely on a previous chat checklist.
- Use `gh-wrapper` when available, otherwise `gh`. Use `moclaw` for all Mopheus operations.
- Never force-push, merge failing checks, guess an ambiguous ticket, clean a dirty worktree, or touch unrelated branches/worktrees.
- Keep GitHub content and commit messages in English. Match the Mopheus ticket's language in comments.
- Preserve partial success on failure. Verify whether an external write succeeded before retrying it.

## 1. Resolve delivery context

1. Resolve the git root, `origin`, GitHub `owner/repo`, current feature branch/worktree, default branch, and main worktree.
2. Read repository instructions and identify the required full verification command.
3. Resolve exactly one existing GitHub issue from explicit context, branch/PR data, or the Mopheus ticket's structured links. This post-implementation workflow does not create a new issue; stop if none can be identified uniquely.
4. Resolve the Mopheus workspace before lookup: explicit task workspace first, then a workspace matching the repository name, then the current workspace only when it contains a matching project. Stop if candidates are ambiguous.
5. Resolve the ticket in this order: explicit ticket ID, `MOCLAW_TICKET_ID`, current task context, then `moclaw --workspace-id <id> repo links --repo <origin-url> --type git_issue --number <n>`.
6. If the issue exists but no ticket is linked, read and invoke [github-issue-to-mopheus-dev-ticket](../github-issue-to-mopheus-dev-ticket/SKILL.md) in its existing-Issue mode. Reuse the created ticket and continue.
7. Once resolved, pass the ticket's workspace ID explicitly to every subsequent `moclaw` command.

Stop on multiple candidate issues/tickets, a non-GitHub origin, a missing required workspace, or mismatched repository identity.

## 2. Verify and commit

1. Fetch the default branch and inspect status, untracked files, diff, and diff check. Confirm every intended file belongs to this change.
2. Run the repository's complete required verification command fresh. Do not commit if it fails.
3. If the intended change is uncommitted, stage only its files, inspect the complete staged diff, and create one accurate Conventional Commit without a co-author trailer.
4. If a suitable commit already exists, reuse it. Never duplicate or amend an unrelated commit.
5. Push the feature branch without force and verify local and remote tips match.

## 3. Create or reuse the PR

1. Look up an existing PR by head branch before creating one.
2. If absent, create a ready-for-review PR against the default branch with a Conventional Commit title and an English body covering description, changes, test evidence, and `Closes #<issue>`.
3. Verify PR number, URL, base/head branches, commit set, and merge-base diff. Use three-dot diff for the PR scope when the default branch advanced.
4. Treat an existing matching PR as success; never create a duplicate.

## 4. Wait and squash merge

1. Poll checks with bounded waits until terminal. Continue when no checks are configured. Stop on failed/cancelled checks, conflicts, missing required approval, draft state, or branch-protection denial.
2. Require the PR to be open and mergeable. Validate or fix its Conventional Commit title.
3. Generate a concise squash body with major changes and relevant minor improvements.
4. Prefer `gh pr merge --squash --delete-branch --subject <title> --body-file <file>` when supported.
5. If the merge command reports a local branch deletion error, query the PR before retrying; the remote merge may already have succeeded.
6. Verify `MERGED`, capture the merge SHA, and read the remote commit through the GitHub API to confirm its exact message.

## 5. Update main and clean only this worktree

1. Fast-forward the main worktree from `origin`.
2. Delete the remote feature branch if the merge left it behind.
3. Read [cleaning-merged-worktrees](../cleaning-merged-worktrees/SKILL.md) and run its detector for the target worktree.
4. Remove only the target worktree when it is clean and classified merged with no review items.
5. Delete only its local feature branch; use `-D` solely for a detector-confirmed squash merge. Prune remote tracking and stale worktree metadata.
6. Verify the path, local branch, and remote branch are absent and `main` is clean and synchronized.

## 6. Close the Mopheus ticket

Perform this only after the merge is verified.

1. Add one completion comment with clickable Markdown links to the GitHub issue, PR, and merge commit; summarize delivered behavior and fresh verification evidence.
2. Refresh and formally link the issue with `moclaw repo issue sync` using its actual state.
3. Refresh and formally link the PR with `moclaw repo pr sync`, including actual title, author, refs, additions, deletions, changed files, closed state, and merged flag.
4. Read `moclaw repo links --ticket <id>` and require both the `git_issue` and merged `git_pull_request` entries.
5. Set the ticket to `done` only after the comment and both links succeed.
6. Re-read the ticket and links; confirm Done, correct URLs, closed issue state, and merged PR state.

## Failure and final report

On a blocker, leave completed external state intact and report the exact failed stage, evidence, and safe resume point. Do not mark the ticket Done.

On success, report only verified identifiers and URLs: commit, PR, merge SHA, issue, ticket, link state, cleanup result, and verification command.
