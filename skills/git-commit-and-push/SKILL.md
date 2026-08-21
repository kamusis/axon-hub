---
name: git-commit-and-push
description: Safely commit and push a completed, coherent set of repository changes. Use whenever the user asks to commit and push, publish the current branch, push finished changes, or prepare an uncommitted branch for a later pull request. Explicit invocation authorizes staging task-related files, creating one Conventional Commit, and performing a normal non-force push, but not rebasing, force-pushing, creating a PR, merging, deleting branches, or running stateful environment setup.
---

# Git Commit and Push

Commit one coherent change and publish its current branch without expanding into pull-request or integration work.

## Authorization boundary

Explicit invocation authorizes these writes:

- Stage files that clearly belong to the user's current task.
- Create one atomic Conventional Commit.
- Push the current branch normally, setting its upstream when needed.

It does not authorize:

- Force-push, rebase, reset, amend, cherry-pick, merge, or history rewriting.
- Push directly to the repository's default branch unless the user explicitly names that branch and asks to push it.
- Create or update a pull request, tag, release, issue, or ticket.
- Delete branches, worktrees, files, or stashes.
- Initialize or start services, containers, databases, migrations, fixtures, or development environments.
- Include unrelated changes merely because they are already staged.

Stop when safe continuation would require any action outside this boundary.

## Workflow

### 1. Resolve repository state

Read repository instructions, then determine:

- repository root and current worktree;
- current branch and detached-HEAD state;
- default branch;
- configured remotes and current upstream;
- staged, unstaged, and untracked changes;
- commits ahead of and behind the relevant remote branch.

Use `git status --short`, `git diff`, `git diff --cached`, and `git log` rather than inferring state from conversation history.

Stop if:

- HEAD is detached;
- no changes or unpushed commits exist;
- the current branch is the default branch without explicit permission to push that branch;
- repository identity or push target is ambiguous;
- an in-progress merge, rebase, cherry-pick, or revert exists;
- remote history would require a non-fast-forward push;
- tracked or untracked files appear to contain credentials, tokens, private keys, local databases, generated secrets, or environment-specific state.

### 2. Define the atomic change

Map every intended file to the current task. Preserve unrelated user changes.

- If all changes form one coherent unit, continue.
- If unrelated changes are present but clearly separable, stage only the task-related paths.
- If staged changes contain unrelated work, do not silently unstage or include it. Stop and report the exact ambiguity.
- If the requested work naturally requires multiple commits, stop and propose the split instead of compressing unrelated concerns into one commit.

Never use `git add .`, `git add -A`, or a broad path that can capture unreviewed files. Stage explicit file paths only.

### 3. Verify without changing runtime state

Read the repository's verification rules and inspect the changed area to select proportionate checks.

- Prefer focused tests, linters, type checks, build checks, and diff validation that do not mutate external state.
- Do not run setup, start, migration, seed, deployment, integration-preview, or service-management commands under this skill.
- Do not assume a command named `check`, `test`, or `verify` is read-only; inspect its definition when it may operate databases, containers, daemons, external services, or shared files.
- If repository policy requires a stateful full check, report that it was not run and why. Run safe focused checks when they provide meaningful evidence, then stop if repository rules prohibit committing without the full check.
- Stop on any failed required check. Do not commit known failing changes.

Always run `git diff --check`. Verification evidence must be fresh for the current diff.

### 4. Review and stage

Review the complete unstaged diff and relevant untracked files before staging. Stage only explicit intended paths, then inspect:

```bash
git status --short
git diff --cached --stat
git diff --cached --name-status
git diff --cached
git diff --cached --check
```

Confirm that the staged patch is complete, coherent, free of unrelated changes, and contains no sensitive material. Stop if it is empty or does not match the task.

### 5. Commit

Generate an accurate Conventional Commit from the staged diff:

```text
type(scope): concise imperative subject
```

Use a body only when it adds material context. Keep GitHub-facing text in English when repository rules require it. Follow repository-specific commit rules, and never add a co-author trailer unless explicitly requested and permitted.

Create one new commit. Do not amend an existing commit. After committing, verify the commit with `git show --stat --oneline --decorate HEAD` and confirm the worktree contains no newly introduced unexpected state.

### 6. Push normally

Fetch the selected remote before pushing. Verify the push remains fast-forward and targets the current branch.

- With an existing upstream, use a normal `git push` to that upstream.
- Without an upstream, use `git push -u <remote> HEAD:<current-branch>`.
- Never use `--force`, `--force-with-lease`, deletion refspecs, or a different destination branch.

If the remote branch advanced, stop and report the divergence. Do not automatically rebase or merge.

### 7. Verify publication

After pushing:

- fetch the remote branch;
- resolve local HEAD and remote branch SHA;
- require the SHAs to match;
- report the branch, commit SHA, commit subject, remote, verification commands, and any intentionally uncommitted files.

End here. A later pull-request workflow can consume the published commit.

## Failure handling

Preserve completed state. If commit succeeds but push fails, do not roll back or retry with broader options. Report the local commit SHA, exact push failure, and safe resume point.

