---
name: using-git-worktrees
description: Create and switch to an isolated git worktree for feature development. Syncs local main with remote before branching, selects local .worktrees or global storage, verifies .gitignore isolation, and halts before environment setup or commits.
---

# Using Git Worktrees

## Overview

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Synced `main` baseline + systematic directory selection + safety verification = reliable isolation.

## Directory Selection Process

Follow this priority order:

### 1. Check Existing Directories

```bash
# Check in priority order
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Check CLAUDE.md / AGENTS.md

```bash
grep -i "worktree.*director" CLAUDE.md AGENTS.md 2>/dev/null
```

**If preference specified:** Use it without asking.

### 3. Ask User

If no directory exists and no configuration preference:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden)
2. ~/.config/superpowers/worktrees/<project-name>/ (global location)

Which would you prefer?
```

## Safety Verification

### For Project-Local Directories (.worktrees or worktrees)

**MUST verify directory is ignored before creating worktree:**

```bash
# Check if directory is ignored (respects local, global, and system gitignore)
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```

**If NOT ignored:**

1. Add the worktree directory (`.worktrees/` or `worktrees/`) to `.gitignore`.
2. Commit the `.gitignore` update immediately.
3. Proceed with worktree creation.

**Why critical:** Prevents accidentally committing worktree contents to repository.

### For Global Directory (~/.config/superpowers/worktrees)

No .gitignore verification needed - outside project entirely.

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Sync Local `main` Branch

**MUST ensure local `main` is up to date with `origin/main` before creating the worktree:**

```bash
# Fetch latest main from remote and fast-forward local main safely
current_branch=$(git symbolic-ref --short -q HEAD)
if [ "$current_branch" = "main" ]; then
  git fetch origin main
  git merge --ff-only origin/main
else
  # Fast-forward local main ref directly without switching current checkout
  git fetch origin main:main
fi
```

**If fast-forward fails** (e.g., local `main` has unpushed or diverged commits):
- **STOP** and report the divergence to the user before creating the worktree.

### 3. Create Worktree from `main`

```bash
# Determine full path
case $LOCATION in
  .worktrees|worktrees)
    path="$LOCATION/$BRANCH_NAME"
    ;;
  ~/.config/superpowers/worktrees/*)
    path="~/.config/superpowers/worktrees/$project/$BRANCH_NAME"
    ;;
esac

# Create worktree with new branch explicitly starting from synced local main
git worktree add "$path" -b "$BRANCH_NAME" main
cd "$path"
```

### 4. Stop at Git Isolation

Creating a worktree ends after `git worktree add` and changing into the new directory. Do not automatically install dependencies, build code, run tests, create environment files, start containers or services, create databases, or run migrations.

Treat every environment preparation or verification command as a separate task action. Run it only when the user's request requires it, after inspecting what the command does and confirming that its mutations stay within the authorized scope.

### 5. Report Location

```
Worktree ready at <full-path>
Branch: <branch-name> (based on main @ <short-sha>)
```

### 6. Delivery Boundaries (No Unauthorized Commit / Push / Merge)

Developing code in a dedicated worktree typically indicates non-trivial or substantial feature work. Never commit, push, create a pull request, or merge a pull request automatically upon finishing code implementation.

When working inside a worktree:
- Completing code implementation and local automated tests only marks development completion inside the isolated workspace.
- **STOP and report to the user** for manual verification, UX review, and testing in the preview environment.
- Do NOT perform `git commit`, `git push`, PR creation, or PR merge unless the user explicitly requests or authorizes it.

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md → Ask user |
| Directory not ignored | Add to .gitignore + commit |
| Before `git worktree add` | Sync local `main` with `origin/main` (fast-forward only) |
| Creating worktree | Always branch explicitly from `main`: `git worktree add "$path" -b "$BRANCH_NAME" main` |
| Worktree created | Report path, branch, and base commit; stop |

## Common Mistakes

### Branching from stale `main` or arbitrary `HEAD`

- **Problem:** Omitting `<start-point>` in `git worktree add "$path" -b "$BRANCH_NAME"` branches from the current checkout's `HEAD` (which may be an unmerged feature branch or an outdated `main`), causing unintended commits or merge conflicts.
- **Fix:** Always sync local `main` with `origin/main` first and pass `main` explicitly as the start point.

### Skipping ignore verification

- **Problem:** Worktree contents get tracked, pollute git status
- **Fix:** Always use `git check-ignore` before creating project-local worktree

### Assuming directory location

- **Problem:** Creates inconsistency, violates project conventions
- **Fix:** Follow priority: existing > CLAUDE.md > ask

### Expanding into environment setup

- **Problem:** Worktree creation unexpectedly installs dependencies or mutates services and databases
- **Fix:** Stop after Git isolation; inspect and authorize setup commands separately

## Example Workflow

```
You: I'm using the using-git-worktrees skill to set up an isolated workspace.

[Check .worktrees/ - exists]
[Verify ignored - git check-ignore confirms .worktrees/ is ignored]
[Sync main - git fetch origin main && fast-forward local main]
[Create worktree: git worktree add .worktrees/auth -b feature/auth main]

Worktree ready at /Users/jesse/myproject/.worktrees/auth
Branch: feature/auth (based on main @ a1b2c3d)
```

## Red Flags

**Never:**
- Create a worktree without first syncing local `main` with `origin/main`
- Run `git worktree add "$path" -b "$BRANCH_NAME"` without explicitly specifying `main` as the start point
- Create worktree without verifying it's ignored (project-local)
- Assume directory location when ambiguous
- Skip CLAUDE.md check
- Run dependency installation, builds, tests, containers, services, database operations, or migrations as part of worktree creation
- Commit, push, create a PR, or merge a PR automatically after code completion without explicit user instruction and manual verification approval (developing in a worktree usually denotes significant feature work; never commit/push/PR/merge without explicit authorization)

**Always:**
- Sync local `main` with `origin/main` (fast-forward only) before creating the worktree
- Explicitly branch the new worktree from `main` (`git worktree add "$path" -b "$BRANCH_NAME" main`)
- Follow directory priority: existing > CLAUDE.md > ask
- Verify directory is ignored for project-local
- Stop after creating the worktree and report its path, branch, and base commit
- Evaluate any later setup or verification command as a separate, scoped action
- Require explicit user review and instruction before any commit, push, PR creation, or PR merge actions

## Integration

**Called by:**
- **brainstorming** (Phase 4) - REQUIRED when design is approved and implementation follows
- Any skill needing isolated workspace

**Pairs with:**
- **finishing-a-development-branch** - REQUIRED for cleanup after work complete
- **executing-plans** or **subagent-driven-development** - Work happens in this worktree
