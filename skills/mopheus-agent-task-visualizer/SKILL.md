---
name: mopheus-agent-task-visualizer
description: >
  Mopheus Agent Task 数据深度统计与 HTML 交互式可视化看板生成器。
  从指定 Mopheus 工作区中增量拉取全量 agent task 及 transcript 消息，
  深入解析思维耗时 (Thinking Duration)、工具调用分布 (tool:Bash, tool:TaskCreate, tool:TaskUpdate, tool:WebFetch, tool:WebSearch 等) 及成功率/失败率，
  沉淀 stage 结构化数据并生成自包含、高交互性的现代化数据可视化 HTML 报告。
  
  触发关键词：agent task统计、agent task可视化、智能体任务统计、task数据可视化、
  agent task 看板、task transcript 统计、agent task 报告、智能体任务分析、
  task thinking 统计、tool 调用统计。
---

# Mopheus Agent Task 数据可视化看板生成技能

本技能实现对 Mopheus 平台中 Agent Task 的**工业级数据统计与交互式可视化分析**。

## 核心架构设计

```
[Mopheus API / CLI]
       │ (增量读取，基于 state_record.json 终态跳过)
       ▼
[1. collect_raw_tasks.py] ──► 缓存至 ~/.mopheus/analytics/<ws>/raw_tasks/
       │
       ▼
[2. process_stage_metrics.py] ──► 深度解析 transcript (Thinking, tool:* 调用, Token)
       │
       ▼
[3. stage_tasks.json] ──► 预聚合维度数据 (纯脚本处理，零 LLM 裸数据开销)
       │
       ▼
[4. generate_html_report.py] ──► 生成现代化、自包含交互式 HTML 可视化报告
```

---

## 统计与可视化维度

1. **基础任务元数据**：
   - 任务总数、成功/失败/取消状态分布、全局成功率。
   - 任务开始时间、完成时间、执行持续时长（Wall-clock Duration）。
   - 关联工单（Ticket Title / Key）、触发者类型、失败原因（Failure Reason 归类）。

2. **智能体维度 (Agent Leaderboard)**：
   - 各 Agent 任务执行量、成功率排行。
   - 各 Agent 平均耗时、平均思考时长、总 Token 消耗对比。

3. **思维与推理维度 (Thinking Analytics)**：
   - Thinking 思考总时长、单任务平均思考时间。
   - Thinking 思考块（Block）数量与字符总数。
   - 任务耗时结构剖析（Thinking vs Tool Execution vs Model Streaming）。

4. **工具调用健康度与耗时 (Tool Invocations & Health)**：
   - 细分工具维度：`tool:Bash`、`tool:TaskCreate`、`tool:TaskUpdate`、`tool:WebFetch`、`tool:WebSearch` 等。
   - 各工具调用频次、成功调用数、失败调用数、工具级成功率。
   - 各工具执行平均延迟（Latency）。

5. **运行时资源守卫与安全审计 (Runtime Guard & Safety Observability)**：
   - 守护插件覆盖：`memory` (物理内存超标)、`process_count` (进程数超限 / Fork Bomb 防护)、`idle` (空闲超时/挂死防护)。
   - 守卫事件统计：80% 警戒水位告警（Alarm Breaches）与超时硬熔断（Circuit Breaker Kills）。
   - 智能体资源风险画像与排行榜（Agent Risk Ranking）。
   - 任务事后取证（Post-Mortem Forensics）：精确记录峰值内存 (Observed RSS)、预算限制 (Budget)、超限时长、被杀死的进程 PIDs 及 Cgroup 路径。

6. **Token 与成本消耗**：
   - Prompt Tokens / Completion Tokens / Total Tokens。

---

## 快速使用

### 一键执行（推荐）
```bash
python3 ~/.gemini/config/skills/mopheus-agent-task-visualizer/scripts/run_visualizer.py -w <workspace_slug>
```
常用选项：
- `-w, --workspace <slug>`: 指定目标工作区（默认 `dev` 或根据当前配置）。
- `-p, --profile <profile>`: 指定 Mopheus CLI Profile。
- `-o, --output <path.html>`: 指定 HTML 报告输出路径。
- `--force`: 强制全量重新抓取并更新已完成的历史任务。
- `--open`: 生成后自动在默认浏览器中打开 HTML 报告。

### 分步执行
1. **增量采集裸数据**：
   ```bash
   python3 ~/.gemini/config/skills/mopheus-agent-task-visualizer/scripts/collect_raw_tasks.py -w dev
   ```
2. **清洗加工 Stage 数据**：
   ```bash
   python3 ~/.gemini/config/skills/mopheus-agent-task-visualizer/scripts/process_stage_metrics.py -w dev
   ```
3. **渲染 HTML 报告**：
   ```bash
   python3 ~/.gemini/config/skills/mopheus-agent-task-visualizer/scripts/generate_html_report.py -w dev
   ```

---

## 持久化与跨 Agent Task 共享存储设计

为支持后续在 Mopheus 平台中配置**定时调度智能体（Scheduled Agent / Cron Job）**周期性执行本技能，状态文件与 Stage 数据支持灵活的跨任务共享存储定位策略（按优先级解析）：

1. **CLI 参数显式覆盖**：`--data-dir <custom_shared_dir>`
2. **环境变量统一定义**：`MOPHEUS_ANALYTICS_DATA_DIR` 或 `MOPHEUS_DATA_DIR`
3. **默认跨任务共享目录**：`~/.mopheus/analytics/<workspace>/`
   - *说明*：Mopheus Daemon 运行每个 Agent Task 时，会为该 Task 分配临时隔离的工作目录（如 `/workdir/<ws>/<task_id>/`），任务完结后临时目录会被回收。而宿主机的 `~/.mopheus/` 目录属于持久层，因此无论今天还是明天由哪个智能体执行，均能稳定命中同一份 `state_record.json` 并在其基础上做增量同步。

## 输出产物说明

- **增量状态持久化文件**：`$DATA_DIR/state_record.json`
- **Stage 结构化指标数据**：`$DATA_DIR/stage_tasks.json`
- **原始任务与转录缓存**：`$DATA_DIR/raw_tasks/<task_id>.json`
- **可视化看板报告**：`$DATA_DIR/agent_task_report_<workspace>_<YYYYMMDD>.html`
