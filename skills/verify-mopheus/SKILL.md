---
name: verify-mopheus
description: "Drive and verify Mopheus web UI, API, and agent behaviors against the deterministic local preview harness (ports 3230/8230). Use whenever asked to verify changes, capture proof screenshots, or validate end-to-end user journeys before completion."
compatibility: Linux (Ubuntu/Debian) or macOS.
---

# Verify Mopheus

Deterministic verification harness for the Mopheus codebase. Directly drives the local preview environment (`wt-preview-test`), validates runtime state, exercises user journeys, and captures physical verification evidence (screenshots, API responses, database assertions).

## 1. Fixed Harness Endpoints & Environment

All verification operations run against fixed local ports and database instances:
- **Backend API**: `http://localhost:8230`
- **Frontend Web**: `http://localhost:3230`
- **Database**: PostgreSQL `mopheus_wt_preview_test` on `localhost:5432` (`mopheus-postgres-1`)
- **Default Test Workspace**: `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`)
- **Fixed Daemon ID**: `5864c916-5e33-4137-8244-d435fd451561`
- **Test Credentials**: `alice@mopheus.dev` / `Mopheus@123` (Owner of `dev-space`)

---

## 2. Launch

To start or synchronize the preview environment from the current feature worktree:

```bash
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/start_preview.sh ["<source-worktree-or-repo-dir>"]
```

### Readiness Verification
Launch is complete ONLY when `doctor.sh` reports healthy (HTTP 200 on backend health and frontend login):

```bash
bash ~/.gemini/config/skills/verify-mopheus/scripts/doctor.sh
```

### Individual Service Restarts
When only frontend or backend needs rebuilding without a full reset:
```bash
# Frontend only (clears .next cache, inherits .env.worktree, awaits :3230)
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/restart_service.sh frontend

# Backend only (recompiles mopheusd and awaits :8230)
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/restart_service.sh backend

# Daemon only (restarts background task runner)
bash ~/.gemini/config/skills/mopheus-integration-preview/scripts/restart_service.sh daemon
```

---

## 3. Doctor

One fast, read-only health check that validates whether the preview instance is healthy and ready to drive:

```bash
bash ~/.gemini/config/skills/verify-mopheus/scripts/doctor.sh
```

**What it checks**:
1. Backend API liveness (`http://localhost:8230/api/v1/health` == 200).
2. Frontend Web liveness (`http://localhost:3230/login` == 200).
3. Auth credentials (`alice@mopheus.dev` can obtain JWT access token).
4. Workspace scopes (resolves `dev-space` and confirms member permissions).
5. Headless browser driver presence (`preview_screenshot.js` and Node runtime).

*Rule*: If `doctor.sh` fails, fix the startup blocker or report it. Never drive an unhealthy instance.

---

## 4. Drive

### A. Web UI Driving & Local Screenshot Capture
Use the authenticated headless Playwright driver:

```bash
node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js \
  --url "/dev-space/tickets" \
  --output "/tmp/verify-<slug>.png" \
  [--selector "<css-selector>"] \
  [--hover "<css-selector>"] \
  [--click "<css-selector>"] \
  [--wait 1000]
```

- **Authentication**: Injects `mopheus_auth` cookie and `localStorage` session as `alice@mopheus.dev`.
- **Target Selection**: Pass `--selector` to capture a specific component (e.g. `[data-ticket-description]` or `table`) or omit for full viewport.
- **Interactions**: Pass `--hover` to trigger tooltips or dropdowns before capturing; pass `--click` to trigger tabs or accordions.

### B. Direct API Driving
```bash
TOKEN=$(curl -s -X POST http://localhost:8230/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@mopheus.dev","password":"Mopheus@123"}' | jq -r .data.accessToken)

curl -s -f http://localhost:8230/api/v1/workspaces/bb08a9c4-9f3f-414d-8632-d23909bada79/<endpoint> \
  -H "Authorization: Bearer ${TOKEN}"
```

### C. CLI Driving
```bash
mopheus --profile wt-preview-test --server_url http://localhost:8230 --workspace-id bb08a9c4-9f3f-414d-8632-d23909bada79 <command>
```

### D. Targeted Playwright E2E Driving
When a feature has an existing spec in `tests/e2e/services/<domain>/<spec>.spec.ts`:
```bash
E2E_SKIP_SETUP=1 \
E2E_FRONTEND_URL=http://localhost:3230 \
E2E_BACKEND_URL=http://localhost:8230 \
pnpm exec playwright test --config=playwright.full.config.ts --project=external-services tests/e2e/services/<domain>/<spec>.spec.ts
```

---

## 5. Evidence Standards

A task is verified ONLY when physical evidence is captured and preserved:
1. **Physical Artifacts**:
   - UI changes: Capture a local PNG screenshot via `preview_screenshot.js` and verify it with `read_file`.
   - API / Backend changes: Capture exact terminal command, response JSON, and exit code 0.
   - Data mutations: Run an independent query verifying the stored value in PostgreSQL:
     ```bash
     docker exec mopheus-postgres-1 psql -U mopheus -d mopheus_wt_preview_test -c "SELECT ... FROM <table> WHERE ...;"
     ```
2. **Zero External Upload Rule**:
   - Never upload temporary verification screenshots to external image hosts (e.g. `see-uploader`). Keep evidence local in `/tmp/` or the task artifact directory.
3. **Evidence Reporting**:
   - Paste command and output verbatim in the final summary.

---

## 6. Cleanup

When tearing down preview instances created for verification:
- Kill background services on `:8230` and `:3230` if they were exclusively started for this verification session:
  ```bash
  fuser -k 8230/tcp 2>/dev/null || true
  fuser -k 3230/tcp 2>/dev/null || true
  ```
- **Strict Evidence Retention**: Cleanup removes running processes and ephemeral sockets, **NEVER the evidence artifacts**. Verification screenshots and output logs must remain intact.

---

## 7. Feature Map Index

For exact driving recipes and observable proofs by domain, refer to [`features/README.md`](./features/README.md):
- [Ticket Lifecycle](./features/ticket-lifecycle.md)
- [Agent Tasks & Execution](./features/agent-tasks.md)
- [Workspace Navigation & Layout](./features/workspace-navigation.md)
