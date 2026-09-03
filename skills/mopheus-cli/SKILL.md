---
name: mopheus-cli
description: Manage Mopheus workspaces, tickets, projects, agents, teams, skills, jobs, and triggers via mop / mopheus CLI and Python helper scripts. Use when querying large structured payloads, posting complex multiline comments/markdown, or managing event/schedule triggers.
---

# Mopheus CLI Skill (`mop` / `mopheus`)

This skill provides a standardized guide and pre-built Python helper scripts for interacting with Mopheus workspaces, tickets, jobs, triggers, agents, teams, and skills via the `mop` (or `mopheus`) CLI.

---

## 1. Quick Reference & Core Commands

| Domain | CLI Command | Purpose |
| :--- | :--- | :--- |
| **Workspace** | `mop workspace list`<br>`mop workspace switch <slug-or-id>`<br>`mop workspace get <id>` | View, inspect, and switch active workspace |
| **Tickets** | `mop ticket list --status open`<br>`mop ticket get <id-or-num>`<br>`mop ticket create --title "..."`<br>`mop ticket status <id> <status>`<br>`mop ticket comment create <id> --content-stdin` | View, create, update, and comment on tickets |
| **Projects** | `mop project list`<br>`mop project get <id>` | List and inspect workspace projects |
| **Agents & Tasks** | `mop agent list`<br>`mop agent-task get <id>`<br>`mop agent-task messages <id>`<br>`mop agent-task cancel <id>` | Inspect agents, dispatches, task transcripts, and cancel tasks |
| **Teams** | `mop team list`<br>`mop team get <id>` | List and inspect teams and team rosters |
| **Skills** | `mop skill list`<br>`mop skill get <id>`<br>`mop skill sync <id>` | Inspect and synchronize workspace skills |
| **Jobs & Triggers** | `mop job list`<br>`mop job get <id>`<br>`mop job runs <id> --limit 10`<br>`mop job trigger <id>`<br>`mop job trigger-add <id> --kind <schedule/event/webhook>` | Inspect jobs, view run history, manage triggers |
| **Event Schemas** | `mop job event-list`<br>`mop job event-schema [event-type]` | Inspect supported domain events, actions, and payload variables |
| **Memory** | `mop memory list`<br>`mop memory search "<query>"`<br>`mop memory get <id>` | Query, search, and inspect workspace memories |
| **Repo & Links** | `mop repo links --ticket <id>`<br>`mop repo issue sync --number <n> --ticket <id>`<br>`mop repo pr sync --number <n> --ticket <id>` | Manage GitHub/GitLab structured issue and PR links |
| **Runtimes & Daemon** | `mop runtime list`<br>`mop daemon status`<br>`mop daemon start / stop` | Inspect runtime nodes and local daemon service status |
| **Auth & Profiles** | `mop auth status`<br>`mop login`<br>`mop token list` | Inspect session, authenticate, and manage user API tokens |
| **Email** | `mop email config --host <host> --port 587 --user <user> --password <pass>`<br>`mop email send --to <email> --subject <title> --body <html>` | Configure SMTP and send outbound emails |

> **Tip**: All commands support `--output json` (or `-o json`) for clean machine-readable output.

---

## 2. Bundled References (Progressive Disclosure)

For detailed specifications, schema catalogs, and deep-dive domain references, consult the dedicated reference documents:

- **Event-Type Jobs & `event-filter` Reference**: Read [`references/event_jobs.md`](references/event_jobs.md)
  - Complete `event-filter` JSON schema and syntax (single object vs array OR matching)
  - Condition matching rules (scalars, slices, array tag containment, nested objects)
  - Supported domain events table (`ticket`, `comment`, `agent_task`, `runtime`), valid actions, condition keys, and enum references
  - Dynamic instruction template placeholders (`{{ticket.title}}`, `{{comment.content}}`, etc.)
  - CLI commands and real-world recipes (auto-triage, auto-responder, failure watchdog, runtime alert)

---

## 3. Python Helper Scripts (For Large Payloads & Structured Updates)

When dealing with **large Markdown files**, **multi-line comments**, **complex JSON event filters**, or **streaming agent task transcripts**, using inline shell strings can lead to character escaping or console buffer issues.

Use the pre-built helper scripts located in `scripts/`:

```
scripts/
├── mop_client.py   # Base JSON runner & binary locator
├── mop_ticket.py   # Ticket & comment manager (file/stdin support)
├── mop_job.py      # Job, trigger, and event schema manager
└── mop_task.py     # Agent task transcript reconstructor & diagnostic tool
```

### 3.1 Job & Event Trigger Management (`mop_job.py`)

```bash
# 1. Create an event job directly with JSON filter file
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_job.py create \
  --name "Security Ticket Responder" \
  --trigger-type event \
  --action-type assign_agent \
  --action-config '{"agentId":"<agent-uuid>"}' \
  --instruction "Handle security issue: {{ticket.title}}" \
  --filter-file path/to/security_filter.json

# 2. Add an event trigger with inline JSON
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_job.py add-trigger <job-id> \
  --kind event \
  --filter-json '[{"event":"comment","actions":["created"],"conditions":{"authorType":0}}]' \
  --label "Human Comments"

# 3. Update an existing trigger's event filter from a file
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_job.py update-trigger <job-id> <trigger-id> \
  --filter-file path/to/new_filter.json --enabled true

# 4. Inspect event schemas and sample payloads
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_job.py event-schema ticket
```

### 3.2 Agent Task & Transcript Analysis (`mop_task.py`)

```bash
# 1. View clean structured transcript (compact dialogue + tool executions)
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_task.py transcript <task-id>

# 2. Show only tool calls (Bash commands, etc.) and their results
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_task.py transcript <task-id> --tools-only

# 3. Filter transcript steps matching a keyword or error
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_task.py transcript <task-id> --grep "email send"
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_task.py transcript <task-id> --grep "error"

# 4. View specific step or limit count
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_task.py transcript <task-id> --limit 10
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_task.py transcript <task-id> --step 48
```

### 3.3 Ticket Operations (`mop_ticket.py`)

```bash
# 1. Fetch ticket details in JSON
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_ticket.py get <ticket-id-or-number>

# 2. Update ticket description safely from a Markdown file
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_ticket.py update-desc <ticket-id> path/to/description.md

# 3. Post a multiline comment from a file
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_ticket.py add-comment <ticket-id> --file path/to/comment.md

# 4. List comments on a ticket
python ~/.gemini/config/skills/mopheus-cli/scripts/mop_ticket.py comments <ticket-id>
```

---

## 4. Safety & Red Line Rules

> [!CAUTION]
> **CRITICAL**: The following safety red lines carry the highest execution priority across all operations. Never violate these constraints under any circumstances.

### Rule 1: Strict Workspace Resolution & Zero Guesswork
- **100% Verified Workspace Target**: When requested to perform operations within a specific workspace (by name, slug, or context), the target workspace **must be 100% unambiguously matched and confirmed** via `mop workspace list` (or `mopheus workspace list`).
- **Halt Immediately When Not Found**: If the specified workspace cannot be found in the current workspace list, **strictly NEVER** pick a default workspace, guess an approximate workspace, or proceed with assumed context. You must **halt immediately**, report the missing workspace, and ask the user for explicit clarification.
- **Halt Immediately on Multiple Matches or Ambiguity**: If fuzzy matching yields multiple candidate workspaces or if there is any ambiguity about the intended target, **strictly NEVER** guess or unilaterally pick one. You must **halt immediately**, present the matching candidates, and ask the user to explicitly select the correct workspace.

---

## 5. Best Practices & Engineering Guidelines

### 5.1 Handling Long Inputs & Markdown Across All Commands
Passing long multi-line Markdown, system prompts, JSON filters, or instructions via inline command arguments (e.g. `--description "..."` or `--content "..."`) inevitably leads to shell quote escaping errors, newline mangling, or command-line length limit violations.

Mopheus CLI provides standardized `--*-file` and `--*-stdin` flags across all resource commands. Always use these flags (or the bundled Python helper scripts) for any text longer than a single sentence:

| Resource Domain | Target Field | Recommended File / Stdin Flags | Example Usage |
| :--- | :--- | :--- | :--- |
| **`ticket`** | Description | `--description-file <file>`<br>`--description-stdin` | `mop ticket create --title "..." --description-file spec.md`<br>`cat desc.md \| mop ticket update <id> --description-stdin` |
| **`ticket`** | Comment Content | `--content-file <file>`<br>`--content-stdin` | `mop ticket comment add <id> --content-file comment.md`<br>`cat report.md \| mop ticket comment add <id> --content-stdin` |
| **`agent`** | System Instructions | `--instructions-file <file>`<br>`--instructions-stdin` | `mop agent create --name "Dev" --instructions-file prompt.md`<br>`mop agent update <id> --instructions-file prompt.md` |
| **`agent`** | Description | `--description-file <file>`<br>`--description-stdin` | `mop agent create --name "Dev" --description-file desc.md` |
| **`agent`** | Environment Config | `--env-file <file.json>`<br>`--env-stdin` | `mop agent env set <id> --env-file env.json` |
| **`team`** | Leader Instructions | `--instructions-file <file>`<br>`--instructions-stdin` | `mop team create --name "QA" --leader <agent> --instructions-file team_prompt.md`<br>`mop team update <id> --instructions-file team_prompt.md` |
| **`team`** | Description | `--description-file <file>`<br>`--description-stdin` | `mop team create --name "QA" --description-file team_desc.md` |
| **`skill`** | Entire Skill Directory | `import --path <dir>`<br>`export --output-dir <dir>` | `mop skill import --path ./my-skill/ --update`<br>`mop skill export --all --output-dir ./exported-skills/` |
| **`skill`** | Skill File Content | `files upsert --content-stdin` | `cat prompt.md \| mop skill files upsert <id> --path SKILL.md --content-stdin` |
| **`job`** | Event Filter | `--event-filter-file <file.json>`<br>`--event-filter-stdin` | `mop job create --trigger-type event --event-filter-file filter.json ...`<br>`mop job trigger-add <id> --kind event --event-filter-file filter.json` |
| **`memory`** | Memory Body | `--content-file <file>`<br>`--content-stdin` | `mop memory store --type error_resolution --content-file memory.md`<br>`cat fix.md \| mop memory store --type error_resolution --content-stdin` |

### 5.2 Handling Long Outputs & Pagination
1. **JSON Output (`--output json`)**: Use `--output json` (or `-o json`) for machine-readable parsing with `jq` or Python scripts.
2. **Streaming Agent Transcripts**: Use `scripts/mop_task.py transcript <task-id>` to reconstruct long, multi-fragment token streams into clear dialogue and tool steps without terminal truncation.
3. **Pagination Navigation**: Use `--page <n>` and `--limit <n>` (or `--per-page <n>`) to traverse large datasets in `ticket list`, `skill list`, `memory list`, `job runs`, and `user list`.

### 5.3 General Engineering Practices
1. **Workspace Routing**:
   - When running CLI inside a repository, the active workspace should match the current repository name or project slug.
   - Run `mop workspace list` to inspect active status.
2. **Zero Hardcoded Schema**:
   - Always query `mop job event-schema` or read [`references/event_jobs.md`](references/event_jobs.md) to discover supported events (`ticket`, `comment`, `agent_task`, `runtime`), valid actions, and payload fields.
3. **Error Handling**:
   - If a command fails with `HTTP 401: INVALID_TOKEN` or `AUTH_REQUIRED`, run `mop login` or verify `~/.mopheus/config.json`.
