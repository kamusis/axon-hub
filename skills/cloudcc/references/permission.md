# 权限管理模块

## 命令

### permission scope — 管辖范围概要

```bash
cloudcc permission scope
cloudcc permission scope --detail   # 显示详细用户列表
```

> **注意**：`scope` 只支持文本输出，不支持 `--output json`。

输出示例：
```
🔐 Authorization Scope
  Current User: yu.chang
  Is Super Admin: false
  Cached: true
  User Count: 25
  Cache Time: 2026-06-02T10:00:00
```

### permission query — 查询管辖用户

```bash
cloudcc permission query [参数...] --output json
```

**参数：**

| 参数 | 说明 | 示例 |
|------|------|------|
| `--name` | 姓名（模糊） | `"张"` |
| `--email` | 邮箱（模糊） | `"enmo"` |
| `--region` | 区域（多选逗号分隔） | `"西区,北区"` |
| `--dept` | 部门（模糊） | `"销售"` |
| `--status` | 职位状态（多选） | `"在职,试用期"` |
| `--system` | 体系（多选） | `"销售体系"` |
| `--page` | 页码（默认 1） | `2` |
| `--pageSize` | 每页数量（默认 50） | `100` |
| `--output` | 输出格式 | `table` / `json` |

### permission refresh — 刷新缓存

```bash
cloudcc permission refresh
```

输出：
```
✓ Authorization scope cache refreshed successfully!
  User Count: 25
  Cache Time: 2026-06-02T17:00:00
```

---

## JSON 响应格式

**注意：数据数组字段名是 `records`，不是 `items`！**

```json
{
  "records": [
    {
      "ccuserName": "张三",
      "ccuserEmail": "zhangsan@enmo.com",
      "ccuserSqy": "西区",
      "ccuserBumen": "恩墨>销售部>西区一部",
      "ccuserZylx": "销售体系",
      "ccuserZwzt": "在职"
    }
  ],
  "total": 25,
  "size": 50,
  "current": 1,
  "pages": 1
}
```

### 字段说明

| 字段 | 含义 |
|------|------|
| `ccuserName` | 姓名 |
| `ccuserEmail` | 邮箱 |
| `ccuserSqy` | 区域 |
| `ccuserBumen` | 部门（多级路径） |
| `ccuserZylx` | 体系 |
| `ccuserZwzt` | 职位状态 |

---

## 常用查询模式

```bash
# 查所有管辖用户
cloudcc permission query --output json

# 按区域筛选
cloudcc permission query --region "西区,北区" --status "在职" --output json

# 按姓名搜索
cloudcc permission query --name "张" --output json

# 按部门搜索
cloudcc permission query --dept "销售" --output json
```
