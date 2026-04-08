---
name: axon-cli
description: >
  Manage AI editor skills, workflows, and commands across machines using the
  axon CLI hub-and-spoke skill manager. Use this skill whenever the user mentions
  axon, wants to sync/install/search/rollback skills, set up a new machine with
  their AI tool environment, or manages a ~/.axon/repo hub. Also triggers on
  requests like "sync my skills", "skill manager", "sync skills across machines",
  "vendor sync", "axon hub", "axon audit", "axon init", or "link my AI tools".
  Use it even if the user only mentions one axon command by name.
---

# axon-cli Skill

axon is a **hub-and-spoke skill manager**: it keeps a central Git repo at
`~/.axon/repo/` (the Hub) and symlinks AI tool directories (the Spokes) to
folders inside it — so every supported editor reads the same skills, workflows,
and commands.

## Quick Decision Tree

Before acting, identify which phase the user is in:

| Situation | Action |
|-----------|--------|
| axon is not installed, or first time on this machine | Read `references/setup.md` and follow the full setup flow |
| axon is installed, user wants to sync, search, rollback, audit, or manage skills | Read `references/daily-ops.md` for the relevant operation |
| Unsure whether axon is installed | Run `axon version` or `axon doctor` to check |

## Environment Preflight

Run these before any operation when the environment state is unknown:

```bash
axon doctor     # checks git availability, binary path, and hub health
axon version    # confirms axon version and build info
```

If `axon doctor` reports problems, resolve them before proceeding.

## Command Quick Reference

| Command | Purpose | Safety |
|---------|---------|--------|
| `axon doctor` | Environment preflight check | ✅ read-only |
| `axon version` | Show version/build info | ✅ read-only |
| `axon status` | Symlink health + hub git status | ✅ read-only |
| `axon status --fetch` | Also compare with remote | ✅ read-only |
| `axon status <skill>` | Skill-level commit history | ✅ read-only |
| `axon list` | List hub content by category | ✅ read-only |
| `axon search <query>` | Keyword or semantic search | ✅ read-only |
| `axon inspect <skill>` | Skill metadata and dependencies | ✅ read-only |
| `axon init [url]` | Bootstrap the hub | ⚠️ writes to disk |
| `axon link <name>` | Create symlink for one AI tool | ⚠️ writes to disk |
| `axon unlink <name>` | Remove symlink (restores backup) | ⚠️ writes to disk |
| `axon sync` | commit → pull → push | ⚠️ git write |
| `axon remote set <url>` | Set hub git remote origin | ⚠️ git write |
| `axon rollback <skill>` | Revert skill to previous commit | ⚠️ destructive |
| `axon rollback --all` | Revert entire hub | ⚠️ destructive |
| `axon audit [target]` | AI-powered security scan | ✅ read-only |
| `axon audit --fix` | Interactive secret redaction | ⚠️ destructive |
| `axon vendor sync` | Mirror external GitHub skills | ⚠️ writes to disk |
| `axon update` | Self-update axon binary | ⚠️ writes to disk |
| `axon search --index` | Build semantic search index | ⚠️ writes to disk |

## Safety Rules

Follow these rules on every operation:

1. **Never run `axon link` without a target name** unless the user explicitly
   says "link everything" or "link all tools". Always ask which tools to link
   after reading `axon status` output.

2. **Before any destructive command** (`rollback`, `unlink`, `audit --fix`),
   run `axon status` first and confirm the hub has no uncommitted changes.
   If the tree is dirty, run `axon sync` to commit first.

3. **Before `axon rollback`**, run `axon status <skill-name>` to show the user
   the commit history so they can pick the right target revision.

4. **After any rollback**, remind the user to run `axon sync` to propagate
   the revert commit to other machines.

5. **`axon sync` conflicts**: if pull/push fails due to diverged history,
   do not force-push. Guide the user through resolving the conflict manually
   inside `~/.axon/repo/`.
