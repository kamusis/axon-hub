# 收入预测模块

## 命令概览

```bash
cloudcc project revenue-prediction  [参数...]   # 查询收入预测列表
```

**输出固定为 JSON**（面向 Agent），所有命令默认 `--output json`。

---

## 业务说明

收入预测是项目管理和财务规划的重要组成部分，记录预期收入的确认情况。每条收入预测记录关联：
- **订单**（dd）：收入预测对应的订单信息
- **合同**（ht）：关联的合同信息
- **业务机会**（opportunity）：来源的业务机会
- **最终客户**（account）：最终客户信息
- **负责人**（ccuser）：收入负责人及其部门

---

## `project revenue-prediction` — 收入预测查询

### 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--sr-name` | 收入预测编号（模糊匹配，`ywjhsrycmx.name`） | `20231116858880` |
| `--knx-min` | 可能性最小值（0-100，`ywjhsrycmx.knx >=`） | `80` |
| `--knx-max` | 可能性最大值（0-100，`ywjhsrycmx.knx <=`） | `100` |
| `--amount-min` | 子项金额最小值（`ywjhsrycmx.shourukenengjine >=`） | `1000` |
| `--amount-max` | 子项金额最大值（`ywjhsrycmx.shourukenengjine <=`） | `5000` |
| `--dd-name` | 订单编号（模糊匹配，`dd.name`） | `202202078811` |
| `--dd-mingcheng` | 订单名称（模糊匹配，`dd.ddmc`） | `"某培训项目"` |
| `--poqyrq-start` | 订单启用日期-起始日期（>=，格式：YYYY-MM-DD，`dd.poqyrq >=`） | `2024-01-01` |
| `--poqyrq-end` | 订单启用日期-结束日期（<=，格式：YYYY-MM-DD，`dd.poqyrq <=`） | `2024-12-31` |
| `--ht-name` | 合同名称（模糊匹配，`ht.name`） | `"某银行培训"` |
| `--htbh` | 合同编号（模糊匹配，`ht.htbh`） | `00027939` |
| `--op-name` | 业务机会名称（模糊匹配，`op.name`） | `"墨天轮付费合同"` |
| `--jsrq-start` | 业务机会结束日期-起始日期（>=，格式：YYYY-MM-DD，`op.jsrq >=`） | `2024-06-01` |
| `--jsrq-end` | 业务机会结束日期-结束日期（<=，格式：YYYY-MM-DD，`op.jsrq <=`） | `2024-12-31` |
| `--zzkehu-name` | 最终客户名称（模糊匹配，`zuizhongkehu.name`） | `"哈尔滨银行"` |
| `--user-name` | 负责人姓名（模糊匹配，`ccuser.name`） | `"张海波"` |
| `--bumen` | 负责人部门（模糊匹配，`suoshubumentxt`） | `"质量与流程优化部"` |
| `--page` | 页码 | `1` |
| `--page-size` | 每页条数（最大100） | `20` |

### 响应字段（关键）

```json
{
  "items": [
    {
      "id": "c9820236490e15eiyhol",
      "srName": "20231116858880",
      "knx": 100,
      "zixiangjine": 1200,
      "zixiangtishuijine": 1132.08,
      "zixiangtishuikenengxingjine": 1132.08,
      "chanpin": "服务/互联网服务/培训服务",
      "ddId": null,
      "ddName": null,
      "ddMingcheng": null,
      "poqyrq": null,
      "htId": null,
      "htName": null,
      "htbh": null,
      "opId": "0022023907DFAECW1zyo",
      "opName": "2023年墨天轮用户线上付费合同-用于开票",
      "jsrq": null,
      "zzkehuName": null,
      "userName": "袁兰兰",
      "bumen": "数据库管理服务产品群>互联网平台服务部>运营发展部"
    }
  ],
  "total": 39610, "page": 1, "pageSize": 10, "totalPages": 7922
}
```

| 字段 | 含义 |
|------|------|
| **收入预测字段** | |
| `id` | 收入预测ID（内部ID） |
| `srName` | 收入预测编号（ywjhsrycmx.name） |
| `knx` | 可能性（0-100，如 100 表示 100%） |
| `zixiangjine` | 子项金额（元，ywjhsrycmx.shourukenengjine） |
| `zixiangtishuijine` | 子项提税金额（元，ywjhsrycmx.shourutishuijine） |
| `zixiangtishuikenengxingjine` | 子项提税可能性金额（元，ywjhsrycmx.kenengtishuijine） |
| `chanpin` | 产品信息（cpyl/cpel/cpsl 拼接，如 "服务/互联网服务/培训服务"） |
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
| `userName` | 负责人姓名 |
| `bumen` | 负责人部门（层级路径，如 "A>B>C"） |

---

## 常用查询示例

### 默认查询（查所有收入预测）

```bash
cloudcc project revenue-prediction
```

### 按收入预测编号查询

```bash
cloudcc project revenue-prediction --sr-name "20231116858880"
```

### 按可能性范围查询

```bash
# 查可能性 = 100% 的收入预测
cloudcc project revenue-prediction --knx-min 100 --knx-max 100

# 查可能性 >= 80% 的收入预测
cloudcc project revenue-prediction --knx-min 80
```

### 按金额范围查询

```bash
# 查子项金额 >= 1000 元的记录
cloudcc project revenue-prediction --amount-min 1000

# 查子项金额在 1000-5000 元之间的记录
cloudcc project revenue-prediction --amount-min 1000 --amount-max 5000
```

### 按订单查询

```bash
# 按订单编号查询
cloudcc project revenue-prediction --dd-name "202202078811"

# 按订单名称模糊查询
cloudcc project revenue-prediction --dd-mingcheng "培训"

# 按订单启用日期范围查询
cloudcc project revenue-prediction --poqyrq-start "2024-01-01" --poqyrq-end "2024-12-31"
```

### 按合同查询

```bash
# 按合同名称查询
cloudcc project revenue-prediction --ht-name "哈尔滨银行培训"

# 按合同编号查询
cloudcc project revenue-prediction --htbh "00027939"
```

### 按业务机会查询

```bash
cloudcc project revenue-prediction --op-name "墨天轮付费合同"

# 按业务机会结束日期范围查询
cloudcc project revenue-prediction --jsrq-start "2024-06-01" --jsrq-end "2024-12-31"
```

### 按最终客户查询

```bash
cloudcc project revenue-prediction --zzkehu-name "哈尔滨银行"
```

### 按负责人查询

```bash
# 按负责人姓名查询
cloudcc project revenue-prediction --user-name "张海波"

# 按负责人部门查询
cloudcc project revenue-prediction --bumen "质量与流程优化部"
```

### 组合查询

```bash
# 查可能性 = 100%、子项金额 >= 1000 元的记录
cloudcc project revenue-prediction --knx-min 100 --knx-max 100 --amount-min 1000 --page-size 20

# 查某部门、高可能性的收入预测
cloudcc project revenue-prediction --bumen "经营发展群" --knx-min 80 --page-size 30
```

---

## 数据权限说明

收入预测查询受**数据权限**控制，按 `ownerid`（负责人）过滤：
- **全部数据权限**：可查看所有收入预测
- **部门数据权限**：仅查看本部门及下级部门的收入预测
- **本人数据权限**：仅查看自己负责的收入预测

权限由系统管理员在 RBAC 系统中配置。

---

## 与其他模块的关系

```
业务机会 (opportunity)
    ↓ (YWJHID 关联)
收入预测 (ywjhsrycmx)
    ↓ (dingdan 关联)
订单 (dd)
    ↓ (id 关联)
合同关联表 (htjc)
    ↓ (htname 关联)
合同详情 (contract)
    ↓ (zzyhmc 关联)
最终客户 (account)
```

**查询策略**：
- 已知业务机会编号 → 先用 `project opportunity --op-xmid` 查询，再用 `--op-name` 查收入预测
- 已知合同编号 → 直接用 `--htbh` 查收入预测
- 已知订单编号 → 直接用 `--dd-name` 查收入预测
- 按负责人查询 → 用 `--user-name` 或 `--bumen`
