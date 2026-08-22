---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evidence before assertions always
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status, completion, or expressing satisfaction:

1. IDENTIFY: What commands and deliverables prove this claim?
2. AUDIT APPLICABLE TEST TIERS (Repository-Adaptive):
   - Discover the repository's test architecture (colocated unit tests, integration test suites, E2E framework, test scripts).
   - Unit Tests: Are dedicated unit tests implemented/updated for all modified logic, models, handlers, and components?
   - Integration Tests: If the repository maintains integration test suites/specs/scripts, are they updated with new capabilities and boundary cases?
   - E2E Tests: If the repository maintains an E2E testing framework (e.g. Playwright, Cypress) and user flows/UI were added or changed, are E2E specs added/updated?
   - Acceptance Criteria: Have all explicit criteria in the issue/ticket/task been verified line by line?
3. RUN: Execute the FULL authoritative verification commands (fresh, complete, no stale cache)
4. READ: Full output, check exit code, count failures (must be 0 failures)
5. VERIFY: Does output confirm the claim across all applicable tiers?
   - If NO: State actual status with evidence of gaps/failures
   - If YES: State claim WITH fresh execution evidence
6. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Unit tests complete | Dedicated unit tests for all modified logic, models, API routes, CLI flags, and UI components in the repo's native test structure | Only running pre-existing tests without adding new coverage |
| Integration tests updated | Integration test suites/specs/scripts updated whenever the repository maintains integration tests | Assuming unit tests are enough when integration test suites exist |
| E2E tests covered | E2E specs added/updated whenever the repository maintains an E2E framework and user-facing UI flows were modified | Only testing with unit/mock tests |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist against all acceptance criteria | Tests passing |

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Adaptive Test Tier Verification (自适应全层级测试完备性门禁)

Before marking any task, ticket, PR, or feature implementation as complete, discover the target repository's testing architecture and verify all **applicable** tiers:

### 1. Repository Test Architecture Discovery (测试架构自适应探测)
- Inspect the codebase to detect available test frameworks and directory layouts:
  - **Unit test conventions**: colocated (e.g. `*_test.go`, `*.test.ts`, `test_*.py`, `src/test/`), `tests/unit/`, `test/`, etc.
  - **Integration test conventions**: dedicated directories (`tests/integration/`, `integration/`, `tests/`), scenario markdown files, shell test suites, API test collections.
  - **E2E test conventions**: Playwright, Cypress, Selenium, Puppeteer (e.g. `tests/e2e/`, `e2e/`, `cypress/`).
  - **Build/Verification targets**: `Makefile`, `npm run test`, `pnpm test`, `cargo test`, `pytest`, `go test ./...`, etc.

### 2. Tier-by-Tier Audit (逐层核对)
- **Tier 1: Unit Tests (单元测试) — Mandatory for all codebases with tests**:
  - All modified or newly added functions, methods, domain models, services, handlers, CLI flags, and UI components must have dedicated unit test cases.
- **Tier 2: Integration Tests (集成测试) — Required if the repository maintains integration suites**:
  - If the repository has integration test suites, scenario documentation, or automated integration scripts, update them to cover the new features, flags, API routes, and boundary cases.
  - If the repository has no integration suite, verify cross-component interactions via available CLI commands, API calls, or integration targets.
- **Tier 3: E2E / Browser Tests (端到端测试) — Required if the repository maintains an E2E framework**:
  - If the repository maintains E2E test suites (e.g. Playwright) AND the change involves user-facing UI flows, pages, dialogs, or cross-cutting interactions, add or update E2E test specs.
  - If the repository is backend-only, library-only, or has no E2E framework configured, this tier is not applicable.
- **Tier 4: Acceptance Criteria (验收标准逐项核验)**:
  - Check every acceptance criterion from the task/issue/ticket description against fresh verification command outputs.

---

## Key Patterns

**1. Unit Tests:**
```
✅ [Run repo unit test command] [See: 0 failures] "All unit tests pass across modified packages"
❌ "Should pass now" / "Looks correct without running unit tests"
```

**2. Integration Tests (when integration suite exists):**
```
✅ [Inspect: integration test specs/scripts updated] [Run: repo integration test command] "Integration tests updated and passing"
❌ "Unit tests passed so skip updating existing integration test suite"
```

**3. E2E Tests (when E2E suite exists and UI was modified):**
```
✅ [Inspect: E2E specs cover new UI flows/dialogs] [Run: repo e2e test command] "E2E flows verified"
❌ "Component tests are sufficient, skip E2E test coverage"
```

**4. Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**5. Build & Typecheck:**
```
✅ [Run build & typecheck commands] [See: exit 0] "Build and typecheck pass"
❌ "Linter passed" (linter doesn't check compilation or type soundness)
```

**6. Acceptance Criteria (Line-by-Line Checklist):**
```
✅ Re-read issue/ticket → Create checklist of all criteria → Verify each with evidence → Report 100% completion
❌ "Tests pass, phase complete" (without verifying all explicit criteria)
```

**7. Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes independently → Report actual state
❌ Trust agent report blindly
```

## Why This Matters

From 24 failure memories:
- your human partner said "I don't believe you" - trust broken
- Undefined functions shipped - would crash
- Missing requirements shipped - incomplete features
- Time wasted on false completion → redirect → rework
- Violates: "Honesty is a core value. If you lie, you'll be replaced."

## When To Apply

**ALWAYS before:**
- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

**Rule applies to:**
- Exact phrases
- Paraphrases and synonyms
- Implications of success
- ANY communication suggesting completion/correctness

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.
