---
name: github-swissql-dev-delivery
description: "Deliver a completed enmotech/swissql-core code change end-to-end: run dual verification (Maven + Go), commit, push, create/reuse PR, wait for checks, squash-merge, safely clean feature worktree, and sync Mopheus ticket and GitHub issue when present."
---

# GitHub SwissQL Dev Delivery

Treat explicit invocation as authorization for every write in this workflow: commit, push, PR creation, squash merge, remote branch deletion, verified worktree cleanup, ticket comments, repo links, and ticket completion when the corresponding records exist. Do not create a missing GitHub issue or Mopheus ticket for this workflow. If either record cannot be found, mark the integration as `SKIPPED` and continue delivery without its writes. Do not ask for step-by-step approval. Stop only on a safety blocker.

## Invariants

- Rebuild state from Git, GitHub, and Mopheus on every run. Resume idempotently; never rely on a previous chat checklist.
- Use `gh-wrapper` when available, otherwise `gh`.
- The GitHub repository is fixed to `enmotech/swissql-core`; its canonical repository URL is `https://github.com/enmotech/swissql-core.git`. Pass `--repo enmotech/swissql-core` to every GitHub CLI command.
- Acceptable `origin` targets: URLs resolving to `enmotech/swissql-core` or authorized push remotes (e.g. `kamusis/swissql-core` redirecting upstream).
- Never force-push, merge failing checks, guess an ambiguous ticket, clean a dirty worktree, or touch unrelated branches/worktrees.
- Never execute destructive git commands (such as `git reset --hard`, `git checkout -f`, or `git clean -fd`) on the main worktree or any workspace containing uncommitted changes. Always protect dirty files and uncommitted user edits.
- Keep GitHub content and commit messages in English. Match the Mopheus ticket's language in comments (typically Chinese).
- Preserve partial success on failure. Verify whether an external write succeeded before retrying it.

## Formal Mopheus CLI boundary

Delivery updates durable records in `https://dev.mopheus.ai`. Never inherit disposable preview identities:
- Require the installed host `mopheus` or `mop` executable (`command -v mopheus` or `command -v mop`).
- Exclusively use the formal `--profile default`; unset preview environment variables (`MOPHEUS_PROFILE`, `MOPHEUS_SERVER_URL`, `MOPHEUS_WORKSPACE_ID`, etc.).
- Ensure configured server URL is `https://dev.mopheus.ai` (verify with `mop auth status`).
- Pass `--profile default --workspace-id <id>` (or ensure active workspace is `dev` / `dev-space`) explicitly to Mopheus commands when needed.

---

## 1. Resolve delivery context

1. Resolve the git root, `origin`, current feature branch/worktree, default branch (`main`), and main worktree.
2. Attempt to resolve exactly one existing GitHub issue from explicit context, branch/PR data, or the Mopheus ticket's structured links. If none is found, record `github_issue=SKIPPED` and continue; stop only when multiple candidates are ambiguous.
3. Resolve the Mopheus workspace: default to `dev` workspace (slug `dev-space`, project `swissql-core`).
4. Resolve the Mopheus ticket in this order: explicit ticket ID/UUID, `MOPHEUS_TICKET_ID`, current task context, then:
   ```bash
   mop repo links --repo https://github.com/enmotech/swissql-core.git --type git_issue --number <issue_number>
   ```
   Do not create a ticket if no matching ticket is found.
5. If the issue exists but no ticket is linked, record `mopheus_ticket=SKIPPED`. If a ticket exists but no issue is found, record `github_issue=SKIPPED` and continue without issue-linking or issue-closing actions.
6. If either `github_issue` or `mopheus_ticket` is `SKIPPED`, omit dependent link, comment, and completion writes.

Stop on multiple candidate issues/tickets, an origin that does not map to `swissql-core`, or unsafe CLI authentication.

---

## 2. Verify and commit

SwissQL Core is a dual-language architecture. **Both test suites MUST be executed fresh and pass with 0 errors/failures.**

1. Fetch the default branch:
   ```bash
   git fetch origin main
   ```
2. **Dual-Stack Verification (Mandatory)**:
   - **CLI (Go)**:
     ```bash
     cd swissql-cli && go test -count=1 ./...
     ```
     Require exit code 0 and 100% pass across all packages (`client`, `cmd`, `internal/config`, `internal/setup`).
   - **Backend (Java / Maven)**:
     ```bash
     mvn -f swissql-backend/pom.xml test -Dtest=!JdbcDriverAutoLoaderTest
     ```
     Require `BUILD SUCCESS`, 0 failures, 0 errors.
   - **RED LINE**: Never commit if either test suite fails. Never substitute one for the other.
3. If the intended change is uncommitted:
   - Inspect status, untracked files, and diff.
   - Stage only files belonging to the change (`git add ...`).
   - Create one accurate Conventional Commit without a co-author trailer.
4. Push the feature branch without force and verify local and remote tips match:
   ```bash
   git push origin <feature-branch>
   ```

---

## 3. Create or reuse the PR

1. Look up an existing PR by head branch on `enmotech/swissql-core`:
   ```bash
   gh pr list --repo enmotech/swissql-core --head <feature-branch> --json number,title,url,state
   ```
2. If absent, create a ready-for-review PR against `main`:
   - Title: Conventional Commit format (e.g. `feat: ...` or `fix: ...`).
   - Body: English description covering summary, component changes (Backend / CLI / Docs), and verification evidence.
   - Add `Closes #<issue>` if `github_issue` was resolved; otherwise omit closing language.
   ```bash
   gh pr create --repo enmotech/swissql-core --base main --head <feature-branch> --title "<title>" --body-file "<file>"
   ```
3. Capture the PR number and URL.

---

## 4. Wait and squash merge

1. Poll checks if configured:
   ```bash
   gh pr checks <pr-number> --repo enmotech/swissql-core
   ```
   Continue when no checks are configured. Stop on failed/cancelled checks, conflicts, or draft state.
2. Require the PR to be open and mergeable. Validate its Conventional Commit title.
3. Execute squash merge:
   ```bash
   gh pr merge <pr-number> --repo enmotech/swissql-core --squash --delete-branch --subject "<title>" --body-file "<squash-body-file>"
   ```
4. Verify merge state and capture the merge commit SHA:
   ```bash
   gh pr view <pr-number> --repo enmotech/swissql-core --json state,mergedAt,mergeCommit
   ```
5. Confirm that the associated GitHub issue transitioned to `CLOSED`.

---

## 5. Update main and clean only this worktree

1. Fast-forward the main worktree safely:
   - Switch or navigate to the main worktree directory.
   - Inspect status with `git status --porcelain`.
   - If dirty: safely stash uncommitted user changes first (`git stash push -u -m "swissql-delivery-auto-stash"`).
   - Fetch and update:
     ```bash
     git fetch origin main && git merge --ff-only FETCH_HEAD
     ```
     (If diverged due to local chore commits, safe rebase `git rebase FETCH_HEAD` to maintain clean fast-forward).
   - If changes were stashed, restore them immediately: `git stash pop`.
   - **SAFETY RED LINE**: NEVER execute `git reset --hard` or `git checkout -f` on the main worktree.
2. Remove the temporary feature worktree:
   ```bash
   git worktree remove .worktrees/<worktree-name>
   ```
3. Delete the local feature branch:
   ```bash
   git branch -D <feature-branch>
   ```
4. Prune stale remote tracking refs:
   ```bash
   git remote prune origin
   ```
5. Verify `git worktree list` shows only the main worktree and `git status` on main is clean and synchronized.

---

## 6. Close the Mopheus ticket when both records exist

Perform this only after the merge is verified and both `github_issue` and `mopheus_ticket` were resolved. If either is `SKIPPED`, skip this section.

1. Add one completion comment to the Mopheus ticket (in Chinese, matching ticket language):
   - Include clickable Markdown links to the GitHub issue, PR, and merge commit.
   - Summarize delivered components, behavior changes, and verification test results.
   ```bash
   mop ticket comment add <ticket-id> --content-file "<file>"
   ```
2. Refresh and formally link the issue:
   ```bash
   mop repo issue sync --number <issue-number> --state closed --ticket <ticket-id> --repo https://github.com/enmotech/swissql-core
   ```
3. Refresh and formally link the merged PR:
   ```bash
   mop repo pr sync --number <pr-number> --state closed --merged --ticket <ticket-id> --repo https://github.com/enmotech/swissql-core --title "<pr-title>" --base main --head <feature-branch> --close-keyword
   ```
4. Verify structured links on the ticket:
   ```bash
   mop repo links --ticket <ticket-id>
   ```
   Confirm both `git_issue` and merged `git_pull_request` entries are present.
5. Set ticket status to `done`:
   ```bash
   mop ticket update <ticket-id> --status done
   ```
6. Re-read the ticket to confirm status `done`.

---

## Failure and final report

- On a blocker: Leave completed external state intact. Report the exact failed stage, evidence, and safe resume point. Do not mark the ticket Done.
- On success: Report only verified identifiers and URLs:
  - Commit SHA & PR URL
  - Merge Commit SHA
  - Closed GitHub Issue URL
  - Mopheus Ticket UUID, title, and updated `done` status
  - Worktree cleanup confirmation
  - Verification test results
