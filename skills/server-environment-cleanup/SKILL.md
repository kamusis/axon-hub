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
- **Rootless Podman & Sandbox Redline (严禁使用 Namespace/tmpfs 绕过沙箱访问 Podman 存储)**:
  - **NEVER** use `unshare`, `nsenter`, `mount`, or a private `tmpfs` over `/run/user/<uid>` (or `/run/user/<uid>/libpod`, `/run/user/<uid>/containers`), **NEVER** set custom `CONTAINERS_STORAGE_CONF`, and **NEVER** write custom namespace wrapper scripts (e.g., `podrun.py`, `podman-ns.sh`) or directly access/modify `~/.local/share/containers/storage/` (`db.sql`, `images.json`). Mounting an empty `tmpfs` over `/run/user/<uid>` while pointing at the real `~/.local/share/containers/storage` causes Podman to think the host rebooted and overwrites all running containers' states in `db.sql` to `Created` (`state=1`)!
  - **Safe Standard Method in `bwrap` Sandbox**: When `/run/user/<uid>` is read-only inside a `bwrap` sandbox on a Rootless Podman host, delegate `docker`/`podman` commands to the host's user systemd manager via D-Bus socket (`/run/user/<uid>/bus`), which runs outside the sandbox in the real host user context:
    ```bash
    systemd-run --user --pipe --wait --quiet -- docker <args...>
    ```
    `scripts/detect-docker-images.sh` automatically detects this and uses `systemd-run --user --pipe --wait --quiet -- docker`. If both direct `docker info` and `systemd-run --user` fail, abort the Docker cleanup step immediately and report the error—never attempt any namespace/mount workaround.
- **Protected Resources (Never Delete)**:
  - Any Docker image in active use by running or stopped containers (`docker ps -a`), or base toolchain/infra images (`alpine`, `golang`, `nginx`, `minio`, `pgvector`, `swissql-core`, etc.).
  - The main repository worktree and main/master branches.
  - Worktrees with uncommitted, untracked, or unique changes.
  - Remote Git branches (`git push --delete` is strictly forbidden).
  - Mopheus Daemon bare repository caches (`~/mopheus_workspace/.repos/*` or `.repos/<workspace-id>/*`) and task `workDir` directories — these are managed exclusively by Mopheus Daemon's built-in GC; inside a Mopheus Agent Task sandbox (`$MOPHEUS_AGENT_TASK_ID` set), sibling task worktrees are masked by `--tmpfs` and must NEVER be scanned, removed, or pruned (`git worktree prune` / `git worktree remove` / `mopheus repo worktree prune`).
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
- **Build Cache**: Builder cache older than 24 hours is safe to prune (`docker builder prune -f --filter "until=24h"`).

---

## 2. Toolchain Caches & Temporary Residue Policy

- **Go Build Cache (`~/.cache/go-build` / `$GOCACHE`)**: Handled automatically by `scripts/detect-docker-images.sh`. Cleaned via `go clean -cache` (or `rm -rf ~/.cache/go-build/*`) when size reaches `>= 4096 MB` (4 GB), or `>= 1024 MB` (1 GB) when root filesystem usage is `>= 75%`.
- **npm Cache (`~/.npm/_cacache`)**: Handled automatically by `scripts/detect-docker-images.sh`. Cleaned when size reaches `>= 2048 MB` (2 GB), or `>= 512 MB` when root filesystem usage is `>= 75%`.
- **`/tmp` & Scratch directories**: Clean top-level (`-maxdepth 1`) build/E2E residue older than 1 day (`/tmp/go-build*`, `/tmp/e2e*`, `/tmp/playwright*`) and integration test scratch folders older than 3 days (`/tmp/mopheus-it-*`, `/tmp/preview-*`). Never run unbounded deep `find` traversals across `$HOME` or `/`.
- **Preserved data**: Never touch `/data`, `/home/*/.ssh`, database persistent volumes, or active workspace checkout roots.

---

## 3. Execution Workflow

### Step 1: Detect Candidates

1. **Docker & Toolchain Cache Detection**:
   Run the helper script (do NOT run raw `docker`/`podman` workarounds; if the script fails or outputs `[AGENT DIRECTIVE — DO NOT WORK AROUND]`, **STOP** all Docker steps immediately, do NOT try any alternative method, and report the error output verbatim):
   ```bash
   bash <skill-dir>/scripts/detect-docker-images.sh --keep 3 --dry-run
   ```
2. **Git Worktree Detection**:
   - **Scope check first**: Only scan host repositories under `/src/*`. If `/src` does not exist or contains no Git repositories, record `0 repositories in scope (/src not present)` and skip Git worktree detection completely. **NEVER run `mopheus repo list`**, because Mopheus-managed repositories (`~/.mopheus_workspace/.repos/*` / `~/mopheus_workspace/.repos/*`) are managed exclusively by the Mopheus Daemon's built-in GC and are strictly out of scope.
   - **Mandatory skill delegation**: When `/src/*` contains Git repositories, invoke the `cleaning-merged-worktrees` skill via the `Skill` tool (or `Read` its `SKILL.md` if the `Skill` tool is unavailable) — do NOT bypass the skill by guessing script paths or running ad-hoc git commands directly. Then follow the loaded `cleaning-merged-worktrees` workflow (Step 1 detection and Step 2 `NEEDS_REVIEW` verification) across `/src/*`.

### Step 2: Present Findings

Format detection findings in a structured Markdown summary:
- **Docker Images**: Outdated daily images to remove vs. protected active/rollback versions.
- **Toolchain & Package Caches**: `~/.cache/go-build` and `~/.npm/_cacache` sizes vs. watermark thresholds.
- **Git Worktrees**: Merged worktrees and stale branches (from `cleaning-merged-worktrees`).
- **Dangling Resources**: Dangling image count and reclaimable disk space.

### Step 3: Execute Safe Cleanup

1. **Clean Outdated Docker Images, Dangling Images, Stale Builder Cache (`24h`), Toolchain Caches, and `/tmp` Residue**:
   Execute the helper script in `--apply` mode (which safely handles outdated images, dangling image pruning, 24h builder cache pruning, `~/.cache/go-build` / `~/.npm/_cacache` watermark cleanup, and `/tmp` residue cleanup, and automatically outputs `[AGENT DIRECTIVE — DO NOT WORK AROUND]` on failure):
   ```bash
   bash <skill-dir>/scripts/detect-docker-images.sh --keep 3 --apply
   ```
   *(If any error occurs, **STOP** immediately, report the error verbatim, and **NEVER** attempt any alternative command or workaround).*
2. **Clean Verified Git Worktrees**:
   Execute worktree, branch, and metadata cleanup strictly according to Step 4 of the loaded `cleaning-merged-worktrees` skill (respecting all its safety principles, including skipping `NEEDS_REVIEW`/dirty items and never pruning Mopheus Daemon `.repos/*` caches).
3. **Prune Stale Docker Resources (Only if Step 3.1 `--apply` was skipped because 0 outdated images were found, but dangling images/cache still need pruning)**:
   ```bash
   (docker image prune -f || systemd-run --user --pipe --wait --quiet -- docker image prune -f) || { echo "[FATAL_BLOCKER] docker image prune failed. [AGENT DIRECTIVE — DO NOT WORK AROUND]: Stop Docker cleanup immediately, report this error to the human operator, and do NOT attempt any alternative workaround." >&2; exit 2; }
   docker builder prune -f --filter "until=24h" 2>/dev/null || systemd-run --user --pipe --wait --quiet -- docker builder prune -f --filter "until=24h" 2>/dev/null || true
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
| Stale builder cache | <Status, e.g. "Pruned (until=24h, nothing older than 24h)" or "~XMB reclaimed (until=24h)"> |
| Toolchain & package caches | <Status, e.g. "go-build XMB, npm YMB (within threshold)" or "Cleaned go-build (~XMB) / npm (~YMB)"> |
| Merged Git worktrees | <Status, e.g. "0 candidates across all detected repos" or "N removed across detected repos"> |
| Stale local branches | <Status, e.g. "0 candidates across all detected repos" or "N deleted"> |
| `/tmp` test residue | <Status, e.g. "0 stale items" or "N stale items cleaned"> |
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
