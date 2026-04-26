---
name: mes-work-report
description: >
  生成团队或大区的 MES 报工统计分析 HTML 可视化看板。
  当用户需要查看某个团队（如东西大区4部、东西大区2部）或某个大区（如东西大区、南北大区）的报工工时统计、满勤率、加班、不达标人员等汇总信息时触发，
  尤其是需要将结果以可视化报告或HTML看板形式输出时。

  触发关键词：报工统计报告、报工看板、工时报表、各团队报工对比、大区报工分析、
  周报统计、满勤率、工时不达标、加班统计、报工汇总HTML、生成报工报告、生成看板、
  报工周报、团队周报、大区周报。
---

# MES 报工统计报告生成器

## 架构概述

本 Skill 采用 **混合方案**：

1. **`scripts/fetch_data.py`** — 纯数据拉取层，调用 `mes` CLI 拉取所有原始数据，输出 JSON
2. **Agent（本 SKILL.md）** — 报告编排层，读取 JSON 数据，按 11 章节结构生成完整 HTML

```
用户请求 → Agent 读 SKILL.md → 执行 fetch_data.py 拉取 JSON → Agent 读取 JSON → 生成 HTML
```

> Agent 负责全部 HTML 生成逻辑，不依赖硬编码模板。新增/修改章节只需改本文件。

## 团队 ID 查找

读取 `references/team_ids.md` 获取团队名称 → ID 的映射。

**常用 ID 速查：**
- 东西大区1部=2，东西大区2部=3，东西大区4部=23，东西大区5部=19
- 南北大区2部=25，南北大区4部=11，南北大区5部=22
- 东西大区（整体）=96，南北大区（整体）=94

未知团队 ID 时执行：`mes -o json util list-teams` 并搜索。

## 工作流

### Step 0：环境检查

确认 Python 和 mes CLI 可用：
```bash
which python3 && python3 --version
mes auth status
```

若未登录，提示用户先执行 `mes auth login --web`。

### Step 1：解析请求

从用户请求中提取：
- **目标范围**：单团队 or 多团队 or 整个大区（多个团队对比）
- **时间范围**：本周/上周/本月/具体日期，转换为 `--from YYYY-MM-DD --to YYYY-MM-DD`

**日期推算规则：**
- "本周"：本周一 ~ 今天（或本周五）
- "上周"：上周一 ~ 上周五
- "本月"：本月1日 ~ 今天
- 直接说"4.14到4.17"：转换为 2026-04-14 ~ 2026-04-17

**注意：** 若用户要求"整个东西大区"对比，分别用 team-id=2,3,23,19（四个服务团队），而**不是** team-id=96（大区整体，无法分团队对比）。

### Step 2：执行数据拉取

调用 `fetch_data.py` 拉取全部数据（JSON 输出）：

```bash
python3 ~/.workbuddy/skills/mes-work-report/scripts/fetch_data.py \
  --team-ids 2,3,23,19 \
  --team-names "东西大区1部,东西大区2部,东西大区4部,东西大区5部" \
  --from 2026-04-21 \
  --to 2026-04-23 \
  --fetch-extra \
  --output /tmp/mes_report_data.json
```

**参数说明：**
- `--team-id` / `--team-ids`：目标团队 ID（必填二选一）
- `--team-name` / `--team-names`：对应团队名称
- `--from` / `--to`：日期范围（必填）
- `--std-hours-per-day`：每日标准工时，默认 8
- `--fetch-extra`：拉取额外数据（文档、评分、服务请求、服务统计、工时分布表）
- `--output`：输出 JSON 文件路径

**JSON 输出结构：**
```json
{
  "meta": {
    "fromDate": "2026-04-21",
    "toDate": "2026-04-23",
    "workDays": 3,
    "workDates": ["2026-04-21", "2026-04-22", "2026-04-23"],
    "stdHoursPerDay": 8,
    "stdHoursTotal": 24,
    "teamNames": ["东西大区1部", "东西大区2部", "东西大区4部", "东西大区5部"]
  },
  "teams": [
    {
      "teamId": 23,
      "teamName": "东西大区4部",
      "memberCount": 20,
      "reportedMemberCount": 18,
      "totalHours": 432.5,
      "avgHours": 24.03,
      "fullCount": 15,
      "fullRate": 83.3,
      "overtimeHours": 48.5,
      "preHours": 320.0,
      "afterHours": 88.5,
      "internalHours": 24.0,
      "docCount": 5,
      "avgScore": 92.3,
      "members": [
        {
          "name": "张三",
          "userId": 12345,
          "city": "深圳",
          "total": 32.0,
          "pre": 24.0,
          "after": 6.0,
          "internal": 2.0,
          "overtime": 8.0,
          "doc": 1,
          "score": 95,
          "recordCount": 12,
          "daily": {"2026-04-21": 10.5, "2026-04-22": 8.0, "2026-04-23": 13.5},
          "shortage": 0,
          "full": true
        }
      ],
      "unreportedMembers": [
        {"name": "李四", "userId": 67890}
      ]
    }
  ],
  "articles": [...],
  "scores": [...],
  "serviceRequests": [...],
  "serviceStats": {...},
  "taskTable": [...]
}
```

### Step 3：读取 JSON 数据

用 `read_file` 读取输出的 JSON 文件，解析数据结构。

### Step 4：生成 HTML 报告

Agent 根据 JSON 数据，按以下 11 个章节生成完整 HTML 文件。**所有 HTML 由 Agent 在本步骤中生成，不依赖预编码模板。**

#### HTML 整体结构

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{报告标题}</title>
  <style>
    /* 全局样式：暗色主题、卡片布局、表格样式、响应式 */
    /* 参考风格：深色背景 #1a1a2e / #16213e，卡片 #0f3460，强调色 #e94560 / #00d4ff */
    /* 表格：斑马纹、圆角、hover 高亮 */
    /* 章节标题：带 emoji 图标，大号字体，底部色条 */
    /* 热力图：cell 用绿色深浅表示工时（8h=深绿，0h=灰色） */
    /* 进度条：渐变色条表示达标率 */
  </style>
</head>
<body>
  <!-- 报告头部：标题、日期范围、工作日天数、生成时间 -->
  <!-- Section 1~11 -->
  <!-- 报告尾部：免责声明 -->
</body>
</html>
```

#### 设计规范

- **配色**：暗色主题，主背景 `#1a1a2e`，卡片 `#16213e`，强调色 `#e94560`（红）/ `#00d4ff`（蓝）
- **布局**：单列居中，最大宽度 1200px，卡片圆角 8px，阴影 `0 4px 6px rgba(0,0,0,0.3)`
- **表格**：宽度 100%，斑马纹（奇数行 `rgba(255,255,255,0.05)`），表头 `#0f3460`，hover 高亮
- **数值高亮**：满勤率 ≥ 80% 显示绿色，60%-80% 显示橙色，< 60% 显示红色
- **热力图**：0h = `#2d2d2d`，1-4h = `#3d6b3d`，5-7h = `#5a9e5a`，≥8h = `#2ecc71`
- **响应式**：表格水平滚动，卡片自适应

---

#### 第一章：团队核心指标对比

**数据来源**：`teams[*]` 顶层字段

**展示内容**：多团队并排卡片 + 对比表格

| 字段 | 说明 |
|------|------|
| teamName | 团队名称 |
| memberCount | 团队真实人数 |
| reportedMemberCount | 已报工人数 |
| totalHours | 总工时 |
| avgHours | 人均工时（已报工人员） |
| fullCount / fullRate | 满勤人数 / 满勤率 |
| overtimeHours | 加班工时 |
| preHours / afterHours / internalHours | 售前/售后/内部工时 |
| docCount | 文档数 |
| avgScore | 平均报工质量分 |

**视觉**：
- 每个团队一张卡片，包含：团队名、人数、总工时（大号）、满勤率（进度条）
- 下方对比表格，横向对比所有团队

---

#### 第二章：成员工时明细 & 每日工时

**数据来源**：`teams[*].members[]`

**展示内容**：每个团队一个子节，内含成员表格 + 每日工时热力图

**成员表格列**：
| 列 | 说明 |
|----|------|
| 姓名 | name |
| 城市 | city |
| 总工时 | total |
| 售前/售后/内部 | pre / after / internal |
| 加班 | overtime |
| 报工条数 | recordCount |
| 评分 | score |
| 不足工时 | shortage（>0 时红色显示） |

**每日工时热力图**：
- 列 = 工作日（`meta.workDates`）
- 行 = 成员（按总工时降序）
- 单元格颜色 = 工时热力图配色
- 悬停显示具体数值

---

#### 第三章：报工不足人员分析

**数据来源**：`teams[*].members[]`（筛选 `full == false`）

**展示内容**：
- 汇总卡片：各团队不达标人数
- 详情表格：

| 列 | 说明 |
|----|------|
| 姓名 | name |
| 团队 | teamName |
| 实际工时 | total |
| 标准工时 | stdHoursTotal |
| 不足工时 | shortage |
| 不足天数 | daily 中工时 < 8 的天数 |

---

#### 第四章：文档编写统计

**数据来源**：`articles[]`

**展示内容**：
- 汇总卡片：总文档数、各团队文档数
- 表格：

| 列 | 说明 |
|----|------|
| 标题 | title |
| 作者 | author |
| 团队 | teamName |
| 创建时间 | createTime |

> 若 `articles` 为空，显示"本周期内暂无文档产出"。

---

#### 第五章：项目成本消耗分析（工时类型分布）

**数据来源**：`teams[*]` 的 `preHours` / `afterHours` / `internalHours`

**展示内容**：
- 各团队工时类型饼图或堆叠条形图
- 汇总表：团队 × 工时类型（售前POC / 售后服务 / 内部事项）
- 占比百分比

> Agent 可使用 CSS 实现简单条形图，或使用 Chart.js CDN 生成图表。

---

#### 第六章：报工质量分析

**数据来源**：`scores[]` + `teams[*].avgScore`

**展示内容**：
- 汇总卡片：各团队平均分
- 评分明细表：

| 列 | 说明 |
|----|------|
| 姓名 | executorName |
| 团队 | teamName |
| 评分 | score |
| 评级 | 根据 score 区间（≥95 优秀 / 85-94 良好 / 70-84 合格 / <70 待改进） |
| 建议 | suggestion（截断显示，hover 完整） |

> 若 `scores` 为空，显示"本周期暂无评分数据"。

---

#### 第七章：项目报工排名（各团队 TOP15）

**数据来源**：`teams[*].members[]`（按 `total` 降序）

**展示内容**：
- 每个团队 TOP15 成员工时排行
- 表格：

| 列 | 说明 |
|----|------|
| 排名 | 序号 |
| 姓名 | name |
| 总工时 | total |
| 占团队比 | total / team.totalHours |

---

#### 第八章：每人每周工作总结

**数据来源**：需要 Agent 补充拉取周报

**数据拉取命令**：
```bash
mes -o json dashboard weeklyReport --period-from {fromDate} --period-to {toDate} --type WEEKLY --page-size 50 > /tmp/weekly_reports.json
```

对返回的每条周报，执行 `view` 获取正文：
```bash
mes -o json dashboard weeklyReport view {id}
```

**展示内容**：
- 按团队分组
- 每人一张卡片：姓名 + 周报摘要（截取前 200 字）
- 点击可展开完整内容

> **注意**：此章节数据不在 `fetch_data.py` 的 JSON 中，需要 Agent 额外拉取。若周报数量多，只展示目标团队相关人员的周报。

---

#### 第九章：服务请求列表

**数据来源**：`serviceRequests[]`（已按团队成员范围筛选）

**展示内容**：
- 汇总卡片：总服务请求数、各团队服务请求数
- 表格：

| 列 | 说明 |
|----|------|
| ID | id |
| 标题 | title |
| 状态 | status（中文） |
| 等级 | type（P0-P5） |
| 负责人 | executorEmployeeName |
| 申报时间 | createdTime |
| 公司 | companyName |

> 状态映射：0=已提交, 1=处理中, 2=已关闭, 3=已归档, 4=待反馈, 5=业务已恢复

---

#### 第十章：综合评价

**数据来源**：综合 `teams[*]` 各项指标

**展示内容**：每个团队一张评价卡片，包含：

1. **总体评价**：根据满勤率、人均工时、质量评分综合生成一句话评价
   - 满勤率 ≥ 90% 且均分 ≥ 90："表现优异，报工规范、工时饱满"
   - 满勤率 70%-90%："整体良好，个别成员需关注"
   - 满勤率 < 70%："需重点关注，报工不足人员较多"
2. **亮点**：团队内工时排名前 3 的成员 + 文档产出较多者
3. **待改进**：报工不足人员（shortage > 0）名单
4. **服务统计**（若 `serviceStats` 存在）：待处理咨询、待处理工单、未关闭工单等

---

#### 第十一章：项目未报工分析

**数据来源**：`teams[*].unreportedMembers[]`

**展示内容**：
- 汇总卡片：各团队未报工人数
- 表格：

| 列 | 说明 |
|----|------|
| 姓名 | name |
| 团队 | teamName |
| userId | userId |

> 若所有团队均无未报工人员，显示"本周期所有团队成员已完成报工 ✅"。

---

### Step 5：输出文件

**文件命名**：`{大区或团队}_报工看板_{日期区间}.html`
- 示例：`东西大区4部报工看板_2026-04-21至04-23.html`
- 示例：`东西大区报工看板_2026-04-21至04-23.html`

**输出路径**：默认输出到当前工作空间。

### Step 6：展示结果

使用 `preview_url` 工具以 `file://` 路径打开 HTML 预览。

---

## 关键注意事项

1. **数据安全**：`fetch_data.py` 产出的临时 JSON 文件（`/tmp/mes_report_data.json`、`/tmp/weekly_reports.json`）在报告生成完成后**必须删除**。
2. **JSON 读取**：mes CLI 返回值可能是 dict 或 list，`fetch_data.py` 已做 `isinstance` 防御，Agent 处理时也需注意。
3. **大区报告**：用户说"东西大区"时，查 4 个子团队（2,3,23,19），而非整体大区 ID（96）。
4. **标准工时**：默认 8h/天，可通过 `--std-hours-per-day` 调整。
5. **依赖**：Python 3.10+、已登录的 `mes` CLI。
6. **周报拉取**（第八章）：这是唯一步骤需要 Agent 在 fetch_data.py 之外额外调用 mes 命令的章节。尽量控制周报拉取数量，避免请求过多。

---

## 踩坑经验

- `statistics list` / 日期字段名：返回记录中没有 `taskDate`，日期在 `start` 字段（如 "2026-04-23 08:00:00"），需取 `[:10]`
- `statistics list` / 分页结构：返回 `{list:[], hasNextPage, endRow, ...}`，不是 `{operateCallBackObj:...}`
- `article list` / 分页结构：返回 `{list:[], total}`，作者字段是 `employeeName`（非 `createdByName`），时间字段是 `createdTime`（非 `createTime`）
- `dashboard score list` / 分页结构：返回 `{operateCallBackObj:{list:[], hasNextPage}}`，需要两层解包
- `service request list` / 日期参数：用 `--start-time` / `--end-time`（非 `--from` / `--to`），且需指定 `--person-id` 筛选范围
- `service request list` / 返回结构：返回 `{list:[], total}`
