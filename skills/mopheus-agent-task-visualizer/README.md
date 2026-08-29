# Mopheus Agent Task Visualizer (Local Skill)

Mopheus Agent Task 数据深度统计与 HTML 交互式可视化看板生成技能。

---

## 特性亮点

- ⚡ **增量状态持久化**：基于 `state_record.json` 自动记录已终态历史任务，跨任务执行零重复拉取。
- 🧠 **Transcript 深度解析**：提取 Thinking 耗时/字符量、细分工具调用分布（`tool:Bash`, `tool:TaskCreate`, `tool:TaskUpdate`, `tool:WebFetch`, `tool:WebSearch` 等）及其成功/失败率与耗时。
- 📊 **Stage 数据分层**：纯脚本完成数据清洗与聚合（`stage_tasks.json`），秒级响应，零 LLM 裸数据 Token 消耗。
- 🎨 **单文件交互式 HTML 看板**：内嵌 Tailwind CSS 与 ECharts 图表，支持搜索、状态筛选、Agent 排行榜与逐条任务展开诊断。
- 🔄 **跨 Agent 稳定共享**：默认基于宿主机持久层 `~/.mopheus/analytics/<workspace>/`，支持不同定时智能体协同增量更新。

---

## 快速使用

```bash
# 一键生成过去 24 小时任务的可视化报告并在浏览器中打开
python3 scripts/run_visualizer.py -w dev --since-hours 24 --open

# 全量历史分析
python3 scripts/run_visualizer.py -w dev
```

---

## 目录结构与规范

```
mopheus-agent-task-visualizer/
├── SKILL.md                          # 技能主入口（Agent 识别规范）
├── README.md                         # 项目概览与开发说明（面向人类）
├── scripts/
│   ├── run_visualizer.py             # 一键执行入口
│   ├── collect_raw_tasks.py          # 增量原始采集
│   ├── process_stage_metrics.py      # Stage 数据加工与转录解析
│   ├── generate_html_report.py       # HTML 看板渲染
│   └── mopheus_client.py             # Mopheus API/CLI 自适应客户端
├── templates/
│   └── dashboard_template.html       # 响应式可视化看板模板
└── references/
    ├── storage_and_persistence.md    # 跨任务持久化与共享存储设计
    ├── state_schema.md               # state_record.json 规范
    └── stage_data_schema.md          # stage_tasks.json 数据字典
```
