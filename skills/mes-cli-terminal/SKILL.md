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
2. 每一次业务动作，通常只涉及到一条mes命令，避免以下场景：当用户请求查询某个合同信息时，先使用关键字查询客户名称->获得客户ID->再使用客户ID查询相关合同信息。应该使用：关键字直接查询合同信息。
   - **例外**：当任务本身需要先获取列表再逐项拉取正文时（如"查上周所有人周报并总结"需先 `weeklyReport list` 得到 ID 列表，再对每个 ID 执行 `weeklyReport view`），允许多条命令串联，但每条命令必须仍是单个 `mes` 调用，不得引入额外脚本或中间转换步骤。
3. 查询类强制使用 `mes -o json ...`。对于预期超过 20 行的多行结果，必须将输出重定向至临时文件并确保完整阅读全文后再提炼，严禁仅参看可能被截断的终端回显（truncated output/delta）。
4. 所有命令均为非交互模式，必须显式传入所有必填参数。
5. 写操作必须先展示将执行的命令；支持 `--dry-run` 时先 dry-run。
6. 不要求用户在聊天里粘贴 token；认证走 `mes auth login ...`。
7. 严禁臆造、填充或基于常见占位符（如张三、李四等）猜测缺失或因截断而无法直接读取的数据。提炼结果必须与真实回传字段严格对应。
8. 完成最终报告之后，必须删除用于重定向的临时文件，以减少信息泄露风险。
9. **分析服务请求详情时**：必须通过 `mes -o json service request view <id>` 将完整 JSON 输出重定向至临时文件并完整读取，不得仅凭截断的终端回显作分析。若 JSON 中存在截图 URL（`attachments`、`images`、`screenshots` 等字段），必须逐一下载并用 Read 工具读取图像内容进行分析，不得跳过任何一张截图。所有截图均分析完毕后，再综合输出结论。
10. ⚠️ **编码处理（仅限跨环境调用场景）**：当 agent 通过 `wsl -d <distro> -- bash -l -c "mes ..."` 从 **Windows 侧远程调用 WSL 中的 mes CLI** 时，输出为 UTF-8 JSON。此时**绝对不能**通过管道或重定向将 mes 输出直接写入 Windows 文件系统（如 `wsl ... > windows_path.json`）——WSL → Windows 的 interop 管道层会按系统默认代码页（中文 Windows 为 GBK/CP936）做编码转换，导致所有中文字段乱码。
   
   **以下场景无需关注本规则**（可直接正常使用）：
   - Agent 直接运行在 Linux/macOS环境中，`mes` 命令在同一 shell 内执行
   - Agent 运行在 WSL Linux 内部，与 mes CLI 处于同一文件系统

   **仅在 Windows → WSL 跨环境调用时，必须分两步执行**：
   - **Step 1** — 将 mes 输出写入 WSL 内部路径：`wsl -d Ubuntu-24.04 -- bash -l -c "MES_NONINTERACTIVE=1 mes -o json <command> > /tmp/data.json"`
   - **Step 2** — 在 WSL 内用 Python3 解析 JSON 并输出关键字段到 stdout：
     ```bash
     wsl -d Ubuntu-24.04 -- bash -l -c 'python3 << "PYEOF"
     import json
     with open("/tmp/data.json", "r", encoding="utf-8") as f:
         d = json.load(f)
     detail = d["detail"]  # 或 d["list"] 等
     print(f"ID: {detail['id']}")
     print(f"标题: {detail['title']}")
     # ... 提取需要的字段
     PYEOF'
     ```
   此方式完全在 WSL 内完成读取与解码，避免跨文件系统的字节流转换问题。

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
   - 查询类：当列表或详情可能产生长文本输出时，默认采用重定向临时文件方式并配合文件读取命令，以保证数据的完整性。如果当前是 **Windows → WSL 跨环境调用**（见 Hard rule #8），则**必须**遵循两步法（WSL 内 `/tmp/` + Python3 解析），以保证中文数据不被破坏且完整可读。
   - ⚠️ 禁止在跨环境调用场景下使用 `wsl ... > windows_file.json` 直接重定向包含中文的 JSON 输出到 Windows 文件系统。
5. **结果回传**
   - JSON 输出下提炼关键字段（id、status、count、time、message）,永远尝试包含happen-time，created-time等时间相关关键字段
   - ⚠️ 若当前是 **Windows → WSL 跨环境调用**（见 Hard rule #8），中文内容必须通过 WSL 内 Python3 解析获取，严禁直接读取 Windows 侧的 JSON 文件提取中文字段。同环境调用（Linux/macOS 原生或 WSL 内部）不受此限制。
   - 出错时直接给可执行修复命令

## Non-interactive policy

- 所有命令均为非交互模式，无交互提示；必须显式传入所有必填参数。
- 对 `mes statistics add`：必须显式提供  
  `--start --end --hours --remark` + 关联信息（`--from-url` 或 `--type + --rid`；必要时 `--acc-id`）
- 若用户给了 support 链接，优先：
  - `mes -o json util parse-support-url "<url>"`
  - 然后把结果映射到 `statistics add`
- 缺少 ID 时使用对应 util 命令查找：
  - 公司 ID：`mes util search-company <keyword>`
  - 用户/执行人 ID：`mes util search-user <keyword>`
  - 团队 ID：`mes util list-teams`
  - 团队成员 ID：`mes util list-members --team-id <id>`
  - 资产 ID：`mes util list-assets --company-id <id>`
  - 合同子项 ID（acc-id）：`mes dashboard delivery contract-items --company-id <id> -o json`
  - Profile 列表：`mes auth profile list`

## Safety classification

**只读查询（可直接执行）**

- `auth status`
- `statistics list|calendar|summary|review-stats|related-hours`
- `service request list|view`
- `plan list|view`
- `article list|view|review-count`
- `contract list|view`
- `dashboard ...` 所有查询
- `util parse-support-url|search-user|search-company|list-teams|list-members|list-assets`
- `auth profile list`

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
