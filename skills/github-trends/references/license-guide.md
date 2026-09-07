# Open-Source License Guide for Commercial Evaluation

When the user asks to compare open-source projects for commercial/closed-source use, use this guide.

## Quick Reference Table

| License | Fork & Sell? | Must Open-Source? | SaaS OK? | Key Gotcha |
|---|---|---|---|---|
| **MIT** | ✅ Yes | ❌ No | ✅ Yes | Just keep copyright notice |
| **Apache 2.0** | ✅ Yes | ❌ No | ✅ Yes | Must state changes; patent grant clause |
| **BSD 2/3** | ✅ Yes | ❌ No | ✅ Yes | Similar to MIT |
| **GPL v3** | ✅ Yes | ✅ Yes (derivative) | ✅ Yes | Copyleft: your changes must be GPL |
| **AGPL v3** | ✅ Yes | ✅ Yes (derivative) | ⚠️ Network use = distribution | SaaS triggers copyleft |
| **SSPL** | ⚠️ Conditional | ✅ Yes if offering as service | ❌ Not without open-sourcing | MongoDB-style; not OSI-approved |
| **BSL / BSL 1.1** | ⚠️ Time-limited | After change date | ❌ Restricted | Converts to open license after N years |
| **Custom "Community"** | ⚠️ Read carefully | Varies | Varies | Often Apache-based + extra restrictions |

## Common Patterns in AI/Agent Tools

1. **Pure MIT/BSD** — Rarest among large projects. Best for commercial fork.
   - Examples: Paperclip (MIT), many small utilities

2. **Apache 2.0 + extra conditions** — Most common in this space.
   - Typical restrictions: no hosted/SaaS without commercial license, must keep branding
   - Examples: Multica (modified Apache), LobeHub (community license)
   - Effectively "open core" — source visible, commercial use requires license purchase

3. **AGPL** — Common in self-hostable SaaS alternatives.
   - Safe for internal use, dangerous if you offer it as a service to others
   - Examples: Nextcloud, Grafana (AGPL since v10)

## Evaluation Checklist for Commercial Fork

When comparing repos for a potential commercial product:

1. **License file** — Read the actual LICENSE, not just the GitHub badge
2. **License headers in source** — Some projects have per-file restrictions
3. **Dependencies** — Check `package.json`/`Cargo.toml` for copyleft deps (GPL/AGPL)
4. **Contributor License Agreement (CLA)** — Some CLAs let the maintainer relicense contributions
5. **Brand/trademark restrictions** — Many "open source" projects restrict use of name/logo
6. **Patent clauses** — Apache 2.0 has explicit patent grant; MIT is ambiguous
7. **Change date / conversion** — BSL licenses convert to open after X years

## How to Check License Programmatically

```bash
# Get license type via GitHub API
gh api repos/{owner}/{repo} --jq '.license.spdx_id'

# Read the actual LICENSE file (always do this — badge != actual terms)
curl -s https://raw.githubusercontent.com/{owner}/{repo}/{branch}/LICENSE | head -40

# Check for license headers in source files
gh api repos/{owner}/{repo}/git/trees/{branch}?recursive=1 --jq '.tree[].path' | grep -i license
```

## Red Flags

- "Based on Apache 2.0 with additional conditions" — read those conditions carefully
- "Community License" / "Enterprise License" naming — often means restricted
- Logo/branding restrictions that prevent white-labeling
- "You may not offer this as a hosted service" — kills SaaS business model
- CLA that lets maintainer change license terms later
