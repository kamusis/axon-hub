# 审批引擎模块

## 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `approval pending` | 分页查询当前用户的待批准项目列表 | 无 |
| `approval progress` | 查询某条业务记录的审批进度 | `--relate-id` |
| `approval submit` | 提交业务记录审批 | `--relate-id` + `--app-path` |
| `approval approve` | 批准审批 | `--work-item-id` |
| `approval reject` | 拒绝审批 | `--work-item-id` |
| `approval reassign` | 重新分配审批 | `--work-item-id` + `--approvers` |
| `approval recall` | 调回审批 | `--relate-id` |

> 通用说明：
> - 所有命令支持 `--output json`，Agent 场景推荐 `--output json`。
> - `relateId` 为业务记录 ID，`workItemId` 来自 `pending` 查询结果。
> - 审批操作通过引擎通用端点执行，仅已注册 Handler 的业务模块可使用。
> - 权限规则：超管可操作全部，普通用户只能操作自己的待审批项。

---

## 待批准项目查询（approval pending）

分页查询当前登录用户作为审批人的待批准项目列表。

```bash
# 查询我的所有待办
cloudcc approval pending

# 按对象类型名称模糊搜索
cloudcc approval pending --keyword "报销单"

# 按提交人姓名模糊搜索
cloudcc approval pending --submitter "张三"

# 组合查询
cloudcc approval pending --keyword "请假单" --submitter "李四"

# 管理员代查他人待办
cloudcc approval pending --target-user "王五" --output json

# JSON 格式输出（Agent 推荐）
cloudcc approval pending --output json
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配对象类型名称（tp_sys_object.label，如 报销单、请假单、出差申请） |
| `--submitter` | 模糊匹配提交人姓名（ccuser.name） |
| `--target-user` | 目标用户搜索（**仅系统管理员可用**，模糊匹配姓名/邮箱/ID；匹配唯一用户时查询其待审批；匹配多个时返回候选列表） |
| `--page` | 页码（默认 1） |
| `--page-size` | 每页条数（默认 10，最大 100） |
| `--output` | 输出格式（table/json，默认 table） |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| workItemId | 审批请求 ID（用于批准/拒绝/转交操作） |
| objId | 业务记录 ID（target_object_id，即 relateId） |
| objPrefix | 对象前缀（3 位，如 a12、007） |
| objType | 对象类型名称（tp_sys_object.label） |
| objName | 业务记录名称（动态查询业务表） |
| objDescription | 业务记录摘要/备注（动态拼装字段标签:值） |
| submitterId | 提交人 ID |
| submitterName | 提交人姓名 |
| ownerId | 记录所有人 ID |
| ownerName | 记录所有人姓名 |
| lastModifyDate | 最后修改时间 |
| currentActorId | 当前审批人 ID |
| currentActorName | 当前审批人姓名 |
| delegated | 是否为委托审批（true=当前用户非直接审批人，系委托代审） |

### JSON 响应示例

```json
{
  "list": [
    {
      "workItemId": "w122026C8A3F291KxYz",
      "objId": "a122026B750D7836UbqD",
      "objPrefix": "a12",
      "objType": "请假单",
      "objName": "QJD20260907001",
      "objDescription": "请假类型:带薪,假期类别:年假,天数:3",
      "submitterId": "005001",
      "submitterName": "张三",
      "ownerId": "005001",
      "ownerName": "张三",
      "lastModifyDate": "2026-09-07T10:30:00",
      "currentActorId": "005002",
      "currentActorName": "李四",
      "delegated": false
    }
  ],
  "total": 5,
  "pageNum": 1,
  "pageSize": 10
}
```

### 管理员代查候选列表

当管理员传入 `--target-user` 匹配到多个用户时，返回候选列表而非待办数据：

```json
{
  "needSelect": true,
  "message": "找到多个匹配用户，请精确选择",
  "candidates": [
    {"id": "005003", "name": "王五", "email": "wangwu@enmotech.com"},
    {"id": "005004", "name": "王五丰", "email": "wangwufeng@enmotech.com"}
  ]
}
```

此时需精确指定用户后重新查询。

---

## 查询审批进度（approval progress）

根据业务记录 ID 查询完整审批进度，含已完成的步骤和后续预测。

> **权限说明**：系统管理员可查询所有记录的审批进度；普通用户只能查询自己提交的记录进度。

```bash
# 查询进度
cloudcc approval progress --relate-id "b522026C0DCB4CCiIyNu"

# JSON 输出
cloudcc approval progress --relate-id "b522026C0DCB4CCiIyNu" --output json
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--relate-id` | 业务记录 ID（必填） |
| `--output` | 输出格式（table/json，默认 table） |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| instanceId | 审批实例 ID |
| approvalId | 审批规则 ID |
| approvalName | 审批规则名称 |
| targetObjectId | 业务记录 ID |
| objectLabel | 对象类型标签 |
| status | 实例状态（Pending/Approved/Rejected/Recalled） |
| statusDesc | 状态中文描述 |
| submitterId | 提交人 ID |
| submitterName | 提交人姓名 |
| submitTime | 提交时间 |
| totalSteps | 总步骤数 |
| completedSteps | 已完成步骤数 |
| remainingSteps | 剩余步骤数 |
| steps | 步骤详情数组 |
| steps[].stepId | 步骤 ID |
| steps[].stepName | 步骤名称 |
| steps[].indexNum | 步骤序号 |
| steps[].status | 步骤状态 |
| steps[].statusDesc | 步骤状态描述 |
| steps[].approvers | 审批人数组（含 userName/status/statusDesc/operateTime/remark） |
| steps[].predicted | 是否为预测步骤（尚未到达） |

### JSON 响应示例

```json
{
  "instanceId": "20260907103000123AbC",
  "approvalId": "sp001",
  "approvalName": "请假审批规则",
  "targetObjectId": "b522026C0DCB4CCiIyNu",
  "objectLabel": "请假单",
  "status": "Pending",
  "statusDesc": "审批中",
  "submitterId": "005001",
  "submitterName": "张三",
  "submitTime": "2026-09-07T10:30:00",
  "totalSteps": 3,
  "completedSteps": 1,
  "remainingSteps": 2,
  "steps": [
    {
      "stepId": "s001",
      "stepName": "部门经理审批",
      "indexNum": 1,
      "status": "Approved",
      "statusDesc": "已通过",
      "approvers": [
        {"userId": "005002", "userName": "李四", "status": "Approved", "statusDesc": "已批准", "operateTime": "2026-09-07T11:00:00", "remark": "同意"}
      ],
      "predicted": false
    },
    {
      "stepId": "s002",
      "stepName": "总监审批",
      "indexNum": 2,
      "status": "Pending",
      "statusDesc": "待审批",
      "approvers": [
        {"userId": "005003", "userName": "王五", "status": "Pending", "statusDesc": "待处理", "operateTime": "", "remark": ""}
      ],
      "predicted": false
    }
  ]
}
```

---

## 提交审批（approval submit）

将业务记录提交到审批引擎，触发 Handler 前置校验、审批规则匹配、实例创建、审批人计算等完整流程。

```bash
# 提交请假单审批
cloudcc approval submit --relate-id "a122026B750D7836UbqD" --app-path "/personnel/leavedetail"

# 提交并加备注
cloudcc approval submit --relate-id "a122026B750D7836UbqD" --app-path "/personnel/leavedetail" --remark "紧急事务"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--relate-id` | 业务记录 ID（必填） |
| `--app-path` | 应用路径（必填，如 `/personnel/leavedetail`） |
| `--remark` | 审批备注（可选） |
| `--output` | 输出格式（json，默认 json） |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| success | 是否成功 |
| errorCode | 错误码（失败时） |
| errorMessage | 错误信息（失败时） |
| instanceId | 审批实例 ID |
| approvalId | 审批规则 ID |
| approvalName | 审批规则名称 |
| approverIds | 审批人 ID 列表 |
| autoApproved | 是否自动通过 |

### 使用说明

- 权限标识 `approval:engine:submit`
- **Handler 注册约束**：仅已注册 Handler 的业务模块可提交，未注册返回错误提示
- **前置校验**：Handler 的 `onBeforeSubmit` 钩子会先执行（如余额校验），校验失败会阻止提交
- **典型流程**：`pending` 查待办 → `submit` 提交 → `approve`/`reject` 审批

---

## 批准审批（approval approve）

批准一条待审批记录，触发步骤流转和下一步审批人计算。

```bash
# 批准
cloudcc approval approve --work-item-id "20260914171103828105"

# 批准并加意见
cloudcc approval approve --work-item-id "20260914171103828105" --comments "同意"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--work-item-id` | 审批请求 ID（必填，从 `approval pending` 查询获取） |
| `--comments` | 审批意见（可选） |
| `--output` | 输出格式（json，默认 json） |

### 使用说明

- 权限标识 `approval:engine:approve`
- **Handler 前置校验**：`onBeforeApprove` 钩子会先执行
- **后置事件**：`onApproved` 钩子在批准后触发（如余额扣减）

---

## 拒绝审批（approval reject）

拒绝一条待审批记录，触发退回流程和通知。

```bash
# 拒绝
cloudcc approval reject --work-item-id "20260914171103828105" --comments "请假天数过多"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--work-item-id` | 审批请求 ID（必填，从 `approval pending` 查询获取） |
| `--comments` | 拒绝意见（可选） |
| `--output` | 输出格式（json，默认 json） |

### 使用说明

- 权限标识 `approval:engine:reject`
- **Handler 前置校验**：`onBeforeReject` 钩子会先执行
- **后置事件**：`onRejected` 钩子在拒绝后触发（如邮件通知）

---

## 重新分配审批（approval reassign）

将待审批记录转交给一个或多个新审批人。

```bash
# 重新分配给常钰
cloudcc approval reassign --work-item-id "20260914171103828105" --approvers "常钰" --comments "转交处理"

# 重新分配给多人
cloudcc approval reassign --work-item-id "20260914171103828105" --approvers "张三,李四"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--work-item-id` | 审批请求 ID（必填，从 `approval pending` 查询获取） |
| `--approvers` | 新审批人列表（必填，姓名或邮箱，逗号分隔） |
| `--comments` | 转交说明（可选） |
| `--output` | 输出格式（json，默认 json） |

### 使用说明

- 权限标识 `approval:engine:reassign`
- 审批人支持姓名或邮箱，服务端自动解析为 ccuserId

---

## 调回审批（approval recall）

撤回已提交的审批，终止审批流程。

```bash
# 调回
cloudcc approval recall --relate-id "a122026B750D7836UbqD" --comments "信息有误，撤回重新提交"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--relate-id` | 业务记录 ID（必填） |
| `--comments` | 调回说明（可选） |
| `--output` | 输出格式（json，默认 json） |

### 使用说明

- 权限标识 `approval:engine:submit`（与提交共用）
- 调回后审批流程终止，记录恢复为可编辑状态
- **后置事件**：`onRecalled` 钩子在调回后触发（如邮件通知）

---

## 权限说明

| 权限编码 | 覆盖操作 | 说明 |
|---------|---------|------|
| `approval:engine:pending` | pending | 查询待办（`--target-user` 仅管理员可用） |
| `approval:engine:progress` | progress | 查询进度（管理员可查全部，普通用户只能查自己提交的记录） |
| `approval:engine:submit` | submit / recall | 提交审批 / 调回审批 |
| `approval:engine:approve` | approve | 批准审批 |
| `approval:engine:reject` | reject | 拒绝审批 |
| `approval:engine:reassign` | reassign | 重新分配审批 |
| `approval:engine:progress` | progress | 查询审批进度 |

## 使用说明

- 典型流程：`pending` 查待办 → `approve`/`reject`/`reassign` 处理 → `progress` 查看进度
- 提交流程：业务模块 `create` 创建记录 → `approval submit` 提交 → 等待审批
- **Handler 注册约束**：仅已注册 Handler 的业务模块可使用审批操作，未注册返回错误提示
- 权限不足返回 403，需联系管理员分配对应权限
- 查询范围为当前登录用户作为**直接审批人**或**委托审批人**的 Pending 状态记录
- 防重复机制：1 小时内已操作的记录不会重复出现在待办列表中
- 表格视图中摘要（`objDescription`）缩进展示在明细行，完整内容请用 `--output json`
- `--target-user` 仅系统管理员有效，非管理员传入此参数会被忽略并记录 WARN 日志
- 响应数组字段名为 `list`（非 `items`），与其他模块不同
- 审批操作命令默认输出 JSON 格式，含 success/errorCode/instanceId 等字段
