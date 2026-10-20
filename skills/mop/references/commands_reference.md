# Mopheus CLI Comprehensive Command Reference

Complete guide for managing Mopheus resources via `mop` (or `mopheus`) CLI.

---

## 1. Workspace & Search

### `mop workspace`
Manage workspace context and multi-tenancy.
- `mop workspace list` - List accessible workspaces with slug, ID, and active marker `*`.
- `mop workspace switch <slug-or-id>` - Switch current active workspace.
- `mop workspace get <id>` - Inspect detailed workspace settings and metadata.

### `mop search`
Global full-text search across all workspace entities.
- `mop search "<query>"` - Search across tickets, agents, skills, and projects.
- `mop search "<query>" --type ticket` - Restrict search to tickets.
- `mop search "<query>" --type agent` - Restrict search to agents.
- `mop search "<query>" --type skill` - Restrict search to skills.
- `mop search "<query>" --limit 50` - Control result limit (1-100, default 20).

### `mop feature`
Inspect workspace feature flags.
- `mop feature list` - List effective feature flags for the active workspace.
- `mop feature check <feature-key>` - Check if a feature flag is enabled (exits with 0 if enabled, 1 if disabled).

---

## 2. Tickets & Workflows (`mop ticket`)

### Querying & Viewing
- `mop ticket list` - List open tickets in active workspace.
- `mop ticket list --status open --priority urgent` - Filter by status and priority.
- `mop ticket list --assignee <id> --page 1 --per-page 20` - Filter by assignee with pagination.
- `mop ticket get <id-or-num>` - Get full ticket details by UUID or ticket sequence number.

### Creation & Updates (Native File First)
- `mop ticket create --title "Title" --description-file spec.md` - Create ticket using Markdown file.
- `mop ticket create --title "Title" --label "backend" --label "p0" --priority urgent` - Create ticket with labels and priority.
- `mop ticket update <id> --priority urgent --label "backend" --label "p0"` - Update priority and labels (alias: `--labels "backend,p0"`).
- `mop ticket update <id> --due-date "2026-12-31T00:00:00Z" --activate-at "2026-10-01T00:00:00Z"` - Set scheduled activation or due date.
- `mop ticket update <id> --status done --cascade-subtickets` - Close ticket and cascade status to open subtickets.
- `mop ticket status <id> <open|in_progress|resolved|closed>` - Transition ticket status.
- `mop ticket assign <id> --assignee <user-or-agent-id>` - Assign ticket to a member or agent.

### Comments & Collaboration
- `mop ticket comment list <id>` - List all comments on a ticket.
- `mop ticket comment add <id> --content-file note.md` - Post comment from Markdown file.
- `mop ticket comment add <id> --content-stdin` - Post multiline comment via stdin (supports interactive ` ```widget ` blocks if `widget` feature is enabled; see `references/ticket_widgets.md`).

### Execution Lifecycle & Diagnostics
- `mop ticket rerun <id>` - Re-enqueue agent task execution on a ticket.
- `mop ticket grill <id>` - Trigger self-Q&A review on a ticket.
- `mop ticket runs <id>` - List all agent task runs for a ticket.
- `mop ticket run-messages <ticket-id> --run <run-id>` - List messages for a specific run.
- `mop ticket transcript <id> --out ./transcripts/` - Export complete task execution transcript.

---

## 3. Agents & Teams

### `mop agent`
Manage AI agents and configurations.
- `mop agent list` - List all agents with role, model, and provider.
- `mop agent get <id-or-name>` - Inspect agent system instructions, prompt, and parameters.
- `mop agent create --name "Dev" --role "Developer" --instructions-file prompt.md` - Create agent.
- `mop agent update <id> --instructions-file prompt.md --model gpt-4o` - Update instructions/model.
- `mop agent skills list <agent-id>` - List skills assigned to agent.
- `mop agent skills add <agent-id> --skill <skill-id>` - Bind skill to agent.
- `mop agent skills remove <agent-id> --skill <skill-id>` - Unbind skill from agent.
- `mop agent tasks <agent-id>` - List recent tasks dispatched to this agent.
- `mop agent env list <agent-id>` / `set` / `unset` - Manage agent-scoped environment variables.

### `mop team`
Manage multi-agent team hierarchies.
- `mop team list` - List workspace teams.
- `mop team get <id>` - View team roster and leader configuration.
- `mop team update <id> --instructions-file leader_prompt.md` - Update leader instructions.
- `mop team member add <id> --member <agent-id>` - Add agent to team.
- `mop team member remove <id> --member <agent-id>` - Remove agent from team.

---

## 4. Tasks, Shortcuts & Chat

### `mop agent-task`
Direct execution monitoring and troubleshooting.
- `mop agent-task get <task-id>` - Inspect status, runtime duration, and error messages.
- `mop agent-task messages <task-id>` - Stream recent task dialogue messages.
- `mop agent-task cancel <task-id>` - Terminate a running or queued task run.
- `python <skill-dir>/scripts/mop_task.py transcript <task-id>` - Reconstruct formatted transcript.
- `python <skill-dir>/scripts/mop_task.py transcript <task-id> --tools-only` - Filter tool executions.

### `mop shortcut`
Execute skills with shortcut capability on tickets.
- `mop shortcut list` - List available shortcuts.
- `mop shortcut run <shortcut-name> -t <ticket-id>` - Run shortcut on specified ticket.

### `mop chat`
Inspect channel and chat context.
- `mop chat list` - List chat sessions in active workspace.
- `mop chat message <session-id>` - List messages in a chat session (includes attachments).
- `mop chat send <session-id> -m "..."` - Send a message to a chat session.
- `mop chat channel list` - List external channel integrations and user bindings.
- `mop chat history` - Read recent messages from bound channel.
- `mop chat thread <thread-id>` - Read a specific channel thread.
- `mop chat send-channel -m "..."` - Send an agent message directly to external channel.

---

## 5. Skills, Jobs & Triggers

### `mop skill`
Workspace skill management.
- `mop skill list` - List installed skills.
- `mop skill get <id>` - Inspect skill YAML frontmatter and body.
- `mop skill import --path <dir> --update` - Import local SKILL.md folder into workspace.
- `mop skill export --all --output-dir <dir>` - Export workspace skills to local directory.

### `mop job`
Automation jobs, schedules, and event-driven triggers.
- `mop job list` - List jobs and their trigger types.
- `mop job get <id>` - Inspect job details.
- `mop job runs <id> --limit 10` - View execution history.
- `mop job trigger <id>` - Manually fire a job run.
- `mop job trigger-add <id> --kind schedule --cron "0 9 * * *"` - Add 5-field cron schedule.
- `mop job trigger-add <id> --kind schedule --cron-dialect quartz --cron "0 0 9 ? * 2-6 *" --timezone "Asia/Shanghai"` - Add 7-field Quartz schedule (weekdays at 09:00).
- `mop job trigger-add <id> --kind event --event-filter-file filter.json` - Add event trigger (v2.2.5+).
- `mop job event-list` - List supported domain event types.
- `mop job event-schema [type]` - Inspect event payload schema and condition variables.

---

## 6. Projects, Repos & Knowledge Base

### `mop project`
- `mop project list` - List projects in workspace.
- `mop project get <id>` - Inspect project details.

### `mop repo`
- `mop repo list` - List registered git repositories.
- `mop repo add <url>` - Register a git repository in the workspace.
- `mop repo checkout <repo-name> [--branch <branch>]` - Create a worktree checkout from a registered repository.
- `mop repo worktree list` - List active local git worktrees.
- `mop repo links --ticket <id>` - List linked GitHub/GitLab PRs and issues.
- `mop repo issue sync --number <n> --ticket <id>` - Associate issue with ticket.
- `mop repo pr sync --number <n> --ticket <id>` - Associate pull request with ticket.

### `mop memory`
- `mop memory list [--per-page <n>]` - List stored memories.
- `mop memory retrieve "<query>"` - Semantic vector / full-text search across memories.
- `mop memory get <memory-id>` - Inspect specific memory details.
- `mop memory store --type <type> --content-file note.md` - Store new memory item.


---

## 7. Runtimes, Daemon & Authentication

### `mop runtime` & `daemon`
- `mop runtime list` - List connected daemon runtimes and worker status.
- `mop daemon status` - Check local daemon status (requires daemon node).
- `mop daemon start / stop` - Manage background service (requires daemon node).
- `mop daemon restart` - Restart running daemon process.
- `mop daemon logs` - Tail daemon system and task logs.
- `mop daemon disk-usage` - Show disk usage of workspace agent task directories.
- `mop daemon install` - Install systemd service for local daemon.

### `mop auth` & `token`
- `mop auth status` - Inspect current authenticated user and session validity.
- `mop login` - Interactive login.
- `mop token list` - List user API access tokens (`moc_...`).

### `mop profile`
Local configuration profile discovery and inspection.
- `mop profile list` (alias: `ls`) - List configured local profiles (`default` and named profiles in `~/.mopheus/profiles/`).
- `mop profile show [name]` (alias: `get`) - Show detailed configuration for default or named profile.
- Both commands support `-o json` for structured JSON output.

---

## 8. IT Assets & Topology Knowledge Graph (`mop asset`)

Manage IT asset ontology, declarative manifests, graph traversal, and topology diagrams.

### Querying & Inspection
- `mop asset list [--concept <name>] [--app <app>] [--env <env>]` - List workspace assets with concept/app/env filters.
- `mop asset inspect <id>` - Inspect asset details, attributes, labels, and incident relations.
- `mop asset resolve <query>` - Resolve an asset by UUID, exact name, or alias.
- `mop asset topology <id> [-d <depth>] [--direction <downstream|upstream|both>]` - Explore subgraph neighborhood around an asset.
- `mop asset path --from <source-id> --to <target-id>` - Discover shortest causal path between two assets.
- `mop asset concept list` - List ontology concept metamodels and validation rules.
- `mop asset concept get <name>` - Inspect concept metamodel definition.

### Declarative Manifest & Mutation
- `mop asset apply -f <manifest.yaml>` - Ingest declarative asset manifest (YAML/JSON, use `-` for stdin).
- `mop asset export [-f <file.yaml>]` - Export workspace assets and relations as declarative manifest.
- `mop asset delete <id>` - Delete an asset and its incident relations.
- `mop asset unlink --from <id> --to <id> --relation <type>` - Remove a specific relation between assets.

### Architecture Diagram Projection
- `mop asset diagram --app <app> [-f <out.json>]` - Project workspace assets into architecture diagram spec.
- `mop asset diagram -i <manifest.yaml> [-f <out.json>]` - Offline diagram projection from local manifest without server query.
- Supports `--locale en|zh-Hans|ja`, `--title "..."`, and `--concept <name>`.

---

## 9. SSH Assets & Remote Bastion Execution (`mop ssh`)

Execute commands and transfer files across remote hosts via JumpServer/bastion integration.

### Asset Discovery & Execution
- `mop ssh list` - List authorized SSH assets with hostnames, IP addresses, protocols, and ports.
- `mop ssh config` - Inspect active SSH source provider configuration.
- `mop ssh exec <host> -- <command...>` - Execute command on remote host.
- `mop ssh exec <host> --user root -- env KEY=VALUE <command>` - Execute as specific user with remote environment.
- `mop ssh exec <host> --script ./deploy.sh -- arg1 arg2` - Execute a local shell script remotely.
- `mop ssh upload <host> --src ./app.tar.gz --dst /opt/app/ [--user root]` - Upload a local file to remote host.
- Supports `--loglevel debug|info|warn|error` and `--logfile <path>`.

---

## 10. Channel Integrations & Chat Routing (`mop channel`)

Manage external collaboration channels (Lark, DingTalk, WeChat Work) and outbound agent dispatch.

- `mop channel list` - List registered channel installations and status.
- `mop channel bindings <installation-id>` - List Mopheus users bound to a channel installation.
- `mop channel chat <installation-id>` - List active chat sessions for an installation.
- `mop channel send --channel <channel> --session <id> -m "..."` - Dispatch an agent message through a channel session.

---

## 11. Personal Runtime Configuration Files (`mop user config-file`)

Manage sensitive credentials and runtime configuration templates for agent tasks.

- `mop user config-file list` - List stored runtime configuration files.
- `mop user config-file templates` - List supported server templates (e.g. `auth`, `kubeconfig`, `maven-settings`).
- `mop user config-file upload <template-name> <file-path>` - Create configuration file from server template.
- `mop user config-file update <id> --file <file-path>` - Update existing configuration file contents.
- `mop user config-file get <id>` - Inspect configuration file metadata.
- `mop user config-file delete <id>` - Remove personal configuration file.
- `mop user config-file render <group>` - Render template group locally into target directories.
- `mop user config-file generate-ssh-key` - Generate and store an SSH key pair.

### User Environment & Shortcuts
- `mop user env list` / `mop user env set <KEY=VALUE>` / `mop user env delete <KEY>` - Manage personal environment variables.
- `mop user shortcut list` / `create` / `get` / `update` / `delete` - Manage personal user shortcuts.
- `mop user profile get` / `update` - Inspect and update personal account profile.

---

## 12. Workspace Entity Labels (`mop label`)

Categorize tickets, assets, and workspace resources with colored tags.

- `mop label list` - List all workspace labels with IDs, names, and hex colors.
- `mop label get <id>` - Inspect label details.
- `mop label create --name "P0-Blocker" [--color "#ef4444"]` - Create a new label.
- `mop label update <id> [--name "New Name"] [--color "#3b82f6"]` - Update label attributes.
- `mop label delete <id>` - Remove a label from the workspace.

---

## 13. Personal Notifications & Inbox (`mop inbox`)

Review and triage personal notifications and task updates.

- `mop inbox list [--unread]` - List inbox notifications.
- `mop inbox get <id>` - Get detailed notification payload.
- `mop inbox read <id>` - Mark a single notification as read.
- `mop inbox read-all` - Mark all workspace notifications as read.
- `mop inbox archive <id>` - Move notification to archive.
- `mop inbox archive-all` - Archive all notifications in the workspace.
- `mop inbox unarchive <id>` / `unarchive-all` - Restore archived notifications.
- `mop inbox delete <id>` / `delete-all` - Permanently remove notifications.

---

## 14. Workspace SMTP Email Dispatch (`mop email`)

Configure workspace SMTP server and dispatch outgoing emails.

- `mop email config --host smtp.example.com --port 587 --username user --password pass --from notify@example.com` - Set SMTP config.
- `mop email send --to "dev@example.com" --subject "Build Finished" --body "All tests passed."` - Send plaintext email.
- `mop email send --to "dev@example.com" --subject "Report" --body-file ./report.html --html` - Send HTML formatted email.

---

## 15. Agent Providers & Model Aliases (`mop provider`)

Inspect and register LLM providers and CLI runner binaries.

- `mop provider list` - List registered providers, CLI command names, and availability status.
- `mop provider register <alias> <type> [--cmd-name <bin>]` - Register provider alias (e.g. `mop provider register my-hermes acp --cmd-name hermes`).
- `mop provider remove <alias>` - Remove provider alias registration.

---

## 16. File Attachments (`mop attachment`)

Direct inspection, upload, and download of workspace attachments.

- `mop attachment list [--ticket <id>] [--session <id>]` - List attachments filtered by ticket or chat session.
- `mop attachment get <id>` - Inspect attachment file metadata, MIME type, and size.
- `mop attachment download <id> -o ./downloaded_file.png` - Download attachment file to local disk.
- `mop attachment delete <id>` - Delete an attachment.
- `mop attachment chat-upload <path>` - Upload file attachment within agent task context.

---

## 17. Knowledge Graph Operations (`mop graph`)

- `mop graph rebuild` - Rebuild the entity-relationship knowledge graph from all enabled memories.

---

## 18. CLI Self-Upgrade (`mop upgrade`)

Download and install the latest `mopheus` / `mop` binary directly from the release distribution server.

- `mop upgrade` - Upgrade to the latest stable release.
- `mop upgrade --dev` - Upgrade to the latest development/beta build.
- `mop upgrade --version v2.2.8` - Install a specific target version.
- `mop upgrade --force` - Reinstall even if already on the target version.

