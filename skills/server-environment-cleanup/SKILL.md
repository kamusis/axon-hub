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

## ⚠️ Absolute Safety First Principle (安全至上，保守第一)

- **Safety Over Aggressiveness**: Safety is always the highest priority. If there is ANY doubt, ambiguity, missing evidence, unexpected error, or uncertainty about whether an item is safe to remove, **DO NOT delete it**. Keeping an obsolete item is completely harmless and can be handled later; deleting an active or unique resource causes irreversible data loss.
- **Never Escalate Destructiveness**: Never use `--force`, `docker rmi -f`, `git worktree remove --force`, or `docker system prune -a --volumes`. If a normal deletion fails, keep the item, record the failure reason, and continue with other independent items.
- **Protected Resources (Never Delete)**:
  - Any Docker image in active use by running or stopped containers (`docker ps -a`), or base toolchain/infra images (`alpine`, `golang`, `nginx`, `minio`, `pgvector`, `swissql-core`, etc.).
  - The main repository worktree and main/master branches.
  - Worktrees with uncommitted, untracked, or unique changes.
  - Remote Git branches (`git push --delete` is strictly forbidden).
  - Persistent volume directories, database storage, user directories, or paths outside authorized temporary scopes.

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
   Execute worktree and branch removals according to the `cleaning-merged-worktrees` protocol. Skip any item classified as `NEEDS_REVIEW` or dirty.
3. **Prune Stale System Resources**:
   ```bash
   docker image prune -f
   docker builder prune -f --filter "until=168h" 2>/dev/null || true
   git worktree prune
   ```

---

## 4. Standard Report Specification (Mandatory)

Every cleanup run must produce a strictly standardized Markdown report posted to the ticket comment.

**Section 1 MUST be the `Overall Status` table followed by the `Outcome` summary:**

```markdown
# Daily Server Environment Cleanup Report — YYYY-MM-DD

**Run Date**: YYYY-MM-DD (Asia/Shanghai)  
**Agent**: Zhongkui  
**Ticket**: [MOC-XXX](mention://ticket/<ticket-id>)  

---

### 1. Overall Status

| Area | Status |
| :--- | :--- |
| Docker image cleanup | <Status, e.g. "No obsolete versions (all within keep=3 buffer)" or "N removed (~XMB reclaimed)"> |
| Dangling images | <Status, e.g. "0 (prune ran, nothing to free)" or "N pruned (~XMB reclaimed)"> |
| Stale builder cache | <Status, e.g. "Pruned (nothing older than 168h)" or "~XMB reclaimed"> |
| Merged Git worktrees | <Status, e.g. "0 candidates across all detected repos" or "N removed across detected repos"> |
| Stale local branches | <Status, e.g. "0 candidates across all detected repos" or "N deleted"> |
| `/tmp` test residue | <Status, e.g. "0 stale items (>3 days)" or "N stale items cleaned"> |
| Disk usage (root fs) | <e.g. "65G / 99G (69%) — stable"> |

**Outcome**: <Concise summary sentence, e.g. "No destructive actions required this run. System already within retention policy. All protected resources preserved." or "Cleanup completed safely. Reclaimed ~X MB of disk space. All active and rollback resources preserved.">

---

### 2. Docker Images & Cache Breakdown

#### Outdated Images Removed
| Image | ID | Size | Reason |
|---|---|---|---|
| `<image:tag>` | `<id>` | `<size>` | Exceeds rollback buffer (keep=3) |
*(Or "None — all images are in-use or within rollback buffer")*

#### Protected & Rollback Images Preserved
| Image | ID | Size | Protection Reason |
|---|---|---|---|
| `<image:tag>` | `<id>` | `<size>` | Current active container / Rollback buffer (keep=3) / Base infra |

#### Dangling Images & Builder Cache
- Dangling images: `<count> pruned, <size> reclaimed`
- Builder cache: `<status/reclaimed space>`

---

### 3. Git Worktrees & Branches

#### Repositories Checked
- `<repo path 1>`
- `<repo path 2>`

#### Removed Worktrees & Branches
| Repo | Item | Type | Commit / Branch | Merge Status |
|---|---|---|---|---|
| `<repo>` | `<path>` | worktree | `<sha>` | Conclusively merged |
*(Or "None — 0 merged worktrees or stale branches detected")*

#### Active / Protected Worktrees
| Repo | Worktree Path | Branch / HEAD | Reason Preserved |
|---|---|---|---|
| `<repo>` | `<path>` | `<branch>` | Main worktree / Active feature branch |

---

### 4. System Disk & Environment Health
- Root filesystem (`df -h /`): `<Used> / <Total> (<Percent>)`
- Post-cleanup verification: `docker images` and `git worktree list` verified clean.
```
