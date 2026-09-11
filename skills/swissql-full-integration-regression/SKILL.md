---
name: swissql-full-integration-regression
description: Run, resume, or validate a complete SwissQL Core full-stack integration regression against a clean, revision-bound repository checkout from remote main. Use this for full-stack integration regression, release candidate verification, cross-component validation (backend + CLI), or audits of integration test results. Read tests/integration-test-guide.md and tests/issue-80-integration-test-guide.md as the authoritative guides, execute isolated backend startup on dynamic/dedicated ports, run the multi-stage CLI & REST integration suite across connection profiles, credential resolution, workspace domain isolation, SQL execution & safety rules, dynamic JDBC driver autoloading, and audit log emission, collect logs and traces under test-results/integration/<runId>/, preserve revision-bound evidence, and enforce cleanup and report completeness. Do not use for unit tests, code coverage, or persistent development environments.
compatibility: Requires a clean SwissQL Core Git checkout from remote main, JDK 21, Maven, Go 1.23+, Python 3.10+, and curl.
---

# SwissQL Full Integration Regression

Coordinate a revision-bound, isolated full-stack integration regression across the Java 21 Spring Boot backend and the Go 1.23 CLI. The target repository owns the operational procedures, test contracts, and domain rules; this Skill supplies contract inspection, sandboxed harness orchestration, stage execution, and completion verification.

> [!NOTE]
> All integration tests must execute against an ephemeral, sandboxed runtime sandbox (`test-results/integration/<runId>/`). Never execute against or pollute host development data directories (`~/.local/share/swissql`).

---

## Inputs & Repository Checkout

1. Obtain a fresh, isolated repository checkout based on the latest remote `main` branch:
   ```bash
   git clone https://github.com/enmotech/swissql-core.git swissql-regression-worktree
   cd swissql-regression-worktree
   git checkout main
   git pull origin main
   ```
   Or use an isolated task worktree created by the runtime.
2. **Never test unmanaged, dirty, or stale host development directories**. Ensure `git status --porcelain` is clean.
3. Record the exact commit SHA of the checkout as `TESTED_REVISION`. All test runs, stage assertions, backend server logs, and the final report must be strictly bound to this revision.

---

## Establish the Contract

Inspect the repository contract and verify prerequisite files before running any tests:

```bash
python3 /path/to/skill/scripts/regression_contract.py inspect <repository-path>
```

The inspection verifies:
- The checkout is clean (no uncommitted diffs or untracked changes).
- The exact `TESTED_REVISION` is resolved.
- Canonical guides exist:
  - `tests/integration-test-guide.md`
  - `tests/issue-80-integration-test-guide.md`
  - `tests/README.md`

Generate a pre-filled markdown report template:

```bash
python3 /path/to/skill/scripts/regression_contract.py generate-template <repository-path> -o test-results/integration/<runId>/REGRESSION_REPORT.md
```

---

## Sandboxed Runtime Environment

Assign a unique run ID and initialize an isolated directory structure:

```bash
RUN_ID="$(date +%Y%m%d_%H%M%S)_$(git -C <repository-path> rev-parse --short HEAD)"
SANDBOX_DIR="test-results/integration/${RUN_ID}"
mkdir -p "${SANDBOX_DIR}/data" "${SANDBOX_DIR}/audit" "${SANDBOX_DIR}/jdbc_drivers" "${SANDBOX_DIR}/bin"
```

### Environment Variables
Configure the isolated test instance:

```bash
export SWISSQL_SERVER_PORT=18080
export SWISSQL_DATA_DIR="${SANDBOX_DIR}/data"
export SWISSQL_AUDIT_LOG_DIR="${SANDBOX_DIR}/audit"
export SWISSQL_JDBC_DRIVERS_AUTO_LOAD_DIR="${SANDBOX_DIR}/jdbc_drivers"
export SWISSQL_SQL_RULES_FILE="${SANDBOX_DIR}/sql-rules.yaml"
export SWISSQL_ADMIN_AUTH_TOKEN="test-admin-secret-${RUN_ID}"
export SWISSQL_SERVER="http://localhost:${SWISSQL_SERVER_PORT}"
```

---

## Execution Pipeline & Ordered Stages

The regression consists of 10 sequential stages (37 individual scenarios):

```
Stage 0: Pre-flight & Build Contract
   │
Stage 1: Backend Daemon Lifecycle & Health
   │
Stage 2: Connection Profile Lifecycle (CRUD & Persistence)
   │
Stage 3: Credential Resolution (Inline, File, Env)
   │
Stage 4: Domain Isolation & Security (Workspace Boundaries & Move)
   │
Stage 5: SQL Execution & Safety Engine (Write Blocking & Timeouts)
   │
Stage 6: SQL Rules Engine & Hot-Reload (YAML Rules & Admin Auth)
   │
Stage 7: Dynamic JDBC Driver Autoloading & Admin Security
   │
Stage 8: Audit Logging & Traceability (Structured JSON Logs)
   │
Stage 9: Global Teardown & Process Leak Audit
```

### Stage 0: Pre-flight & Build Contract

1. **Scenario 0.1**: Verify JDK 21 (`java -version`), Maven (`mvn -version`), Go 1.23+ (`go version`), and `curl`.
2. **Scenario 0.2**: Verify clean git working tree (`git status --porcelain`).
3. **Scenario 0.3**: Package backend jar:
   ```bash
   mvn -f swissql-backend/pom.xml package -DskipTests
   ```
4. **Scenario 0.4**: Compile CLI binary:
   ```bash
   cd swissql-cli && go build -o "${SANDBOX_DIR}/bin/swissql" . && cd ..
   ```

### Stage 1: Backend Daemon Lifecycle & Health

1. **Scenario 1.1**: Launch backend in background redirecting logs to `${SANDBOX_DIR}/backend.log` and poll readiness:
   ```bash
   java -jar $(ls swissql-backend/target/swissql-backend-*.jar | grep -v '\.original$' | head -1) > "${SANDBOX_DIR}/backend.log" 2>&1 &
   BACKEND_PID=$!
   
   for i in $(seq 1 30); do
     curl -s "${SWISSQL_SERVER}/v1/status" | grep -q '"UP"' && break
     sleep 1
   done
   ```
2. **Scenario 1.2**: Probe capabilities:
   ```bash
   curl -s "${SWISSQL_SERVER}/v1/capabilities" | jq .
   ```
3. **Scenario 1.3**: CLI status check:
   ```bash
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" status
   ```

### Stage 2: Connection Profile Lifecycle

1. **Scenario 2.1**: Create connection profile via CLI and REST API:
   ```bash
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" connections add \
     --id test-sqlite-1 \
     --db-type sqlite \
     --dsn "sqlite://${SANDBOX_DIR}/data/test.db" \
     --labels "env=test,tier=local"
   ```
2. **Scenario 2.2**: Retrieve profile list and individual profile:
   ```bash
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" connections list
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" connections get test-sqlite-1
   ```
3. **Scenario 2.3**: Update profile metadata and labels via CLI:
   ```bash
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" connections update test-sqlite-1 --labels "env=regression"
   ```
4. **Scenario 2.4**: Delete connection profile:
   ```bash
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" connections delete test-sqlite-1
   ```
5. **Scenario 2.5**: Verify physical file storage `${SANDBOX_DIR}/data/connections.json` reflects CRUD operations.

### Stage 3: Credential Resolution

1. **Scenario 3.1**: Verify inline password resolution in DSN (`postgres://user:pass@host:port/db`).
2. **Scenario 3.2**: Verify external credential store resolution (`${SANDBOX_DIR}/data/credentials.json`).
3. **Scenario 3.3**: Verify environment variable override resolution (`SWISSQL_CREDENTIAL_<PROFILE_ID>`).

### Stage 4: Domain Isolation & Security (Issue #80)

Restart backend with domain isolation enabled:
```bash
kill "${BACKEND_PID}" && sleep 2
SWISSQL_ISOLATION_ENABLED=true \
SWISSQL_ISOLATION_LABEL_KEY=MOPHEUS_WORKSPACE_ID \
java -jar $(ls swissql-backend/target/swissql-backend-*.jar | grep -v '\.original$' | head -1) > "${SANDBOX_DIR}/backend.log" 2>&1 &
BACKEND_PID=$!
```

1. **Scenario 4.1**: Verify default config when isolation is disabled preserves unrestricted access.
2. **Scenario 4.2**: Verify requests without an isolation domain are rejected (HTTP 400 Bad Request).
3. **Scenario 4.3**: Verify audit label (`MOPHEUS_WORKSPACE_ID=ws-alpha`) takes precedence over declared `--isolation-domain ws-beta`.
4. **Scenario 4.4**: Verify cross-domain access is denied (profiles created in `ws-alpha` cannot be accessed by `ws-beta`).
5. **Scenario 4.5**: Verify domain ownership transfer via `connections move`:
   ```bash
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" connections move test-profile --to-domain ws-gamma
   ```

### Stage 5: SQL Execution & Safety Engine

1. **Scenario 5.1**: Execute read-only query and verify tabular/JSON output:
   ```bash
   "${SANDBOX_DIR}/bin/swissql" -s "${SWISSQL_SERVER}" sql --profile test-db "SELECT 1 AS status, 'ok' AS message"
   ```
2. **Scenario 5.2**: Verify mutating SQL (INSERT/UPDATE/DELETE/DROP) without `--allow-write` is rejected with `CoreApiException`.
3. **Scenario 5.3**: Verify mutating SQL with `--allow-write` succeeds when authorized.
4. **Scenario 5.4**: Verify max row capping (`maxRows`) and statement timeout enforcement.

### Stage 6: SQL Rules Engine & Hot-Reload (Issue #48)

Create sandboxed `sql-rules.yaml`:
```yaml
rules:
  - id: block-drop-table
    pattern: "(?i)\\bDROP\\s+TABLE\\b"
    action: DENY
    message: "DROP TABLE is blocked by safety policy"
```

1. **Scenario 6.1**: Verify rules load and apply to matching SQL queries.
2. **Scenario 6.2**: Verify `DENY` rule blocks statement execution and returns the configured message.
3. **Scenario 6.3**: Verify AI stop-directive comments (`-- stop-directive: ...`) are intercepted.
4. **Scenario 6.4**: Verify authenticated rules reload (`POST /v1/sql/rules/reload`):
   - Without token: HTTP 401 Unauthorized.
   - With `Authorization: Bearer ${SWISSQL_ADMIN_AUTH_TOKEN}`: HTTP 200 OK.

### Stage 7: Dynamic JDBC Driver Autoloading & Admin Security

1. **Scenario 7.1**: Verify built-in drivers (PostgreSQL, Oracle, MySQL) are discovered and active.
2. **Scenario 7.2**: Place dynamic driver manifest in `${SANDBOX_DIR}/jdbc_drivers/custom_db/driver.json` and hot-reload.
3. **Scenario 7.3**: Verify `POST /v1/drivers/reload` requires admin authentication token.

### Stage 8: Audit Logging & Traceability (Issue #73)

1. **Scenario 8.1**: Send request with `X-Executor: agent-qa` and `X-Ticket-Id: MOC-999`.
2. **Scenario 8.2**: Inspect `${SANDBOX_DIR}/audit/audit-YYYY-MM-DD.log`.
3. **Scenario 8.3**: Verify audit entry contains valid JSON with timestamp, executor, ticketId, labels, SQL query text, and duration.

### Stage 9: Global Teardown & Process Audit

1. **Scenario 9.1**: Gracefully stop backend process (`kill ${BACKEND_PID}`).
2. **Scenario 9.2**: Verify port `18080` is released.
3. **Scenario 9.3**: Verify zero orphaned Java or Go processes remain, and archive `${SANDBOX_DIR}` logs.

---

## Coordinate Evidence & Enforce Completion

Use log files and CLI output stored under `test-results/integration/<runId>/` as durable evidence.

After test execution and teardown, run the report verification tool:

```bash
python3 /path/to/skill/scripts/regression_contract.py verify-report <repository-path> <report-path>
```

The report is complete only when:
- It records the exact `TESTED_REVISION`.
- Every scenario (0.1 through 9.3) has a valid terminal status (`PASS`, `FAIL`, `SKIP`).
- Evidence (runId, command executed, or log snippet) is provided for each scenario.
- No scenarios remain in `NOT RUN` or `TODO` state.

---

## Environment Boundaries & Strict Rules

- **Zero host pollution**: Never use `$HOME/.local/share/swissql` or user host configurations.
- **Never test dirty repositories**: `git status --porcelain` must be clean.
- **No external production targets**: Never connect to production databases or use personal CLI profiles.
- **Durable logs**: Always preserve `${SANDBOX_DIR}/backend.log` and `${SANDBOX_DIR}/audit/` for failure triage.
- **Never commit test artifacts**: Do not track `test-results/` or temporary report files in git.

---

## Final Report Format

The final report must contain:

```markdown
# SwissQL Core Full Integration Regression Report

**Revision:** <commit-sha>
**Branch:** main
**Date:** YYYY-MM-DD HH:MM:SS
**Executor:** <agent-or-tester-id>
**Port:** 18080
**Sandbox Directory:** test-results/integration/<runId>

## Summary

| Metric | Count |
| --- | --- |
| Total Scenarios | 37 |
| Passed | 37 |
| Failed | 0 |
| Skipped | 0 |

## Scenario Coverage

| Scenario | Title | Status | Evidence |
| --- | --- | --- | --- |
| 0.1 | Prerequisite Toolchain Verification | PASS | JDK 21, Go 1.23, Maven 3.9 verified |
...
| 9.3 | Sandbox Directory Cleanup & Zero Leaked Processes Audit | PASS | 0 leaked processes, logs archived |

## Failure Details

None.

## Teardown & Resource Verification

- [x] Backend process terminated (kill signal sent and confirmed)
- [x] Port 18080 freed (verified via socket check)
- [x] Sandbox data directory cleaned or archived in test-results/
- [x] Zero leaked Java/Go/Postgres processes confirmed
```
