---
name: mopheus-full-integration-regression
description: Run, resume, or validate a complete Mopheus full-stack E2E regression against a clean, revision-bound repository checkout from remote main. Use this for the Weekly full E2E regression, requests to execute the entire Mopheus E2E test suite (tests/e2e/), or audits of full-stack test results. Read tests/e2e/README.md as the authoritative guide, execute isolated full-stack Playwright E2E (pnpm test:e2e), collect test results, traces, and logs from test-results/e2e-full/<runId>/, preserve revision-bound evidence, and enforce cleanup and report completeness. Do not use this for reusable previews, a single scenario, unit tests, code coverage, or ordinary development environment startup.
compatibility: Requires a clean Mopheus Git checkout from remote main, Docker, Go, Node.js, pnpm, Playwright dependencies / Chromium, and Claude CLI for daemon runtime testing.
---

# Mopheus Full E2E Regression

Coordinate a long-running, revision-bound full-stack E2E regression without copying the test procedure out of the repository. The tested checkout owns commands, specs, isolation lifecycles, and evidence rules; this Skill supplies discovery, execution, and completion checks around that contract.

> [!NOTE]
> The legacy `tests/integration/` directory is **deprecated**. All unified integration journeys and end-to-end user workflows are consolidated into the modern Playwright test suite under `tests/e2e/`.

## Inputs & Repository Checkout

1. Obtain a fresh, isolated repository checkout based on the latest remote `main` branch:
   ```bash
   mopheus repo checkout https://github.com/enmotech/mopheus --ref main --output json
   ```
   Or use the isolated task worktree provided by the runtime.
2. **Never test unmanaged, dirty, or stale host development directories** (e.g., `/home/*/*`).
3. Record the exact commit SHA of the isolated worktree as `TESTED_REVISION`. All assignments, test runs, Playwright artifacts, server logs, and the final report must be strictly bound to this revision.

## Establish the contract

From this Skill directory, run:

```bash
python3 scripts/regression_contract.py inspect-e2e <isolated-repository-path>
```

The command verifies that the checkout is clean, resolves the exact revision, and dynamically inventories all active E2E spec files across `bootstrap/admin/`, `bootstrap/user/`, and `services/*/`. Treat any failure as a blocker; a dirty checkout cannot be represented by a commit SHA alone.

Read this file completely from the tested checkout before executing anything:

- `tests/e2e/README.md`

It is the authoritative guide for full-stack E2E test execution, isolation boundaries, and ordered dependencies.

## Execute the E2E regression

Execute the isolated full-stack Playwright E2E suite:

```bash
pnpm test:e2e
```

(or `pnpm test:e2e:full` / `make test-e2e-full`)

### Execution Pipeline & Ordered Stages

The run follows the strict dependency sequence configured in `playwright.full.config.ts`:

1. **globalSetup**: Spins up an isolated PostgreSQL container, dedicated backend, frontend, and daemon processes on dynamic ports, and generates an isolated `E2E_RUN_ID` state directory.
2. **admin-license** (`bootstrap/admin/01-license.spec.ts`): Admin UI license request export, generator execution, and UI license import.
3. **admin** (`bootstrap/admin/02-admin.spec.ts`): Admin configuration and management tests.
4. **user-bootstrap** (`bootstrap/user/`): Regular user account registration, workspace creation, CLI login, provider registration, daemon runtime startup, and online status verification.
5. **services-workspace** (`services/workspace/`): Completes initial workspace onboarding.
6. **services-***: Parallel/independent service suites including `user`, `ticket`, `skill`, `agent`, `memory`, `inbox`, and `jobs`.
7. **globalTeardown**: Gracefully shuts down daemon, backend, frontend, and PostgreSQL container, and captures capped logs (default 512 KiB) into `test-results/e2e-full/<runId>/`.

Never skip the global setup and teardown unless explicitly testing against pre-existing external services via `E2E_SKIP_SETUP=1`.

## Coordinate long-running work & evidence

Use Playwright test outputs and process logs under `test-results/e2e-full/<runId>/` as durable run evidence.

- Check test logs and output in `test-results/` for failure traces and assertions.
- When an individual spec or assertion fails, record the exact stack trace, screenshot, and console logs.
- Continue running remaining service projects when possible, preserving failure details rather than erasing them.
- If resuming or re-running, rerun contract inspection and require the same `TESTED_REVISION`. Never reuse test results from another checkout or a persistent preview.

Follow Team and Agent instructions for assignment and aggregation. QA Leader coordinates and aggregates; E2E Tester executes assigned projects and returns spec-level evidence.

## Enforce completion

After test execution and cleanup, verify the report with:

```bash
python3 scripts/regression_contract.py verify-e2e-report <isolated-repository-path> <e2e-report-path>
```

The report is complete only when:
- It records the same revision as the checked-out repository (`TESTED_REVISION`).
- It contains test outcomes for all discovered E2E spec files.
- Every row has a valid status (`PASS`, `FAIL`, `SKIP`) and evidence (runId, timing, trace).
- No rows have `NOT RUN` or missing evidence.

Report verification proves coverage completeness, not that all tests passed.

## Environment boundary

Never use `mopheus-integration-preview` for this workflow. That Skill intentionally reuses persistent databases, accounts, feature overrides, and application processes, which violates the fresh isolation contract of full E2E regression.

Never target production, a remote development deployment, a personal CLI profile, or a shared preview database.

## Final report

Return:

- Tested revision (`TESTED_REVISION`) and checkout identity;
- Full E2E runId and execution duration;
- Spec and test totals by `PASS`, `FAIL`, and `SKIP`;
- Project-by-project breakdown (`bootstrap/admin`, `bootstrap/user`, `services-workspace`, `services-*`);
- Failure details with reproducible stack traces, screenshots, and server log excerpts;
- Container, process, and temporary profile cleanup verification;
- Unresolved risks or flaky tests that require follow-up.

Attach the completed E2E regression report directly to the Mopheus ticket. **Never use `git add`, `git commit`, or track test report artifacts in the Git repository.**

Do not claim the regression passed when any test spec failed, remained unaccounted for, used evidence from another revision, or lacked required cleanup.
