---
name: mopheus-dev-grilling
description: "Grill Mopheus architecture, feature designs, or bug fixes against real codebase facts and AGENTS.md rules. First checks out mopheus repo via mop repo checkout, inspects AGENTS.md, verifies models/APIs/components, and conducts rigorous domain-aware grilling."
---

# Mopheus Dev Grilling

Specialized grilling workflow for reviewing, challenging, and refining feature designs, architecture proposals, and bug fixes specifically within the **Mopheus** platform (`enmotech/mopheus`).

## Core Principle: Code-First Investigation (代码事实优先)

Never guess or hallucinate when grilling Mopheus features.
**If a fact can be discovered from the codebase, you MUST discover it yourself before asking or proposing.**

---

## 1. Mandatory Pre-Grill SOP (前置探查标准动作)

When invoked on a Mopheus-related ticket, feature discussion, or PR review:

### Step 1: Checkout the Codebase
If not already running inside the `mopheus` git workspace, immediately checkout the latest worktree:
```bash
mop repo checkout mopheus
```

### Step 2: Read Architectural Source of Truth
Inspect `AGENTS.md` at the repository root. This document is authoritative for all backend, frontend, database, concurrency, and UI conventions.

### Step 3: Locate Codebase Facts
Before asking questions or proposing schemas:
- **Enums & Models**: Check `server/models/*.go` (verify exact enum constants, integer mappings, and Stringer implementations).
- **APIs & Routes**: Check `server/internal/http/*.go` (verify existing route groups, path parameters, handlers, and camelCase JSON contracts).
- **Services & Queries**: Check `server/internal/service/*.go` and `server/internal/repo/*.go`.
- **Database Schema**: Check `server/migrations/*.sql` (verify existing tables, column lengths, and migration sequence numbers).
- **Frontend Components**: Check `apps/web/components/` and `apps/web/components/markdown/` (verify how Markdown, mentions, dialogs, and cards are currently rendered).

---

## 2. Mopheus Invariant Checklist (架构底线核查清单)

Every technical design proposed or reviewed must pass this 10-point architectural invariant checklist:

### Backend & Database Invariants
1. **Zero Foreign Keys & Zero CHECK Constraints**:
   - Mopheus prohibits physical FKs and CHECK constraints in PostgreSQL. All validation must happen in the Go service layer.
2. **Explicit Cascade Deletes (Repo Level)**:
   - When deleting an entity (`DeleteTicket`, etc.), the Repo layer must explicitly delete all dependent records in the same transaction, leaf tables first. Never leave orphaned rows.
3. **Mandatory Multi-tenancy (`workspace_id`)**:
   - Every workspace-scoped entity table must include `workspace_id UUID NOT NULL`.
   - Every database query must filter by `workspace_id`.
4. **Strict camelCase in JSON & HTTP Boundaries**:
   - All JSON fields must use **camelCase** (`workspaceId`, `ticketId`, `createdAt`), never `snake_case`.
   - Validate every UUID at the handler boundary (return 400 immediately on invalid format).
   - Use standard response envelopes: `util.SuccessResponse` or `util.ErrorResponse`.
5. **Enums as Typed INTs**:
   - Enum columns in the DB use `INT`.
   - Go enums are named types with typed constants in `server/models/`.
   - Every enum must implement `fmt.Stringer` and pass `enum_roundtrip_test.go`.

### Frontend & Notification Invariants
6. **Strict State Ownership**:
   - **TanStack Query owns all server state** (tickets, comments, agents, workspaces).
   - **Zustand owns client-only UI state** (`apps/web/stores/`). Never duplicate server data into Zustand.
   - All workspace-scoped query keys must include `workspaceId`.
7. **WebSocket Event Discipline**:
   - Mopheus uses **WebSocket Hub** (`server/internal/notify/`), NOT Server-Sent Events (SSE).
   - **WebSocket events invalidate queries; they never write server data into stores or component state directly.**
   - Pattern: `queryClient.invalidateQueries({ queryKey: [...] })`.
8. **UI Design System**:
   - Pure **Tailwind CSS v4 + shadcn/ui + Radix UI**.
   - Standard card container layout: outer `p-6` (or `p-4 sm:p-6`), inner `<div className="flex flex-1 min-h-0 flex-col overflow-hidden rounded-lg border bg-background">`.
   - PageHeader standard: single-line layout (`[Icon] [Title (font-medium)] [Count] [Inline Tagline]`).
   - Confirmation dialogs: Radix `AlertDialog` with frosted glass overlay; never native `window.confirm`.

### Security & Agent Invariants
9. **Credential Safety**:
   - Never collect or transmit passwords, API tokens, or secrets via ticket comment streams or widgets.
   - Credentials must use workspace tokens or dedicated encrypted settings.
10. **Agent Lifecycle & Natural Conversation**:
    - Avoid out-of-band prompt injections when comment streams already carry context.
    - Rely on standard **Trigger Comment wakeup** mechanisms.
    - Comments and emitted widgets are immutable once posted; corrections happen via new comments or new widgets.

---

## 3. Grilling Execution Flow

During the grilling session:

1. **Recite the core proposal and pinpoint its implicit assumptions.**
2. **Challenge against codebase facts**:
   - "You proposed `CommentType = 4`, but `server/models/ticket_comment.go` currently defines only 0~3. We must define `CommentTypeWidgetEvent = 4` with `String()` and update migrations."
   - "You proposed SSE, but Mopheus uses WebSocket Hub in `server/internal/notify/`."
3. **Present recommended options for each question**: Never ask open-ended questions without providing a recommended answer and technical trade-off rationale. In multi-agent/team grilling sessions (Agent-to-Agent), always format branches and recommendations using native Markdown tables or lists; never emit ````widget` code blocks because follow-up comments from moderators or peers trigger immediate expiration (`hasNewerComment`). Reserve widgets solely for direct human-facing decision points.
4. **Prune speculative complexity**: Apply the *Simplicity First* rule. If a feature can be solved with 3 states instead of 8, or without a retract window, push back firmly.
5. **Output Final Consolidated Spec**: Deliver complete, copy-pasteable JSON schemas, Go DDL/structs, and React component contracts ready for Code Writer.
