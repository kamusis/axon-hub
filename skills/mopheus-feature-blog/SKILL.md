---
name: mopheus-feature-blog
description: Write engaging, accessible, and high-impact technical blog posts, feature deep-dives, architectural breakdowns, and vision articles for Mopheus. Use whenever asked to write an article introducing any Mopheus feature, architecture design, underlying implementation, or conceptual vision. Triggers on phrases like "写一篇介绍 mopheus 某功能的文章", "用 mopheus-feature-blog 技能写文章", "feature blog for mopheus", "把 mopheus 某某功能写成文章", or "撰写 Mopheus 技术博客".
---

# Mopheus Feature & Technical Blog Writer

Write compelling, grounded, and technically rigorous blog posts for Mopheus, targeting real-world developers, architects, DBAs, and engineering leads.

## Core Philosophy

- **Relatable to Every Developer**: Never write as an insular, elitist tool. Anchor every article in the day-to-day realities of ordinary frontend/backend engineers, DBAs, DevOps, and team leads.
- **Engaging without Fluff**: Avoid dry, monotonic manual documentation. Strictly reject hollow hype, exaggerated marketing fluff, and hand-waving claims.
- **Objective & Grounded (客观务实，数据说话)**: Maintain an engineering-first, professional tone. Strictly eliminate boastful, exaggerated adjectives and adverbs. Let the architectural elegance, concrete code, and hard benchmark numbers speak for themselves. Let readers draw their own conclusions without model self-praise.
- **Value-Oriented Presentation (聚焦用户与产品价值，严禁内部汇报式罗列)**: Blog posts are written for external engineers and users. Outcomes and capabilities should be demonstrated through the **diagnostic value, architectural insights, and interactive layers** the feature delivers, rather than dumping internal 24-hour work logs, specific internal agent names, or mechanical task counts like an internal company report.
- **Strict Technical Rigor**: Maintain 100% precision for code, architectures, CLI syntax, configuration keys, and database models. Never confuse speculative ideas with implemented reality.
- **Positive & Speed-Focused Motivation**: Never frame features as solving "human exhaustion or laziness". Engineering rigor is essential; Mopheus exists to achieve continuous, high-speed, automated quality exposure and eliminate workflow roadblocks.
- **Highlight the AI-Native Paradigm**: Clearly articulate why traditional tools (scripts, isolated web chat boxes, fragmented SaaS) fail, and how Mopheus's "People, Agents, Teams (PAT)" unified workspace, real-world execution sandboxes (Daemon/Worktrees), and long-term memory solve the problem natively.

---

## Tone & Phrasing Standards (用词与语言风格规范)

### 1. 严禁主观夸大修饰
- **禁用词汇**：严禁在正文和标题中使用“瞬间”、“极速”、“毫秒级”、“秒级”、“彻底打破/颠覆”、“重磅”、“极其/巨额”等主观自吹或夸大的修饰词。
- **客观陈述**：
  - 若有真实记录的量化执行时间/指标，**按实记录精确数字**（例如：“耗时 2.1 秒”、“消耗 1,140,135 Tokens”）；
  - 若没有留存精确运行耗时，**直接客观陈述事实**（例如：“首次运行同步了全量数据”），严禁擅自脑补“瞬间完成”、“极速同步”。

### 2. 经典正反面对照表 (Good vs Bad Examples)

| 场景 | ❌ 错误示范（浮夸吹捧） | ✅ 正确规范（客观务实） |
| :--- | :--- | :--- |
| **数据同步** | “首次运行**瞬间同步**了全量 1,087 条数据” | “首次运行**同步了**全量 1,087 条数据”（如有记录则写“耗时 X 秒同步了...”） |
| **增量查询** | “二次运行实现了**极速/毫秒级**响应” | “二次运行比对状态并跳过已终态任务，**仅需 2 秒完成**检查与渲染” |
| **标题拟定** | “从黑盒运行到**毫秒级洞察**：**重磅**发布...” | “从黑盒运行到**结构化洞察**：我们是如何为 Mopheus 智能体任务构建数据可视化技能的？” |
| **价值总结** | “用短短不到 1000 行代码**彻底打破/颠覆**了黑盒” | “通过轻量级数据管线，为多智能体任务提供**清晰、透明、可追踪的工程可观测性**” |
| **问题描述** | “面对**极其/巨额**的 Token 消耗和**玄学**” | “避免靠 LLM 直接读取裸数据带来的**高昂 Token 开销与统计不确定性**” |

---

## Adaptive Article Archetypes

Do not force every article into a single rigid template. Detect the topic's core nature and select the appropriate structure:

### Archetype A: Feature Launch & Capability Spotlight (新功能发布与特性解析)
Best for: Griller reviewer agent, ticket comment deep-links, external platform issue/PR mirroring, Lark/DingTalk ChatOps integration.
1. **Hook & Real-World Friction**: Start from a concrete everyday developer frustration (e.g. blind spots in code review, hard-to-share discussion threads).
2. **Core Concept & Origin (if applicable)**: Explain the underlying principle (and credit open-source origins with links if applicable).
3. **The Mopheus Way**: Contrast traditional manual/fragmented workflows against Mopheus's automated, contextual flow (with ASCII diagram).
4. **Engineering Elegance & Design Details**:
   - Minimalist data modeling & role inheritance (e.g. single boolean flags, zero redundant fields).
   - Strict execution/prompt guardrails (thread scoping, language adaptation, hierarchical replies).
   - CLI-First & multi-surface real-time sync (CLI commands, Web UI, WebSocket live updates).
5. **Human & Agent Collaboration (Dual-Track)**: How human engineers and agents interact together without friction.
6. **Future Horizon & Call to Action**: Connect to broader roadmap and invite exploration of Mopheus official website (https://www.mopheus.ai). Never link to private GitHub repositories.

### Archetype B: Deep Architecture & Implementation Breakdown (底层架构与技术实现剖析)
Best for: Three-tier Git virtualization, Daemon execution engine, Worktree isolation, Memory/pgvector recall, WebSocket multiplexing.
1. **The Core Engineering Challenge**: High concurrency, resource explosion, state contamination, or cross-system disconnects.
2. **Tiered Architecture & Data Flow**: Multi-layer topology breakdown with clear ASCII or structural diagrams.
3. **Key Architectural Pillars**: Deep technical dive into each subsystem (e.g. bare repo object reuse, lazy sync on checkout, memory distillation).
4. **End-to-End SOP & Standard Lifecycle**: Step-by-step lifecycle flow from task claim to verification, commit, PR, and ticket closure.
5. **Platform Compatibility & Roadmap**: Neutrality (GitHub/GitLab/Gitea), SDK abstractions, and future evolution.

### Archetype C: Vision & Paradigm Exploration (宏观范式与框架构想)
Best for: AIDevOps (unifying Dev, Ops, and ITSM), Polymorphic Assignees, Multi-Agent Arena, Autonomous Self-Healing.
1. **Industry Status Quo & The "Tool Island" Dilemma**: Friction across Jira, GitLab, Grafana, ITSM, and disconnected chat tools.
2. **Why Agentic AI Ends Fragmentation**: Cross-domain semantic penetration from natural language to AST, PR diffs, and production APM logs.
3. **Mopheus Core Pillars as the Collaboration Hub**: Human-Agent parity, local sandboxes, event-driven automation, long-term memory.
4. **Full Lifecycle End-to-End Walkthrough**: Tracing an issue from PM spec to agent coding, CI gate, lightweight deploy, and monitoring.
5. **The Future of Software Engineering**: Shift from "watching AI work" to "orchestrating autonomous agent swarms with human oversight".

---

## Writing & Formatting Conventions

- **File Location**: Save articles as Markdown under `docs/blog/<slug>.md`.
- **Language**: Default to natural, high-signal Chinese for prose when requested in Chinese, while keeping all code, CLI commands, identifiers, configuration keys, and error names in verbatim English.
- **Visuals & Image Hosting Standard (配图与图床上传规范)**:
  - 架构与数据流优先使用清晰直观的 ASCII 流程图；
  - 若文章中包含实际系统截图、交互式看板或 UI 效果图，**严禁在最终文章中使用本地相对路径（如 `./images/...`）**；
  - **必须使用 `see-uploader` 技能将截图上传至公开图床（S.EE）**：
    ```bash
    python3 ~/.gemini/config/skills/see-uploader/scripts/upload.py --file <path_to_image>
    ```
  - 将返回的公开图床直链（如 `https://files.seeusercontent.com/...`）以标准 Markdown 语法 `![图片说明](https://files.seeusercontent.com/...)` 嵌入文章中，确保文章在官网、微信公众号、技术博客或社区分发时图片均能稳定公开展示。
- **External Links & Call to Action (CTA)**: End every article with a standard blockquote CTA:
  ```markdown
  ---

  > **<针对文章主题的引导问句，如：想让严苛专业的 Griller 智能体为你的团队方案把关吗？>**  
  > 立即上手探索 [Mopheus (mopheus.ai)](https://www.mopheus.ai)，<针对文章主题的价值行动句，如：为你的工作空间配置专属的架构与质量审查官！>
  ```
  第一句引导问句与第二句结尾行动句根据文章内容动态变化，中间“`立即上手探索 [Mopheus (mopheus.ai)](https://www.mopheus.ai)，`”固定不变。**NEVER link to GitHub (enmotech/mopheus is a private repository).**
- **Tone**: Professional, confident, technically sharp, empathetic, and inspiring.
