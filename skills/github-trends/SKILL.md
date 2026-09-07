---
name: github-trends
description: Fetch and report GitHub trending repositories across three dimensions — New Rising (30d), AI/Agent Momentum (1y), and Global Trending (monthly). Use when user asks "github trends", "gittrending", "github trending repos", "今天有什么热门项目", or wants to discover interesting GitHub repositories.
---

# GitHub Trending — Three-Track Report

## Prerequisites

- `gh` CLI authenticated (`gh auth status`)
- `jq` installed
- `python3` installed

## When to Use

Trigger when the user asks for GitHub trending information, such as:
- "github trends"
- "git trending"
- "今天 github 有什么热门"
- "what's hot on GitHub"
- Any variant asking for popular/new GitHub repositories

## Workflow

### Step 1 — Run the script

```bash
/home/kamus/.openclaw/workspace/scripts/github_trends.sh
```

### Step 2 — Report to user

The script outputs a pre-formatted report. Present it directly to the user as your response. No further processing needed.

The report contains three sections:
1. **新锐榜** (Rising Stars) — Top 5 repos created in the last 30 days by stars
2. **动能榜** (AI/Agent Momentum) — Top 10 AI/Agent repos created in the last year, updated in last 30 days
3. **全球热度榜** (Global Trending) — Top 10 from GitHub's official monthly trending page

The underlying script lives at `/home/kamus/.openclaw/workspace/scripts/github_trends.sh` — do not copy it. Call it in place via the absolute path.

## Notes

- The script uses Asia/Tokyo timezone for its timestamp.
- This skill fetches live data on each call — no caching.

## Comparative Evaluation (beyond trending)

When the user asks to **compare**, **evaluate for commercial use**, or **analyze licensing** of GitHub repos (not just list trending ones), use the license guide:

- `references/license-guide.md` — License quick-reference (MIT/Apache/GPL/AGPL/SSPL/BSL), evaluation checklist for commercial forks, programmatic license checking commands, and red flags to watch for.

Workflow: fetch the actual LICENSE file via `curl -s https://raw.githubusercontent.com/{owner}/{repo}/{branch}/LICENSE | head -40`, compare against the guide, and present a structured comparison.

## Additional Resources

- `references/survey-notes.md` — Notes from surveying mattpocock/skills and addyosmani/agent-skills repos for potential skill adoption.
