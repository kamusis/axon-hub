---
name: github-trends
description: Fetch and report GitHub trending repositories across three dimensions — New Rising (30d), Global Trending (monthly), and AI/Agent Momentum (1y). Use when user asks "github trends", "gittrending", "github trending repos", "今天有什么热门项目", or wants to discover interesting GitHub repositories.
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

Run the packaged script within the skill directory:

```bash
bash scripts/github_trends.sh
```

### Step 2 — Post-process and refine the report

The script outputs an initial Markdown report with raw descriptions from GitHub. **The agent MUST post-process the tables before publishing the final report or ticket:**

1. **Mandatory Chinese Distillation (硬性约束)**:
   - Every entry in the `简介` column **MUST be translated and distilled into concise Chinese** (strictly 1–2 short sentences, under 40 characters).
   - **NEVER** leave raw English descriptions in the final table.
   - **Highlight Core Differentiation**: Summarize what problem it solves or why it stands out.
     - ✅ **Good**: "ChatGPT 负责思考，Codex 负责执行的轻量协同调度器"
     - ❌ **Bad**: "A simple Python script that connects to OpenAI API and executes shell commands..."
2. **Preserve Structure**:
   - Keep `#`, `仓库` (links), `⭐`, table headers, section titles, and the footer observation strictly intact.

**Report Structure Reference**:
- **Header**: `# GitHub 趋势深度观察：全维度简报` with generation timestamp in Asia/Tokyo.
- **新锐榜 — 30 天内诞生的全球黑马 (Top 10)**: Table listing repos created in the last 30 days ordered by stars.
- **全球热度榜 — GitHub 官方本月趋势 (Top 10)**: Table listing repos from GitHub's official monthly trending page.
- **动能榜 — AI & Agent 赛道年度活跃标杆 (Top 10)**: Table listing AI/Agent repos created in the last year and updated in the last 30 days.
- **Footer**: `---` followed by `**Kuro 的每日观察**：新锐看爆发，热度看风口，动能看底蕴。🐈‍⬛`

## Notes

- The script uses Asia/Tokyo timezone for its timestamp.
- This skill fetches live data on each call — no caching.

## Comparative Evaluation (beyond trending)

When the user asks to **compare**, **evaluate for commercial use**, or **analyze licensing** of GitHub repos (not just list trending ones), use the license guide:

- `references/license-guide.md` — License quick-reference (MIT/Apache/GPL/AGPL/SSPL/BSL), evaluation checklist for commercial forks, programmatic license checking commands, and red flags to watch for.

Workflow: fetch the actual LICENSE file via `curl -s https://raw.githubusercontent.com/{owner}/{repo}/{branch}/LICENSE | head -40`, compare against the guide, and present a structured comparison.

## Additional Resources

- `references/survey-notes.md` — Notes from surveying mattpocock/skills and addyosmani/agent-skills repos for potential skill adoption.
