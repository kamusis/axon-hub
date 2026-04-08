# axon Setup Reference

Use this guide when axon is not yet installed or the user is setting up axon on
a new machine for the first time.

---

## Step 1: Install the axon binary

Run this one-liner to auto-detect the platform, download the latest release,
and install to `/usr/local/bin/` (Linux/macOS):

```bash
set -e
OS=$(uname -s | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  ARCH="amd64" ;;
  aarch64|arm64) ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" && exit 1 ;;
esac
VERSION=$(curl -fsSL https://api.github.com/repos/kamusis/axon-cli/releases/latest \
  | grep '"tag_name"' | head -1 | sed 's/.*"v\([^"]*\)".*/\1/')
ASSET="axon_${VERSION}_${OS}_${ARCH}.tar.gz"
URL="https://github.com/kamusis/axon-cli/releases/download/v${VERSION}/${ASSET}"
echo "Downloading axon v${VERSION} for ${OS}/${ARCH}..."
curl -fsSL "$URL" -o /tmp/"$ASSET"
tar -xzf /tmp/"$ASSET" -C /tmp/
sudo mv /tmp/axon /usr/local/bin/axon
sudo chmod +x /usr/local/bin/axon
rm -f /tmp/"$ASSET"
echo "Installed: $(axon version)"
```

**Asset naming reference** (GitHub Releases URL pattern):
```
https://github.com/kamusis/axon-cli/releases/download/v{VERSION}/axon_{VERSION}_{OS}_{ARCH}.tar.gz
```

Supported platforms: `linux_amd64`, `linux_arm64`, `darwin_amd64`, `darwin_arm64`,
`windows_amd64` (`.zip` instead of `.tar.gz`).

Alternatively, if axon is already installed at `v0.2.0+`, upgrade in place:

```bash
axon update
```

Verify the install:

```bash
axon version
```

**Windows (PowerShell — run as Administrator):**

```powershell
$version = (Invoke-RestMethod https://api.github.com/repos/kamusis/axon-cli/releases/latest).tag_name -replace '^v',''
$url = "https://github.com/kamusis/axon-cli/releases/download/v${version}/axon_${version}_windows_amd64.zip"
$tmp = "$env:TEMP\axon.zip"
$extract = "$env:TEMP\axon-tmp"
Invoke-WebRequest -Uri $url -OutFile $tmp
Expand-Archive -Path $tmp -DestinationPath $extract -Force
Move-Item -Force "$extract\axon.exe" "C:\Windows\System32\axon.exe"
Remove-Item $tmp, $extract -Recurse -Force
axon version
```

`C:\Windows\System32\` requires Administrator. If you prefer a user-level install
(no admin needed), use `$env:USERPROFILE\bin\axon.exe` instead, then add
`$env:USERPROFILE\bin` to your `$env:PATH`.

**Symlink note:** `axon link` creates symlinks, which require Administrator or
Developer Mode on Windows. WSL is fully supported without this restriction.

---

## Step 2: Environment check

```bash
axon doctor
```

This checks that `git` is on `PATH` and the environment is ready.
Resolve any reported issues before continuing.

---

## Step 3: Initialize the Hub (`axon init`)

Choose one of three modes based on the user's situation:

| Mode | Command | When to use |
|------|---------|-------------|
| **A** Local only | `axon init` | No remote yet; add one later |
| **B** Personal remote | `axon init <git-url>` | User has their own skills repo (recommended) |
| **C** Public upstream | `axon init --upstream` | Read-only; use the curated public axon hub |

**Mode B example:**
```bash
axon init git@github.com:yourname/axon-hub.git
# or HTTPS:
axon init https://github.com/yourname/axon-hub.git
```

**What happens during init:**
- A local Git repo is created at `~/.axon/repo/` (or cloned from the URL).
- `~/.axon/axon.yaml` is generated with pre-configured targets for all
  supported AI tools.
- Existing skills from your current tool directories are **safely imported**:
  - Same content → one copy kept, duplicate skipped.
  - Same name but different content → both preserved with a `.conflict-<tool>`
    suffix. Review these files manually after setup.

---

## Step 4: Inspect the current machine's AI tool state

```bash
axon status
```

Read the output carefully. The status report has four sections:

| Section | Meaning | Agent action |
|---------|---------|--------------|
| `Linked (healthy symlinks)` | Already correctly linked | No action needed |
| `Real directories (not yet converted to symlinks)` | Tool is installed and has content, but not yet linked | **High-priority candidate** — warn user that axon will backup the original directory before linking |
| `Installed but not linked` | Tool is installed, directory is empty or missing | Candidate to link |
| `Not installed (skipped)` | Tool is not installed on this machine | Skip entirely — do not suggest linking |

Present a summary of the candidates to the user. For example:

```
The following AI tools are installed and ready to link:
  [real dir]  windsurf-skills      — has existing content (will be backed up)
  [not linked] claude-code-skills  — empty, safe to link

The following are not installed and will be skipped:
  cursor, neovate, opencode

Which tools would you like to link?
```

---

## Step 5: Link the selected AI tools

For each tool the user confirms, run:

```bash
axon link <target-name>
```

For example:
```bash
axon link windsurf-skills
axon link claude-code-skills
```

**Never run bare `axon link` (without a name)** unless the user explicitly
says "link everything" or "link all tools". The no-argument form links every
configured target at once, which may be unwanted.

If a real directory was backed up, axon reports the backup path. Let the user
know where the backup is:

```
↑  [windsurf-skills] backed up to ~/.axon/backups/windsurf-skills_<timestamp>/
✓  [windsurf-skills] linked
```

---

## Step 6: Set a remote (Mode A only)

If the user chose Mode A (local only) in Step 3, help them attach a remote now:

```bash
axon remote set git@github.com:yourname/axon-hub.git
```

Verify the remote is recognized:

```bash
axon status --fetch
```

---

## Step 7: First sync

```bash
axon sync
```

Behavior depends on `sync_mode` in `~/.axon/axon.yaml`:

- **`read-write`** (default): `git add` → `git commit` → `git pull --rebase` →
  `git push`. Use this when `origin` points to a repo you own.
- **`read-only`**: `git pull --ff-only` only. Set automatically when using
  `axon init --upstream`. Do not change to `read-write` unless you have
  write access to the remote.

After sync, the hub is up to date and all linked AI tools read from it.

---

## Common Setup Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `git: command not found` | git not installed | Install git (see README Prerequisites) |
| `permission denied` creating symlink | Insufficient permissions (Windows) | Run as Administrator or use WSL |
| `.conflict-<tool>.md` files in hub | Name collision during import | Review and merge manually, then `axon sync` |
| `push` rejected on first sync | Remote already has commits | Run `axon sync` again; it will rebase and retry |
