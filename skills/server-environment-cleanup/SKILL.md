---
name: server-environment-cleanup
description: "Server environment cleanup and maintenance skill. Detects and safely removes obsolete Docker daily/beta build images, dangling container images, stale build caches, and temporary runtime residue while protecting active containers, rollback versions, and base infrastructure. Orchestrates Git worktree maintenance via cleaning-merged-worktrees."
---

# Server Environment Cleanup & Maintenance

## Overview

Over time, server environments accumulate obsolete Docker images from daily continuous builds, dangling layers, unused builder cache, temporary test artifacts, and merged git worktrees. This skill defines the rules and workflow for safe, automated, or interactive server garbage collection.

> **Relation to `cleaning-merged-worktrees`:**
> This skill manages host-level environment resources (Docker images, cache, `/tmp` test residue) and coordinates overall maintenance. It delegates Git repository worktree and branch detection to the specialized `cleaning-merged-worktrees` skill rather than duplicating Git merge algorithms.

---

## 1. Docker Cleanup Policy

### A. Protected Resources (Never Delete)
1. **In-Use Images**: Any image associated with a running or stopped container (marked `In Use` or present in `docker ps -a`).
2. **Base Infrastructure & Toolchain Images**:
   - `alpine:*`, `golang:*`, `nginx:*`, `minio/minio:*`
   - `*pgvector:*`, `*swissql-core:*`
   - Any base image required for local compilers, daemons, or database testing.

### B. Daily / Beta Build Image Retention Rules
For application service images built during daily iterations (e.g., `mopheus-backend:v*`, `mopheus-web:v*`):
- **Current Active Version**: Always preserved (`In Use`).
- **Rollback Buffer**: Retain the latest **3** historical daily/beta versions (sorted by tag date or creation time) to enable immediate rollback.
- **Obsolete Versions**: Images older than the rollback buffer that are not in use are classified as **CLEANUP CANDIDATES**.

### C. Dangling Images & Build Cache
- **Dangling Images**: Untagged `<none>:<none>` images are safe to prune (`docker image prune -f`).
- **Build Cache**: Builder cache older than 7 days is safe to prune (`docker builder prune -f --filter "until=168h"`).

---

## 2. Temporary & Residual File Policy

- **`/tmp` & Scratch directories**: Report or clean test scratch folders older than 3 days created by integration tests (`/tmp/mopheus-it-*`, `/tmp/preview-*`).
- **Preserved data**: Never touch `/data`, `/home/*/.ssh`, database persistent volumes, or active workspace checkout roots.

---

## 3. Execution Workflow

### Step 1: Detect Candidates

1. **Docker Detection**:
   Run the helper script or native Docker commands:
   ```bash
   bash <skill-dir>/scripts/detect-docker-images.sh --keep 3 --dry-run
   ```
2. **Git Worktree Detection**:
   Invoke the `cleaning-merged-worktrees` skill across registered workspace repositories:
   ```bash
   bash <cleaning-merged-worktrees-dir>/scripts/detect-merged-worktrees.sh --all
   ```

### Step 2: Present Findings

Format detection findings in a structured Markdown summary:
- **Docker Images**: Outdated daily images to remove vs. protected active/rollback versions.
- **Git Worktrees**: Merged worktrees and stale branches (from `cleaning-merged-worktrees`).
- **Dangling Resources**: Dangling image count and reclaimable disk space.

### Step 3: Execute Safe Cleanup

1. **Clean Outdated Docker Images**:
   ```bash
   bash <skill-dir>/scripts/detect-docker-images.sh --keep 3 --apply
   ```
2. **Clean Verified Git Worktrees**:
   Execute worktree and branch removals according to the `cleaning-merged-worktrees` protocol.
3. **Prune Stale System Resources**:
   ```bash
   docker image prune -f
   docker builder prune -f --filter "until=168h" 2>/dev/null || true
   git worktree prune
   ```

### Step 4: Verify and Close Ticket

1. Post a complete summary comment to the run ticket including:
   - Deleted Docker images and reclaimed disk space.
   - Removed worktrees and deleted merged local branches.
   - Protected images and active worktrees kept.
   - Post-cleanup `docker images` and `git worktree list` verification.
2. If all operations completed without fatal errors, set ticket status to `done`:
   ```bash
   mopheus ticket status <ticket-id> done
   ```

---

## 4. Safety Guardrails

- Never execute `docker rmi -f` on in-use images.
- Never run `docker system prune -a --volumes` (dangerous, could erase persistent volumes and all base images).
- Always verify merge status before removing any Git worktree or branch.
- If image removal fails due to dependent child layers, log the warning and proceed without blocking the run.
