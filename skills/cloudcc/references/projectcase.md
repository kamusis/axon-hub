# 项目个案模块（售前个案 / 售前POC个案）

## 命令概览

```bash
cloudcc projectcase presale  [参数...]   # 查询售前个案列表
cloudcc projectcase poc      [参数...]   # 查询售前POC个案列表
```

**输出固定为 JSON**（面向 Agent），所有命令默认 `--output json`。

---

## 核心概念

- **一对多结构**：一个案对应多条个案反馈（`feedbacks` 数组，按实际响应时间倒序）；无反馈的个案 `feedbacks` 为空数组
- **数据权限**：个案级可见性判断——业务机会负责人或个案负责人任一在当前用户数据范围内，该个案即可见；个案可见时，其下全部反馈均可见
- 售前个案记录类型为「售前个案」，POC 个案记录类型为「售前产品POC个案」，两个命令查询的个案类型不同，不可混用

---

## `projectcase presale` — 售前个案查询

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--case-name` | 个案名称（模糊匹配） | `"某某银行"` |
| `--case-num` | 个案编号（模糊匹配） | `"2026081661719"` |
| `--op-name` | 业务机会名称（模糊匹配） | `"小红书"` |
| `--op-num` | 业务机会编号（模糊匹配） | `"SJ2026001"` |
| `--op-owner` | 业务机会负责人姓名（模糊匹配） | `"张三"` |
| `--case-owner` | 个案负责人姓名（模糊匹配） | `"李四"` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大1000） | `20` |
| `--output` | 输出格式（json/table，默认 json） | `json` |

### 响应字段（关键）

```json
{
  "items": [
    {
      "opId": "...", "opName": "业务机会名称", "opJieduan": "3.1立项",
      "opNum": "业务机会编号", "opOwnerName": "机会负责人", "opKehumc": "客户名称",
      "caseId": "...", "caseName": "个案编号/名称",
      "sqfl": "售前分类", "ywfl": "业务分类", "sqxqcs": "售前需求描述",
      "gajd": "个案阶段", "bjxx": "背景信息", "beizhu": "备注",
      "xwxyrq": "2026-08-13T10:00:00", "spzt": "审批状态",
      "caseRecordType": "售前个案", "caseOwnerName": "个案负责人",
      "feedbacks": [
        {
          "caseId": "...",
          "qkfknew": "情况反馈内容",
          "sjxysj": "2026-08-13T09:00:00",
          "xybjhnew": "下一步计划",
          "fankuiOwnerName": "反馈人姓名"
        }
      ]
    }
  ],
  "total": 4012, "page": 1, "pageSize": 10, "totalPages": 402,
  "hasNext": true, "hasPrevious": false
}
```

### 示例

```bash
# 查我可见的售前个案
cloudcc projectcase presale --output json

# 按个案负责人查
cloudcc projectcase presale --case-owner "翟睿" --output json

# 按个案编号精准定位
cloudcc projectcase presale --case-num "2026081661719" --output json
```

---

## `projectcase poc` — 售前POC个案查询

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--case-name` | 个案名称（模糊匹配） | `"某某银行"` |
| `--case-num` | 个案编号（模糊匹配） | `"2026081961731"` |
| `--op-name` | 业务机会名称（模糊匹配） | `"小红书"` |
| `--op-owner` | 业务机会负责人姓名（模糊匹配） | `"张三"` |
| `--case-owner` | 个案负责人姓名（模糊匹配） | `"李四"` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大1000） | `20` |
| `--output` | 输出格式（json/table，默认 json） | `json` |

> 与 presale 的差异：POC 命令**没有** `--op-num`（业务机会编号）参数。

### 响应字段（关键）

```json
{
  "items": [
    {
      "opId": "...", "opName": "业务机会名称", "opJieduan": "3.1立项", "opOwnerName": "机会负责人",
      "caseId": "...", "caseName": "个案编号/名称",
      "beizhu": "备注", "spzt": "审批状态",
      "zyrjmc": "软件名称（如 软件-zCloud云管平台）",
      "zycpgasx": "个案属性（如 续期个案）",
      "licsl": "License数量", "ksrq": "2026-08-19T00:00:00",
      "cpsyzq": "试用周期（如 1个月）",
      "pocxs": "POC形式（如 产品现场POC）",
      "pocxqly": "需求来源（如 我司激发）",
      "cpxqyx": "需求意向（如 未立项）",
      "caseRecordType": "售前产品POC个案", "caseOwnerName": "个案负责人",
      "feedbacks": [ { "qkfknew": "...", "sjxysj": "...", "xybjhnew": "...", "fankuiOwnerName": "..." } ]
    }
  ],
  "total": 2737, "page": 1, "pageSize": 10, "totalPages": 274,
  "hasNext": true, "hasPrevious": false
}
```

### 示例

```bash
# 查我可见的POC个案
cloudcc projectcase poc --output json

# 按个案负责人查某人的POC
cloudcc projectcase poc --case-owner "李浩" --output json

# 翻页
cloudcc projectcase poc --page 2 --page-size 20 --output json
```

---

## 权限说明

| 权限标识 | 接口 |
|---------|------|
| `projectcase:presale:page` | POST /api/projectcase/presale/page |
| `projectcase:poc:page` | POST /api/projectcase/poc/page |

无权限时返回 `403`，提示联系管理员分配「售前部门经理」等角色。
