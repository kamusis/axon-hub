---
name: tdd
description: >
  Use when implementing any feature, bugfix, refactor, or behavior change before writing implementation code.
  Enforces Repro-First (reproducing broken behavior before editing production code), Sequence-Verifiable-Units
  (commit order that proves the work: red then green for bug fixes), and testing observable behavior over implementation
  details. Also use when asked for test-driven-development, tdd, red-green-refactor, regression tests, or test-first development.
---

# Test-Driven Development (TDD) & Repro-First

## Purpose

Write the test or executable reproduction first, watch it fail for the expected reason, then write the smallest implementation that makes it pass.

The goal is not ceremony. The goal is evidence: a failing test proves the test can catch the missing behavior or bug, and a passing test proves the implementation satisfies that behavior.

## When To Use

Use this skill before implementation for:

- Bug fixes (strictly mandatory Repro-First workflow)
- New features and behavioral extensions
- Refactors that can change behavior
- Public API, CLI, UI, service, parser, storage, or integration behavior changes
- Regression tests for discovered bugs

Reasonable exceptions exist, but state them explicitly and choose another verification path:

- Documentation-only changes
- Pure configuration changes
- Generated code
- Throwaway exploration that will be discarded before real implementation
- Mechanical formatting or renaming with no behavior change
- Cases where no practical automated test seam exists

If production code already exists for the change, do not pretend it was TDD. Add tests before further changes, or if the user explicitly wants strict TDD, discard the exploratory implementation and restart from a failing test.

## Core Principles

### Prove It Works Directly (No Proxies)

Verify every change and reproduction by checking the real artifact directly. Do not infer correctness from proxies, self-reports, or "it compiles":
- Check process liveness directly, not indirectly through derived state.
- Read the actual values and records from the real system (API responses, DB state).
- Script the check whenever possible: a deterministic script or test is an artifact a reviewer can re-run directly.

### Repro-First (Make Broken Behavior Executable First)

For any bug fix or regression repair:
- **Strictly prohibit touching production/business code** before an executable check confirms the failure.
- Reproduce the defect on the real surface where it occurs: unit/integration test, CLI command, HTTP request, or preview harness (`verify-mopheus`).
- Verify that the failure reproduces the exact reported symptom, not a superficial setup crash or unrelated error.

### Test Behavior, Not Implementation

A test is a claim about what the code does for its users: a caller, an end user, or another service. Tests should verify what those users can observe through the interface they use (return values, errors, state they can read back, rows written, events emitted). They should not lock down private methods, internal call order, or incidental structure.

Judge each test against two imagined edits:
- **Break the behavior**: Make the code return a wrong value, skip an effect, or do the effect twice. If the test still passes, it proves nothing.
- **Change the internals**: Keep every observable result the same and restructure the code underneath. If the test now fails, it is pinned to implementation details and will break on every refactor while catching no real bug.

Keep a test that catches the first edit and survives the second. Rewrite or delete the rest.

Good tests:
- Exercise public interfaces
- Use real code paths where practical
- Describe what capability exists
- Survive internal refactors
- Fail when behavior breaks

Bad tests:
- Mock internal collaborators you control
- Assert private method calls
- Depend on internal ordering without user-visible meaning
- Query hidden state instead of verifying through the interface
- Pass even when the user-facing behavior is wrong

### Prefer No New Test Over a Bad Test

Favor the narrowest test that still exercises real behavior.
Mock only at true system boundaries (external third-party APIs, remote payment gateways, real clocks).
Never mock your own domain services, repositories, or internal collaborators just to satisfy a unit test count.

If writing a unit test requires:
- Deeply nested mocks of owned classes,
- Altering production code visibility purely for testing,
- Brittle fixtures that break on internal refactoring,
**STOP.** Do not write a mock-heavy unit test. Instead, use the closest executable real-surface check:
- An integration test with a test database/in-memory instance,
- A deterministic CLI invocation or cURL script,
- Or physical runtime verification via `verify-mopheus` / Playwright.

### Sequence Work Into Verifiable Units (Story Orders)

Never mechanically force every change into two commits. Follow the canonical **Story Orders**: stack commits and PRs in the order that proves the work, where each commit lands on its own and the sequence reads as an argument:

- **Bug Fixes (The Canonical Red-Then-Green)**:
  - Commit 1: `test: add failing reproduction for <issue>` (executable, compilable, and demonstrably failing RED state).
  - Commit 2: `fix: <issue summary>` (minimal implementation, turning the state GREEN).
  - *Reviewer argument*: "Watch it go red, then green."
- **New Features (Scaffold Before Feature or Atomic Unit)**:
  - Do NOT write a fake "failing test" that fails to compile.
  - Option A (Layered sequence for large features): Infrastructure/schema/models first (`scaffold`), business services with tests second, UI/E2E integration third. Every commit must compile and pass tests.
  - Option B (Standard features): One atomic commit containing both the feature implementation and its public behavioral tests.
- **Refactoring (Subtraction Before Reshape)**:
  - Commit 1: Clean up dead code, obsolete callers, and unused imports (`subtraction`).
  - Commit 2: Restructure the remaining implementation (`reshape`) while existing tests stay continuously green.
- **Performance / Optimization (Baseline Capture Before Treatment)**:
  - Commit 1: Benchmark or baseline metric capture proving current cost.
  - Commit 2: Algorithmic optimization (`treatment`) proving metric improvement.

### Work In Vertical Slices

Do not write all tests first and then all implementation. That is horizontal slicing: it bakes in imagined behavior and often produces brittle tests.

Use tracer bullets:

```text
RED      one failing test or reproduction check for one behavior
COMMIT   (for bug fixes) commit the failing test
GREEN    minimal implementation
VERIFY   confirm green state
COMMIT   (for bug fixes) commit the fix
REFACTOR only while green
REPEAT   next behavior
```

Each test should respond to what you learned from the previous cycle.

## Workflow

### 1. Define The Behavior

Before writing code, name the behavior in user-facing terms.

For a bug:

- What input or action reproduces it?
- What exact wrong output, error, or side effect occurs?
- What should happen instead?

For a feature:

- What public interface changes?
- What is the smallest observable capability?
- What edge case matters first?

For ambiguous work, briefly state assumptions or ask the user before coding.

### 2. RED: Write One Failing Test

Write one minimal test for one behavior.

Requirements:

- Clear test name
- One behavior
- Public interface
- Real code path where practical
- No speculative future behavior

Example:

```typescript
test("retries failed operations three times", async () => {
  let attempts = 0;
  const operation = async () => {
    attempts++;
    if (attempts < 3) throw new Error("fail");
    return "success";
  };

  const result = await retryOperation(operation);

  expect(result).toBe("success");
  expect(attempts).toBe(3);
});
```

### 3. Verify RED

Run the focused test and confirm:

- It fails
- It fails for the expected reason
- The failure points to missing or broken behavior, not a typo or bad setup

If the test passes immediately, it is not proving the new behavior. Fix the test or choose a behavior that is not already covered.

If the test errors because of setup, fix the setup and rerun until the failure is meaningful.

### 4. GREEN: Implement The Minimum

Write only enough implementation to satisfy the failing test.

Do not:

- Add extra features
- Add broad configurability that was not requested
- Refactor unrelated code
- Change tests to fit the implementation
- Add abstractions for one use

If a simpler solution passes the behavior, prefer it.

### 5. Verify GREEN

Run the focused test and relevant surrounding tests.

Confirm:

- The new test passes
- Existing tests still pass
- Output is clean enough to trust

If tests fail, fix the implementation first. Do not weaken the test unless the test is genuinely wrong.

### 6. Refactor While Green

Only after tests pass:

- Remove duplication introduced by the change
- Improve names
- Extract helpers when they reduce real complexity
- Move complexity behind a simpler interface when the design clearly benefits

Run tests after each meaningful refactor.

## Bug Fix Pattern (Repro-First & Sequence Verifiable Units)

For bugs, make the broken behavior executable before changing production code. Strictly prohibit modifying business logic until reproduction is confirmed:

```text
1. Understand the bug: Identify intended vs current behavior and the narrowest surface.
2. Executable reproduction: Write the failing regression test, script, or preview test.
3. Verify failure (RED): Run the check. Confirm it fails for the EXACT reported symptom.
4. Commit RED: Commit the failing test first (`test: add failing reproduction for <issue>`).
5. Smallest fix (GREEN): Implement the minimal production fix to make the reproduction pass.
6. Verify fix (GREEN): Rerun the check. Confirm it turns green cleanly.
7. Commit GREEN: Commit the fix on top (`fix: <description>`).
8. Final evidence: Record both the failing-before log and passing-after log.
```

If an automated unit test is impractical (e.g. requires broad mocking of internal modules or production-only state), use the closest real-surface executable check: a deterministic CLI script, cURL, or `verify-mopheus` preview test. **Prefer no new test over a bad, mock-heavy test.**

## Interface Design Guidance

Let tests pressure the design, but do not contort production code for tests.

Good signs:

- The test reads like a usage example
- Setup is small and meaningful
- Assertions are about observable results
- The public interface is easy to explain

Warning signs:

- The test needs extensive internal mocks
- The test needs test-only production methods
- The test asserts many unrelated details
- The interface is hard to call without knowing internals

When the warning signs appear, simplify the public interface or isolate boundary dependencies with dependency injection.

## Completion Checklist

Before claiming the work is complete:

- [ ] (Bug fix) At least one relevant check/test failed before production code modification
- [ ] (Bug fix) The failure reproduced the exact user symptom
- [ ] (Bug fix) Two sequential commits exist in feature worktree (`test: ...` -> `fix: ...`)
- [ ] Implementation was scoped strictly to the tested behavior (no speculative abstractions)
- [ ] New tests verify observable behavior through public interfaces
- [ ] Mocks are strictly limited to external system boundaries (no internal mocks)
- [ ] Relevant focused checks pass cleanly
- [ ] Relevant broader checks pass or any inability to run them is reported
- [ ] Refactors, if any, happened only after green
- [ ] Final evidence includes both failing-before and passing-after execution proof

## Related References

If adding mocks or test utilities, read `testing-anti-patterns.md` in this skill directory before finalizing the test design to avoid brittle mocks and implementation coupling.
