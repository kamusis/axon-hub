---
name: mopheus-skill-sync
description: "Synchronize one local SKILL.md directory into a specified Mopheus workspace. Use whenever the user asks to sync, publish, upload, or update a local skill in a Mopheus workspace. Preserve remote-only YAML frontmatter fields such as capabilities and default_agent_id, update the remaining content from the local skill, and report exactly what was retained and synchronized."
---

# Mopheus Skill Sync

Synchronize one local skill directory into one explicitly named Mopheus workspace. The local skill is the source of truth for its body and shared frontmatter fields. The existing Mopheus skill is the source of truth for frontmatter fields that exist only remotely.

## Inputs and safety

Require both inputs:

- a local skill directory containing exactly one `SKILL.md`;
- a target Mopheus workspace name, slug, or UUID.

Do not infer the target workspace from the active CLI profile when the user did not specify one. Do not modify the local skill directory. Use the installed `mopheus` executable from the host PATH; do not use a repository-built CLI or a preview binary.

Stop before writing when the local path is missing, `SKILL.md` has no valid frontmatter or `name`, the workspace is missing or ambiguous, the repository/API identity is unexpected, or more than one same-name workspace skill is returned.

## 1. Resolve and inspect the target

1. Read the local `SKILL.md` without changing it. Parse its YAML frontmatter and record:
   - the local skill name;
   - all local frontmatter keys;
   - the local body after the closing `---`.
2. Run `mopheus workspace list --output json` and resolve the target by exact UUID, name, or slug. Stop on zero or multiple matches.
3. Pass `--workspace-id <workspace-id>` explicitly to every subsequent Mopheus command.
4. Run `mopheus --workspace-id <workspace-id> skill list --output json` and find an exact case-sensitive match for the local frontmatter `name`. Do not match by description, slug, substring, or fuzzy search.

## 2. No same-name skill: create it

When no exact same-name skill exists, create it directly from the local skill metadata and complete content:

```bash
mopheus --workspace-id <workspace-id> skill create \
  --name <local-name> \
  --description <local-description> \
  --content <complete-local-SKILL.md-content>
```

Do not pass `--update` in this branch. Preserve the complete local `SKILL.md`, including its local frontmatter. If shell argument length or attached files make direct creation unsafe, use `mopheus skill import --path <local-skill-directory>` as the bounded create fallback; still do not pass `--update`.

## 3. Same-name skill: merge before updating

When an exact same-name skill exists:

1. Fetch the complete remote skill with `mopheus --workspace-id <workspace-id> skill get <skill-id> --output json`.
2. Extract the remote `content` field, which contains the remote `SKILL.md` and its YAML frontmatter.
3. Merge only the top-level frontmatter keys:
   - Local keys override remote values. This includes shared fields such as `name` and `description`.
   - Remote keys absent from the local frontmatter are remote-exclusive and must be preserved verbatim as complete YAML blocks. This includes `capabilities`, `default_agent_id`, and any future Mopheus-specific keys.
   - Do not delete, rewrite, normalize, or merge a remote-exclusive list or mapping. Preserve its complete raw block.
   - Use the local body verbatim. Do not retain remote body text.
4. Use the bundled `scripts/merge_frontmatter.py` helper to produce a temporary merged `SKILL.md`. The helper performs a conservative top-level merge and never edits either source file.
5. Copy the local skill directory to a temporary staging directory, replace only its staged `SKILL.md` with the merged file, and update the existing skill:

```bash
mopheus --workspace-id <workspace-id> skill import --path <staging-directory> --update
```

The staging directory must contain only the selected skill directory. Remove only the temporary staging directory after verification; never remove the user's local skill directory.

## 4. Preview and write protocol

Before any create or update, report a concise preview and confirm the calculated scope internally:

```text
Workspace: <name> (<id>)
Skill: <name> (<id or NEW>)
Action: CREATE or UPDATE
Retained remote-only frontmatter: <keys or none>
Synchronized local frontmatter: <keys>
Synchronized body: yes
Attached files: <preserved count/list>
```

Do not overwrite an existing skill until the merge has been produced and the retained remote-only keys are listed. Never use `--update` against a directory containing multiple unrelated skills.

## 5. Verify and report

After the write:

1. Re-run `skill list --output json` and confirm the target skill exists in the requested workspace.
2. Fetch it with `skill get <skill-id> --output json`.
3. Compare the normalized remote content with the staged/local expected content. Normalizing line endings is allowed; changing YAML values is not.
4. Confirm every remote-exclusive frontmatter key is still present with its original value and every synchronized local key/body matches the local source.
5. Report in Simplified Chinese:
   - workspace name, slug, and UUID;
   - skill name, ID, and resulting version;
   - whether the action was CREATE or UPDATE;
   - remote-only frontmatter keys and values retained;
   - local frontmatter keys and body synchronized;
   - attached files preserved;
   - verification command/results.

If verification fails, report the failed comparison and do not claim success. Preserve the successful external write if the API write succeeded but a later verification step failed.
