---
name: see-uploader
description: Upload images to S.EE and get share links in multiple formats.
metadata:
  openclaw:
    emoji: "🖼️"
    requires: { "bins": ["uv", "curl", "python3"], "env": ["SEE_API_TOKEN"] }
    primaryEnv: "SEE_API_TOKEN"
---

# S.EE Uploader

Upload images to S.EE image hosting service.

## Usage

```bash
uv run {baseDir}/scripts/upload.py --file <path_to_image>
```

## Configuration

Set `SEE_API_TOKEN` in the environment. If unset, the script falls back to
scanning shell rc files (`~/.bashrc`, `~/.zshrc`, `~/.bash_profile`,
`~/.profile`, `~/.zshenv`) for an `export SEE_API_TOKEN=...` line.

## Output

Returns Markdown, HTML, and Direct Link.
