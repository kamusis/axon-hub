# MES CLI Examples and Heuristics

## Parameter heuristics

- `support /plan/{id}` => `type=1`, `rid={id}`
- `support /service/request/{id}` => `type=0`, `rid={id}`
- 用户说"我的"优先转换为显式人员参数（如 `--executor-id <uid>` 或 `--person-id <uid>`）
- 用户说"本月/上月/上周"优先映射 `--range`
- 给了精确日期优先 `--from --to` 或 `--start --end`
- 默认输出：查询用 `-o json`；写操作可先文本 + `--dry-run`

## NL -> command templates

### 登录与会话

- "我现在登录了吗"  
  `mes auth status`
- "浏览器登录 dev 环境"  
  `mes auth login --web --env dev`
- "切换到 profile foo"  
  `mes auth switch --profile foo`

### 报工（高频）

- "在这个计划链接上报今天 8 小时"  
  `mes statistics add --from-url "<plan-url>" --start "2026-03-24 09:00:00" --end "2026-03-24 18:00:00" --hours 8 --remark "..." --dry-run`
- "查我本月工时"  
  `mes -o json statistics list --range thisMonth --executor-id <uid>`
- "审批 101,102 通过"  
  `mes statistics review --ids 101,102 --status approved`

### 服务请求

- "列出我的未关闭服务请求"  
  `mes -o json service request list --status 1 --person-id <uid>`
- "搜索标题包含 'Oracle' 的服务请求"  
  `mes -o json service request list Oracle`  
  （等效于 `mes -o json service request list --title "Oracle"`）
- "看服务请求 123 详情，并列出附件列表"  
  `mes service request view 123`
- "用 JSON 看服务请求 123 详情（含完整附件信息）"  
  `mes -o json service request view 123`
- "给服务请求 123 回复：已处理"  
  `mes service request reply 123 --text "已处理，等待验证" --dry-run`

- "服务请求 123 附件太多，我先看看有哪些"  
  `mes service request view 123`  
  （输出会显示附件列表：`[1] 日志文件.log (pdf, 2.3MB)  id=6035`）
- "下载服务请求 123 的指定附件（用 view 中显示的 id）"  
  `mes service request download 123 --file-id 6035`
- "下载服务请求 123 的全部附件（默认行为）"  
  `mes service request download 123`
- "客户上传了报错截图，我下载下来分析"  
  `mes service request download 123 --file-id 6035 -O ~/Downloads/客户日志.pdf`
- "下载到指定目录"  
  `mes service request download 123 -O ~/Downloads/`

- "我回复时附上本地排查截图"  
  `mes service request reply 123 --text "排查截图见附件" --file /home/user/error.png --dry-run`  
  提交时去掉 `--dry-run`。
- "故障已处理，回复客户并附上服务报告 PDF"  
  `mes service request reply 123 --text "故障已处理完毕，详见附件服务报告" --file ./服务报告.pdf`
- "我需要内部回复（不让客户看到附件），附上内部分析文档"  
  `mes service request reply 123 --text "内部分析：根因是 XXX" --file ./分析.doc --internal`

> ⚠️ **已关闭的服务请求上传附件**：必须加 `--internal`，否则报"您没有资源权限"。

- "帮我创建一个服务请求，标题是 '数据库连接失败'"
  `mes service create --title "数据库连接失败" --company-id 4 --acc-id "2025103112176" --type 3 --body-md "### 问题背景\n\n今天早上 9 点开始连接不上数据库。\n\n### 报错信息\n\n\`\`\`\n[错误提示]\n\`\`\`" --dry-run`

### 实施计划

- "查我的实施计划"  
  `mes -o json plan list --executor-id <uid>`
- "查标题含关键词的实施计划"  
  `mes -o json plan list 2025驻场`  
  （等效于 `mes -o json plan list --title "2025驻场"`）
- "结束实施计划 16570"  
  `mes plan end 16570`
- "查实施计划 16570 详情"  
  `mes -o json plan view 16570`

### 合同

- “按关键词查合同”  
  `mes -o json contract list Oracle`  
  （等效于 `mes -o json contract list --search "Oracle"`）
- "按合同编号查询合同子项"  
  `mes -o json contract list-items --contract-num "00032597"`
- "查某合同下实际工时为0的子项"  
  `mes contract list-items --contract-id 12345 --actual-hours-zero-only`
- "查合同 12345 详情"  
  `mes -o json contract view 12345`

### 知识库与文章

- “查知识库待审核数”
  `mes article review-count`
- “保存一篇知识库文章”
  `mes article create --title “Oracle 巡检指南” --content-md “## 巡检项\n\n1. 检查表空间使用率” --tags “oracle,巡检” --menu-id 506`
- “保存知识库文章（正文从文件读取）”
  `mes article create --title “Oracle 巡检指南” --content-md-file ./report.md --tags “oracle,巡检”`
- “仅更新文章 123 的标题”
  `mes article update --id 123 --title “新标题”`

  **Heuristics & Guidance**:
  - **分类映射**:
    - `menuId: 505` 对应 `dict: “其他”` (通用架构/流程类)。
    - `menuId: 506` 对应 `dict: “数据库/Oracle”` (Oracle 专门技术类)。
    - `menuId: 508` 对应 `dict: “数据库/PostgreSQL”` (PostgreSQL 专门技术类)。
    - `menuId: 501` 对应 `dict: “zData”` (zData 产品文档)。

### 服务报告（关联服务请求）

服务报告是 type=7 的知识库文章，自动设置 encrypt-level=INTERNAL 和 menu-id=505，仅内部可见。

- “为服务请求 5183 编写服务报告”
  `mes article create --title “服务请求 5183 处理报告” --content-md “## 问题摘要\n\n...” --tags “服务报告” --sr-id 5183`
- “为服务请求 5183 编写服务报告（正文从文件读取）”
  `mes article create --title “服务请求 5183 处理报告” --content-md-file ./report.md --tags “服务报告” --sr-id 5183`
- “为已有关联文章的服务请求 456 更新服务报告”
  `mes article update --id 123 --sr-id 456 --content-md “## 补充内容\n\n...”`

### 管理看板

- "看交付统计汇总（工程师 123）"  
  `mes dashboard delivery summary --executor-id 123`
- "看工作情况客户工时（上月）"  
  `mes -o json dashboard work --executor-id 123 --range lastMonth`
- "看周报列表（某人+某天）"  
  `mes -o json dashboard weeklyReport --period-from 2026-03-06 --period-to 2026-03-06 --creator 张三`
- "搜索含关键词的周报"  
  `mes -o json dashboard weeklyReport list 磐维`  
  （等效于 `mes -o json dashboard weeklyReport list --search "磐维"`）
- "查报工质量" / "查看报工评分" / "本月报工质量怎么样" / "团队报工质量评分"  
  `mes -o json dashboard score list --month 2026-04`  
  可加 `--executor-id <uid>` 或 `--team-id <tid>` 筛选
- "查看评分规则"  
  `mes dashboard score prompt`

> ⚠️ **区分**：`dashboard score` = 报工质量评分（结果评级）；`statistics review-stats` = 审批工时统计（通过/拒绝统计）。"报工质量"永远走 `dashboard score`，不走 `statistics review-stats`。

### 用户搜索

- "查询用户张三的 ID"  
  `mes util search-user 张三 -o json`
- "搜索用户名包含 '张' 的用户"  
  `mes util search-user 张`

### URL 解析

- "这个 support 链接对应什么类型和 id"  
  `mes -o json util parse-support-url "https://support.enmotech.com/plan/16570"`

### 对象存储与图片上传

- "上传这张本地图片到 MES"
  `mes oss upload image /path/to/img.png`
- "上传图片并查看大小详情"
  `mes -o json oss upload image img.jpg`

> ⚠️ 场景：当用户需要在回复服务请求或保存文档时嵌入本地图片，请先使用 `oss upload image` 获取 URL，再将 URL 填入正文。目前**仅支持图片**，不支持其他文件。

### 发现链 (Discovery Chain): 从公司名找实施计划

- "找到 '云和恩墨虚拟客户' 公司的合同子项"
  1. 查找公司 ID:
     `mes util search-company "云和恩墨虚拟客户" -o json`
     _(获取 `companies[].ID`: 861)_
  2. 列出该公司下的合同:
     `mes contract list --company-id 861 -o json`
     _(获取合同 `id`: 2085, 合同编号 `contractNum`: 00032480)_
  3. 列出合同下的子项:
     `mes contract list-items --contract-id 2085 -o json`
     _(获取子项 `itemId`: 2026040312741)_
  4. 列出合同子项下的实施计划:
     `mes plan list --acc-id 2026040312741 -o json`
     _(获取计划 `planId`: 16905)_

  **Mappings & Heuristics**:
  - **Company Search**: `ID` -> `--company-id`
  - **Contract List**: `id` -> `--contract-id`; `contractNum` -> `--contract-num` (exact match search)
  - **Items List**: `itemId` -> `--acc-id` (used in `service create`)
  - **ID Formats**: `contractID` (id) is usually 4-digit numeric (e.g. 2085); `itemID` (itemId) is long numeric (e.g. 2026040312741).

## 真实场景示例

以下示例可直接作为 agent 的对话模板，优先按"先总结 -> 再执行命令 -> 回传结果"的节奏。

### 从截图创建服务请求（同时将截图包含在服务请求中）

**用户**  
解读这些截图，然后上传，之后创建一个服务请求（用户公司ID：XX，合同子项ID：XX），标题根据截图内容由你来确定，服务请求正文里应该包含所有截图的URL

**Agent should do**

1. 先读取截图内容，提炼关键信息。
2. 上传截图，获取到截图的URL。
3. 用 `service create` 生成并提交服务请求（支持 dry-run）。

**Command**

`mes oss upload image /path/to/img.png`

`mes service create --title "SQL 执行速度较慢分析" --company-id 4 --acc-id "2025103112176" --type 3 --body-md "## 问题描述\n\n数据库存储过程中的一条 SQL 执行速度较慢（约1分钟），客户要求分析是否正常。\n\n## 分析结论\n\n该 SQL 走了索引（LINE_NO字段），但返回行数和数据量仍然很大：\n\n- LINE_NO 字段 distinct value 仅 26 个，选择性差\n- 索引访问预估 944MB，全表访问预估 34.75GB\n- 走索引比全表快约 36 倍，已为最优执行计划\n- 执行 1 分钟左右属于正常现象，非索引问题\n\n## 截图\n\n![](https://oss-esprod-public.enmotech.com/image/base/uploaded-image.jpg)" --dry-run`

提交时去掉 `--dry-run`。

### 自动归纳服务请求内容并报工

**用户**  
请使用mes cli解读服务请求https://support.enmotech.com/service/request/5183 的内容，然后在该服务请求下创建报工，处理时长4小时，从10点到17点，报工工作内容请直接总结服务请求上的回复内容、状态和进度

**Agent should do**

1. 先读取服务请求详情（`mes service request view <id>`），提炼状态、进度、关键动作。
2. 用 `mes statistics add --type 0 --rid <id>` 报工（支持 dry-run）。

**Command**

`mes statistics add --type 0 --rid 5183 --start "2026-03-24 10:00:00" --end "2026-03-24 17:00:00" --hours 4 --remark "服务请求处理：当前状态xxx，进度xxx。今日主要跟进回复：1) xxx。" --dry-run`

提交时去掉 `--dry-run`。

### 先总结今天工作，再在实施计划下报工

**用户**  
上面是我今天的工作内容，请先总结，然后使用mes cli帮我在实施计划下https://support.enmotech.com/plan/16570 完成今天的报工，时间从8点到18点，工时9小时。报工工作内容尽量详细，突出服务价值，字数不少于20字

**Agent should do**

1. 先把"上面工作内容"总结成 1 段报工文案（不少于 20 字）。
2. 命令先 dry-run，再确认提交。
3. 计划链接优先用 `--from-url`，必要时补 `--acc-id`。

**Command**

`mes statistics add --from-url "https://support.enmotech.com/plan/16570" --start "2026-03-24 08:00:00" --end "2026-03-24 18:00:00" --hours 9 --remark "今日完成巡检与问题处置闭环，输出可复用操作建议并同步风险，显著提升服务稳定性与响应效率。" --dry-run`

提交时去掉 `--dry-run`。

### 查询我受理的未关闭服务请求

**用户**  
现在MES上我受理的未关闭的服务请求有哪些

**Command**

`mes -o json service request list --status 1 --person-id <uid>`

### 查询指定服务请求的问题与进度

**用户**  
ID为5184的服务请求，具体是什么问题？，现在处理进度是什么

**Command**

`mes -o json service request view 5184`

**Agent should return**

- 问题摘要（title/核心现象）
- 当前状态（status）
- 当前进度（progress）
- 最近关键回复摘要（如有）

### 给服务请求回复

**用户**  
请给ID为5184的服务请求，回复"xxxx"

**Command (preview)**

`mes service request reply 5184 --text "xxxx" --dry-run`

确认后提交（去掉 `--dry-run`）：

`mes service request reply 5184 --text "xxxx"`

### 查询我负责的进行中实施计划

**用户**  
MES上我负责的进行中的实施计划有哪些？

**Command**

`mes -o json plan list --executor-id <uid> --status 1`

### 查询我负责的超期实施计划

**用户**  
MES上我负责的超期中的实施计划有哪些？

**Agent should do**

1. 先拉取"我负责 + 进行中"计划。
2. 以 `endDate < 今天` 进行本地筛选并输出超期列表。

**Command**

`mes -o json plan list --executor-id <uid> --status 1 --page 1 --page-size 200`

### 关闭实施计划

**用户**  
关闭ID为11678的实施计划

**Command**

`mes plan end 11678`

如果用户要求先确认，可先执行查看：

`mes -o json plan view 11678`

### 查上周所有人周报并总结重点

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
