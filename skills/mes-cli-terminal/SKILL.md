---
name: mes-cli-terminal
description: Convert Chinese or natural-language MES requests into precise mes-cli commands in this repository. Use when users ask to login, report hours, manage service requests/plans/articles/contracts, query dashboard/weekly reports, or parse support URLs.
---

# MES CLI Terminal Skill

## Goal

把用户自然语言稳定地转换为可执行的 `mes` 命令，并在写操作场景下做到可预览、可确认。

## When to use

当用户提到以下任一意图时立即启用本技能：

- MES登录、切换账号、查看登录状态
- 报工、查工时、审批工时、工时日历/汇总
- 服务请求（工单）创建、回帖、恢复、编辑、报工
- 计划任务查询/创建/编辑/结束/删除
- MES文章或合同查询与维护
- MES管理看板（dashboard）查询、周报增删改查
- 给了 support 链接，需要提取 `type/rid`

## Hard rules

1. 只使用 `mes ...` 命令完成 MES 业务动作，不改用其他自造脚本。
2. 查询类强制使用 `mes -o json ...`。对于预期超过 20 行的多行结果，必须将输出重定向至临时文件并确保完整阅读全文后再提炼，严禁仅参看可能被截断的终端回显（truncated output/delta）。
3. 自动化/CI/Agent 无 TTY 场景，优先 `MES_NONINTERACTIVE=1`。
4. 写操作必须先展示将执行的命令；支持 `--dry-run` 时先 dry-run。
5. 不要求用户在聊天里粘贴 token；认证走 `mes auth login ...`。
6. 严禁臆造、填充或基于常见占位符（如张三、李四等）猜测缺失或因截断而无法直接读取的数据。提炼结果必须与真实回传字段严格对应。
7. 完成最终报告之后，必须删除用于重定向的临时文件，以减少信息泄露风险。

## Command-generation workflow

1. **识别意图域**
   - `auth | statistics | service | plan | article | contract | dashboard | util`
2. **抽取参数槽位**
   - 时间槽：`from/to` 或 `range`，以及 `start/end`
   - 对象槽：`id/rid/acc-id/company-id/executor-id/team-id`
   - 文本槽：`title/remark/search/content`
   - 输出槽：是否需要 JSON（通常是）
3. **缺参策略**
   - 查询命令：尽量给默认（如 `range thisMonth`、`page 1`）
   - 写命令：缺关键参数必须追问，或改为交互式命令
   - 无交互运行时不得依赖提示输入，必须补齐必填 flags
4. **执行策略**
   - 先给“将执行命令”
   - 有 `--dry-run` 的先 dry-run
   - 用户确认后再正式执行（同一命令去掉 `--dry-run`）
   - 查询类：当列表或详情可能产生长文本输出时，默认采用重定向临时文件方式并配合文件读取命令，以保证数据的完整性。
5. **结果回传**
   - JSON 输出下提炼关键字段（id、status、count、time、message）,永远尝试包含happen-time，created-time等时间相关关键字段
   - 出错时直接给可执行修复命令

## Non-interactive policy

- 推荐前缀：`MES_NONINTERACTIVE=1`
- 对 `mes statistics add`：在非交互模式必须显式提供  
  `--start --end --hours --remark` + 关联信息（`--from-url` 或 `--type + --rid`；必要时 `--acc-id`）
- 若用户给了 support 链接，优先：
  - `mes -o json util parse-support-url "<url>"`
  - 然后把结果映射到 `statistics add`

## Safety classification

**只读查询（可直接执行）**

- `auth status`
- `statistics list|calendar|summary|review-stats|related-hours`
- `service request list|view`
- `plan list|view`
- `article list|view|review-count`
- `contract list|view`
- `dashboard ...` 所有查询
- `util parse-support-url`

**写操作（先预览/确认）**

- `statistics add|update|delete|review|bonus`
- `service create|history create|request report|request reply|request recover|request edit`
- `plan create|save|edit|end|delete`
- `article save|delete|assign-reviewer|set-level|set-type`
- `dashboard weeklyReport create|update|delete`

## Reference Documents

The detailed parameter breakdown and interaction examples are large and depend on the specific command you are trying to execute. Please consult the following reference files based on your needs:

- **Command parameters and mappings:**  
  Read [references/parameters.md](references/parameters.md) when you need to know the specific flags, options, and parameter extraction rules for any given `mes` subcommand. This file includes the full command map and parameter completion rules.
- **Translation templates and examples:**  
  Read [references/examples.md](references/examples.md) when you need to map natural language to an actual command, understand parameter heuristics, or see realistic dialogue examples of Agent-User interactions.

## Missing-info checklist before write commands

- 是否有目标对象：`id/rid/from-url`
- 是否有时间：`start/end` 或 `period-from/period-to`
- 是否有工时/内容：`hours|remark|text|md/html`
- 是否有关系字段：`company-id/acc-id/executor-id/team-id`
- 是否需要先 dry-run：若支持，默认是

## Output style for agent responses

- **提供确切命令**：首先提供可直接执行的完整命令代码块。
- **简述执行依据**：简要说明最终选用该命令及其参数的逻辑。
- **落实安全原则**：针对存在风险的写操作命令，务必优先提供带 `--dry-run` 选项的预览版本，明确要求用户确认无误后再实际执行。
- **结构化结果展示**：严禁直接粘贴冗长原始 JSON 数据。提取 JSON 中的关键字段，并**优先采用 Markdown 表格格式**进行结构化呈现。
