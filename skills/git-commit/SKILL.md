---
name: git-commit
description: Safely stage and commit a coherent set of repository changes locally without pushing. Use whenever the user asks to commit changes, make a commit, save changes to git, or run git commit without publishing to remote. Explicit invocation authorizes staging task-related files, running non-mutating verification, generating a Conventional Commit message from the staged diff, and creating one local commit, but strictly forbids pushing, rebasing, amending, or resetting.
---

# Git Commit

Stage and commit one coherent set of changes locally without pushing or modifying remote state.

## Authorization boundary

Explicit invocation authorizes these writes:

- Stage files that clearly belong to the user's current task.
- Create one atomic Conventional Commit locally.
- Run safe, non-mutating verification commands (e.g. linters, typechecks, unit tests, `git diff --check`).

It strictly does NOT authorize:

- **Pushing to any remote repository (`git push`)**.
- Force-push, rebase, reset, amend, cherry-pick, merge, or history rewriting.
- Creating or updating pull requests, tags, releases, issues, or tickets.
- Deleting branches, worktrees, files, or stashes.
- Using indiscriminate staging commands (`git add .`, `git add -A`).
- Including unrelated or sensitive files (secrets, tokens, credentials, `.env` files).

Stop when safe continuation would require any action outside this boundary.

## Workflow

### 1. Resolve repository state

Inspect the working tree state using read-only git commands:

```bash
git status --short
git diff
git diff --cached
git log -n 5 --oneline
```

Determine:
- Repository root and current worktree.
- Current branch and detached-HEAD state.
- Staged, unstaged, and untracked changes.

Stop if:
- HEAD is detached.
- There are no changes to commit.
- An in-progress merge, rebase, cherry-pick, or revert exists.
- Working files appear to contain credentials, private keys, local databases, or secrets.

### 2. Define the atomic change

Map every intended file to the current task. Preserve unrelated user changes.

- If all changes form one coherent unit, continue.
- If unrelated changes are present, stage only the task-related paths.
- If staged changes contain unrelated work, do not silently unstage or commit it. Stop and report the ambiguity.
- If the requested work naturally requires multiple commits, stop and propose the split.

Never use `git add .` or `git add -A`. Stage explicit file paths only:

```bash
git add path/to/file1 path/to/file2
```

### 3. Verify without changing runtime state

Inspect the staged changes and run proportionate, non-mutating checks:

- Run `git diff --cached --check` to catch whitespace errors and merge artifacts.
- Run package/project-specific type checks, linters, or focused unit tests (e.g., `pnpm typecheck`, `vitest run <test-file>`, `go test ./...`).
- Do not run stateful migrations, server startups, or external service mutating commands under this skill.
- Stop immediately on any failed verification. Never commit broken or failing code.

### 4. Review staged diff

Review the staged patch before committing:

```bash
git status --short
git diff --cached --stat
git diff --cached --name-status
git diff --cached
```

Confirm that the staged patch is complete, coherent, free of unrelated changes, and contains no sensitive material.

### 5. Generate Conventional Commit message

Analyze the staged changes and formulate an accurate Conventional Commit message:

```text
type(scope): concise imperative subject

Major changes:
- Change 1 description
- Change 2 description

Minor improvements:
- Improvement 1 description
```

- **Commit types**: `feat`, `fix`, `refactor`, `docs`, `chore`, `perf`, `test`.
- **Subject**: Under 50 characters, present tense imperative mood (`add`, not `added`), lowercase/natural casing.
- **Body**: Optional for small changes; structured with bullet points for broader changes.
- **Language**: English for commit messages as required by community guidelines and project rules.
- **Trailer**: Do not add `Co-Authored-By` trailers unless explicitly requested.

### 6. Create the local commit

Commit the staged changes:

```bash
git commit -m "type(scope): subject" -m "Major changes: ..."
```

Or write the message to a temporary file and use `git commit -F <file>`.

### 7. Verify local commit

After committing:

```bash
git show --stat --oneline --decorate HEAD
git status --short
```

Verify:
- The new commit exists and contains exactly the intended file diffs.
- The worktree is clean or contains only intentionally preserved uncommitted files.
- **DO NOT push to remote.**

Report the commit SHA, branch, commit subject, verified tests, and list any uncommitted files that were preserved.
