# MES CLI Parameters Reference

## Full command map (no domain omissions)

- `mes auth`
  - `login`, `status`, `logout`, `switch`, `profile delete`
- `mes statistics`
  - `add`, `update`, `delete`, `review`, `review-stats`, `related-hours`, `bonus`, `list`, `calendar`, `summary`
- `mes service`
  - `create`
  - `history create`
  - `request list|view|report|reply|recover|edit`
- `mes plan`
  - `list`, `view`, `save`, `create`, `edit`, `end`, `delete`
- `mes article`
  - `list`, `view`, `save`, `delete`, `assign-reviewer`, `set-level`, `set-type`, `review-count`
- `mes contract`
  - `list`, `view`
- `mes dashboard`
  - `base`
  - `contract`
  - `service`, `service unclose|rate|request|trend`
  - `delivery`, `delivery summary`, `delivery contracts list`, `delivery contract-items`
  - `work`, `work customers list`
  - `score`, `score list`, `score prompt`
  - `weeklyReport`, `weeklyReport list|view|create|update|delete`
  - `city|team|level|skill|amount|age|task-table|task-treemap`
- `mes util`
  - `parse-support-url`
  - `search-user`
  - `search-company`

## Full parameter reference (agent-facing)

目标：让 agent 在不反复问用户的情况下尽量补齐参数。以下为按命令树整理的参数速查。

### Global flags (all commands)

- `-o, --output text|json`
- `--jq <expr>`（仅 JSON 输出时使用）
- `--template <go-template>`（仅 JSON 输出时使用）
- `--interactive`（强制交互）

### `mes auth`

- `auth login`
  - `--web`
  - `--device`
  - `--web-url <url>`
  - `--with-token <token>`
  - `--env prod|dev|local`
  - `--host <api-base-url>`
  - `--profile <name>`
- `auth status`
  - `--json`
- `auth logout`
  - `--profile <name>`
- `auth switch`
  - `--profile <name>`
- `auth profile delete [names...]`
  - 无专有 flags（不传 name 可交互）

### `mes statistics`

- `statistics add`
  - `--title`
  - `--type`（0=服务请求, 1=计划任务, 3=内部事项）
  - `--service-type`
  - `--rid`
  - `--company-id`
  - `--executor-id`
  - `--acc-id`
  - `--start`
  - `--end`
  - `--hours`
  - `--remark`
  - `--list-title`
  - `--from-url`
  - `--dry-run`
  - `--json`
- `statistics update <id>`
  - `--user-id`
  - `--calendar-from`, `--calendar-to`
  - `--patch-file`, `--patch-json`
  - `--task-time`
  - `--remark`
  - `--start`, `--end`
  - `--title`
  - `--executor-id`
  - `--rid`
  - `--acc-id`
  - `--company-id`
  - `--type`
  - `--service-type`
  - `--overtime-type`（`null|0|1|2`）
  - `--dry-run`
  - `--json`
- `statistics delete <id>`
  - `--json`
- `statistics review`
  - `--ids`
  - `--status approved|rejected`
  - `--json`
- `statistics review-stats`
  - `--from`, `--to`, `--range`
  - `--title`, `--remark`
  - `--company-id`, `--team-id`
  - `--acc-id`
  - `--executor-id`
  - `--service-type`
  - `--missing-acc`, `--missing-impl`
  - `--json`
- `statistics related-hours <faultId>`
  - `--json`
- `statistics bonus`
  - `--task-id`
  - `--fault-id`
  - `--amount`
  - `--json`
- `statistics list`
  - `--from`, `--to`, `--range`
  - `--title`, `--remark` (均支持关键词模糊搜索)
  - `--company-id`, `--team-id`
  - `--acc-id`
  - `--executor-id`
  - `--service-type`
  - `--review-status`, `--sign-status`
  - `--missing-acc`, `--missing-impl`
  - `--page`, `--page-size`
  - `--json`
- `statistics calendar`
  - `--from`, `--to`, `--range`
  - `--user-id`
  - `--company-id`
  - `--json`
- `statistics summary`
  - `--from`, `--to`, `--range`
  - `--user-id`
  - `--team-id`
  - `--work-city`
  - `--group-type`
  - `--json`

### `mes service`

- `service create`
  - `--title`
  - `--body-html` / `--body-html-file`（互斥）
  - `--attach-url`（可重复）
  - `--mode contract|asset`
  - `--company-id`
  - `--acc-id`
  - `--contract-id`
  - `--asset-id`
  - `--type`
  - `--recover-type`
  - `--menu-id`
  - `--team-id`
  - `--executor-id`
  - `--email`
  - `--phone`
  - `--external-plan-id`
  - `--json`
- `service history create`
  - `--title`
  - `--body-html` / `--body-html-file`（互斥）
  - `--prescription-html` / `--prescription-html-file`（互斥）
  - `--handle-over-time`（关键）
  - `--happen-time`（关键）
  - `--created-time`（关键）
  - `--attach-url`（可重复）
  - `--mode contract|asset`
  - `--company-id`
  - `--acc-id`
  - `--contract-id`
  - `--asset-id`
  - `--type`
  - `--recover-type`
  - `--menu-id`
  - `--team-id`（关键）
  - `--executor-id`（关键）
  - `--external-plan-id`
  - `--json`

### `mes service request` 字典

#### status 状态字典

`--status` 参数用于筛选服务请求的状态，支持数字/中文名称：

| 代码 | 状态描述 |
| ---- | -------- |
| -1   | 初始化 |
| 0    | 已提交 |
| 1    | 处理中 |
| 2    | 已关闭 |
| 3    | 已归档 |
| 4    | 待反馈 |
| 5    | 业务已恢复 |

#### type 等级字典

`--level`/`--min-level` 参数用于筛选服务请求的等级，支持数字/P0-P5：

| 代码 | 等级 | 描述 |
| ---- | ---- | ---- |
| 4 | P0 | 我方误操作致业务不可用 |
| 2 | P1 | 核心业务完全不可用（关键业务受影响）|
| 1 | P2 | 非核心业务完全不可用（非关键业务受到影响）|
| 0 | P3 | 部分业务模块不可用（一般故障不影响业务）|
| 3 | P4 | 咨询，业务暂未受影响（技术咨询）|
| 5 | P5 | 问题原因分析 |

- `service request list`
  - `--unclosed`
  - `--is-starred`
  - `--page`, `--page-size`
  - `--id`
  - `--level`
  - `--min-level`
  - `--status`（建议中文；兼容数字：已提交|处理中|已关闭|已归档|待反馈|已恢复 = 0|1|2|3|4|5）
  - `--company-id`
  - `--person-id`
  - `--menu-root-id`
  - `--start-time`, `--end-time`
  - `--title` (按标题关键词模糊搜索，支持部分匹配)
  - `--tags`
  - `--json`
  - **列表 JSON 语义**：`executorEmployeeName` = 当前负责人**真实姓名**；`executorName` 多为账号/昵称。按负责人聚合、筛选、对外展示时**优先** `executorEmployeeName`，缺省再回退 `executorName`。
- `service request view <id|url>`
  - `--json`
- `service request report <id|url>`
  - `--title`
  - `--acc-id`
  - `--company-id`
  - `--start`
  - `--end`
  - `--hours`
  - `--dry-run`
  - `--json`
- `service request reply <id|url>`
  - `--text`
  - `--internal`
  - `--dry-run`
  - `--json`
- `service request recover <id|url>`
  - `--happen-time`
  - `--recover-time`
  - `--recover-type`
  - `--dry-run`
  - `--json`
- `service request edit <id|url>`
  - `--append`
  - `--append-title`
  - `--append-body`
  - `--force`
  - `--dry-run`
  - `--json`

### `mes plan`

#### check-type 字典

`--check-type` 参数用于指定计划任务的类型，支持数字 0-6：

| 数字 | 中文类型 | 常见叫法/说明                    |
| ---- | -------- | -------------------------------- |
| 0    | 巡检     | 巡检、例行检查、定期检查         |
| 1    | 培训     | 培训、授课、技术分享             |
| 2    | 现场人天 | 现场人天、人天服务、按天计费     |
| 3    | 驻场     | 驻场、驻场服务、长期驻场         |
| 4    | 售前POC  | 售前POC、POC、售前验证、技术验证 |
| 5    | 维保     | 维保、维保服务、维护保障         |
| 6    | 内部事项 | 内部事项、内部事务、公司内部     |

**自然语言映射规则：**

当用户提到以下词汇时，映射到对应数字：

- "巡检"、"例行检查" → 0
- "培训"、"授课" → 1
- "现场人天"、"人天" → 2
- "驻场" → 3
- "售前POC"、"POC"、"售前验证" → 4
- "维保" → 5
- "内部事项"、"内部事务" → 6

#### status 状态字典

`--status` 参数用于筛选计划任务的状态，支持数字 0-3：

| 数字 | 状态描述 | 说明 |
| ---- | -------- | ----|
| 0    | 未开始   | 计划尚未开始执行 |
| 1    | 进行中   | 计划正在执行中 |
| 2    | 结束     | 计划已经结束完成 |
| 3    | 已逾期未结束 | 计划已超过结束日期但仍未结束 |

**自然语言映射规则：**

当用户提到以下词汇时，映射到对应数字：

- "未开始" → 0
- "进行中"、"执行中" → 1
- "结束"、"已结束" → 2
- "逾期"、"已逾期"、"超期" → 3

#### 子命令参数

- `plan list`
  - `--new-api`
  - `--page`, `--page-size`
  - `--title` (按标题关键词模糊搜索，支持部分匹配)
  - `--company-name`
  - `--company-id`
  - `--team-id`
  - `--executor-id`
  - `--check-type`
  - `--status`
  - `--range`
  - `--start-date`, `--end-date`
  - `--contract-id`
  - `--acc-id`
  - `--missing-acc`, `--missing-impl`
  - `--json`
- `plan view <id>`
  - `--json`
- `plan save`
  - `--body-file`
  - `--json`
- `plan create`
  - `--title`
  - `--company-id`（`check-type=6` 可自动）
  - `--check-type`
  - `--acc-id`
  - `--start-date`, `--end-date`
  - `--deliver`
  - `--ignore-weekend`
  - `--external-id`
  - `--executor-json`（与下一组二选一）
  - `--executor-id`, `--executor-name`, `--task-time`, `--remarks`
  - `--json`
- `plan edit <id>`
  - `--patch-file` / `--patch-json`
  - `--json`
- `plan end <id>`
  - `--score`
  - `--feedback`
  - `--json`
- `plan delete <id>`
  - `--json`

### `mes article`

- `article list`
  - `--mode manage|audit|my`
  - `--page`, `--page-size`
  - `--status`
  - `--created-by`
  - `--menu-id`
  - `--team-id`
  - `--search`
  - `--start-time`, `--end-time`
  - `--json`
- `article view <id>`
  - `--json`
- `article save`
  - `--body-file`
  - `--id`
  - `--title`
  - `--menu-id`
  - `--status`
  - `--type`
  - `--encrypt-level`
  - `--difficult-level`
  - `--source`
  - `--version`
  - `--platform`
  - `--brief`
  - `--evaluate`
  - `--fault-id`
  - `--tags`
  - `--content-md`
  - `--content-md-file`
  - `--content`
  - `--json`
- `article delete <id>`
  - `--json`
- `article assign-reviewer`
  - `--id`
  - `--reviewer-id`
  - `--json`
- `article set-level`
  - `--id`
  - `--level`
  - `--json`
- `article set-type`
  - `--id`
  - `--type`
  - `--json`
- `article review-count`
  - `--unclosed`
  - `--json`

### `mes contract`

- `contract list`
  - `--page`, `--page-size`
  - `--search`
  - `--owner-id`
  - `--type`
  - `--period-type`（默认 `0`，仅查询服务中/有效期内的合同；传空值可查询全部合同）
  - `--manager-id`
  - `--team-id`
  - `--start-time`, `--end-time`
  - `--json`
- `contract view <id>`
  - `--json`
- `contract list-items`
  - `--company-id` (optional)
  - `--contract-id` (optional)
  - `--contract-num` (optional)
  - `--item-type` - Filter by itemType, e.g. 一般维保
  - `--date-range-start`, `--date-range-end` - both item start and end must be in range
  - `--min-progress-ratio`, `--max-progress-ratio` - Filter by actualHours/planHour
  - `--actual-hours-zero-only` - Only items with actualHours == 0
  - `--page`, `--page-size`, `--all` - Pagination
  - `--json`

### `mes dashboard`

- 说明：`dashboard` 子命令多且参数较细，agent 需按以下高频参数优先补齐。
- 高频公共参数：
  - `--json`
  - 日期：`--from --to --range`
  - 人员：`--executor-id`
  - 分页：`--page --page-size`
- 重点子命令参数：
  - `dashboard delivery` / `delivery summary`：`--executor-id`
  - `dashboard delivery contracts list`：`--executor-id --expiring-only --last-service-date --never-delivered-only --date-range-start --date-range-end --include-expired --json`
  - `dashboard work`：`--executor-id --from/--to or --range --json`
  - `dashboard score` / `score list`：**报工质量评分入口**（非审批统计）。用于查询工程师/团队在某月的报工质量评分列表（包含得分、评级等）。与 `statistics review-stats`（审批通过/拒绝统计）完全不同：
    - **报工质量/评分** → `mes dashboard score list`
    - **审批工时统计** → `mes statistics review-stats`
    - 参数：`--month --team-id --executor-id --page --page-size --sort --truncate --no-truncate --limit --json`
  - `dashboard score prompt`：查看评分规则/提示词
  - `dashboard weeklyReport list`：`--search --created-by --creator --type --period-from --period-to --page --page-size --json`
  - `dashboard weeklyReport view <id>`：`--json`
  - `dashboard weeklyReport create`：`--type --period-from --period-to --md|--md-file|--html --json`
  - `dashboard weeklyReport update <id>`：`--type --period-from --period-to --md|--md-file|--html --json`
  - `dashboard weeklyReport delete <id>`：`--json`
  - `dashboard task-table`：`--from --to --range --json`
  - `dashboard task-treemap`：`--from --to --range --no-acc --service-type --service-account-id --acc-id --executor-id --json`

### `mes util`

- `util parse-support-url <url>`
  - 仅使用全局输出参数（`-o json` 推荐）
- `util search-user <keyword>`
  - 通过用户名/关键字搜索用户，返回 userID、userName、account，支持 `-o json` 输出
- `util search-company <keyword>`
  - 通过公司名称关键字搜索公司，返回 companyID、companyName，支持 `-o json` 输出

### Parameter completion rules for agent

- `service request list` 的 JSON：统计「负责人」用 `executorEmployeeName`（真实姓名），不要用 `executorName` 代替；后者可为登录名。
- 用户给 URL（plan/request）时，优先 `--from-url`，避免手工错填 `type/rid`。
- `statistics add` 若无交互必须带齐：`--start --end --hours --remark` + 关联参数。
- `service history create` 易漏：`--handle-over-time --happen-time --created-time --team-id --executor-id`。
- `plan create` 易漏：`--check-type --start-date --end-date` 和处理人信息。
- 周报 create/update 正文三选一：`--md` / `--md-file` / `--html`（避免同时给）。
- 查询场景默认 `-o json`；写场景默认先 `--dry-run`（若支持）。
