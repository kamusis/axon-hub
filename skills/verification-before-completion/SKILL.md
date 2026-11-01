---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - runs unified dual-engine audit (ponytail-review for lean/caller blast radius + architectural guardrails like mopheus-code-review); strictly scoped to current diff and its direct caller impact without expanding to unrelated code or executing test suites
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
2. **Trace Caller Impact (Blast Radius)**: A change can break code it does not touch. When a function signature, return value, or behavior changes, grep its callers across the codebase to ensure outside call sites are not broken.
3. **Never Audit Pre-Existing Code**: If an untouched file or adjacent pre-existing code violates a convention, ignore it. Do not attempt drive-by cleanups.
4. **Clean Up Only Your Mess**: Check that your change did not leave orphaned imports, unused variables, or broken call sites in touched code.

## The Review Gate (Dual-Engine Pipeline)

```
BEFORE claiming any status, completion, or committing/opening a PR:

1. INSPECT CURRENT DIFF: Review modified/added/deleted lines (git diff / git diff HEAD~1).
2. PHASE A: PONYTAIL LEAN & CALLER AUDIT (`ponytail-review`)
   - Caller Blast Radius: Grep callers of every modified function/signature; ensure outside code is not broken.
   - Lean & Anti-Bloat: Smallest complete change. Check if newly added lines can be eliminated, simplified, or use existing helpers (Lean: -N lines). Reject speculative abstractions.
   - Concurrency & Scale: Check check-then-write races, N+1 queries, memory growth, unrecovered goroutines/workers under expected load.
   - Risky Logic & Tests: Risky new logic (branches, parsers, security, writes) must have focused behavioral tests.
3. PHASE B: ARCHITECTURAL COMPLIANCE AUDIT
   - If working in `enmotech/mopheus`: Read and apply `mopheus-code-review` (`Step 1: 1A–1G` component checklists matched to touched file paths) as the single source of truth.
   - For all other repositories: Check the diff against the Universal Quality & Architectural Review Checklist below and the repository's `AGENTS.md` / `CLAUDE.md`.
4. RESOLVE OWN VIOLATIONS & VERDICT:
   - Fix all [Blocking] defects and unnecessary bloat before claiming completion.
   - Both Phase A and Phase B must pass (Ship / Approved).

Skip any step = incomplete review
```

*(Note: Test execution is handled by dedicated test workflows or CI pipelines, not by this review skill).*

## Repository-Specific Routing: `enmotech/mopheus`

When the current repository is `enmotech/mopheus` (detected via `git remote get-url origin` or `.agents/skills/mopheus-code-review/SKILL.md`):
- **Do NOT maintain or rely on a duplicate static checklist here.**
- **Mandatory Action**: Read `.agents/skills/mopheus-code-review/SKILL.md` (or invoke the `mopheus-code-review` skill), match the changed file paths in `git diff --name-only` against **Step 1 (`1A`–`1G`)**, and audit the diff strictly against the activated component checklists (`1A` Migrations, `1B` Go Backend & CLI, `1C` Web Frontend, `1D` Trilingual Docs, `1E` Env/Config, `1F` Agent Skills, `1G` Playwright E2E Tests).

## Universal Quality & Architectural Review Checklist (Non-Mopheus / General Diff Scope)

For repositories without a dedicated review skill, audit the **changed lines** against these baseline defenses:

| Category | Check / Guardrail (On Changed Lines Only) | Anti-Pattern to Reject in Diff |
| :--- | :--- | :--- |
| **Constants & Enums** | Single source of truth: reuse existing definitions across packages. Search before defining new status maps, priority enums, or type dictionaries. | Defining duplicate or private status/priority maps or enum lists across multiple files. |
| **State & Store Isolation** | Keep client UI state and server cache state separated per project conventions. Isolate persisted filter keys between distinct views. | Shared filter keys causing cross-page interference; duplicating server entities into local UI stores. |
| **API & Boundary Safety** | Validate inputs and parse external/API responses safely with explicit fallbacks and `default` branches for enums. | Unchecked type assertions on external payloads; truthy/falsy assumptions on nullable booleans. |
| **UI & Confirmation Safety** | Follow project modal/dialog conventions for destructive actions and prevent unintended event propagation (`stopPropagation`). | Unconfirmed destructive actions or unhandled click bubbling in interactive rows. |
| **Internationalization (i18n)** | Use the project's i18n mechanism for all user-visible copy when the codebase is localized. | Hardcoded text literals in localized UI components. |
| **Data & Concurrency Safety** | Maintain transactional integrity on writes/deletes and ensure background workers/goroutines recover from panics/errors. | Partial non-transactional deletes leaving orphaned records; unrecovered background goroutines/tasks. |
| **Test & Doc Synchronization** | Place new tests in the repository's active test directories and update user-facing docs/prompts when CLI flags or public behavior change. | Adding tests to deprecated directories or changing public interfaces without updating corresponding docs. |
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
