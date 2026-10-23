---
name: mopheus-code-review
description: "Component-scoped architectural guardrails and code review workflow for enmotech/mopheus. Used by Code Writer before coding and before committing (to prevent regressions across backend, frontend, migrations, docs, and E2E tests) and by Code Reviewer during PR reviews (enforcing diff-driven component routing, Quick/Standard/Deep review tiers, zero-noise output, and multi-round convergence)."
---

# Mopheus Code Review & Component Guardrails

Single source of truth for component-scoped architectural guardrails in `enmotech/mopheus`, shared by both **`Code Writer`** (pre-implementation design & pre-PR self-review) and **`Code Reviewer`** (PR verification).

## Usage by Role

- **For `Code Writer` (Pre-Implementation & Pre-PR Self-Review)**:
  1. **Before writing code**: Identify which repository paths your task will touch and read **only** the matching checklists in **Step 1 (`1A`–`1G`)** below so your implementation follows every component invariant from the start.
  2. **Before committing (`git-commit-and-push`)**: Audit `git diff` against those same matched `1A`–`1G` checklists and resolve any violation before pushing.
- **For `Code Reviewer` (Pull Request Review)**:
  - Execute **Steps 1 through 4** in order: route by diff paths (`Step 1`), apply the review depth tier (`Step 2`), classify issues and converge (`Step 3`), and output using the strict review contract (`Step 4`).

## Core Principles

1. **Component-Scoped Inspection Only**: First determine which repository components are modified in the diff. **Activate ONLY the checklists matching touched file paths.** Never inspect, run checks for, or comment on untouched components (e.g., if a PR only modifies `server/**`, never evaluate or mention frontend rules).
2. **Evidence-Backed Findings**: Every finding must cite an exact `file:line` in the diff and explain the concrete failure mode. Never guess based on function or variable names alone.
3. **Zero-Noise Output**: When `blocking == 0`, approve directly without inventing style nits, optional cleanups, or out-of-scope suggestions.

---

## Step 1: Diff Inspection & Component Routing

Before evaluating any rule, inspect the changed file list:

```bash
git diff --name-only <base>...<head>
# or: gh pr view <pr> --json files --jq '.files[].path'
```

Activate **only** the component checklists whose path patterns match the changed files:

| Path Pattern in Diff | Activated Component Checklist |
| --- | --- |
| `server/migrations/**` | **1A. Database Migrations** |
| `server/**` (excluding migrations-only) | **1B. Go Backend & CLI** |
| `apps/web/**` | **1C. Web Frontend (Next.js / React)** |
| `packages/docs-content/**` | **1D. Product Documentation (Trilingual)** |
| `.env.example` or config loading (`server/config/**`) | **1E. Environment & Configuration** |
| `.agents/skills/**` | **1F. Agent Skills** |
| `tests/e2e/**` or `playwright*.config.ts` | **1G. Playwright E2E Tests (`tests/e2e/**`)** |

If a component's path pattern is **not** present in the diff, skip its checklist completely.

### 1A. Database Migrations (`server/migrations/**`)
- **No FK / No CHECK**: Migrations must not contain `FOREIGN KEY`, `REFERENCES`, or `CHECK` constraints; all validation belongs in application code.
- **Immutability**: Never modify or renumber an already-applied migration; schema changes require a new sequential migration pair (`.up.sql` / `.down.sql`).
- **Mandatory Comments**: Every new table and column requires `COMMENT ON TABLE` / `COMMENT ON COLUMN`, including integer enum value mappings.
- **Multi-tenancy & Types**: Workspace-scoped tables must include `workspace_id UUID NOT NULL`. Status/enum columns use `INT` (with named Go types and `fmt.Stringer` in `server/models/`). Standard `VARCHAR` lengths: short=50, medium=100, email/URL=255, long URLs=512/1024, descriptions=TEXT.

### 1B. Go Backend & CLI (`server/**`)
- **Workspace Isolation (`workspace_id`)**: Every database query on a workspace-scoped entity in `server/internal/repo/` must filter by `workspace_id`. Never leak data across workspace boundaries.
- **Leaf-First Cascade Deletes**: Entity deletion in `server/internal/repo/` must explicitly delete dependent records within the same transaction, leaf tables first. Adding a table referencing an existing entity requires updating that entity's delete path.
- **Goroutine Panic Recovery**: Every background goroutine (cron loops, watchers, schedulers, WebSocket pumps, hub loops, service/daemon goroutines) must use `util.SafeGo(logger, func())`.
- **HTTP Handler Boundaries**:
  - Validate every incoming UUID at the handler boundary; return 400 immediately on invalid format.
  - Never call `c.JSON()` directly; always use `util.SuccessResponse`, `util.ErrorResponse`, `util.ErrorResponseF`, or `util.PaginatedResponse`.
  - All JSON struct tags must use **camelCase** (`workspaceId`, `createdAt`), never `snake_case`.
  - Context keys must use constants from `server/text/text.go`, never raw string literals.
- **Centralized Error Codes**: Application error codes must be defined in `server/internal/errx`; never pass literal error-code strings to `errx.New`, `errx.Wrap`, `errx.Wrapf`, or `errx.Errorf` inside `http/`, `service/`, or `repo/`.
- **Service Parameter Standard**: New or modified service methods must follow `(ctx, params, input)` per `docs/service-params-standard.md` (resource IDs, `WorkspaceID`, actor, and pagination in `params`; business payload and filters in `input`).
- **Go Idioms & Comments**:
  - Bilingual Go doc comments (English first, Chinese second); inline comments in English only.
  - Never shadow `err` across scopes; fail fast with `if err := ...; err != nil`.
- **CLI & Prompt Synchronization**: If CLI flags, subcommands, or behavior under `server/cmd/` change, verify corresponding updates in `server/pkg/prompt/` (`provider_prompt_slim.go`) and affected `server/internal/service/builtin_skills/`. Repeatable flags default to singular nouns (`--label`, `--attachment`); plural nouns are reserved for batch ID lists (`--ids`, `--skill-ids`).

### 1C. Web Frontend (`apps/web/**`)
- **State Ownership**:
  - **TanStack Query** owns all server state; workspace-scoped query keys must include `workspaceId`.
  - **Zustand** (`apps/web/stores/`) owns client-only UI state. Never copy server data into Zustand. WebSocket events must only invalidate queries (`queryClient.invalidateQueries`), never write payloads directly into stores.
  - Hooks needing workspace context must accept `workspaceId` as a parameter rather than calling `useWorkspaceId()` internally.
- **List Query & URL Sync Anti-Flicker**:
  - TanStack Query list hooks accepting dynamic pagination, sorting, search, or filter parameters must set `placeholderData: keepPreviousData` so changing sort/page/filter never unmounts the view into a full-page loading skeleton. Do not apply redundant synchronous client-side search filtering on top of server-filtered query data.
  - Syncing client-managed list state (sort, page, filter, search, tab) to the browser URL bar in `"use client"` pages must use `window.history.replaceState(null, "", targetUrl)` rather than `router.replace(...)`, preventing Next.js App Router RSC server round-trips (`_rsc` fetches) and Suspense flashes.
- **API Parsing & Safety**:
  - Parse API responses with Zod schemas and safe fallbacks; never use bare `as` casts on response payloads.
  - Server-driven enum `switch` statements must include a `default` branch.
- **UI, Destructive Actions & i18n**:
  - Every user-visible string must use `useT("namespace")` from `@/lib/i18n/use-t`; never hardcode UI copy.
  - Resource list rows must never render naked destructive buttons on hover or use `window.confirm`; destructive actions belong inside a `DropdownMenu` (`text-destructive`) confirmed via Radix `AlertDialog` with `e.stopPropagation()`.
  - Tiptap editor code (`apps/web/components/editor/`) must read and dispatch through `editor.view.state`, never `editor.state`.
- **Route Slugs**: Any new global pre-workspace route must also be added to `reservedSlugs` in `server/internal/service/workspace.go`.

### 1D. Product Documentation (`packages/docs-content/**`)
- **Trilingual Synchronization**: Keep `packages/docs-content/en/`, `packages/docs-content/zh-Hans/`, and `packages/docs-content/ja/` synchronized in the same PR.
- **Navigation Registry**: Adding, renaming, or removing a doc page requires updating both `<section>/meta.json` and `nav.json` across all 3 locales, verified via `make check-docs-nav`.

### 1E. Environment & Configuration
- Any newly introduced environment variable must be documented in `.env.example`.

### 1F. Agent Skills (`.agents/skills/**`)
- Verify valid YAML frontmatter (`name`, `description`) and clear, unambiguous instructions without contradicting `AGENTS.md`.

### 1G. Playwright E2E Tests (`tests/e2e/**` & `playwright*.config.ts`)
- **Executable Source Precedence Over Stale Ticket Prose**:
  - Before writing or reviewing an `[E2E Gap]` spec, inspect the target production components (`apps/web/`, `server/internal/http/`, `server/cmd/`) at current `HEAD`. If commits merged after the ticket's `updatedAt` altered the DOM structure, i18n copy, receipt format, route, or API payload, **always follow current executable production code as the source of truth** and note the evolution delta in the PR/ticket comment rather than coding against outdated ticket prose.
- **Strict-Mode Locator Scoping (Prevent Multi-Element Collisions)**:
  - **Optimistic Mutation vs. Editor Collision**: After submitting a comment or form, never assert with an unscoped `page.getByText(...)` while the optimistic cache entry (`onMutate`) and the still-filled editor (`reply-input-shell` or inline editor before `onSuccess` clears it) can coexist. Always await the `POST`/`PUT`/`PATCH` response, read the server-assigned ID, and scope assertions to the target container (e.g., `page.locator("#ticket-comment-<id>")`).
  - **`getByRole("alert")` Collision**: Never use bare `page.getByRole("alert")` (which collides with Next.js `__next-route-announcer__` in strict mode). Always chain `.filter({ hasText: ... })` or scope inside the active dialog/form container.
  - **Listbox / Combobox Option Collision**: When picking an option from a `Select`, `Combobox`, or `Command` menu, always scope the option click to `page.getByRole("listbox")` or `getByRole("option")` so it never collides with the trigger button/chip when the current value matches the target option (e.g., default timezone `Asia/Tokyo`).
  - **File Tree / Table / Sidebar Scoping**: Scope item clicks and text assertions to their structural container (`tr`, `[role="tree"]`, dialog, or specific button role) rather than matching bare filenames or labels across the whole page.
- **Await Mutation Network Responses Before Reload / Navigation**:
  - Never rely solely on generic toast text (e.g., `/saved/i`) or immediately call `page.reload()` / `page.goto()` after clicking Save/Submit/Delete, which aborts in-flight requests. Always synchronize on the network response (e.g., `await Promise.all([page.waitForResponse((res) => res.url().includes("/api/v1/...") && res.request().method() === "PUT"), saveButton.click()])`).
- **Ban Arbitrary Sleeps & Timer Races**:
  - Never use `page.waitForTimeout(...)` or fixed `setTimeout(resolve, N)` delays inside `page.route()` mocks. Use deterministic Promise gates, `page.waitForResponse(...)`, DOM state assertions, or `expect.poll(...)`.
- **Shared Workspace Hygiene & Idempotent Teardown (`try ... finally` / `afterEach`)**:
  - Full E2E runs serially (`workers: 1`) against a shared bootstrapped workspace (`fullUserState`). Any test that mutates workspace-level state (such as feature flag overrides via `PUT /api/v1/workspaces/:wsId/features/:key`, system settings, or global templates) **must** restore the original state in `try ... finally` or `test.afterEach` / `test.afterAll`, and clean up created test entities so subsequent specs are never polluted.
- **Reuse Shared E2E Fixtures & Helpers**:
  - Use `fullFrontendUrl`, `fullBackendUrl`, `createTestApi()`, and `loginAsDefault()` from `tests/e2e/services/shared/{fixtures,helpers}.ts` with `test.use({ baseURL: fullFrontendUrl })`. Never hardcode `localhost:3000` or `localhost:8080`.
- **Playwright Config Registration (`playwright.full.config.ts`)**:
  - Any new spec file under `tests/e2e/services/<domain>/*.spec.ts` must reside in a `<domain>` registered in the service project list in `playwright.full.config.ts` (or add the domain to `playwright.full.config.ts`).

---

## Step 2: Review Depth Tier Routing (`Quick` / `Standard` / `Deep`)

Use the `Review Tier` specified by `Team Leader`, or classify automatically from the touched paths:

1. **`Quick` (Low Risk)**:
   - **Scope**: Only `.agents/skills/**`, `packages/docs-content/**`, comments/copy tweaks, pure unit test additions (`*_test.go`, `*.test.ts`, `*.test.tsx`), or local constant exports with no behavior change. *(Note: `tests/e2e/**` changes are never `Quick`; they require `Standard` tier).*
   - **Action**: Check the activated component checklist and verification result. **Skip the `Requirement Traceability` matrix table.**
2. **`Standard` (Normal Business Change & E2E Journeys)**:
   - **Scope**: Standard Go HTTP/Service/Repo logic, CLI subcommands/flags, React components/hooks, or Playwright E2E test journeys (`tests/e2e/**`).
   - **Action**: Check activated component checklists + verify core acceptance criteria in the `Requirement Traceability` table.
3. **`Deep` (High Blast Radius)**:
   - **Scope**: Auth/RBAC (`docs/permissions.md`), encryption/credentials (`server/pkg/crypto/`), database migrations & cascade deletes (`server/migrations/`, `server/internal/repo/`), concurrency/WebSocket/Daemon scheduling, or CI/Release workflows (`.github/workflows/`).
   - **Action**: Check activated component checklists + enforce full 3-link `Requirement Traceability` matrix (production implementation + real production call path + boundary/negative tests).

---

## Step 3: Issue Classification & Multi-Round Convergence

### Finding Categories
- **`[Blocking]`**: Violates acceptance criteria, introduces a logic/concurrency/security bug, breaks a matched component invariant above, or lacks required behavioral tests. Must include `file:line` and concrete fix direction. Triggers `Verdict: CHANGES REQUESTED`.
- **`[Pre-existing]`**: A flaw in surrounding untouched or legacy code **not introduced by this PR**. May be noted in one objective line only if it directly affects current safety, **never triggers `CHANGES REQUESTED`**, and must not require the author to refactor unrelated code.
- **Discard Style Nits**: Formatting, import ordering, subjective naming preferences, or speculative refactors must be discarded.

### Convergence Rules
1. **Flag the Class of Bug Once**: In Round 1, if a class of violation is found (e.g., missing `workspace_id` filter, raw error code string, missing i18n), scan the entire diff and report all occurrences in a single pass.
2. **Diff-Only Re-review (Round 2+)**: On subsequent review rounds, inspect **only** the new commits' incremental diff and previously open `[Blocking]` items. Never raise new findings on lines that were already reviewed and unchanged since Round 1.
3. **3-Round Cap**: If `[Blocking]` issues remain unresolved after 3 review rounds, stop normal rejection loops and instruct `Team Leader` to escalate to the human reporter.

---

## Step 4: Output Format Contract

Always start with the single-line summary count:

```markdown
Summary: <N> blocking, <M> pre-existing
Review Tier: <Quick | Standard | Deep> (Touched components: <e.g. Go Backend, Database Migrations>)
```

- **When `blocking == 0` (Plain Pass)**:
  - Omit `Required Changes` and `Suggestions` sections completely.
  - Include `Requirement Traceability` table only for `Standard` and `Deep` tiers.
  - Include `Verification` and end with `Verdict: APPROVED`.
- **When `blocking > 0`**:
  - List only `[Blocking]` items under `Required Changes:` with `file:line`, failure mode, and fix.
  - Optionally list `[Pre-existing]` items (if any) under a brief `Pre-existing Notes (Non-blocking):` line.
  - Include `Requirement Traceability` (for `Standard`/`Deep`), `Verification`, and end with `Verdict: CHANGES REQUESTED`.
