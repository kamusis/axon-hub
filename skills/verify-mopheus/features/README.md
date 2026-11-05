# Mopheus Verification Map

This directory is the maintained source for verifying user-facing behaviors in Mopheus against the deterministic local preview harness (`wt-preview-test`). Read this index before driving the app, then follow the matching feature recipe.

## Baseline Preconditions

- **Backend API**: Healthy at `http://localhost:8230/api/v1/health` (HTTP 200).
- **Frontend Web**: Healthy at `http://localhost:3230/login` (HTTP 200).
- **Database**: PostgreSQL `mopheus_wt_preview_test` on `localhost:5432` (`mopheus-postgres-1`).
- **Default Actor**: `alice@mopheus.dev` (Owner of `dev-space`; password resolved from `.env.worktree` / `MOPHEUS_TEST_PASSWORD`).
- **Default Workspace**: `dev-space` (`bb08a9c4-9f3f-414d-8632-d23909bada79`).
- **Health Gate**: Run `~/.gemini/config/skills/verify-mopheus/scripts/doctor.sh` and confirm exit code 0 before driving any feature.

## Driving Conventions

- **Browser UI**: Driven via `node ~/.gemini/config/skills/mopheus-integration-preview/scripts/preview_screenshot.js` (or focused Playwright spec).
- **API Endpoints**: Driven via authenticated `curl` with Bearer token obtained from `POST /api/v1/auth/login`.
- **CLI Commands**: Driven via `mopheus --profile wt-preview-test --server_url http://localhost:8230 --workspace-id bb08a9c4-9f3f-414d-8632-d23909bada79`.
- **Target Selectors**: Prefer semantic attributes (`role`, `data-testid`, accessible label) over brittle DOM paths.
- **Artifacts**: Store captured screenshots and logs in `/tmp/mopheus-verify-<slug>/` or the active task artifact directory. Never delete evidence artifacts during cleanup.

## Feature Entry Contract

Each feature file starts with an H1 title and a concise summary paragraph. It contains exactly four H2 sections in this order:
1. `Sub-features`: Bulleted list of short identifiers and behaviors.
2. `How to get to it (user POV)`: All human user entry points (routes, buttons, shortcuts).
3. `Driving it with <harness>`: Preconditions followed by exact executable commands and observable results.
4. `Gotchas`: Known pitfalls, race conditions, or edge cases.

## Features Index

- [Ticket Lifecycle](./ticket-lifecycle.md) covers ticket creation, detail rendering, status transitions, and DB consistency.
- [Agent Tasks & Transcript](./agent-tasks.md) covers agent task assignment, dispatching, thinking/tool display, and run history.
- [Workspace Navigation & Layout](./workspace-navigation.md) covers workspace switching, sidebar navigation, search, and container boundaries.
