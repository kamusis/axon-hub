# 销售活动模块

## 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `activity query` | 查询销售活动列表 | `--date` |
| `activity create` | 创建销售活动 | `--opportunity`, `--contact`, `--date`, `--type`, `--result`, `--importance`, `--next-step`, `--feedback`, `--glcj`, `--gxjmd` |

> **交互原则**：当用户要求添加销售活动时，Agent 应优先通过交互式问答逐步引导用户确认所需信息，而非要求用户一次性提供全部字段，使交互体验更加友好自然。

---

## 创建活动

> **前置步骤 1 — 确认业务机会**：Agent 创建销售活动前，**必须**先确认业务机会存在：
> - 使用 `cloudcc project opportunity query --keyword "业务机会编号或名称"` 搜索业务机会
> - 如果返回 0 条：提示用户业务机会不存在，需先创建业务机会
> - 如果返回 1 条：自动使用该业务机会的编号
> - 如果返回多条：展示所有匹配的业务机会名称、编号、阶段和金额，要求用户选择或输入精确编号
>
> **前置步骤 2 — 确认主要联系人**：Agent 需确认主要联系人存在：
> - 使用 `cloudcc customer contact query --keyword "联系人姓名或编号"` 搜索联系人
> - 如果返回 0 条：提示用户联系人不存在，需先创建联系人（参见 [联系人创建](customer.md#联系人创建) 章节）
> - 如果返回 1 条：自动使用该联系人的编号
> - 如果返回多条：展示所有匹配的联系人的姓名、编号、所属客户和负责人，要求用户选择或输入精确编号

```bash
cloudcc activity create \
  --opportunity "业务机会编号或名称" \
  --contact "联系人编号或名称" \
  --date "2026-07-30" \
  --type "见面拜访" \
  --result "活动结果描述" \
  --importance "普通" \
  --next-step "下一步安排" \
  --feedback "无" \
  --glcj "中层(部门总经理/副总)" \
  --gxjmd "信任(对我司或人非常认可)" \
  [可选参数...]
```

### 必填参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--opportunity` | 业务机会编号或名称（模糊匹配，必须唯一） | `"20260186825"` |
| `--contact` | 主要联系人编号或名称（按客户过滤，必须唯一） | `"2023032931098"` |
| `--date` | 活动日期（格式 YYYY-MM-DD） | `"2026-07-30"` |
| `--type` | 活动类型（见下方枚举） | `"见面拜访"` |
| `--result` | 活动结果（最多4000字符） | `"客户对方案认可"` |
| `--importance` | 重要程度：`普通` / `重要`（默认普通） | `"重要"` |
| `--next-step` | 下一步安排（最多4000字符） | `"提供技术方案"` |
| `--feedback` | 反馈涉及（多选以;分隔，见下方枚举，默认`无`） | `"售前同步(邮件触发到售前相关人员)"` |
| `--glcj` | 联系人在公司层级（见下方枚举） | `"中层(部门总经理/副总)"` |
| `--gxjmd` | 联系人关系紧密度（见下方枚举） | `"信任(对我司或人非常认可)"` |

### 可选参数

| 参数 | 默认 | 说明 |
|------|------|------|
| `--cpfl` | — | 产品分类（反馈涉及含产品方面时必填） |
| `--cpfk` | — | 产品反馈（反馈涉及含产品方面时必填） |
| `--output` | table | 输出格式：table / json |

### 枚举值（必须包含括号内描述）

**活动类型 `--type`：**
- `电话沟通`
- `见面拜访`
- `组织多人参加的技术交流`
- `参加议标投标`
- `餐饮招待`
- `出差陪同`
- `陪同来司参观`
- `投标结果反馈`

**反馈涉及 `--feedback`（多选以 `;` 分隔）：**
- `无`（默认）
- `收款方面(邮件触发到运营相关人员)`
- `产品方面(邮件触发到产品相关人员)`
- `交付问题(邮件触发到交付相关人员)`
- `售前同步(邮件触发到售前相关人员)`
- `合作伙伴经理(邮件触发到合作伙伴负责人)`
- `其他`

> **条件校验**：反馈涉及包含“产品方面”时，`--cpfl` 和 `--cpfk` 均为必填。

**联系人在公司层级 `--glcj`：**
- `高层(公司分管副总及以上)`
- `中层(部门总经理/副总)`
- `操作层(室经理/主管/组长)`
- `执行层(工程师/专员)`

**联系人关系紧密度 `--gxjmd`：**
- `同盟(会推荐给其他客户)`
- `信任(对我司或人非常认可)`
- `中立(和其他友商一视同仁)`
- `反对(支持友商/不信任我司或人)`

**产品分类 `--cpfl`：**
- `软件-zDATA`
- `软件-zCloud云管平台`
- `软件-MogDB`
- `软件-Bethune X`
- `软件-ZDBM：备份一体机`
- `软件-SQM`
- `软件-MyData：MySQL数据库一体机`
- `河图数据分析系统`
- `软件-zAIoT`

### 创建示例

```bash
# 基础创建
cloudcc activity create \
  --opportunity "20260186825" \
  --contact "2023032931098" \
  --date "2026-07-30" \
  --type "电话沟通" \
  --result "初步沟通客户需求" \
  --next-step "跟进客户反馈" \
  --feedback "无" \
  --glcj "高层(公司分管副总及以上)" \
  --gxjmd "信任(对我司或人非常认可)"

# 完整参数创建
cloudcc activity create \
  --opportunity "20260186825" \
  --contact "2023032931098" \
  --date "2026-07-30" \
  --type "见面拜访" \
  --importance "重要" \
  --result "客户对MogDB方案认可" \
  --next-step "提供详细技术方案" \
  --feedback "产品方面(邮件触发到产品相关人员);售前同步(邮件触发到售前相关人员)" \
  --glcj "中层(部门总经理/副总)" \
  --gxjmd "信任(对我司或人非常认可)" \
  --cpfl "软件-MogDB" \
  --cpfk "客户对MogDB高可用方案有需求" \
  --output json
```

### 创建响应

```json
{
  "name": "20260730123456",
  "queryUrl": "https://ccc.enmotech.com/query.action?id=a93xxx&m=query"
}
```

| 字段 | 含义 |
|------|------|
| `name` | 活动编号 |
| `queryUrl` | Oracle CC 系统跳转链接 |

---

## 交互式创建销售活动

当用户口头描述要添加销售活动时，按以下流程操作：

### 执行步骤

1. **收集基本信息**：询问用户以下信息（可一次性提供或逐步补充）：
   - 业务机会（编号或名称）
   - 主要联系人（姓名或编号）
   - 活动日期（默认今天）
   - 活动类型
   - 活动结果
   - 重要程度（默认“普通”）
   - 下一步安排
   - 反馈涉及（默认“无”）
   - 联系人在公司层级
   - 联系人关系紧密度

2. **确认业务机会**：使用 `cloudcc project opportunity query --keyword "业务机会"` 搜索
   - 匹配到 0 条：提示业务机会不存在，需先创建业务机会
   - 匹配到 1 条：自动使用该业务机会的编号
   - 匹配到多条：展示所有匹配结果，要求用户选择或输入精确编号

3. **确认主要联系人**：使用 `cloudcc customer contact query --keyword "联系人"` 搜索
   - 匹配到 0 条：提示联系人不存在，引导用户先创建联系人（参见 [联系人创建](customer.md#联系人创建) 章节）
   - 匹配到 1 条：自动使用该联系人的编号
   - 匹配到多条：展示所有匹配结果，要求用户选择或输入精确编号

4. **补充可选字段**：根据活动类型和反馈涉及判断是否需要补充：
   - 如果反馈涉及包含“产品方面(邮件触发到产品相关人员)”，必须询问：
     - 产品分类（`--cpfl`）
     - 产品反馈（`--cpfk`）

5. **确认信息**：将收集到的所有信息汇总展示给用户确认

6. **执行创建**：调用 `activity create` 命令，创建成功后展示活动编号和查看链接

### 字段映射

| 用户输入 | CLI 参数 | 是否必填 | 默认值 |
|----------|----------|----------|--------|
| 业务机会 | `--opportunity` | 必填 | - |
| 主要联系人 | `--contact` | 必填 | - |
| 活动日期 | `--date` | 必填 | 今天 |
| 活动类型 | `--type` | 必填 | - |
| 活动结果 | `--result` | 必填 | - |
| 重要程度 | `--importance` | 必填 | 普通 |
| 下一步安排 | `--next-step` | 必填 | - |
| 反馈涉及 | `--feedback` | 必填 | 无 |
| 联系人在公司层级 | `--glcj` | 必填 | - |
| 联系人关系紧密度 | `--gxjmd` | 必填 | - |
| 产品分类 | `--cpfl` | 条件必填（反馈含产品方面时） | - |
| 产品反馈 | `--cpfk` | 条件必填（反馈含产品方面时） | - |

### 约束

- 所有必填字段不可省略，用户未提供时必须主动询问
- 枚举值必须包含括号内完整描述，如 `高层(公司分管副总及以上)`，不可省略括号部分
- 创建前必须先确认业务机会和联系人存在，不存在则引导用户先创建
- 创建成功后必须展示活动编号和查看链接

---

## 查询活动

## 参数参考

### 基础筛选

| 参数 | 说明 | 示例 |
|------|------|------|
| `--date` | 日期范围 | `本月` `上月` `本周` `近7天` `近30天` `2026-01-01:2026-12-31` |
| `--customer` | 客户名称（模糊） | `"某科技"` |
| `--creator` | 创建人姓名 | `"张三"` |
| `--region` | 区域（逗号分隔） | `西区,北区` |
| `--op-knx` | 可能性范围 | `60-100` |
| `--type` | 活动类型（逗号分隔） | `电话沟通,见面拜访` |
| `--industry` | 行业（逗号分隔） | `制造业,金融业` |

> **注意**：`--date` 不支持"昨天"、"今天"，需用明确范围如 `2026-06-02:2026-06-02`

### 商机参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--op-name` | 商机名称（模糊） | `"数据库"` |
| `--op-code` | 商机编号（精确） | `"20260587919"` |
| `--op-stage` | 商机阶段 | `3.1立项` `4.1方案设计` `7.5购买签约` |
| `--op-product` | 产品大类 | `项目服务` `自有软件` `硬件设备` |
| `--op-customer` | 新老客户 | `新客户` `老客户` |

### 客户详情参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--kehu-qy` | 客户区域 | `西区` |
| `--kehu-ss` | 客户省份 | `四川省` |
| `--kehu-industry` | 客户大行业 | `制造业` |

### 创建人详情参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--creator-email` | 创建人邮箱 | `"user@enmo.com"` |
| `--creator-dept` | 创建人部门 | `"销售部"` |
| `--creator-status` | 职位状态 | `在职` `试用期` |

### 输出控制

| 参数 | 默认 | 说明 |
|------|------|------|
| `--output` | table | 格式：table / json / csv |
| `--output-file` | — | 导出到文件路径 |
| `--simple` | false | 简化 7 列模式 |
| `--page` | 1 | 页码 |
| `--pageSize` | 10 | 每页数量（驼峰命名） |

### 智能分页（配合 `--page-all`）

| 参数 | 默认 | 说明 |
|------|------|------|
| `--page-all` | false | 自动遍历所有页 |
| `--page-limit` | 0 | 最大页数（0=自动策略） |
| `--page-size` | 50 | 每页记录数（连字符命名，最大200） |
| `--page-delay` | 300 | 请求间隔ms |

> **重要**：普通查询用 `--pageSize`（驼峰），智能分页用 `--page-size`（连字符）。

**智能分页策略：**
- ≤500条 → 直接全取
- 500-1000条 → 限制20页
- 1000-10000条 + `--output-file` → 流式写入
- >10000条 → 拒绝执行，提示添加过滤条件

### 高级参数

| 参数 | 说明 |
|------|------|
| `--config` | 从 JSON 配置文件读取查询参数 |
| `--validate-only` | 仅验证参数，不执行查询 |
| `--json-help` | 输出 JSON 格式帮助信息 |

---

## JSON 响应字段

```json
{
  "items": [
    {
      "xshdName": "拜访客户",
      "xshdHdrq": "2026-05-15",
      "xshdHdlx": "见面拜访",
      "xshdZycd": "高",
      "xshdHdjg": "",
      "xshdHdxq": "讨论数据库方案",
      "xshdZylxr": "张三",
      "xshdYewujihuijieduan": "3.1立项",
      "opName": "数据库统一管理",
      "opXmid": "20260587919",
      "opJieduan": "3.1立项",
      "opKnx": 80,
      "opXmlx": "项目服务",
      "opJine": 500000.00,
      "kehuName": "某科技公司",
      "kehuQy": "西区",
      "kehuSs": "四川省",
      "kehudahangye": "制造业",
      "ccuserName": "李四",
      "ccuserEmail": "lisi@enmo.com",
      "ccuserSqy": "西区",
      "ccuserBumen": "销售一部"
    }
  ],
  "total": 150,
  "page": 1,
  "pageSize": 10,
  "totalPages": 15,
  "hasNext": true,
  "hasPrevious": false
}
```

### 字段中文对照

| 字段 | 含义 | | 字段 | 含义 |
|------|------|-|------|------|
| `xshdName` | 活动名称 | | `opName` | 商机名称 |
| `xshdHdrq` | 活动日期 | | `opXmid` | 商机编号 |
| `xshdHdlx` | 活动类型 | | `opJieduan` | 商机阶段 |
| `xshdZycd` | 重要程度 | | `opKnx` | 可能性(0-100) |
| `xshdHdjg` | 活动结果 | | `opXmlx` | 项目类型 |
| `xshdHdxq` | 活动详情 | | `xshdZylxr` | 主要联系人 |
| `xshdYewujihuijieduan` | 产生商机时的阶段（历史快照） | | `opJieduan` | 商机最新阶段 |
| `opJine` | 商机金额 | | `kehuName` | 客户名称 |
| `ccuserName` | 创建人 | | `kehuQy` | 客户区域 |
| `ccuserEmail` | 创建人邮箱 | | `kehuSs` | 客户省份 |
| `ccuserSqy` | 创建人区域 | | `kehudahangye` | 客户大行业 |
| `ccuserBumen` | 创建人部门 | | `ccuserZylx` | 创建人体系 |

---

## 常用查询模式

### 按区域

```bash
cloudcc activity query --region 西区 --date 本月 --output json
cloudcc activity query --region "西区,北区" --date 本月 --output json
```

### 高可能性商机（KNX）

```bash
cloudcc activity query --op-knx 60-100 --date 本月 --output json   # 高
cloudcc activity query --op-knx 40-60 --date 本月 --output json    # 中
cloudcc activity query --op-knx 0-40 --date 本月 --output json     # 低
```

**KNX 分级**：高(60-100) / 中(40-60) / 低(0-40)

### 按商机阶段

```bash
cloudcc activity query --op-stage "3.1立项" --date 本月 --output json
cloudcc activity query --op-stage "3.1立项,4.1方案设计" --date 本月 --output json
```

### 按创建人

```bash
cloudcc activity query --creator "张三" --date 本月 --output json
cloudcc activity query --creator-email "user@enmo.com" --date 本月 --output json
cloudcc activity query --creator-dept "销售部" --date 本月 --output json
```

### 按客户/行业

```bash
cloudcc activity query --customer "长虹" --date 本月 --output json
cloudcc activity query --industry 制造业 --date 本月 --output json
cloudcc activity query --kehu-qy 西区 --kehu-industry 制造业 --date 本月 --output json
```

### 组合查询

```bash
# 西区 + 高可能性 + 已立项
cloudcc activity query --region 西区 --op-knx 60-100 --op-stage "3.1立项" --date 本月 --output json

# 制造业 + 新客户 + 项目服务
cloudcc activity query --industry 制造业 --op-customer 新客户 --op-product 项目服务 --date 本月 --output json
```

### 导出大数据集

```bash
# 本月全部
cloudcc activity query --date 本月 --page-all --output json --output-file month_data.json

# 调大页数减少请求
cloudcc activity query --date 本月 --page-all --page-size 200 --output json --output-file data.json

# 限定页数
cloudcc activity query --date 本月 --page-all --page-limit 5 --output json --output-file data.json
```

### 配置文件查询

```bash
cloudcc activity query --config query.json --output json
```

配置文件格式：
```json
{
  "pageNumber": 1,
  "pageSize": 50,
  "xshdHdrqStart": "2026-06-01",
  "xshdHdrqEnd": "2026-06-30",
  "ccuserSqyList": ["西区"],
  "opKnxMin": 60,
  "opKnxMax": 100
}
```
