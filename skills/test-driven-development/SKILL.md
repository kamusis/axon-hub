---
name: test-driven-development
description: Use when implementing any feature, bugfix, refactor, or behavior change before writing implementation code. Guides a practical red-green-refactor workflow with behavior-focused tests through public interfaces. Also use when the user asks for TDD, test-first development, red-green-refactor, regression tests, or integration-style tests.
---

# Test-Driven Development (TDD)

## Purpose

Write the test first, watch it fail for the expected reason, then write the smallest implementation that makes it pass.

The goal is not ceremony. The goal is evidence: a failing test proves the test can catch the missing behavior or bug, and a passing test proves the implementation satisfies that behavior.

## When To Use

Use this skill before implementation for:

- New features
- Bug fixes
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

### Test Behavior, Not Implementation

Tests should verify what users, callers, APIs, commands, or systems observe. They should not lock down private methods, internal call order, or incidental structure.

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

### Prefer Integration-Style Tests

Favor the narrowest test that still exercises the real behavior. Often this is an integration-style unit test around a service, controller, CLI command, parser, or API client.

Mock only at true system boundaries:

- External services
- Network APIs
- Time and randomness
- File systems when a temp directory is not practical
- Databases when a test database or embedded substitute is not practical

Do not mock your own modules just to make the test smaller. If testing requires mocking everything, the design may be too coupled.

### Work In Vertical Slices

Do not write all tests first and then all implementation. That is horizontal slicing: it bakes in imagined behavior and often produces brittle tests.

Use tracer bullets:

```text
RED   one failing test for one behavior
GREEN minimal implementation
REFACTOR only while green
REPEAT next behavior
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

## Bug Fix Pattern

For bugs, the first test should reproduce the reported failure as closely as possible.

```text
1. Create a failing regression test that shows the bug.
2. Verify the failure matches the user's symptom.
3. Implement the smallest fix.
4. Verify the regression test passes.
5. Run the relevant broader test suite.
```

Do not fix a bug only by inspection when an automated regression test is practical.

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

- [ ] At least one relevant test failed before implementation
- [ ] The failure reason was verified
- [ ] Implementation was scoped to the tested behavior
- [ ] New tests use public interfaces where practical
- [ ] Mocks are limited to system boundaries
- [ ] Relevant focused tests pass
- [ ] Relevant broader tests pass or any inability to run them is reported
- [ ] Refactors, if any, happened only after green

## Related Reference

If adding mocks or test utilities, read `testing-anti-patterns.md` in this skill directory before finalizing the test design.
