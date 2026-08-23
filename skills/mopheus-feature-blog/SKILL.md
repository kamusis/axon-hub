---
name: mopheus-feature-blog
description: Write engaging, accessible, and high-impact technical blog posts, feature deep-dives, architectural breakdowns, and vision articles for Mopheus. Use whenever asked to write an article introducing any Mopheus feature, architecture design, underlying implementation, or conceptual vision. Triggers on phrases like "写一篇介绍 mopheus 某功能的文章", "用 mopheus-feature-blog 技能写文章", "feature blog for mopheus", "把 mopheus 某某功能写成文章", or "撰写 Mopheus 技术博客".
---

# Mopheus Feature & Technical Blog Writer

Write compelling, grounded, and technically rigorous blog posts for Mopheus, targeting real-world developers, architects, DBAs, and engineering leads.

## Core Philosophy

- **Relatable to Every Developer**: Never write as an insular, elitist tool. Anchor every article in the day-to-day realities of ordinary frontend/backend engineers, DBAs, DevOps, and team leads.
- **Engaging without Fluff**: Avoid dry, monotonic manual documentation. Strictly reject hollow hype, exaggerated marketing fluff, and hand-waving claims.
- **Strict Technical Rigor**: Maintain 100% precision for code, architectures, CLI syntax, configuration keys, and database models. Never confuse speculative ideas with implemented reality.
- **Positive & Speed-Focused Motivation**: Never frame features as solving "human exhaustion or laziness". Engineering rigor is essential; Mopheus exists to achieve continuous, high-speed, automated quality exposure and eliminate workflow roadblocks.
- **Highlight the AI-Native Paradigm**: Clearly articulate why traditional tools (scripts, isolated web chat boxes, fragmented SaaS) fail, and how Mopheus's "People, Agents, Teams (PAT)" unified workspace, real-world execution sandboxes (Daemon/Worktrees), and long-term memory solve the problem natively.

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
6. **Future Horizon & Call to Action**: Connect to broader roadmap and invite exploration of `enmotech/mopheus` on GitHub.

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
- **Visuals**: Use clear ASCII flowcharts and data flow diagrams to make complex mental models instantly graspable.
- **Tone**: Professional, confident, technically sharp, empathetic, and inspiring.
