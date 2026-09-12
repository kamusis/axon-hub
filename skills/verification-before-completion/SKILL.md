---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - audits the current change set or PR diff against architectural rules, coding standards, and quality guardrails; strictly scoped to modified lines without expanding to pre-existing repository code or executing test commands
---

# Verification Before Completion (Diff-Scoped Code Review)

## Overview

Claiming work is complete without auditing the change set against established rules creates bugs and regressions.

**Core principle:** Strict code review focused entirely on the **current change set / commit / PR diff**.
- **Diff-scoped only:** Audit what you changed. Do NOT expand the review to pre-existing repository code or audit untouched files.
- **Review only:** Verify architectural compliance and code quality — **do not execute test suites or act as a test runner**.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT DIFF AUDIT AND RULE COMPLIANCE REVIEW
```

Always inspect the current diff (`git diff`, staged changes, or branch diff) line-by-line against project rules before claiming work is finished.

## Scoping Rules (Diff-First)

1. **Audit Only What You Changed**: Inspect only modified, added, or deleted lines in the current change set.
2. **Never Audit Pre-Existing Code**: If an untouched file or adjacent pre-existing code violates a convention, ignore it. Do not attempt drive-by cleanups.
3. **Clean Up Only Your Mess**: Check that your change did not leave orphaned imports, unused variables, or broken call sites in touched code.

## The Review Gate

```
BEFORE claiming any status, completion, or committing/opening a PR:

1. INSPECT CURRENT DIFF: Review modified/added/deleted lines (git diff / git diff HEAD~1).
2. AUDIT MODIFIED CODE: Check the diff against the Architectural & Quality Checklist below.
3. VERIFY SURGICAL PRECISION: Confirm every changed line traces directly to the task. Reject unrequested abstractions or formatting churn.
4. RESOLVE OWN VIOLATIONS: If your changes introduce an anti-pattern or rule violation, fix it immediately.

Skip any step = incomplete review
```

*(Note: Test execution is handled by dedicated test workflows or CI pipelines, not by this review skill).*

## Quality & Architectural Review Checklist (Diff Scope)

Audit the **changed lines** against these critical defenses:

| Category | Check / Guardrail (On Changed Lines Only) | Anti-Pattern to Reject in Diff |
| :--- | :--- | :--- |
| **Constants & Enums** | Single source of truth: reuse existing definitions across packages. Search before defining new status maps, priority enums, or type dictionaries. | Defining duplicate or private `STATUS_TO_INT`, `PRIORITY_TO_INT`, or status lists across multiple components/files. |
| **State & Store Isolation** | Client state in UI stores (e.g. Zustand), server state in query caches (e.g. TanStack Query). Isolate persisted filter keys between distinct pages/views. Never duplicate server entities into client stores. | Shared filter keys causing "ghost filtering" between pages; duplicating server entities into global stores. |
| **API Boundary Safety** | Validate and parse API responses with runtime schemas (e.g. Zod) with safe fallbacks. Use explicit boolean `=== true` checks and `default` branches for enums. | Bare `as SomeType` assertions on API responses; truthy/falsy assumptions on server booleans. |
| **Destructive UI Safety** | Never use browser `window.confirm`. Require modal dialogs (e.g. Radix `AlertDialog`) with explicit consequence warning callouts and `e.stopPropagation()` on triggers. | Naked destructive buttons on hover without confirmation; unhandled click bubbling triggering parent row navigation. |
| **Internationalization (i18n)** | All user-visible strings must use the project's i18n hook/method (e.g. `useT(...)`). | Hardcoded English or Chinese text literals in JSX/templates, alerts, placeholders, or empty states. |
| **Cascade Deletes** | Explicit transactional cascade in the repository layer, leaf tables first. Update parent entity delete methods when new referencing tables are added. | Relying on DB foreign keys or leaving orphaned child rows after parent record deletion. |
| **Concurrency Safety** | All background goroutines, schedulers, loops, and workers must use panic-recovery wrappers (e.g. `util.SafeGo`). | Bare `go func()` calls without panic recovery. |
| **Test Structure & Colocation** | Ensure newly added tests conform to repository colocation and active test paths. Reject placement in deprecated test folders. | Writing new tests in deprecated directories (e.g. `tests/integration/` instead of `tests/e2e/services/`). |
| **CLI & Prompt Sync** | Repeatable CLI flags must be singular (`--label`), batch collections plural (`--ids`). Synchronize CLI flag changes with system prompts and builtin skills. | Mismatched singular/plural flags; CLI options undocumented or omitted from system prompt templates. |
| **Documentation Sync** | Synchronize multilingual user-facing documentation and navigation configs in the same change whenever features or CLI behaviors change. | Updating feature code without updating all supported documentation locales (e.g. `en`, `zh-Hans`, `ja`). |
| **Surgical Precision** | Minimum code that solves the problem. No speculative abstractions, no unrelated formatting/code cleanup, no orphaned variables or imports. | Overengineering, unrequested flexibility, modifying unrelated adjacent code. |

## Red Flags - STOP

- Expanding review scope to audit untouched files or whole-repo code
- Attempting to fix pre-existing defects unrelated to the current task
- Claiming completion without reviewing `git diff`
- Introducing duplicate constants, hardcoded strings, or bare type casts in the diff
- Expressing satisfaction before checking the current change set against the checklist

## When To Apply

**ALWAYS before:**
- Claiming task/ticket completion
- Creating commits or submitting Pull Requests
- Declaring a bug fix or feature implementation done
- Handing off work to the user or downstream processes
