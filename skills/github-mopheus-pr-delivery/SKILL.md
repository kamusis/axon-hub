---
name: github-mopheus-pr-delivery
description: "Complete delivery of an already-created and reviewed Mopheus pull request: validate the existing PR and linked issue/ticket, wait for GitHub checks, squash merge, verify the merge, safely clean the feature worktree and branches, synchronize Mopheus repository links, add completion evidence, and close the ticket. Use when the Dev Team leader explicitly hands an approved PR to the Mopheus Release Agent for merge and closure. This skill starts at PR delivery and never implements code, commits, pushes feature changes, creates a PR, performs review, or publishes a version."
---

# GitHub Mopheus PR Delivery

Deliver an existing reviewed PR from merge readiness through verified Mopheus ticket closure.

Explicit invocation authorizes the writes in this workflow: squash merge, remote feature-branch deletion, verified local worktree and branch cleanup, main fast-forward, Mopheus ticket comments, repository-link synchronization, and ticket completion. It does not authorize implementation, commit creation, feature-branch pushes, PR creation or editing, review, test-environment setup, deployment, or version release.

## Operating contract

- Treat Team Leader delegation as the organizational review gate. Do not duplicate or reinterpret the team's reviewer-routing policy inside this skill.
- Independently verify every mechanical delivery fact from Git, GitHub, and Mopheus.
- Use `gh-wrapper` when available, otherwise `gh`. Use `mopheus` with an explicit workspace ID for all Mopheus operations.
- Resume idempotently from partial success. Query external state before retrying a write.
- Never force-push, bypass GitHub checks or branch protection, guess an ambiguous issue or ticket, clean a dirty worktree, or touch unrelated branches and worktrees.
- Keep GitHub and commit content in English. Match the Mopheus ticket language in comments.

## 1. Resolve the delivery context

Resolve and verify exactly one of each:

- GitHub repository and default branch;
- existing pull request, its base/head branches, current head SHA, state, draft status, author, title, and URL;
- existing GitHub issue associated through the PR body, branch context, or structured Mopheus links;
- Mopheus workspace and ticket;
- feature worktree and main worktree when local cleanup is possible.

Prefer explicit task context, then PR metadata and structured Mopheus repository links. Pass the resolved workspace ID to every `mopheus` command.

Stop when:

- the PR does not exist, is closed without being merged, is draft, or targets an unexpected base branch;
- repository, PR, issue, workspace, or ticket identity is missing or ambiguous;
- the issue and ticket are not already linked;
- the PR head differs from the delegated head SHA when one was supplied;
- the PR includes unexpected commits or files outside the delegated change;
- local repository identity does not match the GitHub repository.

Do not create missing issues, tickets, commits, branches, or PRs. Return the missing prerequisite to Team Leader.

## 2. Validate merge readiness

Fetch the default and feature refs without modifying history. Verify:

- the local feature tip, remote feature tip, and PR head SHA agree when a local checkout exists;
- the PR is open, non-draft, and reports a mergeable state;
- the PR title already follows the repository's Conventional Commit policy;
- GitHub checks apply to the current head SHA;
- there are no failed, cancelled, timed-out, action-required, or pending required checks at merge time;
- branch protection and required approvals, when configured by GitHub, permit merge.

Poll checks with bounded waits until terminal. If no checks are configured, record that fact and continue. If the PR head changes while waiting, restart readiness validation for the new SHA rather than merging with stale evidence.

Do not edit the PR title/body, push fixes, run implementation tests, manufacture review evidence, or override protection rules. Stop and return those prerequisites to their owning role.

## 3. Squash merge

Build a concise English squash message from the existing PR title and verified PR contents. Preserve the valid PR title as the squash subject and summarize the delivered behavior in the body.

Prefer:

```bash
gh pr merge <number> --squash --delete-branch --subject <title> --body-file <file>
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

Fast-forward the registered main worktree to the remote default branch. Do not merge or reset a divergent or dirty main worktree.

Delete the remote feature branch if GitHub did not remove it. For local cleanup:

1. Read and follow `cleaning-merged-worktrees`.
2. Run its detector for the exact feature worktree.
3. Remove only a clean worktree classified as merged with no review items.
4. Delete only the corresponding local feature branch. Use forced local deletion solely when the detector confirms a squash merge.
5. Prune stale remote tracking and worktree metadata.

If no local worktree can be resolved, report cleanup as not applicable. If it is dirty or uncertain, preserve it and report the blocker; the verified remote merge remains successful.

Verify the expected local/remote feature refs are absent and the main worktree is clean and synchronized when cleanup was performed.

## 5. Synchronize and close the Mopheus ticket

Perform this stage only after the remote merge is verified.

1. Add one completion comment containing clickable links to the GitHub issue, PR, and merge commit; include the merged head SHA, check evidence, delivered behavior, and cleanup result.
2. Refresh the issue through `mopheus repo issue sync` using its actual GitHub state.
3. Refresh the PR through `mopheus repo pr sync` using its actual title, author, refs, additions, deletions, changed-file count, closed state, and merged flag.
4. Read `mopheus repo links --ticket <id>` and require both the `git_issue` and merged `git_pull_request` entries.
5. Set the ticket to `done` only after the completion comment and both structured links succeed.
6. Re-read the ticket and links. Confirm the ticket is Done, the URLs are correct, the issue state is current, and the PR is recorded as merged.

Do not close the ticket when the PR is unmerged, link synchronization fails, or the ticket identity is ambiguous.

## Failure and final report

Preserve every verified successful external change. Report the exact failed stage, evidence, and safe resume point. A cleanup failure after a verified merge must not trigger another merge or hide the successful remote state.

On success report only verified identifiers and evidence:

- repository and PR URL;
- merged PR head SHA and merge commit SHA;
- GitHub issue URL;
- Mopheus workspace and ticket;
- check result;
- structured-link state;
- main synchronization and cleanup result.
