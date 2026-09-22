# 报销单查询模块

> 本文档覆盖**报销单查询**（`reimbursement expense`）。报销导入/附件管理见 [reimbursement-import.md](reimbursement-import.md)。

## 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `reimbursement expense` | 分页查询报销单（立体结构：主单+报销明细） | `--qs-date-from` / `--qs-date-to` |

> 通用说明：
> - 只读分页查询；除必填日期范围外，其余搜索条件可选、任意组合取交集；结果受登录用户**数据权限**约束。
> - 通用参数：`--page`（默认 1）、`--page-size`（默认 10，最大 100）、`--output table/json`。
> - 列表按创建时间 `createdate` **降序**返回（最新在前）。
> - **报销起止日期为必填**（后端强制校验，缺失返回 400）：用于收敛大表扫描量，避免查询超时。

---

## 报销单查询（reimbursement expense）⭐ 立体结构

分页查询费用报销单（fybxd），**分页粒度为报销单（主单）**；每条主单内嵌 `details` 报销明细列表。`total` 为单据数。

```bash
# 按日期范围查询（必填）
cloudcc reimbursement expense --qs-date-from 2026-01-01 --qs-date-to 2026-12-31

# 按报销单编号/申请人姓名/资源体系模糊搜索
cloudcc reimbursement expense --keyword "张三" --qs-date-from 2026-01-01 --qs-date-to 2026-12-31

# 按部门模糊搜索（支持部门路径中任意一级）
cloudcc reimbursement expense --bumen "中部大区" --qs-date-from 2026-01-01 --qs-date-to 2026-12-31

# 按项目名称模糊搜索（明细维度）
cloudcc reimbursement expense --xmmc "中部大区客户1部" --qs-date-from 2026-01-01 --qs-date-to 2026-12-31

# 组合查询：某部门 + 审批通过 + 报销类型
cloudcc reimbursement expense --bumen "江西办事处" --spzt 审批通过 --bxlx 差旅费 --qs-date-from 2026-01-01 --qs-date-to 2026-12-31
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--qs-date-from` | **必填** 报销开始日期，格式 2026-01-01（区间重叠语义，见下） |
| `--qs-date-to` | **必填** 报销结束日期，格式 2026-12-31（含当日） |
| `--keyword` | 模糊匹配报销单编号、申请人姓名、资源体系 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--spzt` | 审批状态（精确：如 审批通过 / 草稿） |
| `--bxlx` | 报销类型（精确，明细维度） |
| `--fylx` | 费用类型（精确，明细维度） |
| `--xmmc` | 项目名称（模糊，明细维度，匹配明细所属项目 `xm.name`） |

### 日期区间重叠语义

日期范围与明细的起止区间 `[qsrq, jsrq]` 取**交集**：只要两个区间有重叠即命中（判定公式：明细开始 ≤ 查询结束 且 明细结束 ≥ 查询开始）。
例如查询 `2026-01-01 ~ 2026-02-01` 时，明细 `2025-12-20 ~ 2026-01-15`（跨年跨越查询起点）也会被查出；`jsrq` 为空的明细按单日（`qsrq`）处理。

### 明细维度条件语义

`--bxlx` / `--fylx` / `--xmmc` / 日期范围同为**明细维度条件**，语义为：存在**同一条明细**同时满足全部已给条件时，才保留该主单（EXISTS 语义）。

### 响应字段（JSON）

主单字段：

| 字段 | 说明 |
|------|------|
| id | 报销单ID |
| name | 报销单编号 |
| spzt | 审批状态 |
| sqrxm | 申请人姓名 |
| zyyjtxnew | 资源体系 |
| ssqynew | 所属区域 |
| ssgs | 所属公司 |
| bumen | 任职部门（含上级部门路径，如 `恩墨>中部大区>江西办事处`） |
| totalBxje | 单内报销金额合计（各明细求和） |
| details | 报销明细列表（见下） |

明细字段（`details[]`）：

| 字段 | 说明 |
|------|------|
| id | 明细ID |
| name | 明细编号 |
| qsrq | 起始日期 |
| jsrq | 结束日期 |
| bxlx | 报销类型 |
| fylx | 费用类型 |
| bxje | 报销金额 |
| fysm | 费用说明 |
| xmmc | 项目名称 |

### JSON 响应示例

```json
{
  "items": [
    {
      "id": "a12201600540272KtwUg",
      "name": "202608275550",
      "spzt": "草稿",
      "sqrxm": "张三",
      "zyyjtxnew": "销售体系",
      "ssqynew": "中区",
      "ssgs": "云和恩墨（北京）信息技术有限公司",
      "bumen": "恩墨>中部大区事业部",
      "totalBxje": 3306.5,
      "details": [
        {
          "id": "b112017E8C42695tPfnv",
          "name": "202608275550-1",
          "qsrq": "2026-08-20",
          "jsrq": "2026-08-22",
          "bxlx": "差旅费",
          "fylx": "交通费",
          "bxje": 580,
          "fysm": "客户拜访高铁往返",
          "xmmc": "2026年_中部大区客户1部_ID"
        }
      ]
    }
  ],
  "total": 1409,
  "page": 1,
  "pageSize": 10,
  "totalPages": 141,
  "hasNext": true,
  "hasPrevious": false
}
```

### 使用说明

- 权限标识 `reimbursement:expense:page`，权限不足返回 403
- 缺少日期范围时后端返回 400（"报销开始日期不能为空" / "报销结束日期不能为空"），退出码 3
- `total` 是**报销单数量**，不是明细条数；一张单据多条明细不会被跨页切断
- 表格视图以 `├` 缩进展示明细（起止日期、报销/费用类型、金额、项目），完整字段请用 `--output json`
- 所有搜索条件与数据权限是 **AND** 叠加：结果永远在当前登录用户可见范围内
- 分页响应数组字段名为 `items`，与其他模块一致
