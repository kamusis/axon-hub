---
name: mop
description: Manage Mopheus workspaces, tickets, projects, agents, teams, skills, jobs, and triggers via mop CLI. Supports slash command /mop with interactive wizard, natural language intent translation, and Claude Code aliases.
---

# Mopheus CLI Skill (`mop` / `mopheus`)

Standardized guide for querying and managing Mopheus workspaces, tickets, agents, teams, skills, jobs, and event triggers via the `mop` (or `mopheus`) CLI.

## 1. Safety Invariants (Zero Guesswork)

> [!CAUTION]
> **Workspace Verification Gate**:
> - **100% Verified Workspace Target**: When requested to perform operations in a specific workspace, verify the target workspace first with `mop workspace list` (or `mopheus workspace list`).
> - **Halt on Missing Workspace**: If the workspace cannot be found, **NEVER** guess or pick a default workspace. Halt immediately, report the missing workspace, and ask for clarification.
> - **Halt on Ambiguity**: If multiple workspaces match, **NEVER** choose unilaterally. Halt immediately, list the candidates, and request selection.
> - **Repository Association**: When inside a git repository, match the workspace or project to the repository name/slug before mutating state.

## 2. Interaction Modes & Slash Command Mappings

`mop` supports two complementary interaction patterns across different AI agent hosts:

### Mode A: Intent Routing & Wizard Flow (Universal `/mop` in Codex & Claude)

#### Language Matching Rule:
- Default to **English** for guidance, responses, and interactive menus.
- **Language Adaptation**: If the user communicates in Chinese or the conversation context is in Chinese, seamlessly translate the interactive guidance and summaries into Chinese.
- Regardless of conversation language, all CLI command syntax, flags, identifiers, and code blocks MUST remain verbatim English.

When the user invokes `/mop` without exact CLI syntax:
- **Bare Invocation (`/mop`)**: Immediately output the compact quick-guide below without extra tool calls, then prompt the user (adapt language per rule above):
  ```text
  ### 🎯 Mopheus CLI (`mop`) Ready
  Tell me what you would like to do, or use one of the common actions below:
  1. 🎫 Tickets: `mop ticket list --status open` / `mop ticket get <id>` / `mop ticket assign <id>`
  2. 🤖 Agents & Teams: `mop agent list` / `mop agent get <id>` / `mop agent skills list <id>`
  3. 🔍 Search: `mop search "<query>"` (Full-text search across tickets, agents, skills)
  4. 🏢 Workspace: `mop workspace list` / `mop workspace switch <slug>`
  5. ⚡ Jobs & Shortcuts: `mop job list` / `mop shortcut list` / `mop shortcut run <name> -t <id>`
  6. 🩺 Diagnostics: `mop agent-task get <id>` / `python <skill-dir>/scripts/mop_task.py transcript <id>`
  ```
- **Natural Language Intent (e.g. `/mop check urgent tickets` or `/mop 帮我查紧急工单`)**: Translate the user's intent to the appropriate `mop` command (e.g. `mop ticket list --priority urgent -o json`), execute it, and present clean formatted results. The user does not need to memorize CLI subcommands.
- **Direct CLI Invocation (`/mop ticket list --status open`)**: Directly execute the command.

### Mode B: Claude Code Slash Command Aliases (`/mop:ticket`, `/mop:agent`, etc.)
In Claude Code (or clients supporting custom slash command files), pre-packaged command aliases are provided in `adapters/claude-code/commands/mop/`:
- `/mop:ticket`: Direct ticket inspection, assignment, comments, and rerun.
- `/mop:agent`: Inspect agents, view system prompts, bind skills, and view task runs.
- `/mop:search`: Workspace-wide search across tickets, agents, skills, and projects.
- `/mop:workspace`: Workspace listing and switching.
- `/mop:job`: Scheduled jobs and event trigger configurations.
- `/mop:task`: Agent task transcript and tool step debugging.

Run `python <skill-dir>/scripts/install_claude_commands.py` to link them into `~/.claude/commands/`.

## 3. Quick Reference & Core Commands

Always prefer `--output json` (or `-o json`) when parsing programmatically.

| Domain | CLI Command | Purpose |
| :--- | :--- | :--- |
| **Workspace & Search** | `mop workspace list`<br>`mop workspace switch <slug-or-id>`<br>`mop workspace get <id>`<br>`mop search "<query>" [--type ticket,agent,skill]` | Inspect and switch workspace; workspace-wide full-text search across all resources |
| **Tickets** | `mop ticket list [--status open] [--priority urgent]`<br>`mop ticket get <id-or-num>`<br>`mop ticket create --title "..." --description-file <file>`<br>`mop ticket update <id> [--priority <p>] [--tags <t>]`<br>`mop ticket status <id> <status>`<br>`mop ticket assign <id> --assignee <user-or-agent-id>`<br>`mop ticket comment add <id> --content-file <file>`<br>`mop ticket rerun <id>`<br>`mop ticket grill <id>`<br>`mop ticket transcript <id> [--out <dir>]` | Query, create, update, assign, and comment on tickets; trigger task re-runs, reviews, and transcript export |
| **Agents** | `mop agent list`<br>`mop agent get <id-or-name>`<br>`mop agent create --name "..." --role "..." --instructions-file <file>`<br>`mop agent update <id> [--instructions-file <file>] [--model <m>]`<br>`mop agent skills list <id>`<br>`mop agent skills add <id> --skill <skill-id>`<br>`mop agent skills remove <id> --skill <skill-id>`<br>`mop agent tasks <id>`<br>`mop agent env list/set/unset <id>` | Inspect workspace agents, view system prompts, configure models, manage skill bindings, inspect tasks, and manage env vars |
| **Teams** | `mop team list`<br>`mop team get <id>`<br>`mop team update <id> --instructions-file <file>`<br>`mop team member add/remove <id> --member <id>` | List and inspect teams, update team leader instructions, and manage team members |
| **Shortcuts & Tasks** | `mop shortcut list`<br>`mop shortcut run <shortcut-name> -t <ticket-id>`<br>`mop agent-task get <id>`<br>`mop agent-task messages <id>`<br>`mop agent-task cancel <id>`<br>`mop chat history`<br>`mop chat message <session-id>` | List and run skill shortcuts on tickets; inspect agent task runs, transcripts, and chat channel history |
| **Skills** | `mop skill list`<br>`mop skill get <id>`<br>`mop skill import --path <dir> --update`<br>`mop skill export --all --output-dir <dir>` | Inspect, import local SKILL.md folders, and export workspace skills |
| **Jobs & Triggers** | `mop job list`<br>`mop job get <id>`<br>`mop job runs <id> --limit 10`<br>`mop job trigger <id>`<br>`mop job trigger-add <id> --kind <schedule/event/webhook>`<br>`mop job event-list`<br>`mop job event-schema [event-type]` | Inspect jobs, view run history, manage triggers and condition filters, inspect domain events |
| **Projects & Repos** | `mop project list`<br>`mop project get <id>`<br>`mop repo links --ticket <id>`<br>`mop repo issue sync --number <n> --ticket <id>`<br>`mop repo pr sync --number <n> --ticket <id>` | List and inspect projects; manage GitHub/GitLab structured issue and PR links |
| **Memory** | `mop memory list`<br>`mop memory search "<query>"`<br>`mop memory store --type <type> --content-file <file>` | Query, search, and store workspace memories |
| **Runtimes & Daemon** | `mop runtime list`<br>`mop daemon status`<br>`mop daemon start / stop` | Inspect runtime nodes and local daemon status |
| **Auth & Profiles** | `mop auth status`<br>`mop login`<br>`mop token list` | Inspect session, authenticate, and manage user API tokens |

## 4. Handling Long Inputs & Markdown (Native First)

Avoid passing long multi-line strings, Markdown specs, or JSON filters directly via command line arguments (`--description "..."`). Shell quotes frequently corrupt formatting and newlines.

Always use native `--*-file` or `--*-stdin` flags:

| Resource Domain | Target Field | Recommended Native Flags | Example Usage |
| :--- | :--- | :--- | :--- |
| **`ticket`** | Description | `--description-file <file>`<br>`--description-stdin` | `mop ticket create --title "..." --description-file spec.md` |
| **`ticket`** | Comment | `--content-file <file>`<br>`--content-stdin` | `mop ticket comment add <id> --content-file comment.md` |
| **`agent`** | Instructions / Prompt | `--instructions-file <file>`<br>`--instructions-stdin` | `mop agent create --name "Dev" --instructions-file prompt.md` |
| **`team`** | Leader Instructions | `--instructions-file <file>`<br>`--instructions-stdin` | `mop team update <id> --instructions-file prompt.md` |
| **`job`** | Event Filter | `--event-filter-file <file.json>`<br>`--event-filter-stdin` | `mop job trigger-add <id> --kind event --event-filter-file filter.json` |
| **`memory`** | Memory Body | `--content-file <file>`<br>`--content-stdin` | `mop memory store --type <type> --content-file note.md` |
| **`skill`** | Entire Directory | `import --path <dir>` | `mop skill import --path ./my-skill/ --update` |

## 5. Capability Gating & Automatic Version Detection

External environments (non-Mopheus daemon on Windows/Linux) run diverse `mop` / `mopheus` binary versions.

Before invoking advanced or version-sensitive commands (or when a command fails with an unrecognized flag or subcommand), use `scripts/check_version.py` to check capability readiness:

```bash
# Check single capability readiness (returns exit code 0 if supported, 1 if missing)
python <skill-dir>/scripts/check_version.py --check <capability_id>

# Run full capability diagnostic report
python <skill-dir>/scripts/check_version.py
```

### Automatic Interception & Degradation Rule:
When a capability check indicates the user's CLI version is insufficient or missing:
1. **Do not fail silently or retry blindly.**
2. **Proactively notify the user** using the warning output from `check_version.py` (which specifies the installed version, required version, missing feature description, and `mop upgrade` command).
3. **Execute the documented fallback** immediately so the user's task makes progress.
4. **Daemon Separation**: If an action requires `daemon.local_management`, notify the user that current execution is in non-daemon pure client mode and provide the remote API alternative.

## 6. Helper Utilities (`scripts/`)

For specialized tasks that exceed basic CLI ergonomics, use the bundled scripts:

- **Capability Matrix Detector (`check_version.py`)**:
  Probes installed CLI version, tests capability support, and provides formatted warning alerts and fallback actions.
- **Agent Task Transcript Reconstruction (`mop_task.py`)**:
  Reconstructs streaming, fragmented agent task transcripts into structured dialogue and tool steps without terminal truncation:
  ```bash
  # View clean compact transcript
  python <skill-dir>/scripts/mop_task.py transcript <task-id>
  
  # Filter tool calls only (e.g. Bash executions)
  python <skill-dir>/scripts/mop_task.py transcript <task-id> --tools-only
  
  # Grep for specific errors or keywords
  python <skill-dir>/scripts/mop_task.py transcript <task-id> --grep "error"
  ```

- **Complex Job & Event Filter Assembly (`mop_job.py`)**:
  Facilitates validating and creating multi-branch event triggers from JSON files:
  ```bash
  python <skill-dir>/scripts/mop_job.py add-trigger <job-id> \
    --kind event \
    --filter-file path/to/event_filter.json \
    --label "Production Incident Filter"
  ```

## 7. Progressive References

- **Comprehensive Command Reference**: Read [`references/commands_reference.md`](references/commands_reference.md) for full subcommands, flags, and workflow examples across all Mopheus domains.
- **Capability Matrix & Version Mapping**: Read [`references/capabilities.json`](references/capabilities.json) for the complete list of capabilities, minimum CLI versions, daemon requirements, and fallbacks.
- **Event-Type Jobs & JSON Filters**: Read [`references/event_jobs.md`](references/event_jobs.md) for full JSON schema, matching semantics (scalars, OR arrays, tag containment), domain event types (`ticket`, `comment`, `agent_task`, `runtime`), and template variables.
