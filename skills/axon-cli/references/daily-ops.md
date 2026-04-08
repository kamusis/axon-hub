# axon Daily Operations Reference

Use this guide for any operation after axon is installed and the hub is
initialized. Covers four areas: sync, discovery, rollback, and advanced ops.

---

## 1. Sync & Status

### Check hub health

```bash
axon status
```

Shows symlink health for all configured targets and the hub's local git status.
Run this before any write operation to confirm the working tree is clean.

```bash
axon status --fetch
```

Also fetches `origin` and reports whether the local hub is ahead or behind the
remote. If the remote is newer, run `axon sync`.

```bash
axon status <skill-name>
```

Skill-level inspection: shows the skill's resolved path, whether it is linked,
and its recent commit history. Use this before `axon rollback` to browse commits.

### Sync the hub

```bash
axon sync
```

In `read-write` mode (default): `git add` → `git commit` → `git pull --rebase`
→ `git push`.

In `read-only` mode: `git pull --ff-only` only.

**If `axon sync` fails:**
- Pull conflict → do not force-push. Resolve diverged history manually inside
  `~/.axon/repo/`, then re-run `axon sync`.
- Push rejected → check that `origin` points to a repo you own. Use
  `axon remote set <url>` to correct it.

### Change the remote

```bash
axon remote set git@github.com:yourname/axon-hub.git
```

After setting, run `axon status --fetch` to verify the new remote is detected.

**After changing the remote, also update `sync_mode` in `~/.axon/axon.yaml`
to match your access level:**

| Situation | Set `sync_mode` to |
|-----------|-------------------|
| Remote is a repo **you own** (can push) | `read-write` |
| Remote is a **public/shared hub** you don't own (e.g. `kamusis/axon-hub`) | `read-only` |

```yaml
sync_mode: read-write   # or read-only
```

- **`read-write`**: `axon sync` will commit, pull, and push. Use when you own the remote.
- **`read-only`**: `axon sync` will only `git pull --ff-only`. Use when pointing to
  someone else's hub to pull their latest skills without pushing your changes.

Without updating this field, `axon sync` may try to push to a repo you don't
have write access to (or fail to push to your own).

---

## 2. Discovery & Search

### List hub content

```bash
axon list
```

Lists all items in the hub grouped by category (skills, workflows, commands,
rules). Useful for a quick inventory.

### Search skills

```bash
# Semantic search (preferred — falls back to keyword if index unavailable)
axon search "database performance tuning"

# Force keyword-only search
axon search --keyword "git release"

# Force semantic search (errors if index is not built)
axon search --semantic "postgres index"

# Limit results
axon search --k 10 "authentication"
```

**To enable semantic search**, build the index first (requires embeddings
config in `~/.axon/.env`):

```bash
# ~/.axon/.env
AXON_EMBEDDINGS_PROVIDER=openai
AXON_EMBEDDINGS_MODEL=text-embedding-3-small
AXON_EMBEDDINGS_API_KEY=YOUR_API_KEY_HERE
```

```bash
axon search --index           # build or update the index
axon search --index --force   # force full rebuild
```

The embeddings model must match the model used to build the index. If the
model changes, rebuild the index.

### Inspect a skill

```bash
axon inspect humanizer          # exact name
axon inspect git                # fuzzy match — shows all matches
axon inspect windsurf-skills    # by target name
```

Shows the skill's name, version, description, trigger phrases, allowed tools,
bundled scripts, and declared dependencies with live availability check.

---

## 3. Rollback & Recovery

Always follow this sequence — never skip the status check:

**Step 1: Check hub is clean**
```bash
axon status
```
If the working tree is dirty, commit first:
```bash
axon sync
```

**Step 2: Browse the skill's commit history**
```bash
axon status <skill-name>
```
Note the SHA of the commit you want to target.

**Step 3: Roll back**
```bash
# Revert one skill to the previous commit
axon rollback <skill-name>

# Revert one skill to a specific commit
axon rollback <skill-name> --revision <sha>

# Revert the entire hub one commit back
axon rollback --all

# Revert the entire hub to a specific commit
axon rollback --all --revision <sha>
```

`axon rollback` creates a new forward commit (never rewrites history), so
`axon sync` can safely propagate it to all machines.

**Running rollback twice on the same target cancels it out.** To go back
multiple steps, use `--revision <sha>` to target a specific commit directly.

**Step 4: Propagate**
```bash
axon sync
```

Remind the user to run this after every rollback so other machines receive
the revert commit.

---

## 4. Advanced Operations

### Vendor sync (mirror external skills)

Import skills from an external GitHub repository into the hub.

**When the user asks to add a vendor URL, first check if they provided a GitHub
tree URL — all fields can be auto-derived from it:**

```
https://github.com/{owner}/{repo}/tree/{ref}/{subdir}
                   └─ repo ────────────┘  └ref┘ └subdir┘
```

Example: `https://github.com/kamusis/anthropics-skills/tree/main/skills/mcp-builder`
- `name`   → `mcp-builder` (last path segment of subdir)
- `repo`   → `https://github.com/kamusis/anthropics-skills.git`
- `subdir` → `skills/mcp-builder`
- `dest`   → `skills/mcp-builder` (same as subdir)
- `ref`    → `main`

If the URL does not follow the tree format (e.g., bare repo URL with no subdir),
collect the missing fields from the user:

| Field | Description | Default if omitted |
|-------|-------------|-------------------|
| `name` | Unique identifier for this vendor entry | Derive from repo name |
| `repo` | Full Git URL of the external repository | (required — ask if missing) |
| `subdir` | Subdirectory inside the external repo to import | Ask the user |
| `dest` | Destination path relative to hub root (`~/.axon/repo/`) | Same as `subdir` |
| `ref` | Branch, tag, or SHA to pin to | `main` |

**Procedure:**

1. Parse the URL if it is a GitHub tree URL; otherwise collect missing fields.
2. Read `~/.axon/axon.yaml` to see if a `vendors:` section already exists.
3. Append the new entry under `vendors:` (create the section if absent).
4. Save the file, then run `axon vendor sync`.

**Example entry to append to `~/.axon/axon.yaml`:**

```yaml
vendors:
  - name: community-skills
    repo: https://github.com/someuser/cool-skills.git
    subdir: skills/coding
    dest: skills/coding
    ref: main
```

Then run:

```bash
axon vendor sync
```

This uses sparse-checkout and mirrors plain files (no `.git` metadata). Local
changes in the hub destination are overwritten. If the upstream SHA hasn't
changed since the last sync, the mirror step is skipped.

**To remove a vendor entry:**

1. Read `~/.axon/axon.yaml` and locate the entry by `name`.
2. Delete the entire `- name: ...` block for that entry.
3. Save the file. The mirrored files in the hub are **not** automatically
   deleted — remove them manually from `~/.axon/repo/<dest>/` if needed,
   then run `axon sync` to commit the deletion.

### Add a custom target (non-built-in AI tool)

If the user wants to link an AI tool that is not in the default `targets` list,
add a new entry to `~/.axon/axon.yaml` under `targets:`:

```yaml
targets:
  - name: <unique-name>          # used with axon link <name>
    source: skills                # hub subfolder to symlink from (skills/workflows/commands/rules)
    destination: ~/.myapp/skills  # absolute path the AI tool reads from
    type: directory
```

**Procedure:**

1. Ask the user for `name`, `destination` path, and which hub `source` category
   (`skills`, `workflows`, `commands`, or `rules`).
2. Append the entry to the `targets:` list in `~/.axon/axon.yaml`.
3. Run `axon link <name>` to create the symlink immediately.
4. Verify with `axon status`.

---

### Security audit

```bash
axon audit                  # scan entire hub
axon audit <skill-name>     # scan a single skill
axon audit workflow.md      # scan a single file
axon audit --force          # re-scan, bypass cache
```

Requires LLM config in `~/.axon/.env`:
```bash
AXON_AUDIT_PROVIDER=openai
AXON_AUDIT_MODEL=gpt-4o-mini
AXON_AUDIT_API_KEY=YOUR_API_KEY_HERE
# Optional: for Ollama or custom endpoints
AXON_AUDIT_BASE_URL=
```

Audit results are cached in `~/.axon/audit-results/`. Use `--force` to bypass.

**Interactive fix mode** — destructive, confirm with user first:
```bash
axon audit --fix
```
For each finding the user can: `r` redact, `d` delete line, `s` skip, `q` quit.

### Add or remove AI tool links

When the user installs a new AI editor after initial setup:
```bash
axon status                  # identify the newly installed tool
axon link <target-name>      # add the symlink
```

To remove a link (restores backup if one exists from a prior `axon link`):
```bash
axon unlink <target-name>
```

### Self-update axon

```bash
axon update --check   # check if a newer version is available
axon update           # download and install the latest release
axon update --force   # reinstall even if already on the latest version
```

`axon update` verifies checksums and rolls back automatically on failure.
Requires `v0.2.0` or later; upgrade manually once if on an older release.
