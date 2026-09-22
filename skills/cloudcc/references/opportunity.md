# 商机管理模块

## 命令概览

```bash
cloudcc project opportunity  [参数...]   # 查询商机管理列表
```

**输出固定为 JSON**（面向 Agent），所有命令默认 `--output json`。

---

## 默认行为

- **结束日期（jsrq）默认过滤当前年份**：不传日期参数时，自动查询 `当前年-01-01` 至 `当前年-12-31` 的数据
- 传入 `--end-date-from` 或 `--end-date-to` 时，使用自定义日期范围，不再默认当前年份

---

## `project opportunity` — 商机管理查询

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--owner-name` | 负责人姓名（模糊匹配） | `"张三"` |
| `--owner-bumen` | 负责人部门（模糊匹配） | `"数字化部"` |
| `--owner-tixi` | 负责人体系（模糊匹配） | `"销售体系"` |
| `--op-name` | 商机名称（模糊匹配） | `"小红书"` |
| `--op-xmid` | 商机编号（模糊匹配） | `"SJ2026001"` |
| `--jieduan` | 商机阶段（模糊匹配） | `"2.1激发需求"` |
| `--xmlx` | 项目类型（模糊匹配） | `"维保"` |
| `--product-type` | 产品大类（模糊匹配） | `"项目服务"` |
| `--product-sub-type` | 产品小类（模糊匹配） | `"一般维保"` |
| `--service-start-from` | 预计服务开始日期起始（`op.yjfwksrq >=`） | `2026-01-01` |
| `--service-start-to` | 预计服务开始日期截止（`op.yjfwksrq <=`） | `2026-12-31` |
| `--service-end-from` | 预计服务结束日期起始（`op.yjfwjsrq >=`） | `2026-01-01` |
| `--service-end-to` | 预计服务结束日期截止（`op.yjfwjsrq <=`） | `2026-12-31` |
| `--end-date-from` | 结束日期起始（`op.jsrq >=`） | `2026-01-01` |
| `--end-date-to` | 结束日期截止（`op.jsrq <=`） | `2026-12-31` |
| `--jine-min` | 金额最小值（`op.jine >=`） | `100000` |
| `--jine-max` | 金额最大值（`op.jine <=`） | `500000` |
| `--kehu-name` | 客户名称（模糊匹配） | `"国网"` |
| `--kehu-qy` | 客户区域（模糊匹配） | `"北区"` |
| `--kehu-ss` | 客户所属（模糊匹配） | `"北京"` |
| `--zzkehu-name` | 最终客户名称（模糊匹配） | `"国网"` |
| `--zzkehu-qy` | 最终客户区域（模糊匹配） | `"北区"` |
| `--zzkehu-ss` | 最终客户所属（模糊匹配） | `"北京"` |
| `--industry` | 最终客户大行业（模糊匹配） | `"制造业"` |
| `--industry-sub` | 最终客户小行业（模糊匹配） | `"钢铁"` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大100） | `20` |

### 响应字段（关键）

```json
{
  "items": [
    {
      "ownerName": "张三",
      "ownerBumen": "数字化部",
      "ownerTixi": "销售体系",
      "ownerZhiweizhuangtai": "在职",
      "opId": "a123456789",
      "opName": "2026年国网数据库维保项目",
      "opXmid": "SJ2026001",
      "opJieduan": "2.1激发需求",
      "opKnx": 60,
      "opXmlx": "维保",
      "opYwjhcplx": "项目服务",
      "opYwjhcpxlnew": "一般维保",
      "opYjfwksrq": "2026-01-01",
      "opYjfwjsrq": "2026-12-31",
      "opJsrq": "2026-06-30",
      "opJine": 110000,
      "opXyhtjsrq": "2027-06-30",
      "kehuName": "国网科技有限公司",
      "kehuQy": "北区",
      "kehuSs": "北京",
      "zzkehuName": "国网科技有限公司",
      "zzkehuQy": "北区",
      "zzkehuSs": "北京",
      "zzkehudahangye": "制造业",
      "zzkehuxiaohangye": "钢铁"
    }
  ],
  "total": 1, "page": 1, "pageSize": 10, "totalPages": 1
}
```

| 字段 | 含义 |
|------|------|
| **负责人字段** | |
| `ownerName` | 负责人姓名 |
| `ownerBumen` | 负责人部门 |
| `ownerTixi` | 负责人体系 |
| `ownerZhiweizhuangtai` | 职位状态 |
| **商机字段** | |
| `opId` | 商机ID（内部ID） |
| `opName` | 商机名称 |
| `opXmid` | 商机编号 |
| `opJieduan` | 商机阶段 |
| `opKnx` | 可能性（0-100） |
| `opXmlx` | 项目类型 |
| `opYwjhcplx` | 产品大类 |
| `opYwjhcpxlnew` | 产品小类 |
| `opYjfwksrq` | 预计服务开始日期 |
| `opYjfwjsrq` | 预计服务结束日期 |
| `opJsrq` | 结束日期 |
| `opJine` | 金额（元） |
| `opXyhtjsrq` | 续约合同结束日期 |
| **客户字段** | |
| `kehuName` | 客户名称 |
| `kehuQy` | 客户区域 |
| `kehuSs` | 客户所属 |
| **最终客户字段** | |
| `zzkehuName` | 最终客户名称 |
| `zzkehuQy` | 最终客户区域 |
| `zzkehuSs` | 最终客户所属 |
| **行业字段** | |
| `zzkehudahangye` | 最终客户大行业 |
| `zzkehuxiaohangye` | 最终客户小行业 |

---

## 常用查询示例

### 默认查询（当前年份）

```bash
cloudcc project opportunity
```

### 按负责人查询

```bash
cloudcc project opportunity --owner-name "张"
```

### 按客户查询

```bash
cloudcc project opportunity --kehu-name "国网"
```

### 按商机阶段查询

```bash
cloudcc project opportunity --jieduan "2.1激发需求"
```

### 按产品大类查询

```bash
cloudcc project opportunity --product-type "项目服务"
```

### 按金额范围查询

```bash
cloudcc project opportunity --jine-min 100000 --jine-max 500000
```

### 按日期范围查询（覆盖默认年份）

```bash
cloudcc project opportunity --end-date-from 2025-01-01 --end-date-to 2025-12-31
```

### 组合查询

```bash
cloudcc project opportunity --owner-name "张" --kehu-name "国网" --product-type "项目服务" --page-size 20
```

### 按行业查询

```bash
cloudcc project opportunity --industry "制造业"
```

### 按最终客户区域查询

```bash
cloudcc project opportunity --zzkehu-qy "北区"
```
