# 采购申请模块

## 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `procurement application` | 分页查询采购申请单（四级立体结构：主单+采购价格+付款申请+付款明细） | 无 |

> 通用说明：
> - 只读分页查询，所有搜索条件可选、任意组合取交集；结果受登录用户**数据权限**约束。
> - 通用参数：`--page`（默认 1）、`--page-size`（默认 10，最大 100）、`--output table/json`。
> - 列表按创建时间 `createdate` **降序**返回（最新在前）。

---

## 采购申请单查询（procurement application）⭐ 立体结构

分页查询采购申请单（cgsqd），**分页粒度为采购申请单（主单）**；每条主单内嵌 `details` 采购价格列表，采购价格内再嵌套 `paymentRequests` 付款申请，付款申请内再嵌套 `details` 付款明细。`total` 为单据数。

```bash
# 按采购单编号/申请人姓名/资源体系模糊搜索
cloudcc procurement application --keyword "张三"

# 按部门模糊搜索（支持部门路径中任意一级）
cloudcc procurement application --bumen "交付部"

# 按审批状态精确过滤
cloudcc procurement application --spzt 审批通过

# 按申请日期范围查询（仅年月日，含边界）
cloudcc procurement application --sqrq-from 2026-01-01 --sqrq-to 2026-06-30

# 组合查询
cloudcc procurement application --bumen "西区" --spzt 审批通过 --cglx "办公用品"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配采购单编号、申请人姓名、资源体系 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--spzt` | 审批状态（精确：如 审批通过 / 草稿） |
| `--cglx` | 采购类型（精确） |
| `--cglxmxDx` | 采购类型明细对象（精确） |
| `--sqrq-from` / `--sqrq-to` | 申请日期区间（含边界，格式 2026-01-01，仅年月日；匹配采购申请单申请日期 `cgsqd.sqrq`，终点含当日全天） |

### 响应字段（JSON）

主单字段：

| 字段 | 说明 |
|------|------|
| id | 采购申请单ID |
| name | 采购申请单编号 |
| spzt | 审批状态 |
| cgwpmc | 采购物品名称 |
| cglx | 采购类型 |
| cglxmxDx | 采购类型明细对象 |
| yt | 用途 |
| je | 预算金额（单价×数量） |
| sqrq | 采购预算申请日期（cgsqd.sqrq） |
| sqrxm | 申请人姓名 |
| zyyjtxnew | 资源体系 |
| ssqynew | 所属区域 |
| ssgs | 所属公司 |
| bumen | 任职部门（含上级部门路径，如 `恩墨>交付部>西区`） |
| totalJe | 单内采购金额合计（各采购价格求和） |
| totalSjfkje | 单内实际付款金额合计（各付款明细求和） |
| details | 采购价格列表（见下） |

采购价格字段（`details[]`）：

| 字段 | 说明 |
|------|------|
| id | 采购价格ID |
| name | 采购价格编号 |
| jygys | 建议供应商 |
| khyh | 开户银行 |
| yhzh | 银行账号 |
| spzt | 审批状态 |
| je | 采购金额（单价×数量） |
| sqrq | 采购结果申请日期（cgjg.sqrq） |
| paymentRequests | 付款申请列表（见下） |

付款申请字段（`details[].paymentRequests[]`）：

| 字段 | 说明 |
|------|------|
| id | 付款申请ID |
| name | 付款申请编号 |
| spzt | 审批状态 |
| fkje | 付款金额（计划付款总额） |
| jhfksj | 建议付款日期（fksq.jhfksj） |
| totalSjfkje | 实际付款金额合计（本付款申请内明细求和） |
| details | 付款明细列表（见下） |

付款明细字段（`details[].paymentRequests[].details[]`）：

| 字段 | 说明 |
|------|------|
| id | 付款明细ID |
| name | 付款明细编号 |
| sjfkjeNew | 实际付款金额 |
| sjfkrq | 实际付款日期（fkmx.sjfkrq） |

### JSON 响应示例

```json
{
  "items": [
    {
      "id": "a12201600540272KtwUg",
      "name": "CGSQ-000123",
      "spzt": "审批通过",
      "cgwpmc": "笔记本电脑",
      "cglx": "办公设备",
      "cglxmxDx": "电脑",
      "yt": "新员工入职",
      "je": 12000,
      "sqrq": "2026-08-01T00:00:00",
      "sqrxm": "张三",
      "zyyjtxnew": "交付体系",
      "ssqynew": "北区",
      "ssgs": "云和恩墨（北京）信息技术有限公司",
      "bumen": "恩墨>交付部>西区",
      "totalJe": 12000,
      "totalSjfkje": 12000,
      "details": [
        {
          "id": "b112017E8C42695tPfnv",
          "name": "CGJG-000123",
          "jygys": "某科技有限公司",
          "khyh": "招商银行",
          "yhzh": "6226...",
          "spzt": "审批通过",
          "je": 12000,
          "sqrq": "2026-08-05T00:00:00",
          "paymentRequests": [
            {
              "id": "c112017E8C42695tPfnv",
              "name": "FKSQ-000123",
              "spzt": "审批通过",
              "fkje": 12000,
              "jhfksj": "2026-08-10T00:00:00",
              "totalSjfkje": 12000,
              "details": [
                { "id": "d112017E8C42695tPfnv", "name": "FKMX-000123", "sjfkjeNew": 12000, "sjfkrq": "2026-08-12T00:00:00" }
              ]
            }
          ]
        }
      ]
    }
  ],
  "total": 88,
  "page": 1,
  "pageSize": 10,
  "totalPages": 9,
  "hasNext": true,
  "hasPrevious": false
}
```

### 使用说明

- 权限标识 `procurement:application:page`，权限不足返回 403
- `total` 是**采购申请单数量**，不是明细条数；一张单据多层明细不会被跨页切断
- 表格视图以 `├`/`└` 缩进展示四级结构（采购价格 → 付款申请 → 付款明细），完整字段请用 `--output json`
- 所有搜索条件与数据权限是 **AND** 叠加：结果永远在当前登录用户可见范围内
- 分页响应数组字段名为 `items`，与其他模块一致
