---
name: coverage-driven-test-improvement
description: Use when the user asks to improve tests based on a code coverage report, fill uncovered lines, raise coverage, add tests for uncovered branches, or decide what coverage gaps matter. Guides agents to turn coverage evidence into behavior-focused tests through observable public boundaries, not implementation-detail tests created only to increase percentages.
---

# Coverage-Driven Test Improvement

## Purpose

Use coverage reports to choose meaningful tests to add. The goal is stronger regression protection, not a prettier percentage.

Coverage identifies code paths that tests did not execute. It does not prove that existing assertions are meaningful. Treat coverage as a map of blind spots, then decide which blind spots represent real product, API, safety, or operational risk.

When adding tests, cover uncovered paths through observable behavior whenever practical:

- Public APIs, commands, UI actions, or service methods.
- Returned values, status codes, error codes, events, logs, persisted files, or visible side effects.
- Domain decisions such as authorization, validation, routing, policy evaluation, state transitions, retries, or cleanup.

Do not test private implementation details merely to light up uncovered lines.

## Relationship To TDD

This workflow starts from an existing coverage report, so it is not strict test-first development from a blank slate. Still apply TDD discipline when adding or changing tests:

1. Define the missing behavior in user-facing or caller-facing terms.
2. Add one focused test that would fail if that behavior were broken.
3. For bug regressions, verify the test fails for the expected reason when practical.
4. Make the smallest production change only if the test exposes a real bug.
5. Re-run focused tests, relevant broader tests, and coverage.

If the user asks for a new feature or bug fix rather than coverage improvement, use the `test-driven-development` skill first.

## Workflow

### 1. Start From Evidence

Use an existing coverage report or run the project's coverage tooling.

Gather:

- Component, package, module, or feature area.
- File/class/function and line or branch evidence.
- Current coverage numbers if available.
- Test command used to generate the report.
- Whether the gap is line, branch, function, statement, or mutation coverage.

Do not guess uncovered areas from memory. Do not invent coverage numbers.

### 2. Separate Signal From Noise

Coverage reports often highlight code that is not worth direct testing. Before writing tests, classify each low-coverage area.

Likely signal:

- Public endpoint, command, function, or service behavior.
- Security, permission, credential, policy, validation, or safety logic.
- Persistence, serialization, migration, caching, or state recovery.
- Error handling, fallback, cleanup, timeout, retry, cancellation, or resource lifecycle behavior.
- Boundary adapters that translate requests, responses, files, network calls, or external system errors.
- Domain-specific branching with real user or operational consequences.

Likely noise:

- Generated code.
- Plain data carriers with no validation or behavior.
- Framework bootstrap or dependency-injection wiring.
- Trivial accessors, builders, or enum plumbing.
- Defensive guards that are unreachable under current invariants.
- Code only testable by reflection or private-method access.

Noise can still matter if it carries validation, mapping, compatibility, or security behavior. Inspect the source before dismissing it.

### 3. Rank Gaps By Risk, Not Percentage

Do not rank solely by the largest number of missed lines. A small uncovered authorization branch can matter more than a large uncovered formatting helper.

Use this priority order:

1. **Safety and security**
   - Auth, permissions, secrets, encryption, policy enforcement, data loss prevention, unsafe operations.

2. **User-visible contracts**
   - API status codes, response bodies, CLI output, UI states, validation errors, public function behavior.

3. **Persistence and recovery**
   - File/database writes, migrations, corrupt input, missing data, reload, restart, rollback, cache invalidation.

4. **External boundary behavior**
   - HTTP clients, database drivers, message queues, filesystem, subprocesses, cloud APIs, third-party SDKs.

5. **Stateful lifecycle behavior**
   - Connection pools, locks, classloaders, sessions, retries, cancellation, cleanup, resource closing.

6. **Domain branching**
   - Routing, parsing, normalization, rule matching, feature flags, compatibility modes.

7. **Presentation and formatting**
   - Important when output is a contract; lower priority when purely cosmetic.

8. **Implementation noise**
   - Usually defer or document.

### 4. Choose The Right Test Boundary

Use the narrowest boundary that still observes real behavior.

Prefer:

- API/controller/handler tests for request validation, auth boundaries, status codes, and response contracts.
- Service/domain tests for business rules and state transitions.
- Repository/store tests for persistence using temporary real files or test databases.
- Adapter/client tests for outbound request construction and inbound error translation.
- Command/UI tests for flags, arguments, output, and user-visible errors.
- Integration tests when several modules must cooperate for the behavior to be meaningful.

Mock only true external boundaries or expensive nondeterminism:

- Network services.
- Time and randomness.
- External databases or services when a local fixture is not practical.
- Filesystem only when temporary real files are not practical.
- Hardware, OS-specific behavior, or unavailable infrastructure.

Avoid mocking the system's own internal modules just to force a line to execute. If a gap can only be covered by mocking most of the system, reconsider the boundary or document why it is not worth covering.

### 5. Translate Uncovered Lines Into Behavior

For each candidate gap, ask:

- What condition makes this line or branch execute?
- Who can observe the outcome?
- What would break if this path behaved incorrectly?
- Can I trigger it through a public or semi-public boundary?
- What assertion proves the behavior, not just execution?
- Is this a real product risk or coverage noise?

Write the test name from the behavior, not the line number.

Good:

- `returns forbidden when admin token is missing`
- `reload preserves previous configuration after invalid file`
- `closes old resource when replacing an active entry`
- `reports validation error for missing required field`

Bad:

- `covers line 142`
- `calls helper method`
- `executes private branch`
- `increases coverage for Foo`

### 6. Add Tests In Small Batches

Work in small vertical slices:

1. Pick one behavior.
2. Add one focused test.
3. Run the focused test.
4. Run nearby tests.
5. Re-run coverage for the touched component.
6. Repeat.

Do not add a large batch of speculative tests before verifying the first one. Coverage-driven work can easily drift into brittle implementation locking if done in bulk.

### 7. Apply The Mandatory Test Quality Gate

Review every new or changed test before accepting it. A test is not behavior-focused merely because it calls a public method. Its assertions must distinguish the claimed behavior from unrelated success or failure paths.

For each test, answer:

- What exact regression would make this test fail?
- Does the assertion observe the behavior named by the test?
- Could an unrelated error, timeout, unavailable dependency, or generic failure make the test pass?
- Does the test depend on machine state that is not part of the documented test environment?
- Would a harmless internal refactor break the test even if public behavior stayed the same?

Reject or rewrite tests with weak discriminating power. Common warning signs include:

- Asserting only `error != nil`, `ok == false`, non-null output, a generic status, or "does not throw" when the test claims a more specific behavior.
- Calling a real local database, network service, daemon, cloud endpoint, filesystem location, environment variable, or executable from a unit test without an explicit integration-test contract.
- Accepting multiple incompatible outcomes, such as success or failure, merely to execute a path.
- Skipping the test when the expected behavior is not observed.
- Reimplementing production logic in the test and asserting that the copy agrees with itself.
- Accessing private methods, fields, or internal state through reflection solely to increase line or branch coverage.
- Asserting mock interactions without also asserting the caller-visible result when the visible result is the behavior that matters.

These assertion shapes are not always wrong. They are valid when the broad outcome itself is the complete public contract. For example, "missing optional resource does not throw" can be meaningful. The test name, setup, and assertion must describe the same contract.

Keep unit tests hermetic and deterministic. Use temporary resources, controlled fakes, protocol-level test servers, or existing project fixtures for external boundaries. Run tests against real infrastructure only when the repository defines them as integration or end-to-end tests and documents the prerequisites.

If a valuable behavior cannot be observed through the current design, choose one of these options:

1. Test it through a broader public integration boundary.
2. Add the smallest production seam only when it improves the design and is not a test-only hook.
3. Record the gap as intentional and explain why a brittle test would be worse.
4. Create a separate design or testability issue when the missing seam requires non-trivial production work.

Coverage targets never justify low-signal tests. If reaching a target requires tests that fail this quality gate, preserve the lower percentage and report the remaining risk honestly.

### 8. Verify

Run the repository's focused test command for the touched area, then the relevant broader suite, then coverage.

Examples of command categories:

- Focused unit/service/controller test.
- Package/module test suite.
- Full component test suite.
- Coverage command for the component.

Use the actual commands from the repository documentation, build files, or prior coverage report. Do not substitute unrelated commands.

### 9. Report The Result

Use this structure:

```markdown
## Coverage-Driven Test Update

### Tests Added
- `[test name]` covers `[behavior]` through `[public boundary]`.

### Coverage Evidence
- Before: ...
- After: ...
- Report path or command: ...

### Behavior Protected
- ...

### Remaining Gaps
- `[area]`: left uncovered because `[reason]`.

### Verification
- `[command]` — passed/failed
```

If coverage did not improve but the test is behaviorally valuable, say so. Coverage is a guide, not the only success metric.

## Common Patterns

### Low Controller Or Handler Coverage

Look for missing tests around:

- Missing or invalid input.
- Authenticated versus unauthenticated requests.
- Not found, conflict, validation, and permission errors.
- Response shape and error contract.
- Calls into the domain layer that produce observable results.

Prefer API/handler tests over directly testing private request parsing helpers.

### Low Persistence Coverage

Look for:

- Missing file or missing table.
- Empty store.
- Invalid or corrupt data.
- Save then reload.
- Migration from old format.
- Concurrent or repeated writes if relevant.

Prefer temporary real files or test databases. Assert the public store behavior and persisted result.

### Low Credential Or Secret Handling Coverage

Look for:

- Missing secret source.
- Invalid secret reference.
- Wrong key or corrupt ciphertext.
- Plaintext migration.
- Redaction and masking behavior.

Treat this as high risk. Assert observable security properties, such as "secret is retrievable by authorized path" and "secret is not exposed or persisted in plaintext" when those are requirements.

### Low Resource Lifecycle Coverage

Look for:

- Replace existing resource.
- Reload after invalid config.
- Close, cleanup, deregister, rollback, or timeout.
- Repeated start/stop.
- Failure during initialization.

Assert visible lifecycle effects: old resource closed, registry updated, previous state preserved, cleanup called at boundary, or subsequent operations behave correctly.

### Low Formatting Or Presentation Coverage

Only prioritize if output is a user-facing or machine-readable contract. Prefer snapshot-like assertions sparingly and keep them focused on meaningful output.

## Important Constraints

- Do not chase 100% coverage with brittle tests.
- Do not weaken existing tests to make coverage easier.
- Do not add production-only hooks just for tests.
- Do not modify unrelated code while improving coverage.
- Do not test private methods through reflection unless the user explicitly requests it and there is no better boundary.
- When a gap is intentionally left uncovered, explain why.
