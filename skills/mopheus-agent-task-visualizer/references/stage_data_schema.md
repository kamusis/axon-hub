# Stage Data Schema (`stage_tasks.json`)

## 目的
由 Python 脚本清洗并深度解析后的结构化数据，提供全维度指标聚合，用于直接驱动 HTML 看板渲染。

## 结构说明
- `meta`: 全局 KPI 概览（总数、成功率、耗时、Token、Thinking 总时长、工具调用总量）。
- `summary_by_agent`: 按执行智能体维度的统计聚合（负荷、成功率、平均耗时、平均思考、Token）。
- `summary_by_tool`: 按工具名称（如 `tool:Bash`, `tool:TaskCreate`, `tool:TaskUpdate`, `tool:WebFetch`, `tool:WebSearch`）聚合的调用量、成功/失败率与平均耗时。
- `timeline`: 每日/趋势维度的调用量与成功量。
- `tasks`: 清洗后的任务明细列表，包含每个任务的 Thinking 细分与 Tool 调用清单。
