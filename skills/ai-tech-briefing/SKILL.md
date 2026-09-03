---
name: ai-tech-briefing
description: "一键并发抓取全网 28 个 AI 厂商、Agent/IDE、开源趋势、ITSM 及行业动态信源，快速去重并编译为结构化中文 Markdown 早报，支持推送企业微信 Webhook 并自动归档 Mopheus 工单。用于早报机器人日常巡检与资讯汇编。"
---

# AI 与科技资讯早报 (AI & Tech Daily Briefing)

## 概述

此 Skill 用于高效生成每日 AI 与科技产品资讯早报。通过内置的高并发多线程爬虫脚本（`scripts/fetch_news.py`），可在 **5 秒内并发拉取全网 28 个信源**（涵盖 OpenAI、Anthropic、Google AI、GitHub Trending、Agent/IDE、ITSM 动态、Reddit 社区等），彻底替代昂贵且易超时的交互式网页逆向爬取与多 Subagent 派发。

Agent 仅需执行一键拉取脚本，并专注于内容研读、中文精选翻译、产品策略提炼与格式排版。

---

## 核心工作流

```
┌──────────────────────────────────────────────────────────┐
│ Step 1. 读取工单上下文 & 去重基线 (ticket metadata)       │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Step 2. 一键并发抓取 (python scripts/fetch_news.py, ~5s)   │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Step 3. 智能编译中文 Markdown 早报 (LLM 研读与精选)       │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Step 4. 推送企业微信群 (python scripts/post_webhook.py)   │
└────────────────────────────┬─────────────────────────────┘
                             ▼
┌──────────────────────────────────────────────────────────┐
│ Step 5. 归档工单与元数据写入 (status=archived)            │
└──────────────────────────────────────────────────────────┘
```

---

## 详细执行步骤

### 步骤 1：获取工单上下文与去重基线

1. 获取当前关联工单详情：
   ```bash
   mopheus ticket get <ticket-id> --output json
   ```
2. 更新工单标题为当日日期：
   ```bash
   mopheus ticket update <ticket-id> --title "$(TZ='Asia/Shanghai' date +'%Y-%m-%d') - AI与科技资讯早报"
   ```
3. 检查工单 metadata（若有 `news_last_posted_at` 作为去重基线时间，传给抓取脚本；若有 `news_window_days` 传给脚本）。

---

### 步骤 2：执行高并发数据抓取

运行内置脚本进行并发拉取（输出结构化 JSON 到 `/tmp/news_fetch/news.json`）：

```bash
python scripts/fetch_news.py \
  --output /tmp/news_fetch/news.json \
  --window-days 1
```

*(可选参数：若工单存在去重基线，可追加 `--last-posted-at "<timestamp>"`)。*

**脚本特性**：
- 28 个核心信源全覆盖；
- 内置线程池并发请求，耗时仅 3~5 秒；
- 自动处理 RSS 2.0、Atom 及轻量 HTML 结构；
- 智能防封：Reddit 自动降速限流保护，避免 HTTP 429 封禁。

---

### 步骤 3：智能精选与编译早报

读取 `/tmp/news_fetch/news.json` 中的各分类条目，按下列规范撰写**单一 Markdown 早报**：

#### 编译准则
1. **去重与合并**：同一重大事件在多处报道时（例如 OpenAI 发布新模型），合并为一条并附加多个来源链接；
2. **描述简洁**：中文简述核心事实，突出对产品经理（PM）或工程师有价值的特性，每条不超过 80 字；
3. **总量控制**：单次早报总条目控制在 15~25 条之间，单源最多精选 3~5 条，切勿凑数。

#### 早报 Markdown 模板

```markdown
# 🌅 AI 与科技资讯早报（YYYY-MM-DD 周X）

> 今日共 N 条更新 · 覆盖 K 个信息源 · 由资讯早报机器人自动汇编
> 关注视角：大模型厂商一手动态 + 开发者工具/IDE 演进 + PM 决策洞察

## 🚀 一手厂商动态
- **OpenAI**：<标题>（发布日期）— [链接](URL)
  - <一句话中文要点，说明上线了什么新能力/变动>
- **Anthropic**：...
- **Google AI / Hugging Face**：...

## 🧰 工具 / Agent / IDE 更新
- **Cursor / Codex / Kiro / Claude Code**：<标题> — [链接](URL)
  - <一句话中文要点>
- **Dify / Multica / Obsidian**：...

## 💡 产品策略与决策启发
- **Stratechery / Lenny's Newsletter**：<标题> — [链接](URL)
  - <要点解析，说明为什么对产品规划有参考意义>

## 📰 行业新闻与社区脉搏
- **Hacker News / TechCrunch**：...
- **Reddit 社区热点 (r/ClaudeAI, r/LocalLLaMA...)**：...

## 🌟 GitHub Trending 今日精选
- **[repo/name](URL)** (语言 ★Stars): 核心功能与亮点一句话简介

---
来源：AI资讯早报机器人 · 工单 ID: <ticket-id>
```

---

### 步骤 4：推送到企业微信 Webhook

将整理好的 Markdown 保存至临时文件（如 `/tmp/news_fetch/report.md`），并运行内置推送脚本：

```bash
python scripts/post_webhook.py \
  --url "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=4ad80392-e6f1-45e5-80cf-ac592d1ff9d1" \
  --content-file /tmp/news_fetch/report.md
```

**自动拆包能力**：企微 Webhook 单条消息硬上限为 4096 字节。脚本会自动按 `## ` 标题将超长早报拆分为 `[1/N]`、`[2/N]` 多条连续发送，防止被企微截断拒绝。

---

### 步骤 5：工单归档与审计记录

1. **发表归档评论**：将完整的 Markdown 早报与抓取统计（源数量、条目数、Webhook 状态）作为评论发表到工单下：
   ```bash
   mopheus ticket comment add <ticket-id> --content-file /tmp/news_fetch/report.md
   ```
2. **更新工单状态**：推送成功后，将工单标记为已归档（`archived`）：
   ```bash
   mopheus ticket update <ticket-id> --status archived
   ```
3. **更新元数据（Metadata）**：
   ```bash
   mopheus ticket metadata set <ticket-id> news_last_posted_at "$(date -Iseconds)"
   mopheus ticket metadata set <ticket-id> news_last_errcode "0"
   ```

---

## 异常与边界处理

- **个别源超时/失败**：脚本会自动跳过并在 `sources_summary` 中标明 `fetch_failed`，早报正常生成，不要因单一源失败中断流程；
- **全部源抓取为空**：若网络彻底断开，不要向企业微信发送空消息，在工单评论中记录 `empty_run` 并将 `news_last_errcode` 设为 `-1`；
- **Webhook 发送失败**：若返回 `errcode != 0`，保持工单状态为 `todo`，并在评论中记录失败详情，便于人工复查。
