# 客户管理模块

## 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `customer account query` | 查询客户列表 | `--keyword` |
| `customer account search` | 根据客户名称精确搜索客户 | `--name` |
| `customer account create` | 创建客户 | `--name`, `--khjc`, `--khdj`, `--qy`, `--khszcs`, `--khhyc` |
| `customer account industries` | 查询行业选项（大行业 + 小行业） | 无 |
| `customer account cities` | 搜索城市（模糊匹配） | `--keyword` |
| `customer contact query` | 查询联系人列表 | `--keyword` |
| `customer contact search` | 根据三元组精确搜索联系人 | `--name`, `--shouji`, `--account` |
| `customer contact create` | 创建联系人 | `--account`, `--name`, `--bumen`, `--zhiwu`, `--shouji`, `--source` |

> **交互原则**：当用户要求添加客户或联系人时，Agent 应优先通过交互式问答逐步引导用户确认所需信息，而非要求用户一次性提供全部字段，使交互体验更加友好自然。

---

## 客户查询

```bash
cloudcc customer account query --keyword "自然之心" --page 1 --page-size 20 --output json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--keyword` | 是 | 客户名称、客户简称或客户编号（模糊匹配） |
| `--page` | 否 | 页码，默认 1 |
| `--page-size` | 否 | 每页条数，默认 20 |
| `--output` | 否 | 输出格式：table / json |

### 响应字段

| 字段 | 说明 |
|------|------|
| id | 客户ID |
| name | 客户名称 |
| khbh | 客户编号 |
| ownerName | 负责人姓名 |

---

## 客户精确搜索

根据客户名称精确搜索客户（不带数据权限过滤，允许跨权限查找），用于创建联系人前确认客户是否存在。

```bash
cloudcc customer account search --name "自然之心科技有限公司" --output json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name` | 是 | 客户名称（精确匹配） |
| `--output` | 否 | 输出格式：table / json |

### 响应字段

| 字段 | 说明 |
|------|------|
| id | 客户ID |
| name | 客户名称 |
| khbh | 客户编号 |
| ownerName | 负责人姓名 |

### 使用说明

- 返回 null 表示客户不存在
- 即使存在同名客户也只返回第一条（历史数据可能有重复）
- 不受数据权限限制，可查找其他同事负责的客户

---

## 客户创建

> **前置步骤 1 — 重复检查（必须）**：创建客户前，**必须**先执行 `cloudcc customer account search --name "客户名称"` 检查是否已存在同名客户：
> - 如果返回客户信息（非 null）：说明客户已存在，**禁止重复创建**，直接告知用户该客户已存在并展示客户名称、编号和负责人信息
> - 如果返回 null：客户不存在，可继续执行创建流程
>
> **前置步骤 2 — 获取行业选项**：Agent 创建客户前，**必须**先执行 `cloudcc customer account industries` 从后端获取行业选项列表，根据用户提供的行业信息从中选择最匹配的行业名称作为 `--khhyc` 参数值。**禁止**凭记忆或猜测填写行业名称。

```bash
cloudcc customer account create --name "客户名称" --khdj "核心" --qy "东区" --khszcs "上海" --khhyc "软件开发" --output json
```

### 参数说明

| 参数 | 必填 | 说明 | 可选值 |
|------|------|------|--------|
| `--name` | 是 | 客户名称 | - |
| `--khjc` | 是 | 客户简称（Agent 可自动从客户名称提取，如"自然之心科技有限公司"→"自然之心"） | - |
| `--khdj` | 是 | 客户等级（后端自动转为完整格式，如“核心”→“A（核心）”） | 核心、重要、普通、待拓展 |
| `--qy` | 是 | 客户所在区域 | 北区、东区、西区、南区、海外 |
| `--khszcs` | 是 | 客户所在城市名称（后端自动匹配 ID） | - |
| `--khhyc` | 是 | 客户行业名称（**必须先执行 `cloudcc customer account industries` 获取实际行业选项**，后端同时模糊匹配大行业和小行业名称） | - |
| `--beizhu` | 否 | 备注说明（最大 4000 字，默认“无”。Agent 可搜索客户相关资料并总结一句关键有用信息填入；如未找到相关资料，则填写“未找到相关资料”） | - |
| `--output` | 否 | 输出格式 | table / json |

### 响应字段

| 字段 | 说明 |
|------|------|
| id | 客户ID |
| name | 客户名称 |
| khbh | 客户编号（系统自动生成） |
| khjc | 客户简称 |
| khdj | 客户等级 |
| qy | 所在区域 |
| khszcs | 客户所在城市（sjdzk ID） |
| khszcsName | 客户所在城市名称 |
| shengfen | 客户所在省份 |
| khdhycz | 大行业ID（自动匹配） |
| khdhyczName | 大行业名称（自动匹配） |
| khxhycz | 小行业ID（自动匹配） |
| khxhyczName | 小行业名称（自动匹配） |
| khhyc | 客户行业（格式：大行业-小行业） |
| ownerid | 负责人ID |
| ownerName | 负责人姓名 |
| url | 查看链接（可在系统中查看客户详情） |

### 示例

```bash
# 创建核心客户（输入行业名称，后端自动匹配大行业和小行业）
cloudcc customer account create \
  --name "自然之心科技有限公司" \
  --khjc "自然之心" \
  --khdj "核心" \
  --qy "东区" \
  --khszcs "上海" \
  --khhyc "软件开发" \
  --output json

# 也可以输入大行业名称（如果唯一匹配到一条记录）
cloudcc customer account create \
  --name "自然之心科技有限公司" \
  --khdj "重要" \
  --qy "东区" \
  --khszcs "上海" \
  --khhyc "IT/互联网" \
  --output json
```

---

## 行业选项查询

查询客户大行业和小行业的可选值（存储在 optioncfg 表中，大行业和小行业存在层级关系）。

```bash
# 查询行业选项（表格格式）
cloudcc customer account industries

# 查询行业选项（JSON 格式）
cloudcc customer account industries --output json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--output` | 否 | 输出格式：table / json |

### 响应字段（JSON）

返回字符串数组，每个元素格式为 `"大行业名称-小行业名称"`，例如：
```json
[
  "IT/互联网-软件开发",
  "IT/互联网-人工智能",
  "金融-银行"
]
```

### 使用说明

创建客户时，**直接传入行业名称即可**（大行业或小行业名称均可），后端会同时模糊匹配：
1. 执行 `cloudcc customer account industries` 查看可用行业选项
2. 使用大行业或小行业名称作为 `--khhyc` 参数值
3. 后端同时在大行业和小行业名称中模糊匹配，唯一匹配时自动设置
4. 如果匹配到 0 条或多条记录，会返回错误提示，让用户选择更精准的

---

## 城市搜索

根据关键字模糊搜索城市（存储在 sjdzk 表中），用于客户创建时选择城市。

```bash
# 搜索包含“邯郸”的城市
cloudcc customer account cities --keyword "邯郸"

# JSON 格式
cloudcc customer account cities --keyword "北京" --output json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--keyword` | 是 | 城市名称关键字（模糊匹配） |
| `--output` | 否 | 输出格式：table / json |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| id | 城市ID（sjdzk 表） |
| yjcs | 省份 |
| name | 城市名称 |

### 使用说明

创建客户时，**直接传入城市名称作为 `--khszcs` 参数值**，后端会自动从 sjdzk 表模糊匹配：
1. 执行 `cloudcc customer account cities --keyword "关键字"` 搜索城市
2. 使用城市名称作为 `--khszcs` 参数值
3. 如果匹配到 0 条或多条记录，后端会提示错误，需精确指定

---

## 联系人查询

```bash
cloudcc customer contact query --keyword "张三" --output json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--keyword` | 是 | 联系人姓名、联系人编号（模糊匹配）或客户编号（精确匹配） |
| `--account-id` | 否 | 按客户ID过滤 |
| `--page` | 否 | 页码，默认 1 |
| `--page-size` | 否 | 每页条数，默认 20 |
| `--output` | 否 | 输出格式：table / json |

### 响应字段

| 字段 | 说明 |
|------|------|
| id | 联系人ID |
| name | 联系人姓名 |
| lxrbh | 联系人编号 |
| accountName | 所属客户名称 |
| ownerName | 负责人姓名 |

---

## 联系人精确搜索

根据三元组（姓名 + 手机号 + 客户名称/编号）精确搜索联系人（不带数据权限过滤），用于创建联系人前确认联系人是否已存在。

```bash
cloudcc customer contact search --name "张三" --shouji "13800138000" --account "自然之心" --output json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name` | 是 | 联系人姓名（精确匹配） |
| `--shouji` | 是 | 手机号（精确匹配） |
| `--account` | 是 | 客户名称或客户编号（系统自动解析为客户ID） |
| `--output` | 否 | 输出格式：table / json |

### 响应字段

| 字段 | 说明 |
|------|------|
| id | 联系人ID |
| name | 联系人姓名 |
| lxrbh | 联系人编号 |
| accountName | 所属客户名称 |
| ownerName | 负责人姓名 |

### 使用说明

- 返回 null 表示联系人不存在
- 客户参数支持名称/编号模糊匹配（与创建联系人时的 `--account` 逻辑一致）
- 不受数据权限限制，可查找其他同事负责的联系人

---

## 联系人创建

> **前置步骤 — 重复检查（必须）**：创建联系人前，**必须**先执行 `cloudcc customer contact search --name "姓名" --shouji "手机号" --account "客户名称"` 检查是否已存在相同联系人：
> - 如果返回联系人信息（非 null）：说明联系人已存在，**禁止重复创建**，直接告知用户该联系人已存在并展示姓名、编号、所属客户和负责人信息
> - 如果返回 null：联系人不存在，可继续执行创建流程

```bash
cloudcc customer contact create --account "自然之心" --name "张三" --bumen "销售部" --zhiwu "经理" --shouji "13800138000" --source "主动销售" --output json
```

### 参数说明

| 参数 | 必填 | 说明 |
|------|------|------|
| `--account` | 是 | 客户名称、简称或编号（用于关联客户） |
| `--name` | 是 | 联系人姓名 |
| `--bumen` | 是 | 部门 |
| `--zhiwu` | 是 | 职务 |
| `--shouji` | 是 | 手机号 |
| `--email` | 否 | 邮箱 |
| `--dianhua` | 否 | 电话 |
| `--source` | 是 | 联系人来源 |
| `--beizhu` | 否 | 备注说明（选填） |
| `--output` | 否 | 输出格式：table / json |

### 客户匹配规则

- 使用 `--account` 参数按客户名称、客户简称或客户编号模糊匹配（不受数据权限限制，可为其他同事负责的客户创建联系人）
- 匹配到 **0 条**：提示客户不存在，需先创建客户（参见 [客户创建](#客户创建) 章节），创建完成后继续使用已识别的信息创建联系人
- 匹配到 **1 条**：自动关联该客户
- 匹配到 **多条**：展示所有匹配客户的名称、编号和负责人，要求用户输入精确的客户编号

### 响应字段

| 字段 | 说明 |
|------|------|
| id | 联系人ID |
| name | 姓名 |
| lxrbh | 联系人编号 |
| accountid | 关联客户ID |
| accountName | 关联客户名称 |
| bumen | 部门 |
| zhiwu | 职务 |
| shouji | 手机 |
| email | 邮箱 |
| dianhua | 电话 |
| lxrly | 联系人来源 |
| lxrzt | 联系人状态 |
| ownerid | 负责人ID |
| ccuserEmail | 负责人邮箱 |
| url | 查看链接 |

---

## 名片扫描添加联系人

当用户提供名片图片时，按以下流程操作：

### 执行步骤

1. **识别名片图片**：提取姓名、部门、职务、手机、邮箱、电话、公司等字段
2. **展示识别结果**：将提取的信息展示给用户确认
3. **补充必填字段**：如名片上缺少以下必填信息，需询问用户补充：
   - 姓名（name）
   - 部门（bumen）
   - 职务（zhiwu）
   - 手机（shouji）
   - 联系人来源（source）— 名片上通常没有，需主动询问
4. **查找关联客户**：使用公司名搜索客户（`cloudcc customer account search --name "公司名"`）
   - 匹配到客户（非 null）：确认关联
   - 未匹配到客户（返回 null）：提示用户是否需要先创建客户，如用户确认则按 [客户创建](#客户创建) 流程执行（含重复检查），创建完成后继续创建联系人
5. **联系人重复检查**：执行 `cloudcc customer contact search --name "姓名" --shouji "手机号" --account "客户名称"` 检查联系人是否已存在
   - 如果已存在（非 null）：**禁止重复创建**，告知用户联系人已存在并展示信息
   - 如果不存在（返回 null）：继续执行创建
6. **执行创建**：调用 `customer contact create` 命令

### 字段映射

| 名片字段 | CLI 参数 | 是否必填 |
|----------|----------|----------|
| 姓名 | `--name` | 必填 |
| 部门 | `--bumen` | 必填 |
| 职务 | `--zhiwu` | 必填 |
| 手机 | `--shouji` | 必填 |
| 邮箱 | `--email` | 选填 |
| 电话 | `--dianhua` | 选填 |
| 公司 | 用于 `--account` 搜索 | - |
| 来源 | `--source` | 必填（需询问用户） |
| 备注 | `--beizhu` | 选填（Agent 可搜索客户相关资料并总结关键信息填入） |

### 约束

- 所有必填字段不可省略，即使名片上未找到也必须向用户询问
- **创建前必须先执行重复检查**：客户用 `customer account search` 检查，联系人用 `customer contact search` 检查，已存在则禁止重复创建
- 创建前必须确认客户在系统中存在，如不存在需先创建客户
- 客户搜索不受数据权限限制，可为其他同事负责的客户添加联系人
- 创建成功后展示返回的查看链接
