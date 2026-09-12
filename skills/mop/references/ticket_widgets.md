# Interactive Decision Widgets (Ticket Widgets)

Reference specification for embedding interactive decision widgets in Mopheus ticket comments and descriptions.

## 1. Overview & Capability Gating

When an agent or user needs the team to make choices, pick parameters, or confirm high-risk operations, they can embed an interactive widget block (` ```widget ... ``` `) directly in Markdown content. The Mopheus Web UI renders this block into a native, clickable interactive card.

> [!IMPORTANT]
> **Feature Gate Requirement**:
> Interactive decision widgets are gated by the `widget` workspace feature flag.
> Before emitting a ` ```widget ` block, agents **MUST** probe whether the workspace has the feature enabled (e.g. via `mop feature check widget` or inspecting `mop feature list -o json`).
> If the `widget` feature is disabled or unavailable, the agent **MUST** degrade gracefully to standard Markdown text bullet lists.

---

## 2. Schema Specifications (v: "1")

Every widget JSON block must be enclosed in a ` ```widget ` code fence and contain:
- `v`: Schema version string (currently `"1"`).
- `id`: A unique string identifier for the widget within the ticket (e.g. `"w_plan_choice"`).
- `type`: One of `"single-select"`, `"multi-select"`, or `"confirm-action"`.
- `label`: Card title or prompt displayed in the UI.
- `props`: Object containing type-specific parameters.

### 2.1 Single Select Widget (`single-select`)
Used for mutually exclusive decisions (e.g., choosing an execution plan, rollback version, or deployment method).

````markdown
```widget
{
  "v": "1",
  "id": "w_plan_choice",
  "type": "single-select",
  "label": "选择执行方案",
  "props": {
    "options": [
      {
        "value": "plan_a",
        "label": "方案 A (推荐)",
        "description": "在线热迁移，无服务中断",
        "intent": "positive"
      },
      {
        "value": "plan_b",
        "label": "方案 B (维护窗口)",
        "description": "停机重建索引，耗时 10 分钟",
        "intent": "danger"
      }
    ],
    "default": "plan_a"
  }
}
```
````

**Props**:
- `options` (array, required): List of option objects:
  - `value` (string, required): Unique value submitted when selected.
  - `label` (string, required): Human-readable display text.
  - `description` (string, optional): Supplementary detail.
  - `intent` (string, optional): `"positive"` (green accent), `"danger"` (red/warning accent), or neutral.
- `default` (string, optional): Pre-selected option value.

---

### 2.2 Multi Select Widget (`multi-select`)
Used for choosing one or more items from a set (e.g., selecting target services, test suites, or notification channels).

````markdown
```widget
{
  "v": "1",
  "id": "w_services_choice",
  "type": "multi-select",
  "label": "选择目标服务",
  "props": {
    "options": [
      { "value": "auth-svc", "label": "Auth Token Service" },
      { "value": "gateway-svc", "label": "API Gateway Service" },
      { "value": "worker-queue", "label": "Async Worker Queue" }
    ],
    "minSelected": 1,
    "maxSelected": 2
  }
}
```
````

**Props**:
- `options` (array, required): List of options with `value`, `label`, and optional `description`.
- `minSelected` (number, optional): Minimum number of selections required before submitting.
- `maxSelected` (number, optional): Maximum number of allowed selections.
- `default` (array of strings, optional): Array of pre-selected values.

---

### 2.3 Confirm Action Widget (`confirm-action`)
Used for critical approvals, production releases, destructive operations, or branching actions with optional feedback input.

````markdown
```widget
{
  "v": "1",
  "id": "w_confirm_deploy",
  "type": "confirm-action",
  "label": "确认发布生产环境",
  "props": {
    "description": "变更将执行生产 DDL 结构调整，请确认维护窗口放行。",
    "actions": [
      { "intent": "positive", "label": "确认执行" },
      { "intent": "negative", "label": "终止操作" },
      { "intent": "feedback", "label": "提出修改意见", "placeholder": "请说明需要调整的参数..." }
    ]
  }
}
```
````

**Props**:
- `description` (string, optional): Clarifying context or consequence warning displayed above action buttons.
- `actions` (array, required): Action button definitions:
  - `intent`: `"positive"` (primary/confirm button), `"negative"` (rejection/abort button), or `"feedback"` (opens inline feedback input).
  - `label`: Button display text.
  - `placeholder` (string, optional): Input placeholder when `intent` is `"feedback"`.

---

## 3. CLI Command Usage

### 3.1 Adding a Comment with Widget (`mop ticket comment add`)
Always use heredoc with `--content-stdin` (ensuring `--content-stdin` is the final flag before `<<'EOF'`):

```bash
mop ticket comment add <ticket-id> --content-stdin <<'EOF'
已完成方案设计，请确认后续执行策略：

```widget
{
  "v": "1",
  "id": "w_deploy_strategy",
  "type": "single-select",
  "label": "选择发布策略",
  "props": {
    "options": [
      { "value": "canary", "label": "金丝雀发布 (10%)", "intent": "positive" },
      { "value": "blue_green", "label": "蓝绿部署 (全量切流)" }
    ],
    "default": "canary"
  }
}
```
EOF
```

### 3.2 Embedding in Ticket Creation (`mop ticket create`)
When a newly filed ticket requires upfront choices before work starts:

```bash
mop ticket create --title "生产发布申请" --priority high --description-stdin <<'EOF'
## 变更申请

请选择维护窗口以启动自动化执行流程：

```widget
{
  "v": "1",
  "id": "w_maintenance_window",
  "type": "single-select",
  "label": "选择维护窗口",
  "props": {
    "options": [
      { "value": "tonight", "label": "今晚 02:00-04:00 (推荐)", "intent": "positive" },
      { "value": "weekend", "label": "周六凌晨 02:00-04:00" }
    ],
    "default": "tonight"
  }
}
```
EOF
```

---

## 4. Perceiving User Decisions (Receipts)

1. **State Transition**: When a user clicks an action or submits their selection in the Web UI, the widget card freezes into an immutable completed state recording the submitter identity and timestamp.
2. **Receipt Comment**: Mopheus automatically posts a structured receipt comment to the ticket's timeline containing the user's decision (`action`, `selected`, and optional feedback note).
3. **Agent Inspection**:
   Before proceeding with downstream actions, query the ticket comments:
   ```bash
   mop ticket comment list <ticket-id> -o json
   ```
   Inspect the latest receipt comments in the timeline to parse the user's selected value and proceed accordingly.
