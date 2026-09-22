# 人员档案模块

## 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `personnel query` | 分页查询员工档案 | 无 |
| `personnel resignation` | 分页查询离职管理记录 | 无 |
| `personnel businesstrip` | 分页查询出差申请 | 无 |
| `personnel businesstrip create` | 创建出差申请 | `--ccksrq --ccjsrq --type --ccjtgj --ccsy --cfd --ccdnew --yjclzc --xiangmu` |
| `personnel businesstrip update` | 修改出差申请（仅草稿/驳回可改） | `--keyword` + 可选修改字段 |
| `personnel leave` | 分页查询请假单（立体结构：主单+内嵌明细） | 无 |
| `personnel overtime` | 分页查询加班单（立体结构：主单+内嵌明细） | 无 |
| `personnel overtime create` | 创建加班单（明细通过 --items-json 传入） | `--items-json` |
| `personnel overtime update` | 修改加班单明细（整体替换，仅草稿可改） | `--keyword --items-json` |
| `personnel attendancepatch` | 分页查询考勤补卡记录 | 无 |

> 通用说明：
> - 分页查询为只读，所有搜索条件可选、任意组合取交集；结果受登录用户**数据权限**约束。
> - create/update 为写操作，受审批状态约束（仅草稿/驳回可修改）。
> - 通用参数：`--page`（默认 1）、`--page-size`（默认 10，最大 100）、`--output table/json`。
> - 所有列表按创建时间 `createdate` **降序**返回（最新在前）。
> - 通用搜索参数语义：
>   - `--keyword`：多列模糊（各服务匹配字段见各自小节）
>   - `--bumen`：模糊匹配任职部门，支持部门路径中任意一级（如搜"交付部"命中下属所有子部门）
>   - `--spzt`：审批状态精确匹配（如 审批通过 / 草稿）

---

## 员工档案查询（personnel query）

分页查询员工档案（ygda）及其任职部门、所属公司、个人职级信息。

```bash
# 按姓名/邮箱模糊搜索
cloudcc personnel query --keyword "张三"

# 组合查询
cloudcc personnel query --bumen "西区" --zyzt 在职 --yglx 正式

# 按入职日期范围查询
cloudcc personnel query --rzrq-from 2026-01-01 --rzrq-to 2026-06-30
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配姓名、私人邮箱、公司邮箱 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--zhiwu` | 担任职务（模糊匹配） |
| `--zyzt` | 职位状态（精确：在职 / 离职 / 待离职） |
| `--yglx` | 员工类型（精确：正式 / 实习） |
| `--rzrq-from` / `--rzrq-to` | 入职日期范围（含边界），格式 2026-01-01 |
| `--xl` | 学历（模糊匹配） |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| id | 员工档案ID |
| name | 员工姓名 |
| xb | 性别 |
| csny | 出生年月（格式 yyyyMMdd） |
| srDzyx | 私人邮箱 |
| gsDzyx | 公司邮箱 |
| rzrq | 入职日期 |
| zyyjtxnew | 资源体系 |
| bumen | 任职部门（含上级部门路径，如 `恩墨>交付部>西区`） |
| drzw | 担任职务 |
| zyzt | 职位状态（在职、离职、待离职） |
| yglx | 员工类型（正式、实习） |
| hkxz | 户口性质 |
| zzmm | 政治面貌 |
| country | 工作国家 |
| gzcs | 工作城市 |
| sbjnd | 社保缴纳地 |
| ssgs | 所属公司 |
| grzj | 个人职级 |
| jszj | 技术职级 |
| ssqynew | 员工所属区域 |
| xl | 学历 |
| zhuguanname | 主管姓名 |

### 使用说明

- 权限标识 `personnel:profile:page`，权限不足返回 403
- `--zyzt` / `--yglx` 传非法值时后端返回参数校验错误（退出码 3）
- 表格视图仅展示核心字段，户口性质、政治面貌、工作国家/城市、社保缴纳地、所属公司、个人职级、技术职级、主管姓名等请用 `--output json` 查看

---

## 离职管理查询（personnel resignation）

分页查询离职管理记录（lzgl）及员工信息。

```bash
# 按员工姓名/离职编号/资源体系模糊搜索
cloudcc personnel resignation --keyword "张三"

# 按离职类型精确过滤
cloudcc personnel resignation --sjlzlx 主动离职

# 按最后工作日范围查询
cloudcc personnel resignation --sjzhgzr-from 2025-01-01 --sjzhgzr-to 2025-12-31
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配离职编号、员工姓名、资源体系 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--spzt` | 审批状态（精确） |
| `--sjlzlx` | 实际离职类型（精确：主动离职 / 被动离职） |
| `--sjzhgzr-from` / `--sjzhgzr-to` | 实际最后工作日范围（含边界），格式 2026-01-01 |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| id | 离职单ID |
| name | 离职编号 |
| spzt | 审批状态 |
| sjzhgzr | 实际最后工作日 |
| sjlzlx | 实际离职类型（主动离职 / 被动离职） |
| beizhu | 备注 |
| ygxm | 员工姓名 |
| zyyjtxnew | 资源体系 |
| ssqynew | 所属区域 |
| ssgs | 所属公司 |
| bumen | 任职部门（含上级部门路径） |
| gsDzyx | 员工公司邮箱 |

### 使用说明

- 权限标识 `personnel:resignation:page`

---

## 出差申请查询（personnel businesstrip）

分页查询出差申请（ccsqnew）。

```bash
# 按申请人/出差编号/出差事由模糊搜索
cloudcc personnel businesstrip --keyword "常钰"

# 按出差时段范围查询（区间重叠：出差 [ccksrq, ccjsrq] 与查询区间有交集即命中）
cloudcc personnel businesstrip --ccksrq-from 2025-01-01 --ccksrq-to 2025-12-31

# 组合：某部门 + 审批通过
cloudcc personnel businesstrip --bumen "西区" --spzt 审批通过
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配出差编号、申请人姓名、出差事由、资源体系 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--spzt` | 审批状态（精确） |
| `--ccksrq-from` / `--ccksrq-to` | 查询区间（含边界，格式 2026-01-01；**区间重叠语义**：出差时段与之有交集即命中，跨期出差不会漏查；`ccjsrq` 为空按单日处理） |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| id | 出差单ID |
| name | 出差编号 |
| spzt | 审批状态 |
| ccksrq | 出差开始日期 |
| ccjsrq | 出差结束日期 |
| ccsy | 出差事由 |
| cfd | 出发地（名称） |
| ccd | 出差地（名称） |
| chuchaileixing | 出差类型 |
| ccjtgj | 出差交通工具 |
| xiangmu | 项目（名称） |
| yjclzc | 预计差旅支出 |
| sqrxm | 申请人姓名 |
| zyyjtxnew | 资源体系 |
| ssqynew | 所属区域 |
| ssgs | 所属公司 |
| bumen | 任职部门（含上级部门路径） |
| gsDzyx | 员工公司邮箱 |

### 使用说明

- 权限标识 `personnel:businesstrip:page`
- 表格视图中出差事由缩进展示在明细行（截断至 80 字符），完整事由请用 `--output json`

---

## 出差申请写操作（personnel businesstrip create/update）

创建或修改出差申请（ccsqnew）。

### 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `personnel businesstrip create` | 创建出差申请 | `--ccksrq --ccjsrq --type --ccjtgj --ccsy --cfd --ccdnew --yjclzc --xiangmu` |
| `personnel businesstrip update` | 修改出差申请（仅草稿/驳回可改） | `--keyword` + 至少一个修改字段 |

### 创建参数

| 参数 | 说明 |
|------|------|
| `--ccksrq` | 出差开始日期（必填，格式 2026-10-01） |
| `--ccjsrq` | 出差结束日期（必填，格式 2026-10-03） |
| `--type` | 出差类型（必填：市场培育 / 业务支持） |
| `--ccjtgj` | 出差交通工具（必填，多选用分号分隔，如 `"火车;飞机"`） |
| `--ccsy` | 出差事由（必填） |
| `--cfd` | 出发地（必填，支持名称或ID，后端自动识别；中文→名称模糊匹配，唯一匹配才成功） |
| `--ccdnew` | 出差地（必填，同 cfd 规则） |
| `--yjclzc` | 预计差旅支出（必填，数字） |
| `--xiangmu` | 项目（必填，支持名称或ID，后端自动识别；名称模糊匹配受数据权限过滤，超过20个匹配时提示缩小范围） |

### 修改参数

| 参数 | 说明 |
|------|------|
| `--keyword` | 出差申请ID或编号（必填，后端自动识别；ID 以 d19 开头，编号为纯数字） |
| `--ccksrq` | 出差开始日期（可选） |
| `--ccjsrq` | 出差结束日期（可选） |
| `--type` | 出差类型（可选） |
| `--ccjtgj` | 出差交通工具（可选） |
| `--ccsy` | 出差事由（可选） |
| `--cfd` | 出发地（可选） |
| `--ccdnew` | 出差地（可选） |
| `--yjclzc` | 预计差旅支出（可选） |
| `--xiangmu` | 项目（可选） |

### 示例

```bash
# 创建出差申请
cloudcc personnel businesstrip create \
  --ccksrq 2026-10-01 --ccjsrq 2026-10-03 \
  --type "业务支持" --ccjtgj "火车;飞机" \
  --ccsy "年度数据库巡检与优化服务" \
  --cfd "上海" --ccdnew "杭州" \
  --yjclzc 4200 --xiangmu "招商银行"

# 修改出差申请（按编号定位，仅修改出差事由）
cloudcc personnel businesstrip update --keyword "QJD-000228" --ccsy "更新后的出差事由"

# 修改出差申请（按ID定位，同时修改多个字段）
cloudcc personnel businesstrip update --keyword "d192026CF136D66YM01h" --ccsy "新事由" --yjclzc 5000
```

### 使用说明

- 创建权限 `personnel:businesstrip:create`，修改权限同
- 出发地/出差地/项目均支持名称模糊匹配，后端自动解析为ID；多个匹配时返回候选列表供选择
- 修改仅允许“草稿”和“驳回”状态，审批中和审批通过不允许修改
- 输出格式默认 JSON（包含完整 VO 字段）

---

## 请假单查询（personnel leave）⭐ 立体结构

分页查询请假单（qjd），**分页粒度为请假单（主单）**，每条主单内嵌 `details` 明细列表；`total` 为单据数而非明细数。

```bash
# 按申请人姓名搜索某人的所有请假单
cloudcc personnel leave --keyword "常钰"

# 按审批状态过滤
cloudcc personnel leave --spzt 审批通过

# 按明细请假时段范围过滤（区间重叠：明细 [qjqsrq, qjjsrq] 与查询区间有交集即命中任一条明细即保留主单）
cloudcc personnel leave --qjqsrq-from 2025-01-01 --qjqsrq-to 2025-12-31
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配请假单ID、请假单编号、申请人姓名、资源体系 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--spzt` | 审批状态（精确） |
| `--qjlx` | 请假类型（精确）。注意：该字段存的是"带薪/不带薪"；"年假/病假/事假"在明细的 `jqlb`（假期类别）字段，目前不支持按假期类别过滤 |
| `--qjqsrq-from` / `--qjqsrq-to` | 查询区间（含边界，格式 2026-01-01；**区间重叠语义**：明细请假时段与之有交集即命中任一条明细即保留主单） |

### 响应字段（JSON）

主单字段：

| 字段 | 说明 |
|------|------|
| id | 请假单ID |
| name | 请假单编号 |
| spzt | 审批状态 |
| sqrxm | 申请人姓名 |
| zyyjtxnew | 资源体系 |
| ssqynew | 所属区域 |
| ssgs | 所属公司 |
| bumen | 任职部门（含上级部门路径） |
| gsDzyx | 员工公司邮箱 |
| totalQjts | 单内总请假天数（各明细天数求和） |
| details | 请假明细列表（见下） |

明细字段（`details[]`）：

| 字段 | 说明 |
|------|------|
| mxid | 明细ID |
| mxname | 明细编号 |
| qjlx | 请假类型（带薪 / 不带薪） |
| jqlb | 假期类别（年假 / 病假 / 事假等） |
| qjqsrq | 请假开始日期 |
| qjjsrq | 请假结束日期 |
| qjts | 请假天数（小数，如 0.5） |
| shijiandanwei | 实际单位（天 / 小时） |
| qjyy | 请假原因（无原因时为"无"） |
| zftsList | 销假作废天数列表（可能多条，无销假时为空数组） |

### JSON 响应示例

```json
{
  "items": [
    {
      "id": "a12201600540272KtwUg",
      "name": "QJD-000228",
      "spzt": "审批通过",
      "sqrxm": "张三",
      "zyyjtxnew": "交付体系",
      "ssqynew": "北区",
      "ssgs": "云和恩墨（北京）信息技术有限公司",
      "bumen": "数据库管理服务产品群>技术研究中心",
      "gsDzyx": "zhangsan@enmotech.com",
      "totalQjts": 2,
      "details": [
        {
          "mxid": "b112017E8C42695tPfnv",
          "mxname": "20171225138",
          "qjlx": "带薪",
          "jqlb": "年假",
          "qjqsrq": "2013-12-05",
          "qjjsrq": "2013-12-06",
          "qjts": 2,
          "shijiandanwei": "天",
          "qjyy": "无",
          "zftsList": []
        }
      ]
    }
  ],
  "total": 25745,
  "page": 1,
  "pageSize": 10,
  "totalPages": 2575,
  "hasNext": true,
  "hasPrevious": false
}
```

### 使用说明

- 权限标识 `personnel:leavedetail:page`
- `total` 是**请假单数量**，不是明细条数；一张单据多条明细不会被跨页切断
- 表格视图中明细以 `├` 缩进展示（假期类别、起止日期、天数、事由、销假作废天数）
- **默认查询今年**：未传任何搜索条件（keyword/bumen/spzt/qjlx/日期）时，后端自动限定为当前年度（1月1日~12月31日），避免全表扫描超时；传入任意条件后按用户条件查询，不受此限制

---

## 请假单写操作（personnel leave create/update/check/submit）

请假单的创建、修改明细、提交前校验三个写操作命令。

> 审批操作（提交/批准/拒绝/转交/调回）已迁移至审批引擎通用命令，详见 [approval.md](approval.md)。

### 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `personnel leave create` | 创建请假单（同时创建主单和明细） | `--items-json` |
| `personnel leave update` | 修改请假单明细（整体替换，仅草稿可改） | `--items-json` + `--leave-id` 或 `--leave-name` |
| `personnel leave check` | 提交前校验（余额/有效性/天数上限） | `--items-json` |

### 明细 JSON 格式（`--items-json`）

`--items-json` 接受 JSON 数组字符串，也支持 `@文件路径` 从文件读取。每个明细项字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| qjlx | 是 | 请假类别：`带薪` / `扣薪` |
| jqlb | 是 | 假期类别：`年假` / `事假` / `病假` / `倒休` / `婚假` / `丧假` / `产假` / `陪产假` / `工伤假` / `产检假` |
| qjqsrq | 是 | 请假开始日期（格式 2026-09-01） |
| qjjsrq | 是 | 请假结束日期（格式 2026-09-03） |
| qjts | 是 | 请假数量（小数，如 0.5；倒休单位为小时时填小时数） |
| shijiandanwei | 否 | 实际单位（`天` / `小时`，默认`天`；**仅倒休支持小时**，其他类型必须为天） |
| qjyy | 是 | 请假原因（最多500字符） |

**请假类别与假期类别组合规则：**

| 请假类别 (qjlx) | 允许的假期类别 (jqlb) |
|----------------|---------------------|
| 带薪 | 全部 10 种（年假、倒休、病假、事假、丧假、婚假、产假、工伤假、陪产假、产检假） |
| 扣薪 | 仅事假、病假（2 种） |

**倒休余额校验说明：**
- jqgl（假期管理台账）中倒休余额以**小时**为单位存储
- 当 `shijiandanwei` 为 `天` 时，系统自动将 `qjts × 8` 转换为小时后与余额对比
- 当 `shijiandanwei` 为 `小时` 时，直接使用 `qjts` 与余额对比
- 余额校验仅针对带薪明细中的年假、倒休、病假、事假四种类型

### 示例

```bash
# 创建请假单（一条明细）
cloudcc personnel leave create --items-json '[{"qjlx":"带薪","jqlb":"年假","qjqsrq":"2026-09-01","qjjsrq":"2026-09-03","qjts":3,"qjyy":"个人事务处理"}]'

# 创建请假单（多条明细）
cloudcc personnel leave create --items-json '[{"qjlx":"带薪","jqlb":"年假","qjqsrq":"2026-09-01","qjjsrq":"2026-09-03","qjts":3,"qjyy":"个人事务"},{"qjlx":"带薪","jqlb":"病假","qjqsrq":"2026-09-10","qjjsrq":"2026-09-10","qjts":1,"qjyy":"医院复查"}]'

# 创建请假单（倒休，按天，自动转小时校验）
cloudcc personnel leave create --items-json '[{"qjlx":"带薪","jqlb":"倒休","qjqsrq":"2026-09-20","qjjsrq":"2026-09-21","qjts":2,"qjyy":"倒休2天"}]'

# 创建请假单（倒休，按小时）
cloudcc personnel leave create --items-json '[{"qjlx":"带薪","jqlb":"倒休","qjqsrq":"2026-09-20","qjjsrq":"2026-09-20","qjts":4,"shijiandanwei":"小时","qjyy":"倒休4小时"}]'

# 从文件读取明细
cloudcc personnel leave create --items-json @leave-items.json

# 提交前校验（检查余额/有效性/天数上限，不实际提交）
cloudcc personnel leave check --items-json '[{"qjlx":"带薪","jqlb":"年假","qjqsrq":"2026-09-01","qjjsrq":"2026-09-03","qjts":3,"qjyy":"个人事务"}]'

# 修改请假单明细（仅草稿状态可修改，整体替换旧明细）
cloudcc personnel leave update --leave-id "a122026B750D7836UbqD" --items-json '[{"qjlx":"带薪","jqlb":"年假","qjqsrq":"2026-09-01","qjjsrq":"2026-09-02","qjts":2,"qjyy":"个人事务"}]'

# 通过请假单编号修改
cloudcc personnel leave update --leave-name "QJD20260907001" --items-json '[{"qjlx":"带薪","jqlb":"年假","qjqsrq":"2026-09-01","qjjsrq":"2026-09-02","qjts":2,"qjyy":"个人事务"}]'

# 通过审批引擎提交请假单审批（审批操作已迁移至 approval 模块）
cloudcc approval submit --relate-id "a122026B750D7836UbqD" --app-path "/personnel/leavedetail"
```

### 参数说明

**create / check：**

| 参数 | 说明 |
|------|------|
| `--items-json` | 请假明细 JSON 数组（必填，支持 `@文件路径`） |

**update：**

| 参数 | 说明 |
|------|------|
| `--leave-id` | 请假单ID（与 `--leave-name` 二选一） |
| `--leave-name` | 请假单编号（与 `--leave-id` 二选一） |
| `--items-json` | 新的请假明细 JSON 数组（必填，整体替换旧明细） |

**submit（通过审批引擎）：**

参见 [approval.md](approval.md) 中的提交审批章节。

### 使用说明

- 权限标识：create/update 为 `personnel:leavedetail:create`，check 为 `personnel:leavedetail:submit`
- **典型流程**：`create` → `check`（可选，提前校验余额） → `approval submit`（通过审批引擎提交）
- **审批操作**：提交后通过 `approval approve`/`approval reject`/`approval reassign` 执行审批，通过 `approval recall` 调回
- **修改限制**：仅“草稿”状态允许 `update`，“审批中”和“审批通过”不允许
- **明细整体替换**：`update` 是整体替换策略（先软删旧明细再插入新明细），不是增量修改
- **编号重复**：`update` 通过 `--leave-name` 定位时，若编号对应多条记录会报错提示改用 `--leave-id`
- `create`/`update`/`check` 输出为 JSON 格式

---

## 请假单附件管理（personnel leave upload-attachment / list-attachments / delete-attachment）

请假单附件的上传、查询和删除操作。

> 附件存储在 Oracle 数据库的 TP_SYS_ATTACHEMENT 表中，附件 ID 前缀为 `bda`。

### 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `personnel leave upload-attachment` | 上传请假单附件 | `-f` (文件路径) + `-l` (请假单ID/编号) |
| `personnel leave list-attachments` | 查询请假单附件列表 | `-l` (请假单ID/编号) |
| `personnel leave delete-attachment` | 删除请假单附件（逻辑删除） | `-a` (附件ID) |

### 示例

```bash
# 上传附件到请假单（通过ID）
cloudcc personnel leave upload-attachment -f ./结婚证.pdf -l "a1220269EA934AFtWAVz"

# 上传附件到请假单（通过编号）
cloudcc personnel leave upload-attachment -f ./病假证明.pdf -l "20260915561251"

# 查询请假单附件
cloudcc personnel leave list-attachments -l "a1220269EA934AFtWAVz"

# 删除附件
cloudcc personnel leave delete-attachment -a "bda2026E7C82981M3Hjk"
```

### 参数说明

**upload-attachment：**

| 参数 | 说明 |
|------|------|
| `-f` / `--file` | 附件文件路径（必填，最大 100MB） |
| `-l` / `--leave` | 请假单ID或编号（必填） |
| `--output` | 输出格式 (table/json)，默认 table |

**list-attachments：**

| 参数 | 说明 |
|------|------|
| `-l` / `--leave` | 请假单ID或编号（必填） |
| `--output` | 输出格式 (table/json)，默认 table |

**delete-attachment：**

| 参数 | 说明 |
|------|------|
| `-a` / `--attachment-id` | 附件ID（必填） |
| `--output` | 输出格式 (table/json)，默认 table |

### 响应字段（JSON）

**upload-attachment 响应：**

```json
{
  "success": true,
  "attachmentId": "bda2026E7C82981M3Hjk",
  "fileName": "结婚证",
  "suffix": "pdf",
  "fileSize": 102400,
  "fileSizeText": "100.00 KB",
  "relatedId": "a1220269EA934AFtWAVz",
  "createdAt": "2026-09-15 10:30:00"
}
```

**list-attachments 响应：**

```json
{
  "success": true,
  "leaveId": "a1220269EA934AFtWAVz",
  "count": 2,
  "attachments": [
    {
      "index": 1,
      "fileName": "结婚证.pdf",
      "fileSize": 102400,
      "fileSizeText": "100.00 KB",
      "attachmentId": "bda2026E7C82981M3Hjk",
      "createdAt": "2026-09-15 10:30:00"
    }
  ]
}
```

**delete-attachment 响应：**

```json
{
  "success": true,
  "attachmentId": "bda2026E7C82981M3Hjk",
  "message": "附件已删除"
}
```

### 业务规则

**文件大小限制：**
- 单个附件最大 **100MB**，超过限制会报错并显示友好提示

**审批状态与上传/删除权限：**

| 审批状态 (spzt) | 普通用户上传/删除 | 超级管理员上传/删除 |
|----------------|------------------|------------------|
| 草稿 | ✅ 允许 | ✅ 允许 |
| 审批中 | ❌ 禁止 | ✅ 允许（超管豁免） |
| 审批通过 | ❌ 禁止 | ✅ 允许（超管豁免） |
| 已拒绝 | ✅ 允许 | ✅ 允许 |

**查询范围：**
- 超级管理员：可查询所有请假单的附件
- 普通用户：只能查询自己请假单的附件（按 ccuserId 过滤）

**提交审批前附件必传校验：**

以下假期类别提交审批时**必须已上传附件**，否则会被拦截：

| 假期类别 | 附件要求 |
|----------|----------|
| 产检假 | 必须上传 |
| 婚假 | 必须上传 |
| 陪产假 | 必须上传 |
| 产假 | 必须上传 |
| 医疗期 | 必须上传 |
| 病假 | 天数 ≥ 3天时必须上传 |

> 系统会按假期类别分组汇总天数，即使用户创建了多条同类明细也会正确判断。

### 使用说明

- 权限标识：upload 为 `personnel:leaveattachment:upload`，list 为 `personnel:leaveattachment:view`，delete 为 `personnel:leaveattachment:delete`
- **典型流程**：`create` → `upload-attachment`（上传附件） → `list-attachments`（确认附件） → `approval submit`（提交审批）
- **下载接口暂停**：当前下载接口已暂停，待后续优化
- **逻辑删除**：删除操作仅标记 `is_deleted = '1'`，数据保留用于审计
- **编号支持**：上传和查询均支持通过请假单ID或编号操作
- **多记录报错**：通过编号操作时，若编号匹配多条记录会报错提示改用ID

---

## 加班单查询（personnel overtime）⭐ 立体结构

分页查询加班单（jb），结构与请假单一致：**主单分页 + 内嵌 `details` 明细**。

```bash
# 按申请人姓名搜索
cloudcc personnel overtime --keyword "张三"

# 按明细加班时段范围过滤（格式含时间；区间重叠：明细 [jbqssj, jbjssj] 与查询区间有交集即命中任一条明细即保留主单）
cloudcc personnel overtime --jbqssj-from "2025-01-01 00:00:00" --jbqssj-to "2025-12-31 23:59:59"
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配加班单编号、申请人姓名、资源体系 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--spzt` | 审批状态（精确） |
| `--jbqssj-from` / `--jbqssj-to` | 查询区间（含边界，格式 `2026-01-01 00:00:00`；**区间重叠语义**：明细加班时段与之有交集即命中任一条明细即保留主单） |

### 响应字段（JSON）

主单字段：

| 字段 | 说明 |
|------|------|
| id | 加班单ID |
| name | 加班单编号 |
| spzt | 审批状态 |
| sqrxm | 申请人姓名 |
| zyyjtxnew | 资源体系 |
| ssqynew | 所属区域 |
| ssgs | 所属公司 |
| bumen | 任职部门（含上级部门路径） |
| gsDzyx | 员工公司邮箱 |
| totalJbxs | 单内总加班小时数（各明细求和） |
| details | 加班明细列表（见下） |

明细字段（`details[]`）：

| 字段 | 说明 |
|------|------|
| mxid | 明细ID |
| mxname | 明细编号 |
| jbdd | 加班地点 |
| jbqssj | 加班开始时间（含时分秒） |
| jbjssj | 加班结束时间（含时分秒） |
| jbxsshjsz | 加班小时数计算值 |
| jbsy | 加班事由（无事由时为"无"） |

### 使用说明

- 权限标识 `personnel:overtimedetail:page`
- `total` 是**加班单数量**；表格视图中明细以 `├` 缩进展示（起止时间、小时数、地点、事由）

---

## 加班单写操作（personnel overtime create/update）

创建或修改加班单（jb），结构与请假单写操作一致：**通过 `--items-json` 传入明细列表**。

### 命令概览

| 命令 | 说明 | 必填参数 |
|------|------|----------|
| `personnel overtime create` | 创建加班单（同时创建主单和明细） | `--items-json` |
| `personnel overtime update` | 修改加班单明细（整体替换，仅草稿可改） | `--keyword --items-json` |

### 明细 JSON 格式（`--items-json`）

`--items-json` 接受 JSON 数组字符串，也支持 `@文件路径` 从文件读取。每个明细项字段：

| 字段 | 必填 | 说明 |
|------|------|------|
| jbdd | 是 | 加班地点（最多200字符） |
| jbqssj | 是 | 加班开始时间（格式 `2026-09-20 09:00`，精确到分钟） |
| jbjssj | 是 | 加班结束时间（格式 `2026-09-20 18:00`，精确到分钟） |
| jbxsshjsz | 是 | 加班小时数（如 8、0.5） |
| jbsy | 是 | 加班事由（最多500字符） |
| bgd | 否 | 报告单（最多200字符） |
| xm | 否 | 项目（最多200字符） |
| jblx | 否 | 加班类型（`非法定节假日` / `法定节假日`，默认 `非法定节假日`；后端会根据日期自动判断法定节假日） |

### 示例

```bash
# 创建加班单（一条明细）
cloudcc personnel overtime create --items-json '[{"jbdd":"北京","jbqssj":"2026-09-20 09:00","jbjssj":"2026-09-20 18:00","jbxsshjsz":8,"jbsy":"项目支持"}]'

# 创建加班单（多条明细，含法定节假日）
cloudcc personnel overtime create --items-json '[{"jbdd":"北京","jbqssj":"2026-10-01 09:00","jbjssj":"2026-10-01 18:00","jbxsshjsz":8,"jbsy":"国庆值班"},{"jbdd":"北京","jbqssj":"2026-10-02 09:00","jbjssj":"2026-10-02 12:00","jbxsshjsz":3,"jbsy":"国庆值班"}]'

# 从文件读取明细
cloudcc personnel overtime create --items-json @overtime-items.json

# 修改加班单明细（仅草稿状态可修改，整体替换旧明细）
cloudcc personnel overtime update --keyword "a122026B750D7836UbqD" --items-json '[{"jbdd":"上海","jbqssj":"2026-09-21 09:00","jbjssj":"2026-09-21 18:00","jbxsshjsz":8,"jbsy":"项目支持（修改）"}]'

# 通过加班单编号修改
cloudcc personnel overtime update --keyword "JBD20260917001" --items-json '[{"jbdd":"上海","jbqssj":"2026-09-21 09:00","jbjssj":"2026-09-21 18:00","jbxsshjsz":8,"jbsy":"项目支持"}]'

# 提交审批（通过审批引擎）
cloudcc approval submit --relate-id "a122026B750D7836UbqD" --app-path "/personnel/overtimedetail"
```

### 参数说明

**create：**

| 参数 | 说明 |
|------|------|
| `--items-json` | 加班明细 JSON 数组（必填，支持 `@文件路径`） |

**update：**

| 参数 | 说明 |
|------|------|
| `--keyword` | 加班单ID或编号（必填，后端自动识别） |
| `--items-json` | 新的加班明细 JSON 数组（必填，整体替换旧明细） |

### 使用说明

- 权限标识：create/update 均为 `personnel:overtimedetail:create`
- **典型流程**：`create` → `approval submit`（通过审批引擎提交）
- **审批操作**：提交后通过 `approval approve`/`approval reject`/`approval reassign` 执行审批，通过 `approval recall` 调回
- **修改限制**：仅“草稿”状态允许 `update`，“审批中”和“审批通过”不允许
- **明细整体替换**：`update` 是整体替换策略（先软删旧明细再插入新明细），不是增量修改
- **加班类型自动计算**：后端根据加班开始时间自动判断是否为法定节假日，无需手动指定 `jblx`
- `create`/`update` 输出为 JSON 格式

---

## 考勤补卡查询（personnel attendancepatch）

分页查询考勤补卡记录（bdk）。

```bash
# 按申请人/补卡原因模糊搜索
cloudcc personnel attendancepatch --keyword "忘打卡"

# 按补卡时段范围查询（区间重叠，仅年月日）
cloudcc personnel attendancepatch --dkkssj-from 2025-01-01 --dkkssj-to 2025-12-31
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--keyword` | 模糊匹配补卡原因、申请人姓名、资源体系 |
| `--bumen` | 模糊匹配任职部门（含上级路径任意一级） |
| `--spzt` | 审批状态（精确） |
| `--dkkssj-from` / `--dkkssj-to` | 查询区间（含边界，格式 2026-01-01，仅年月日；**区间重叠语义**：补卡时段 [dkkssj, dkjssj] 与之有交集即命中；终点含当日全天，`dkjssj` 为空按单时点处理） |

### 响应字段（JSON）

| 字段 | 说明 |
|------|------|
| dkkssj | 打卡开始时间（补卡时间点） |
| dkjssj | 打卡结束时间（补卡时间点） |
| bdkyy | 补卡原因 |
| spzt | 审批状态 |
| sqrxm | 申请人姓名 |
| zyyjtxnew | 资源体系 |
| ssqynew | 所属区域 |
| ssgs | 所属公司 |
| bumen | 任职部门（含上级部门路径） |
| gsDzyx | 员工公司邮箱 |

### 使用说明

- 权限标识 `personnel:attendancepatch:page`
- 表格视图中补卡原因缩进展示在明细行，完整内容请用 `--output json`

---

## 通用注意事项

- 6 个接口分别需要独立权限标识（`personnel:{profile/resignation/businesstrip/leavedetail/overtimedetail/attendancepatch}:page`），权限不足返回 403
- 加班单写操作权限标识为 `personnel:overtimedetail:create`（create/update 共用）
- 所有搜索条件与数据权限是 **AND** 叠加：结果永远在当前登录用户可见范围内
- 分页响应数组字段名为 `items`，与 activity / project 模块一致
- 请假/加班为立体结构：分页粒度是单据，`total` 是单据数，明细内嵌于 `details` 不会跨页切断
- 排序统一为 `createdate` 降序（最新创建的单据在前）
