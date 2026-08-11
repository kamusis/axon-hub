---
name: mopheus-integration-preview
description: Discover, create, and start reusable local Mopheus integration-test previews from linked Git worktrees. Use this whenever the user asks to start, prepare, bootstrap, reopen, or inspect a Mopheus preview, integration-test environment, local worktree environment, or test login. Detect already-running previews before startup, require confirmation before parallel startup or service shutdown, preserve and optionally reuse preview databases, enable every registered feature dynamically, and print local test credentials after readiness checks.
compatibility: Requires macOS or Linux with bash, git, Docker, curl, jq, make, lsof, Node.js, pnpm, Python 3, and Go. The target must be an existing linked Mopheus Git worktree using a local .env.worktree database.
---

# Mopheus Integration Preview

Discover and start a disposable local preview from an existing Mopheus linked worktree. Preserve databases and test data between runs so future integration checks can reuse the same state without silently creating competing application processes.

## Required input

Require one existing Mopheus worktree path. Resolve it to an absolute physical path before running the bundled script.

If the user gives no path, ask for it. Do not infer the repository root or silently create a worktree.

## Discover existing previews first

Before every startup attempt, execute:

```bash
bash <skill-directory>/scripts/discover_previews.sh <absolute-target-worktree-path>
```

The discovery script maps active frontend and backend listeners from other linked worktrees to their ports and database names. If it prints any row, report the complete mapping and pause for an explicit user decision. Ask whether to:

1. stop one existing preview's frontend and backend, then reuse its database for the target worktree; or
2. keep existing previews running and start an independent target preview.

Do not stop services, rewrite `.env.worktree`, switch databases, or start another preview before the user chooses. Merely asking to start a preview does not authorize shutting down an existing one.

## Run the preview

When discovery finds no other running preview, execute:

```bash
bash <skill-directory>/scripts/start_preview.sh <absolute-worktree-path>
```

After the user explicitly approves keeping existing previews and starting another independent instance, execute:

```bash
bash <skill-directory>/scripts/start_preview.sh --allow-existing-previews <absolute-target-worktree-path>
```

After the user explicitly approves stopping an existing preview and reusing its database:

1. Stop the source preview with `make -C <absolute-source-worktree> stop-worktree`.
2. Stop the target preview too if it is already running, using its own `make ... stop-worktree` command.
3. Execute:

```bash
bash <skill-directory>/scripts/start_preview.sh \
  --reuse-db-from <absolute-source-worktree> \
  <absolute-target-worktree>
```

Database reuse copies only `POSTGRES_DB` and `DATABASE_URL` into the target's ignored `.env.worktree`. The target retains its own frontend and backend ports. The source database and all test data remain intact. The command refuses reuse while either source or target application services are still listening.

The startup script owns the remaining workflow after discovery and confirmation:

1. Validate that the path is a linked worktree of the Mopheus repository.
2. Refuse an unconfirmed parallel startup when another linked-worktree preview is active.
3. Generate or reuse `.env.worktree` with worktree-specific application ports and database name, or reuse an explicitly approved source database.
4. Reuse the shared Docker container named `mopheus-postgres-1`.
5. Install dependencies, create the selected database when missing, and run migrations through the repository Make targets.
6. Clear only the ignored worktree-local Next.js build cache before a cold start, then start backend and frontend as persistent local background processes.
7. Wait until the auth API and login page both respond successfully.
8. Dynamically list every registered feature and set its system state to `enabled`.
9. Create or reuse the dedicated regular test user and `dev-space` workspace.
10. Set every registered feature override to `true` for the test workspace and verify every effective value is enabled.
11. Print URLs, database details, enabled features, backend/frontend log paths, and test email/password.

Do not manually repeat these steps unless diagnosing a script failure. The bundled script is the source of truth for deterministic setup.

## Credential exception

The dedicated preview credential is intentionally safe to print because it is restricted to disposable local integration environments. The script prints it at the end of every successful run.

Never use this credential against:

- a production deployment;
- `dev.kamusis.me` or another remote server;
- the server in the user's default Mopheus CLI profile.

Keep the test identity at system `role = 0`. The workspace-local Owner membership supplies preview permissions. Never assign the test email to `ADMIN_EMAIL`, because Mopheus would promote it to system Admin and workspace pages would become inaccessible.

## Feature policy

Preview environments enable all current and future feature flags dynamically. Do not hard-code `memory`, `git`, or any other key in the Skill.

The script must satisfy both tiers:

- system state is `2` (`enabled`);
- the target workspace override is `true`.

After updates, require `/features/effective` to return `true` for every discovered key. A partial result is a failed preview setup.

## PostgreSQL reuse and conflicts

The preview database must be local and worktree-specific, but all previews share the existing `mopheus-postgres-1` container and its persistent Docker volume.

- Start `mopheus-postgres-1` when it exists but is stopped.
- Do not remove or recreate the shared container or volume.
- Do not clean databases or test data after integration testing.
- If another process or container occupies the configured PostgreSQL port, stop and report its identity. Do not stop unrelated containers without explicit user authorization.
- If `mopheus-postgres-1` does not exist, stop and explain that the shared prerequisite is missing. Do not create a second PostgreSQL container implicitly.

## Idempotency

Repeated runs against the same worktree must reuse:

- `.env.worktree`;
- the worktree database;
- the regular test account;
- the `dev-space` workspace;
- existing user-created test data;
- already-running healthy backend and frontend processes.

Database reuse across worktrees is allowed only after explicit confirmation and after both affected application pairs are stopped. It must not delete the target's former database; changing `.env.worktree` only changes which preserved database the target uses.

Do not delete, truncate, reseed, or reset existing data.

## Success report

Return the script's final summary without redacting the local test email or password. Include:

- frontend login and workspace URLs;
- backend URL;
- PostgreSQL container, port, and database name;
- enabled feature keys;
- test email and password;
- backend and frontend log paths;
- whether services were started or reused.

Do not claim readiness merely because processes were spawned. Both HTTP readiness checks and effective-feature verification must pass.

## Failure handling

- Invalid or primary checkout path: ask for a linked Mopheus worktree.
- Dirty worktree: allowed; preview setup does not edit tracked source files.
- Missing command: report the exact dependency and stop.
- Port conflict: report the PID or container and wait for user authorization.
- Other linked-worktree preview detected: report its worktree, frontend/backend ports and PIDs, and database; pause for the user's decision.
- Database reuse requested while source or target services are running: report the listeners and stop without changing configuration.
- Shared PostgreSQL missing: report the missing `mopheus-postgres-1` prerequisite.
- Migration or startup failure: show the relevant log tail and keep all data.
- Test-account password mismatch: stop rather than resetting a persistent account silently.
- Feature enablement mismatch: list the keys that remain disabled and stop.

## Stop application processes

Only when the user asks to stop this preview, run:

```bash
make -C <absolute-worktree-path> stop-worktree
```

This stops the worktree backend and frontend while preserving the shared PostgreSQL container, database, and all test data.
