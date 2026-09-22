---
name: cloudcc
description: >
  CloudCC CRM 平台命令行工具。支持：(1)销售活动多维查询与数据分析
  (2)销售活动创建（交互式引导，自动关联业务机会和联系人）
  (3)管辖权限管理 (4)报销单端到端处理（发票识别→Excel填充→系统导入）
  (5)项目管理查询（订单合同/合同子项实施计划/收入计划/商机管理/项目收款/签单预测/收入预测）
  (6)报销附件管理（上传附件/查询附件列表）
  (7)客户管理（客户查询/客户创建/联系人查询/联系人创建/名片扫描添加联系人）
  (8)审批管理（查询我的待办审批记录）
  (9)项目个案查询（售前个案/售前POC个案，含个案反馈一对多）
  (10)人员档案查询与管理（员工档案/离职管理/出差申请/请假单查询与写操作（创建/修改/校验）/请假单附件管理（上传/查询/删除）/加班单查询与写操作（创建/修改）/考勤补卡分页查询，请假与加班为立体结构：主单+内嵌明细）
  (11)报销单查询（按日期范围/部门/项目名称等分页查询报销单，立体结构：主单+报销明细）
  (12)采购申请单查询（分页查询采购申请单，四级立体结构：主单+采购价格+付款申请+付款明细）
  (13)审批引擎（待办查询/进度查询/提交审批/批准审批/拒绝审批/重新分配审批/调回审批）。
  当用户提及 cloudcc、销售活动、业务机会、KNX、商机、报销、报销单查询、报销记录、发票、导入Excel、
  管辖范围、权限、下属、CRM、费用类型、报销模板、expense、附件上传、附件查询、
  订单、合同、合同编号、合同子项、实施计划、收入计划、项目管理、商机管理、商机查询、opportunity、
  收款、收款计划、收款查询、payment-plan、
  签单预测、签单可能性、sign-prediction、
  收入预测、收入可能性、revenue-prediction、
  客户、联系人、客户查询、客户创建、添加联系人、名片扫描、名片识别、
  审批、待办、待办审批、审批记录、
  售前个案、个案反馈、POC个案、POC、项目个案、projectcase、
  员工档案、人员档案、员工查询、人员查询、员工邮箱、入职日期、离职、出差记录、创建出差、修改出差、请假、请假单、请假附件、附件上传、加班、加班单、创建加班、修改加班、补卡、考勤、personnel、创建请假单、修改请假明细、校验请假余额、
  采购、采购申请、采购单、付款申请、付款明细、procurement、
  审批、待办、待批准、待审批、审批引擎、approval、审批进度、提交审批、批准审批、拒绝审批、重新分配、调回审批、
  创建活动、添加活动、新建活动、销售活动创建 等关键词时触发。
  Use when user mentions cloudcc, 销售活动, KNX, 商机, 报销, 报销单查询, 发票, 订单, 合同, 收入计划, 项目管理, 商机管理, opportunity, reimbursement, expense, invoice, project, contract, attachment, 客户, 联系人, customer, contact, 名片, business card, 客户创建, 新建客户, 收款, 收款计划, payment-plan, 签单预测, sign-prediction, 收入预测, revenue-prediction, 售前个案, 个案反馈, POC, projectcase, 员工档案, 人员档案, personnel, employee, 离职, 出差, 创建出差, 修改出差, 请假, 请假附件, 加班, 创建加班, 修改加班, 补卡, 考勤, 创建请假单, 修改请假明细, 校验请假余额, 采购, 采购申请, procurement, 审批, 待办, 待批准, 待审批, 审批引擎, approval, 审批进度, 提交审批, 批准审批, 拒绝审批, 重新分配, 调回审批, 创建活动, 添加活动.
---

# CloudCC CLI

CloudCC 平台命令行工具，用于查询和管理 CRM 销售数据、管辖权限、费用报销。

## 命令树

```
cloudcc
├── auth                        认证管理
│   ├── send-code               发送邮筱验证码
│   ├── login                   邮筱验证码登录
│   ├── logout                  退出登录
│   └── status                  检查登录状态
├── activity                    销售活动
│   ├── query                   多维度查询销售活动
│   └── create                  创建销售活动（交互式引导）
├── permission                  权限管理
│   ├── scope                   查看管辖范围概要
│   ├── query                   查询管辖用户（分页）
│   └── refresh                 刷新管辖范围缓存
├── project                     项目管理
│   ├── order                   查询订单-合同列表
│   ├── subitem                 查询合同子项+实施计划
│   ├── revenue                 查询收入子项+收入计划
│   ├── opportunity             查询商机管理列表
│   ├── payment-plan            查询项目收款计划
│   ├── sign-prediction         查询签单预测
│   └── revenue-prediction      查询收入预测
├── reimbursement               费用报销
│   ├── import                  批量导入报销明细（Excel）
│   ├── upload-attachment       上传报销单附件
│   ├── list-attachments        查询报销单附件列表
│   └── expense                 报销单分页查询（立体：主单+明细）
├── procurement                 采购申请
│   └── application             采购申请单分页查询（四级立体：主单+采购价格+付款申请+付款明细）
├── customer                    客户管理
│   ├── account                 客户
│   │   ├── query               查询客户列表
│   │   ├── create              创建客户
│   │   ├── industries          查询行业选项（大行业 + 小行业）
│   │   └── cities              搜索城市（模糊匹配）
│   └── contact                 联系人
│       ├── query               查询联系人列表
│       └── create              创建联系人
├── projectcase                 项目个案
│   ├── presale                 查询售前个案（含个案反馈）
│   └── poc                     查询售前POC个案（含个案反馈）
├── personnel                   人员档案
│   ├── query                   员工档案分页查询
│   ├── resignation             离职管理分页查询
│   ├── businesstrip            出差申请
│   │   ├── (default)           分页查询
│   │   ├── create              创建出差申请
│   │   └── update              修改出差申请（仅草稿/驳回可改）
│   ├── leave                   请假单
│   │   ├── (default)           分页查询（立体：主单+明细；无条件默认今年）
│   │   ├── create              创建请假单（明细通过 --items-json 传入）
│   │   ├── update              修改请假单明细（整体替换，仅草稿可改）
│   │   ├── check               提交前校验（余额/有效性/天数上限）
│   │   ├── upload-attachment   上传请假单附件（最大100MB）
│   │   ├── list-attachments    查询请假单附件列表
│   │   └── delete-attachment   删除请假单附件（逻辑删除）
│   ├── overtime                加班单
│   │   ├── (default)           分页查询（立体：主单+明细）
│   │   ├── create              创建加班单（明细通过 --items-json 传入）
│   │   └── update              修改加班单明细（整体替换，仅草稿可改）
│   └── attendancepatch         考勤补卡分页查询
├── approval                    审批引擎
│   ├── pending                 查询待批准项目列表
│   ├── progress                查询审批进度
│   ├── submit                  提交审批（引擎通用）
│   ├── approve                 批准审批（引擎通用）
│   ├── reject                  拒绝审批（引擎通用）
│   ├── reassign                重新分配审批（引擎通用）
│   └── recall                  调回审批（引擎通用）
└── update                      版本管理
    ├── check                   检查最新版本
    └── info                    查看当前版本信息
```

## 核心规则

### 0. 安装与目录结构（必须保持）

本 Skill 以完整目录结构发布，**解压后必须保持原样，不可拆分或移动子目录**：

```
cloudcc-skill/                     ← 技能目录（安装为整体）
├── bin/
│   └── cloudcc(.exe)              ← CLI 可执行文件
├── SKILL.md                       ← 本文件（Agent 入口）
├── references/                    ← 各模块参考文档
├── scripts/                       ← Python 辅助脚本
│   └── requirements.txt           ← Python 依赖清单
└── assets/                        ← 预置资源（模板等）
```

**安装步骤：**
1. 解压到任意目录，保持目录结构不变
2. 安装 Python 依赖：`pip install -r scripts/requirements.txt`
3. 无需额外配置，CLI 通过相对路径 `./bin/cloudcc` 自动定位

### 1. CLI 二进制路径

按以下优先级检测 `cloudcc` 可执行文件：

1. 环境变量 `CLOUDCC_CLI_PATH`
2. 相对路径 `./bin/cloudcc`（相对于本 SKILL.md 所在目录）
3. 系统 PATH 中的 `cloudcc`

如均不存在，提示用户确认安装包是否完整解压。

### 2. 认证前置（必须遵守）

**每次执行业务命令前，先检查认证状态：**

```bash
cloudcc auth status
```

- `✓ Logged in` → 继续执行
- `✗ Not logged in` → 先登录
- 命令返回 401 → Token 已过期，提示重新登录

**认证快速流程：**
```bash
cloudcc auth send-code --email user@company.com
cloudcc auth login --email user@company.com --code <验证码>
```

**绝不在未认证状态下执行查询/导入命令。**

### 4. 版本检查（推荐）

**首次使用或定期执行版本检查：**

```bash
cloudcc update check
```

- `✓ 已是最新版本` → 继续使用
- `✗ 有新版本可用` → 按提示下载更新

**版本检查时机：**
- 首次安装后验证版本
- 每周定期检查一次
- 遇到已知问题时检查是否需要升级

**注意：** 版本检查不会自动下载或安装,仅提供下载链接和 SHA256 校验值。

### 3. 输出格式选择

| 场景 | 推荐格式 |
|------|----------|
| Agent 程序处理 | `--output json` |
| 用户快速浏览 | `--simple` 或默认 table |
| 导出到文件 | `--output json --output-file path.json` |
| 大数据集（>100条） | `--page-all --output json --output-file path.json` |

**Agent 场景默认使用 `--output json` 获取结构化数据。**

---

## 模块路由

根据用户意图，加载对应 reference 获取详细信息：

| 用户意图 | 加载文件 |
|---------|---------|
| 登录/认证/验证码/Token 过期 | → [auth.md](references/auth.md) |
| 销售活动/商机/KNX/客户/拜访 | → [activity.md](references/activity.md) |
| 数据分析/报表/统计/转化率 | → [activity.md](references/activity.md)（导出数据后自行分析） |
| 管辖/权限/下属/团队成员 | → [permission.md](references/permission.md) |
| 报销/发票/导入/Excel模板 | → [reimbursement-import.md](references/reimbursement-import.md) |
| 报销单查询/报销记录/某人的报销/按项目查报销 | → [reimbursement-expense.md](references/reimbursement-expense.md) |
| 采购/采购申请/采购单/付款申请/付款明细 | → [procurement.md](references/procurement.md) |
| (报销时)字段映射/填充规则 | → [reimbursement-field-mapping.md](references/reimbursement-field-mapping.md) |
| (报销时)费用分类/类型判断 | → [reimbursement-expense-types.md](references/reimbursement-expense-types.md) |
| 订单/合同/合同编号/合同子项/实施计划/收入计划 | → [project.md](references/project.md) |
| 商机/商机管理/业务机会查询/opportunity | → [opportunity.md](references/opportunity.md) |
| 收款/收款计划/收款查询/预计收款/payment-plan | → [project.md](references/project.md)（项目收款章节） |
| 报工/工时/报工查询/工时查询/work-report | → [project.md](references/project.md)（项目报工章节） |
| 签单预测/签单可能性/sign-prediction | → [sign-prediction.md](references/sign-prediction.md) |
| 收入预测/收入可能性/revenue-prediction | → [revenue-prediction.md](references/revenue-prediction.md) |
| 客户/联系人/客户查询/客户创建/添加联系人/名片扫描 | → [customer.md](references/customer.md) |
| 售前个案/POC个案/个案反馈/项目个案/projectcase | → [projectcase.md](references/projectcase.md) |
| 员工档案/人员档案/员工查询/员工邮箱/入职日期/离职记录/出差记录/创建出差/修改出差/请假/加班/创建加班/修改加班/补卡/考勤/创建请假单/修改请假明细/请假附件 | → [personnel.md](references/personnel.md) |
| 审批/待办/待批准/待审批/我的待办/审批进度/提交审批/批准审批/拒绝审批/重新分配/调回审批/approval | → [approval.md](references/approval.md) |
| **故障排查/错误解决** | → **[troubleshooting.md](references/troubleshooting.md)** |

### 项目查询核心规则

- `--contract-code` 是**跨三个子命令的统一快捷入口（首选）**，CLI 内部自动联动（合同→订单→子项/收入），调用方无需关心 orderId
- 合同与订单是**一对多**关系，`--contract-code` 会自动合并该合同下所有订单的数据
- 已知 orderId 时，可用 `--order-id` 进行单订单精准查询（**进阶优化**：省去联动请求，适合多步查询第 2/3 步）；已知订单编号（dd.name）时用 `--order-name`
- 收入查询默认过滤 `approvalStatus=审批通过`，传空字符串可查全部
- 输出固定为 JSON，字段含义见 [project.md](references/project.md)

### 报销场景强制约束

**报销/发票相关任务启动时，必须按顺序读取以下 3 个文档，缺一不可：**

1. `reimbursement-import.md` — 完整端到端流程（不读 → 流程遗漏步骤）
2. `reimbursement-field-mapping.md` — 金额取值规则 + 字段映射（不读 → 金额错误）
3. `reimbursement-expense-types.md` — 费用类型判断规则（不读 → 分类错误）

**禁止行为：**
- 不读参考文档，凭自身知识判断费用类型或提取金额
- 跳过任何一个文档直接开始处理发票

---

## JSON 响应格式差异（重要）

不同模块返回的 JSON 结构**不同**，解析时务必使用正确的字段名：

### activity / project / projectcase / personnel / reimbursement expense / procurement

数组字段名：**`items`**（projectcase 的每条记录内还嵌套 `feedbacks` 反馈数组；personnel 的 leave/overtime 与 reimbursement expense 每条主单内嵌 `details` 明细数组；procurement 为四级嵌套：`details`→`paymentRequests`→`details`；`total` 均为单据数）
```json
{ "items": [...], "total": 100, "page": 1, "pageSize": 10, "totalPages": 10 }
```

### permission query

数组字段名：**`records`**
```json
{
  "records": [...],
  "total": 50,
  "size": 50,
  "current": 1,
  "pages": 1
}
```

### customer query / create

数组字段名：**`items`**（与 activity / project 一致）
```json
{ "items": [...], "total": 1, "page": 1, "pageSize": 20, "totalPages": 1, "hasNext": false, "hasPrevious": false }
```

### approval pending

数组字段名：**`list`**（注意：不是 `items`），分页字段为 `pageNum`/`pageSize`（非 `page`/`pageSize`）
```json
{ "list": [...], "total": 5, "pageNum": 1, "pageSize": 10 }
```

### approval progress

返回进度对象（非分页），含 `steps` 数组，每个步骤含 `approvers` 数组：
```json
{
  "instanceId": "...", "approvalName": "...", "status": "Pending", "statusDesc": "审批中",
  "totalSteps": 3, "completedSteps": 1, "remainingSteps": 2,
  "steps": [{"stepId": "...", "stepName": "...", "indexNum": 1, "status": "Approved", "approvers": [...], "predicted": false}]
}
```

### reimbursement import

直接返回结果对象（非分页）：
```json
{
  "successCount": 5,
  "failCount": 0,
  "orderId": "BX20260610001",
  "detailUrl": "https://...",
  "errorMessages": []
}
```

### personnel leave write operations (create/update/check)

- `create` / `update`：返回单个请假单对象（与查询响应中单条 `items[]` 结构相同，含 `id`/`name`/`spzt`/`details` 等）
- `check`：校验通过无返回体（CLI 输出“✓ 校验通过”），校验失败返回错误信息

### personnel overtime write operations (create/update)

- `create` / `update`：返回单个加班单对象（与查询响应中单条 `items[]` 结构相同，含 `id`/`name`/`spzt`/`details` 等）

### approval operations (submit/approve/reject/reassign/recall)

返回审批操作结果对象：
```json
{
  "success": true,
  "errorCode": "",
  "errorMessage": "",
  "instanceId": "审批实例ID",
  "approvalId": "审批规则ID",
  "approvalName": "请假审批规则",
  "approverIds": ["审批人ID"],
  "autoApproved": false
}
```

---

## 错误处理（通用）

| 错误 | 原因 | 处理 |
|------|------|------|
| `401` / `token has expired` | Token 过期 | 重新登录 |
| `not logged in` | 未登录 | 执行认证流程 |
| `403` | 权限不足 | 联系管理员 |
| `500` | 服务端异常 | 稍后重试 |
| 文件不存在 | Excel 路径错误 | 检查路径 |
| `update check failed` | 网络连接问题 | 检查网络后重试 |
| `version.json not found` | 服务器配置问题 | 联系管理员 |
| `unsupported version` | 版本过低已废弃 | 立即升级到最新版本 |

### 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 成功 |
| 1 | 通用错误 |
| 2 | 认证失败 |
| 3 | 参数验证失败 |
| 4 | 网络连接错误 |

---

## 常用场景映射

| 用户说法 | 命令 |
|----------|------|
| "查本月活动" | `cloudcc activity query --date 本月 --output json` |
| "查西区商机" | `cloudcc activity query --region 西区 --date 本月 --output json` |
| "查高可能性商机" | `cloudcc activity query --op-knx 60-100 --date 本月 --output json` |
| "导出本月数据" | `cloudcc activity query --date 本月 --page-all --output json --output-file data.json` |
| "查管辖范围" | `cloudcc permission scope` |
| "查管辖用户" | `cloudcc permission query --output json` |
| "导入报销单" | `cloudcc reimbursement import -f ./报销单.xlsx` |
| "上传报销附件" | `cloudcc reimbursement upload-attachment -f 发票.pdf -o 报销单编号` |
| "查看报销附件" | `cloudcc reimbursement list-attachments -o 报销单编号` |
| "查报销单/报销记录" | `cloudcc reimbursement expense --qs-date-from 2026-01-01 --qs-date-to 2026-12-31 --output json`（日期必填） |
| "查某人的报销单" | `cloudcc reimbursement expense --keyword "张三" --qs-date-from 2026-01-01 --qs-date-to 2026-12-31 --output json` |
| "查某部门的报销单" | `cloudcc reimbursement expense --bumen "中部大区" --qs-date-from 2026-01-01 --qs-date-to 2026-12-31 --output json` |
| "查某项目的报销" | `cloudcc reimbursement expense --xmmc "中部大区客户1部" --qs-date-from 2026-01-01 --qs-date-to 2026-12-31 --output json` |
| "查采购申请单" | `cloudcc procurement application --output json` |
| "查某人的采购单" | `cloudcc procurement application --keyword "张三" --output json` |
| "查某部门的采购单" | `cloudcc procurement application --bumen "交付部" --output json` |
| "查审批通过的采购单" | `cloudcc procurement application --spzt 审批通过 --output json` |
| "KNX分析" | 先导出数据再用 Python 分析（Agent 根据需求自行生成代码） |
| "识别发票生成报销单" | 完整流程 → [reimbursement-import.md](references/reimbursement-import.md) |
| "查客户" | `cloudcc customer account query --keyword "客户名称" --output json` |
| "创建客户" | `cloudcc customer account create --name "客户名称" --khdj A --qy "东区" --khszcs "上海" --khxhycz "软件开发" --output json` |
| "搜索城市" | `cloudcc customer account cities --keyword "邯郸" --output json` |
| "查联系人" | `cloudcc customer contact query --keyword "联系人名称" --output json` |
| "添加联系人" | `cloudcc customer contact create --account "客户名称" --name "姓名" --bumen "部门" --zhiwu "职务" --shouji "手机" --source "主动销售"` |
| "扫描名片添加联系人" | 识别名片图片 → 提取字段 → 补充必填项 → `customer contact create`，详见 [customer.md](references/customer.md) |
| "创建销售活动" | 交互式引导 → [activity.md](references/activity.md)（创建活动章节） |
| "查商机" | `cloudcc project opportunity --output json` |
| "查某人负责的商机" | `cloudcc project opportunity --owner-name "张三" --output json` |
| "查某客户的商机" | `cloudcc project opportunity --kehu-name "国网" --output json` |
| "查收款计划" | `cloudcc project payment-plan --output json` |
| "查某人收款计划" | `cloudcc project payment-plan --owner-name "张三" --output json` |
| "查某年收款" | `cloudcc project payment-plan --pay-date-from 2026-01-01 --pay-date-to 2026-12-31 --output json` |
| "查收款未完成" | `cloudcc project payment-plan --pay-status 收款未完成 --output json` |
| "查项目报工/工时" | `cloudcc project work-report --output json` |
| "查某人的报工" | `cloudcc project work-report --owner-name "张三" --output json` |
| "查某时间段的工时" | `cloudcc project work-report --start-time-from 2026-01-01 --start-time-to 2026-06-30 --output json` |
| "查签单预测" | `cloudcc project sign-prediction --output json` |
| "查高可能性签单" | `cloudcc project sign-prediction --qdknx-min 80 --output json` |
| "查某人签单预测" | `cloudcc project sign-prediction --user-name "张三" --output json` |
| "查收入预测" | `cloudcc project revenue-prediction --output json` |
| "查高可能性收入" | `cloudcc project revenue-prediction --knx-min 80 --output json` |
| "查某人收入预测" | `cloudcc project revenue-prediction --user-name "张三" --output json` |
| "查合同/订单" | `cloudcc project order --contract-code 00032838` |
| "查实施计划/合同子项" | `cloudcc project subitem --contract-code 00032838` |
| "查收入计划" | `cloudcc project revenue --contract-code 00032838` |
| "查合同全貌（订单+子项+收入）" | 依次执行 order/subitem/revenue，均传 `--contract-code` |
| "查售前个案" | `cloudcc projectcase presale --output json` |
| "查某人的售前个案" | `cloudcc projectcase presale --case-owner "张三" --output json` |
| "查个案反馈" | `cloudcc projectcase presale --case-num "个案编号" --output json`（feedbacks 数组） |
| "查POC个案" | `cloudcc projectcase poc --output json` |
| "查某人的POC" | `cloudcc projectcase poc --case-owner "张三" --output json` |
| "查员工档案/人员档案" | `cloudcc personnel query --output json` |
| "查某人的邮箱" | `cloudcc personnel query --keyword "张三" --output json` |
| "查某部门的员工" | `cloudcc personnel query --bumen "交付部" --output json` |
| "查在职正式员工" | `cloudcc personnel query --zyzt 在职 --yglx 正式 --output json` |
| "查某时间段入职的员工" | `cloudcc personnel query --rzrq-from 2026-01-01 --rzrq-to 2026-06-30 --output json` |
| "查离职记录/某人离职信息" | `cloudcc personnel resignation --keyword "张三" --output json` |
| "查出差记录/某人出差" | `cloudcc personnel businesstrip --keyword "张三" --output json` |
| "创建出差申请" | `cloudcc personnel businesstrip create --ccksrq 2026-10-01 --ccjsrq 2026-10-03 --type "业务支持" --ccjtgj "火车;飞机" --ccsy "出差事由" --cfd "上海" --ccdnew "杭州" --yjclzc 4200 --xiangmu "项目名称"` |
| "修改出差申请" | `cloudcc personnel businesstrip update --keyword "ID或编号" --ccsy "新事由"`（仅草稿/驳回可改） |
| "查请假记录/某人请假" | `cloudcc personnel leave --keyword "张三" --output json`（立体结构，明细在 details；无搜索条件时默认查询今年） |
| "创建请假单" | `cloudcc personnel leave create --items-json '[{"qjlx":"带薪","jqlb":"年假","qjqsrq":"2026-09-01","qjjsrq":"2026-09-03","qjts":3,"qjyy":"个人事务"}]'` |
| "校验请假单余额" | `cloudcc personnel leave check --items-json '[{...}]'`（提交前校验余额/有效性/天数上限） |
| "修改请假单明细" | `cloudcc personnel leave update --leave-id "ID" --items-json '[{...}]'`（仅草稿可改，整体替换） |
| "上传请假附件" | `cloudcc personnel leave upload-attachment -f 文件.pdf -l 请假单ID或编号` |
| "查询请假附件" | `cloudcc personnel leave list-attachments -l 请假单ID或编号` |
| "删除请假附件" | `cloudcc personnel leave delete-attachment -a 附件ID` |
| "提交请假单审批" | `cloudcc approval submit --relate-id "ID" --app-path "/personnel/leavedetail"` |
| "批准请假单审批" | `cloudcc approval approve --work-item-id "ID" --comments "同意"` |
| "拒绝请假单审批" | `cloudcc approval reject --work-item-id "ID" --comments "不同意"` |
| "转交请假单审批" | `cloudcc approval reassign --work-item-id "ID" --approvers "姓名" --comments "转交处理"` |
| "调回请假单审批" | `cloudcc approval recall --relate-id "ID" --comments "信息有误"` |
| "查加班记录/某人加班" | `cloudcc personnel overtime --keyword "张三" --output json`（立体结构，明细在 details） |
| "创建加班单" | `cloudcc personnel overtime create --items-json '[{"jbdd":"北京","jbqssj":"2026-09-20 09:00","jbjssj":"2026-09-20 18:00","jbxsshjsz":8,"jbsy":"项目支持"}]'` |
| "修改加班单明细" | `cloudcc personnel overtime update --keyword "ID或编号" --items-json '[{...}]'`（仅草稿可改，整体替换） |
| "提交加班单审批" | `cloudcc approval submit --relate-id "ID" --app-path "/personnel/overtimedetail"` |
| "查补卡记录/考勤补卡" | `cloudcc personnel attendancepatch --keyword "张三" --output json` |
| "查某时间段的请假" | `cloudcc personnel leave --qjqsrq-from 2026-01-01 --qjqsrq-to 2026-06-30 --output json`（无搜索条件默认今年） |
| "查我的待办/待批准项目" | `cloudcc approval pending --output json` |
| "查某人提交的待办" | `cloudcc approval pending --submitter "张三" --output json` |
| "按类型查待办" | `cloudcc approval pending --keyword "报销单" --output json` |
| "管理员代查他人待办" | `cloudcc approval pending --target-user "王五" --output json` |
| "查询审批进度" | `cloudcc approval progress --relate-id "业务记录ID" --output json` |
| "提交审批" | `cloudcc approval submit --relate-id "业务记录ID" --app-path "/personnel/leavedetail"` |
| "批准审批" | `cloudcc approval approve --work-item-id "审批请求ID" --comments "同意"` |
| "拒绝审批" | `cloudcc approval reject --work-item-id "审批请求ID" --comments "不同意"` |
| "重新分配审批" | `cloudcc approval reassign --work-item-id "审批请求ID" --approvers "姓名" --comments "转交"` |
| "调回审批" | `cloudcc approval recall --relate-id "业务记录ID" --comments "信息有误"` |
| "提交审批" | `cloudcc approval submit --relate-id "业务记录ID" --app-path "/personnel/leavedetail"` |
| "批准审批" | `cloudcc approval approve --work-item-id "审批请求ID" --comments "同意"` |
| "拒绝审批" | `cloudcc approval reject --work-item-id "审批请求ID" --comments "不同意"` |
| "重新分配审批" | `cloudcc approval reassign --work-item-id "审批请求ID" --approvers "姓名" --comments "转交"` |
| "调回审批" | `cloudcc approval recall --relate-id "业务记录ID" --comments "信息有误"` |

---

## 脚本资源

详见 [报销导入流程](references/reimbursement-import.md#脚本资源)

## 预置资源

| 文件 | 说明 |
|------|------|
| `assets/reimbursement-template.xlsx` | 预置报销模板，复制到工作目录后直接使用 |