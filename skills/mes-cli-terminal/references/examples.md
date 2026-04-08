# MES CLI Examples and Heuristics

## Parameter heuristics

- `support /plan/{id}` => `type=1`, `rid={id}`
- `support /service/request/{id}` => `type=0`, `rid={id}`
- 用户说“我的”优先转换为显式人员参数（如 `--executor-id <uid>` 或 `--person-id <uid>`）
- 用户说“本月/上月/上周”优先映射 `--range`
- 给了精确日期优先 `--from --to` 或 `--start --end`
- 默认输出：查询用 `-o json`；写操作可先文本 + `--dry-run`

## NL -> command templates

### 1) 登录与会话

- “我现在登录了吗”  
  `mes auth status`
- “浏览器登录 dev 环境”  
  `mes auth login --web --env dev`
- “切换到 profile foo”  
  `mes auth switch --profile foo`

### 2) 报工（高频）

- “在这个计划链接上报今天 8 小时”  
  `mes statistics add --from-url "<plan-url>" --start "2026-03-24 09:00:00" --end "2026-03-24 18:00:00" --hours 8 --remark "..." --dry-run`
- “查我本月工时”  
  `mes -o json statistics list --range thisMonth --executor-id <uid>`
- “审批 101,102 通过”  
  `mes statistics review --ids 101,102 --status approved`

### 3) 服务请求

- “列出我的未关闭工单”  
  `mes -o json service request list --status 1 --person-id <uid>`
- “搜索标题包含 'Oracle' 的服务请求”  
  `mes -o json service request list --title "Oracle"`
- “看工单 123 详情”  
  `mes -o json service request view 123`
- “给工单 123 回复：已处理”  
  `mes service request reply 123 --text "已处理，等待验证" --dry-run`
- “按工单 123 报工 2 小时”  
  `mes service request report 123 --start "2026-03-24 14:00:00" --end "2026-03-24 16:00:00" --hours 2 --dry-run`

### 4) 计划任务

- “查我的计划”  
  `mes -o json plan list --executor-id <uid>`
- “结束计划 16570”  
  `mes plan end 16570`
- “新建计划（单处理人）”  
  `mes plan create --title “...” --check-type 1 --company-id 91 --acc-id “20260301345” --start-date “2026-03-24 09:00:00” --end-date “2026-03-24 18:00:00” --executor-id 11111 --executor-name “张三” --task-time “8”`

### 5) 文章与合同

- “查知识库待审核数”  
  `mes article review-count`
- “按关键词查合同”  
  `mes -o json contract list --search "Oracle"`

- "按合同编号查询合同子项"  
  `mes -o json contract list-items --contract-num "00032597"`
- "查某合同下实际工时为0的子项"  
  `mes contract list-items --contract-id 12345 --actual-hours-zero-only`
### 6) 管理看板

- "看交付统计汇总（工程师 123）"  
  `mes dashboard delivery summary --executor-id 123`
- "看工作情况客户工时（上月）"  
  `mes -o json dashboard work --executor-id 123 --range lastMonth`
- "看周报列表（某人+某天）"  
  `mes -o json dashboard weeklyReport 20260306 张三`
- "查报工质量" / "查看报工评分" / "本月报工质量怎么样" / "团队报工质量评分"  
  `mes -o json dashboard score list --month 2026-04`  
  可加 `--executor-id <uid>` 或 `--team-id <tid>` 筛选
- "查看评分规则"  
  `mes dashboard score prompt`

> ⚠️ **区分**：`dashboard score` = 报工质量评分（结果评级）；`statistics review-stats` = 审批工时统计（通过/拒绝统计）。"报工质量"永远走 `dashboard score`，不走 `statistics review-stats`。

### 7) 用户搜索

- "查询用户张三的 ID"  
  `mes util search-user 张三 -o json`
- "搜索用户名包含 '张' 的用户"  
  `mes util search-user 张`

### 8)URL 解析

- “这个 support 链接对应什么类型和 id”  
  `mes -o json util parse-support-url "https://support.enmotech.com/plan/16570"`

## Realistic dialogue examples

以下示例可直接作为 agent 的对话模板，优先按“先总结 -> 再执行命令 -> 回传结果”的节奏。

### Example A: 先总结今天工作，再在计划任务下报工

**用户**  
上面是我今天的工作内容，请先总结，然后使用mes cli帮我在计划任务下https://support.enmotech.com/plan/16570 完成今天的报工，时间从8点到18点，工时9小时。报工工作内容尽量详细，突出服务价值，字数不少于20字

**Agent should do**

1. 先把“上面工作内容”总结成 1 段报工文案（不少于 20 字）。
2. 命令先 dry-run，再确认提交。
3. 计划链接优先用 `--from-url`，必要时补 `--acc-id`。

**Command**
`mes statistics add --from-url "https://support.enmotech.com/plan/16570" --start "2026-03-24 08:00:00" --end "2026-03-24 18:00:00" --hours 9 --remark "今日完成巡检与问题处置闭环，输出可复用操作建议并同步风险，显著提升服务稳定性与响应效率。" --dry-run`

提交时去掉 `--dry-run`。

### Example B: 在服务请求下按回复内容自动归纳报工

**用户**  
请使用mes cli在服务请求https://support.enmotech.com/service/request/5183 上完成今天报工，处理时长4小时，从10点到17点，报工工作内容请直接总结服务请求上的回复内容、状态和进度

**Agent should do**

1. 先读取工单详情/回复，提炼状态、进度、关键动作。
2. 用 `service request report` 生成并提交报工（支持 dry-run）。

**Command**
`mes service request report "https://support.enmotech.com/service/request/5183" --start "2026-03-24 10:00:00" --end "2026-03-24 17:00:00" --hours 4 --dry-run`

提交时去掉 `--dry-run`。

### Example C: 查上周所有人周报并总结重点

**用户**  
请使用mes cli查看上周所有人的周报，然后总结升级的事项和需要我关注的事项

**Agent should do**

1. 先查询列表（上周一到上周日）。
2. 必要时逐条 `view` 拉正文。
3. 输出两段总结：`升级事项`、`需要关注`。

**Command (list)**
`mes -o json dashboard weeklyReport list --type WEEKLY --period-from "2026-03-16" --period-to "2026-03-22" --page 1 --page-size 100`

**Command (view each id)**
`mes -o json dashboard weeklyReport view <id>`

### Example D: 查询我受理的未关闭服务请求

**用户**  
现在MES上我受理的未关闭的服务请求有哪些

**Command**
`mes -o json service request list --status 1 --person-id <uid>`

### Example E: 查询指定服务请求的问题与进度

**用户**  
ID为5184的服务请求，具体是什么问题？，现在处理进度是什么

**Command**
`mes -o json service request view 5184`

**Agent should return**

- 问题摘要（title/核心现象）
- 当前状态（status）
- 当前进度（progress）
- 最近关键回复摘要（如有）

### Example F: 给服务请求回复

**用户**  
请给ID为5184的服务请求，回复"xxxx"

**Command (preview)**
`mes service request reply 5184 --text "xxxx" --dry-run`

确认后提交（去掉 `--dry-run`）：
`mes service request reply 5184 --text "xxxx"`

### Example G: 查询我负责的进行中计划任务

**用户**  
MES上我负责的进行中的计划任务有哪些？

**Command**
`mes -o json plan list --executor-id <uid> --status 1`

### Example H: 查询我负责的超期计划任务

**用户**  
MES上我负责的超期中的计划任务有哪些？

**Agent should do**

1. 先拉取“我负责 + 进行中”计划。
2. 以 `endDate < 今天` 进行本地筛选并输出超期列表。

**Command**
`mes -o json plan list --executor-id <uid> --status 1 --page 1 --page-size 200`

### Example I: 关闭计划任务

**用户**  
关闭ID为11678的计划任务

**Command**
`mes plan end 11678`

如果用户要求先确认，可先执行查看：
`mes -o json plan view 11678`
