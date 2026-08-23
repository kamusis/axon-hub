---
name: mopheus-full-integration-regression
description: Run, resume, or validate a complete Mopheus integration regression against a clean, revision-bound repository checkout from remote main. Use this for the Weekly full integration regression, requests to execute the entire Mopheus integration suite, or audits of whether a full regression report covers every current repository scenario. Read the repository guides as the sole test procedure, execute all required automation, reconcile every Markdown scenario, preserve revision-bound evidence, and enforce cleanup and report completeness. Do not use this for reusable previews, a single scenario, unit tests, code coverage, or ordinary development environment startup.
compatibility: Requires a clean Mopheus Git checkout from remote main, Python 3, Bash, Docker, Go, Node.js, pnpm, Playwright dependencies, and any external capability explicitly required by the repository integration guides.
---

# Mopheus Full Integration Regression

Coordinate a long-running, revision-bound regression without copying the test procedure out of the repository. The current checkout owns commands, scenarios, capability gates, evidence rules, and cleanup rules; this Skill supplies discovery and completion checks around that contract.

## Inputs & Repository Checkout

1. Obtain a fresh, isolated repository checkout based on the latest remote `main` branch:
   ```bash
   mopheus repo checkout https://github.com/enmotech/mopheus --ref main --output json
   ```
   Or use the isolated task worktree provided by the runtime.
2. **Never test unmanaged, dirty, or stale host development directories** (e.g., `/home/*/*`).
3. Record the exact commit SHA of the isolated worktree as `TESTED_REVISION`. All assignments, commands, browser runs, evidence, and the final report must be bound to this revision.

## Establish the contract

From this Skill directory, run:

```bash
python3 scripts/regression_contract.py inspect <isolated-repository-path>
```

The command verifies that the checkout is clean, resolves the exact revision, and dynamically inventories the current numbered specifications and scenarios. Treat any failure as a blocker; a dirty checkout cannot be represented by a commit SHA alone.

Read these files completely from the tested checkout before executing anything:

- `tests/integration-testing-guide.md`
- `tests/TEST-EXECUTION-GUIDE.md`

They are the sole source of test procedure. If this Skill conflicts with either guide, follow the guide and report the Skill defect.

## Execute the regression

Follow the mandatory full-regression protocol in the execution guide exactly. This includes its report generator, every automated shell runner, the complete Playwright phase, direct intelligent execution of uncovered Markdown behavior, capability-gate evidence, and cleanup.

An automated runner name or successful exit does not cover a Markdown scenario by itself. Credit automation only when its assertions satisfy the complete user-observable scenario. Execute partially covered or uncovered assertions through the public boundary specified by the repository.

Continue independent phases after an assertion failure when the guide permits it. Preserve the original failure rather than replacing it with a later success. Stop when isolation, revision identity, or infrastructure ownership cannot be proven.

## Coordinate long-running work

Use the generated integration report as the durable run ledger. Update scenario rows as evidence arrives so interruption does not erase progress.

When resuming, rerun the contract inspection and require the same `TESTED_REVISION`. Reuse existing evidence only when its command output, environment, and scenario identity remain attributable to that revision. Never reuse results from another checkout or a persistent preview.

Follow Team and Agent instructions for assignment and aggregation. This Skill does not redefine QA Leader or Integration Tester responsibilities.

## Enforce completion

After scenario reconciliation and cleanup, run:

```bash
python3 scripts/regression_contract.py verify-report <isolated-repository-path> <integration-report-path>
```

The report is complete only when it contains exactly the scenarios discovered from the tested checkout, records the same revision, has no `NOT RUN` row, uses a valid execution source, and includes evidence for every outcome. `FAIL` and evidence-backed `SKIP` are complete outcomes; they must not be converted to `PASS`.

Report verification proves coverage-accounting completeness, not that the product passed.

## Environment boundary

Never use `mopheus-integration-preview` for this workflow. That Skill intentionally reuses persistent databases, accounts, feature overrides, and application processes, which violates the fresh isolation and cleanup contract of full regression.

Never target production, a remote development deployment, a personal CLI profile, or a shared preview database.

## Final report

Return:

- tested revision and checkout identity;
- automation and Playwright outcomes;
- scenario totals by `PASS`, `FAIL`, and `SKIP`;
- failures with reproducible redacted evidence;
- unavailable capability gates and their evidence;
- report verification result;
- cleanup result and remaining isolated resources;
- unresolved risks that require follow-up.

Do not claim the regression passed when any scenario failed, remained unaccounted for, used evidence from another revision, or lacked required cleanup.
