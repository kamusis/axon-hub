---
name: karpathy-guidelines
description: Behavioral guidelines to reduce common LLM coding mistakes. Use whenever planning, writing, fixing, reviewing, or refactoring code to surface assumptions, prefer existing and platform-native solutions, avoid overengineering, make surgical root-cause changes, and define verifiable success criteria.
license: MIT
---

# Karpathy Guidelines

Behavioral guidelines to reduce common LLM coding mistakes, derived from [Andrej Karpathy's observations](https://x.com/karpathy/status/2015883857489522876) on LLM coding pitfalls and extended with platform-first solution selection.

**Tradeoff:** These guidelines bias toward caution and simplicity over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Do not assume or hide confusion. Surface assumptions and tradeoffs.**

Before implementing:

- State assumptions that materially affect the solution.
- If multiple interpretations would produce meaningfully different behavior, present them and ask.
- If a safe, reversible default is clear, state it and proceed instead of blocking unnecessarily.
- If a simpler approach exists, say so and explain the tradeoff.
- Read the code the change touches and trace the real production flow before choosing an implementation.
- Treat explicit acceptance criteria as authoritative. Do not silently reduce requested scope in the name of simplicity.

## 2. Select The Smallest Sufficient Solution

**Prefer capabilities the codebase and platform already provide.**

After understanding the requirement, use the first option that fully satisfies it:

1. Do not build behavior that is not required.
2. Reuse an existing repository helper, type, component, or established pattern.
3. Prefer the standard library.
4. Prefer a native browser, operating-system, database, language, or runtime capability.
5. Prefer an already-installed dependency.
6. Only then write the smallest readable custom implementation.

This is a decision order, not a code-golf target. Correctness, repository conventions, maintainability, and explicit requirements take precedence. Add a dependency or abstraction when it clearly handles required complexity better than a local implementation, and record the concrete reason.

## 3. Simplicity First

**Write the minimum code that solves the current problem. Nothing speculative.**

- Do not add features beyond what was requested.
- Do not create abstractions for a single use without a present requirement.
- Do not add flexibility, configuration, or extension points nobody currently needs.
- Do not add speculative handling for states that established contracts make impossible.
- Prefer boring, readable code over compressed or clever code.
- If the implementation is substantially larger than the behavior requires, simplify it before handoff.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 4. Fix Root Causes

**A small fix in the right shared location is better than repeated symptom patches.**

For bug fixes:

- Reproduce or otherwise establish the failure before editing.
- Inspect callers and sibling paths of the function or component being changed.
- Fix the shared root cause once when the affected paths genuinely share the same invariant.
- Do not broaden a focused fix into an unrelated refactor.
- Add regression coverage through the repository's existing test interfaces.

## 5. Make Surgical Changes

**Touch only what the task requires. Clean up only consequences of your own change.**

When editing existing code:

- Do not improve adjacent code, comments, naming, or formatting without a task-related reason.
- Do not refactor unrelated code.
- Match the existing style and architecture unless changing them is part of the requirement.
- If you notice unrelated dead code or defects, report them instead of silently expanding scope.

When your changes create orphans:

- Remove imports, variables, functions, and files made unused by your change.
- Do not remove pre-existing dead code unless requested.

Every changed line should trace to the requirement, its regression protection, or necessary cleanup caused by the change.

## 6. Preserve Engineering Boundaries

**Minimalism must not weaken required protection or evidence.**

Never simplify away:

- Validation at trust boundaries.
- Authentication, authorization, and other security controls.
- Error handling that prevents data loss, corrupted state, or misleading success.
- Accessibility requirements.
- Required observability, audit behavior, migrations, or compatibility guarantees.
- Tests and verification required by the repository, implementation plan, acceptance criteria, or Definition of Done.

Use the repository's existing test framework. Add the smallest set of behavior-focused tests that provides meaningful regression protection and satisfies the acceptance criteria. Do not introduce redundant fixtures, test infrastructure, or implementation-detail tests.

## 7. Execute Toward Verifiable Goals

**Define success criteria and loop until the evidence satisfies them.**

Transform vague tasks into observable outcomes:

- "Add validation" becomes tests for invalid inputs followed by the implementation that passes them.
- "Fix the bug" becomes a regression test that reproduces the failure followed by the root-cause fix.
- "Refactor X" becomes preservation of behavior verified before and after the change.

For multi-step tasks, keep the plan concrete:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Before claiming completion, report the exact verification evidence required by the repository or team workflow. Passing tests do not compensate for unmet acceptance criteria, and a small diff is not evidence that the change is correct.

## Review Application

When reviewing code, check correctness and required behavior first. Then identify dependencies, abstractions, configuration, duplicated logic, or custom implementations that are unnecessary for the current requirement. Suggest removal only when the smaller alternative preserves correctness, security, maintainability, tests, and acceptance criteria.
