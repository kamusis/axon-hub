---
name: mopheus-mes-ticket-bridge
description: Bridge MES service-request webhook events into Mopheus workspace tickets. Use this skill whenever an MES webhook envelope (event_type + mes_sr_id + payload) must be processed — covering ticket.created, ticket.replied, and ticket.closed. The skill handles per-event routing, dedup, ticket creation (agent-owned), DBA dispatch, and mes-cli rate-limited outbound replies (Markdown format).
compatibility: Requires bash, jq, an authenticated moclaw CLI, and (for outbound replies) the `mes` CLI on PATH.
---

# MES → Mopheus Ticket Bridge

Synchronize an MES service-request event into the agent's active Mopheus workspace.

## Architecture (v14: agent-owned ticket lifecycle)

The MES Webhook Handler job uses `actionType=assign_agent`, so the agent (mes-leader) receives the raw MES envelope directly in its trigger context — there is **no transit-ticket placeholder**. The agent invoking this skill is responsible for the full ticket lifecycle:

- For `ticket.created` → the bridge creates the canonical Mopheus ticket itself via `ticket create`.
- For `ticket.replied` / `ticket.closed` → the bridge finds the existing canonical ticket and patches / closes it.

The skill is a thin dispatcher that routes a single MES envelope to one of three event handlers. All per-event-type logic is implemented in bash, **not** in prompts — the agent invoking the skill should not reimplement any of the steps below.

```
bridge.sh  (entry; uses the agent's active workspace — no flag required)
  ├─ event_created.sh        (ticket.created   — create canonical ticket + assign DBA + mes-cli reply)
  ├─ event_replied.sh        (ticket.replied   — patch existing ticket + dispatch DBA + mes-cli reply)
  └─ event_closed.sh         (ticket.closed    — patch + flip canonical ticket to done)
```

Shared helpers (parsing, dedup, metadata, routing, mes-cli rate-limit, agent-run polling) live in `lib_common.sh`.

## Required behavior

1. Read the complete JSON payload from a file or stdin. Treat it as authoritative — preserve every field, nested object, array, HTML tag, and original formatting.
2. Extract `event_type` (top-level) and `mes_sr_id` (top-level, numeric).
3. Dispatch by `event_type` to the matching handler. Refuse unknown event types.
4. For `ticket.created`: the bridge creates the canonical Mopheus ticket directly via `ticket create`. If a canonical ticket already exists for the same `mes_sr_id`, ack dup and exit.
5. For every other supported event (`ticket.replied`, `ticket.closed`): **locate the existing canonical ticket by `mes_sr_id` and refuse to create a new one.** If none exists, abort with an error.
6. Use idempotency keys (`replyId`, `(stateUpdateTime,status)`) to skip duplicate events.
7. Route the assigned DBA agent (`mes-mysql` / `mes-postgresql` / `mes-oracle`) based on `payload.dict.itemName`; fall back to `mes-mysql` if unknown.
8. For `ticket.replied`, after patching the canonical ticket, post a follow-up comment with `@[agent](mention://agent/<id>)` to dispatch the assigned DBA agent for continued analysis. Wait for the agent run to complete (≤10 min), then send the DBA agent's **actual analysis** as the mes-cli internal reply body (Markdown rendered, `--internal --markdown`).
9. For `ticket.created`, the bridge creates the canonical ticket, assigns the routed DBA agent, and flips status to `todo` — the platform then auto-enqueues the DBA agent run. The bridge waits for that run (≤10 min), captures the DBA agent's analysis from its first comment, and sends it as the mes-cli internal reply body (`--internal --markdown`). This closes the loop on `created` events so the MES customer sees the DBA's read-only analysis without manual follow-up.
10. For `ticket.replied`, send the DBA agent's captured analysis to MES immediately via `mes sr reply --internal --markdown`. No bridge-side rate-limit is applied — duplicate sends are already blocked upstream by `seen_reply_ids` (item 6), so the earlier 1h deferral that silently swallowed follow-up replies has been removed.

## Workspace safety

The design does not cross workspaces — the bridge skill intentionally does **not** accept `--workspace-id`, never hard-codes a workspace name or ID, and never exports `WORKSPACE_ID`. All `moclaw` calls inside the bridge inherit the agent's currently active workspace, so do not pass `--workspace-id` to `bridge.sh`, do not export it manually in your prompt, and do not hard-code it in any caller. Letting the task handle workspace context automatically is intentional: a hand-typed workspace ID can bypass the platform's permission scope.

## Shell implementation

Use the bundled dispatcher:

```bash
scripts/bridge.sh payload.json
```

Or via stdin:

```bash
cat payload.json | scripts/bridge.sh
```

v14 has **no** `--transit-ticket` flag and **no** `--workspace-id` flag. The agent invokes the bridge with the raw envelope from its trigger context; the bridge owns the ticket lifecycle.

## Hard rules

- **Always** use `bridge.sh` — do not reimplement the per-event logic in agent prompts.
- For non-created events, the skill **refuses** to create a new ticket. Do not override.
- Do not pass `--transit-ticket`. There is no transit ticket in v14.
- The `ticket.created` handler calls `ticket create` directly (NOT `ticket update`) — the agent owns the full ticket lifecycle.
- The mes-cli reply for `ticket.replied` and `ticket.created` uses `--internal --markdown` (not `--text`). `--text` wraps the body in literal `<p>...</p>` and breaks Markdown rendering on MES.
- Never use `curl` or raw HTTP for Mopheus operations. The `moclaw` CLI is the only allowed interface.
- Never invent or normalize MES field values. Preserve the raw payload verbatim.
- Every MES SR reference must hyperlink `https://support.enmotech.com/service/request/<id>`.
- If `bridge.sh` exits non-zero, surface the stderr to the user and stop. Do not retry the same payload blindly.

## Return contract

`bridge.sh` prints one line on success:

```
created ticket <id> (mes_sr_id=<n>, db_type=<t>, routed to <agent>, agent-wait=<w>, mes-cli=<s>)  # for ticket.created (<w>=completed/timeout; <s>=sent/send_failed/deferred/mes-cli-not-available)
patched ticket <id> (mes_sr_id=<n>, replyId=<id>, agent-wait=<w>, mes-cli=<s>, dba=<r>)         # for ticket.replied
closed ticket <id> (mes_sr_id=<n>, closed_by=<name>)                                             # for ticket.closed
duplicate <event> <key> for [MES SR#<id>] — skipped                                              # when idempotency hits
```

Errors go to stderr with a `error:` prefix and exit code ≥ 1.

## Changelog

- **v14.2 (2026-07-17)** — single-comment-per-event fixes:
  - `event_replied.sh`: merged customer reply body + DBA `@`-mention dispatch into ONE comment (was 2). The merged comment's ID serves as both the reply record and the agent run's `triggerCommentId`.
  - `event_closed.sh`: removed standalone closure-record comment. Closure details are still written to metadata (`mes_sr_status`, `mes_sr_closed_at`, `mes_sr_closed_by`, `mes_sr_closure_reason`, …); mes-leader's agent summary is the only visible record per closure event.
  - Net effect: each MES webhook event now produces at most one ticket comment authored by the bridge, on top of which the mes-leader agent posts its own summary per CLAUDE.md.
- **v14.1** — agent-owned ticket lifecycle (no transit-ticket placeholder; bridge creates / patches / closes via `ticket create` / `ticket update` / `ticket status done`).
- **v14.0** — initial v14 dispatcher (per-event handler split: `event_created.sh`, `event_replied.sh`, `event_closed.sh`, with shared `lib_common.sh`).
