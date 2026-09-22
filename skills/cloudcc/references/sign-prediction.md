# 签单预测模块

## 命令概览

```bash
cloudcc project sign-prediction  [参数...]   # 查询签单预测列表
```

**输出固定为 JSON**（面向 Agent），所有命令默认 `--output json`。

---

## 业务说明

签单预测是销售漏斗中的重要环节，记录业务机会的签单预期情况。每条签单预测记录关联：
- **订单**（dd）：签单预测对应的订单信息
- **合同**（ht）：关联的合同信息
- **业务机会**（opportunity）：来源的业务机会
- **最终客户**（account）：最终客户信息
- **负责人**（ccuser）：签单负责人及其部门

---

## `project sign-prediction` — 签单预测查询

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--sign-name` | 签单编号（模糊匹配，`ywjhqdglmx.name`） | `202309134922950` |
| `--qdknx-min` | 签单可能性最小值（0-100，`ywjhqdglmx.qdknx >=`） | `60` |
| `--qdknx-max` | 签单可能性最大值（0-100，`ywjhqdglmx.qdknx <=`） | `100` |
| `--amount-min` | 签单可能性金额最小值（`ywjhqdglmx.ywjhjeknx >=`） | `100000` |
| `--amount-max` | 签单可能性金额最大值（`ywjhqdglmx.ywjhjeknx <=`） | `500000` |
| `--dd-name` | 订单编号（模糊匹配，`dd.name`） | `201812292244` |
| `--dd-mingcheng` | 订单名称（模糊匹配，`dd.ddmc`） | `"某项目"` |
| `--poqyrq-start` | 订单启用日期-起始日期（>=，格式：YYYY-MM-DD，`dd.poqyrq >=`） | `2024-01-01` |
| `--poqyrq-end` | 订单启用日期-结束日期（<=，格式：YYYY-MM-DD，`dd.poqyrq <=`） | `2024-12-31` |
| `--ht-name` | 合同名称（模糊匹配，`ht.name`） | `"某公司维保"` |
| `--htbh` | 合同编号（模糊匹配，`ht.htbh`） | `00022231` |
| `--op-name` | 业务机会名称（模糊匹配，`op.name`） | `"数据库维保"` |
| `--jsrq-start` | 业务机会结束日期-起始日期（>=，格式：YYYY-MM-DD，`op.jsrq >=`） | `2024-06-01` |
| `--jsrq-end` | 业务机会结束日期-结束日期（<=，格式：YYYY-MM-DD，`op.jsrq <=`） | `2024-12-31` |
| `--zzkehu-name` | 最终客户名称（模糊匹配，`zuizhongkehu.name`） | `"海尔"` |
| `--user-name` | 签单负责人姓名（模糊匹配，`ccuser.name`） | `"贾益清"` |
| `--bumen` | 签单负责人部门（模糊匹配，`suoyourenbumen/suoyourenshangjibumen`） | `"东区客户1部"` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大100） | `20` |

### 响应字段（关键）

```json
{
  "items": [
    {
      "id": "signPredictionId_xxx",
      "signName": "202309134922950",
      "qdknx": 100,
      "ywjhjeknx": 34883.72,
      "ywjhwgjeknx": 0,
      "qdzyjeknx": 34883.72,
      "chanpin": "服务/周期服务/年度运维",
      "currency": "CNY",
      "yifangqianyuegongsi": "某客户公司名称",
      "ddId": "ddId_xxx",
      "ddName": "201812292244",
      "ddMingcheng": "某项目订单",
      "poqyrq": "2024-01-15",
      "htId": "htId_xxx",
      "htName": "某合同名称",
      "htbh": "00022231",
      "opId": "opId_xxx",
      "opName": "业务机会名称",
      "jsrq": "2024-12-31",
      "zzkehuName": "海尔融资租赁股份有限公司",
      "userName": "贾益清",
      "bumen": "东区客户1部/国际事业部"
    }
  ],
  "total": 51834, "page": 1, "pageSize": 10, "totalPages": 5184
}
```

| 字段 | 含义 |
|------|------|
| **签单预测字段** | |
| `id` | 签单预测ID（内部ID） |
| `signName` | 签单编号（ywjhqdglmx.name） |
| `qdknx` | 签单可能性（0-100，如 100 表示 100%） |
| `ywjhjeknx` | 签单可能性金额（元） |
| `ywjhwgjeknx` | 签单可能性外购金额（元） |
| `qdzyjeknx` | 签单可能性自有金额（元） |
| `chanpin` | 产品信息（cpyl/cpel/cpsl 拼接，如 "服务/周期服务/年度运维"） |
| `currency` | 币种（ywjhqdglmx.currency，如 CNY/USD） |
| `yifangqianyuegongsi` | 乙方公司名称（ywjhqdglmx.yifangqianyuegongsi） |
| **订单字段** | |
| `ddId` | 订单ID |
| `ddName` | 订单编号（dd.name） |
| `ddMingcheng` | 订单名称（dd.ddmc） |
| `poqyrq` | 订单启用日期（dd.poqyrq） |
| **合同字段** | |
| `htId` | 合同ID |
| `htName` | 合同名称 |
| `htbh` | 合同编号 |
| **业务机会字段** | |
| `opId` | 业务机会ID |
| `opName` | 业务机会名称 |
| `jsrq` | 业务机会结束日期（op.jsrq） |
| **最终客户字段** | |
| `zzkehuName` | 最终客户名称 |
| **负责人字段** | |
| `userName` | 签单负责人姓名 |
| `bumen` | 签单负责人部门（suoyourenbumen/suoyourenshangjibumen 拼接） |

---

## 常用查询示例

### 默认查询（查所有签单预测）

```bash
cloudcc project sign-prediction
```

### 按签单编号查询

```bash
cloudcc project sign-prediction --sign-name "202309134922950"
```

### 按签单可能性范围查询

```bash
# 查可能性 >= 80% 的签单预测
cloudcc project sign-prediction --qdknx-min 80

# 查可能性在 60%-100% 之间的签单预测
cloudcc project sign-prediction --qdknx-min 60 --qdknx-max 100
```

### 按金额范围查询

```bash
# 查签单可能性金额 >= 10万的记录
cloudcc project sign-prediction --amount-min 100000

# 查签单可能性金额在 10万-50万之间的记录
cloudcc project sign-prediction --amount-min 100000 --amount-max 500000
```

### 按订单查询

```bash
# 按订单编号查询
cloudcc project sign-prediction --dd-name "201812292244"

# 按订单名称模糊查询
cloudcc project sign-prediction --dd-mingcheng "维保"

# 按订单启用日期范围查询
cloudcc project sign-prediction --poqyrq-start "2024-01-01" --poqyrq-end "2024-12-31"
```

### 按合同查询

```bash
# 按合同名称查询
cloudcc project sign-prediction --ht-name "某公司维保"

# 按合同编号查询
cloudcc project sign-prediction --htbh "00022231"
```

### 按业务机会查询

```bash
cloudcc project sign-prediction --op-name "数据库维保"

# 按业务机会结束日期范围查询
cloudcc project sign-prediction --jsrq-start "2024-06-01" --jsrq-end "2024-12-31"
```

### 按最终客户查询

```bash
cloudcc project sign-prediction --zzkehu-name "海尔"
```

### 按负责人查询

```bash
# 按负责人姓名查询
cloudcc project sign-prediction --user-name "贾益清"

# 按负责人部门查询
cloudcc project sign-prediction --bumen "东区客户1部"
```

### 组合查询

```bash
# 查某部门、可能性 >= 80%、金额 >= 10万的签单预测
cloudcc project sign-prediction --bumen "东区" --qdknx-min 80 --amount-min 100000 --page-size 20
```

---

## 数据权限说明

签单预测查询受**数据权限**控制，按 `ownerid`（签单负责人）过滤：
- **全部数据权限**：可查看所有签单预测
- **部门数据权限**：仅查看本部门及下级部门的签单预测
- **本人数据权限**：仅查看自己负责的签单预测

权限由系统管理员在 RBAC 系统中配置。

---

## 与其他模块的关系

```
业务机会 (opportunity)
    ↓ (YWJHID 关联)
签单预测 (ywjhqdglmx)
    ↓ (dingdan 关联)
订单 (dd)
    ↓ (id 关联)
合同 (htjc)
    ↓ (htname 关联)
合同详情 (contract)
    ↓ (zzyhmc 关联)
最终客户 (account)
```

**查询策略**：
- 已知业务机会编号 → 先用 `project opportunity --op-xmid` 查询，再用 `--op-name` 查签单预测
- 已知合同编号 → 直接用 `--htbh` 查签单预测
- 已知订单编号 → 直接用 `--dd-name` 查签单预测
- 按负责人查询 → 用 `--user-name` 或 `--bumen`
