# 报销导入 — 步骤引导流程

**核心目标：** 将发票文件转换为报销单并导入 CloudCC 系统。

**处理能力：**
- 文本层 PDF：直接提取文本识别（无需 OCR）
- 图片/扫描版 PDF：通过多模态大模型视觉能力识别（无需安装 OCR 模块）
- **附件管理**：支持上传和查询报销单附件（PDF/图片/文档等）

---

## 前置检查（自动执行）

每次启动报销流程前，Agent 自动检查：

1. **登录状态**：`cloudcc auth status` → 未登录则先引导登录
2. **Python 依赖**：检测 `openpyxl` 是否可用 → 缺失则提示 `pip install -r scripts/requirements.txt`

检查不通过时，先解决再继续，**不跳过**。

**边界情况：** 用户未提供任何文件时，主动询问："请提供发票文件（PDF/图片）或已填充的报销模板（Excel）。"

---

## 导入模板

报销导入基于 Excel 模板，模板随 skill 包自带（相对于 Skill 安装目录）：`assets/reimbursement-template.xlsx`

### 模板结构

- **Sheet 名：** `批量导入`
- **前 2 行为表头**：第 1 行中文标签，第 2 行字段代码
- **第 3~6 行为提示与示例**：导入程序自动跳过
- **第 7 行起为真实数据区**

### 列定义

| 列 | 中文标签 | 字段代码 | 必填 | 说明 |
|----|---------|---------|------|------|
| A | *费用发生起始日期 | qsrq | 是 | YYYY-MM-DD |
| B | *费用发生结束日期 | jsrq | 是 | YYYY-MM-DD |
| C | *报销类型 | bxlx | 是 | 下拉选择，不可手工输入 |
| D | *费用类型 | fylx | 是 | 下拉选择，不可手工输入 |
| E | *费用说明 | fysm | 是 | 格式见 field-mapping 文档 |
| F | *报销金额 | bxje | 是 | 纯数字，两位小数 |
| G | 发票号 | fapiaohao | 否 | 有则填 |
| H | 项目编号 | xmmc | 否 | 业务机会编号 |
| I | 销售活动编号 | xshdbh | 否 | |
| J | 报工单 | bgd | 否 | |
| K | 出差申请 | ccsqv1 | 否 | |
| L | 外派申请 | wpgzsq | 否 | |

> 星号（*）标记的字段为必填项。报销类型和费用类型为下拉列表，必须从系统预置选项中选择，不可手工输入。

### 数据流向

```
空白模板（assets/reimbursement-template.xlsx）
    ↓ 填充脚本写入发票数据
已填充 Excel（报销单批量导入_已填充.xlsx）
    ↓ CLI 调用 API
CloudCC 系统入库
```

---

## 路径分流（自动判断）

根据用户提供的文件类型，自动选择处理路径：

```
用户提供的是什么？
    │
    ├── .xlsx / .xls 文件（已填充的报销模板）
    │     → 🚀 快捷路径：跳过 Step 1~2，直接进入 Step 3 确认
    │
    └── 发票文件（PDF/图片等）
          → 📋 完整路径：Step 1 → Step 2 → Step 3 → Step 4
```

**判断依据：**
- 文件扩展名为 `.xlsx` 或 `.xls` → 快捷路径
- 文件扩展名为 `.pdf` / `.jpg` / `.png` / `.jpeg` → 完整路径
- 用户口述"我已有 Excel"或"直接导入" → 快捷路径
- 用户同时提供 Excel + 发票文件 → 询问用户意图："已检测到 Excel 和发票文件，是追加到已有 Excel 还是新建？"

进入快捷路径时，告知用户："检测到已填充的 Excel 文件，跳过识别步骤。"

---

## 🚀 快捷路径：直接导入

用户已准备好填充完毕的 Excel 文件，无需识别发票。

**Agent 动作：**
1. 读取 Excel 汇总（不修改文件）：
   ```bash
   python scripts/reimbursement-fill-invoice.py 报销单.xlsx --summary
   ```
2. 展示汇总数据，等待用户确认
3. 用户确认后执行导入

**输出模板：**
```markdown
## 📊 Excel 数据汇总

📄 **文件：** `{Excel文件路径}`

### 数据明细（X 张，合计 ¥XX,XXX.XX）
| # | 发票号 | 金额 | 费用类型 | 日期 |
|---|--------|------|---------|------|

---
> 请确认数据无误后回复"确认导入"。如需修改请直接编辑 Excel 文件后告诉我重新检查。
```

**交互规则：**
- 必须等待用户确认后才执行导入
- 用户如需修改，提示"请直接编辑 Excel 文件，修改后告诉我重新检查"
- 用户说"确认导入" → 进入 Step 4

---

## Step 1：文件分类

**Agent 动作：** 扫描用户提供的文件，按类型分组。

**分类决策树：**

```
用户提供文件
    │
    ├── .pdf
    │     ├── 有文本层（电子发票）  → ✅ 文本提取
    │     └── 无文本层（扫描件/多票合并） → 👁️ 视觉识别
    │
    ├── .jpg / .png / .jpeg       → 👁️ 视觉识别
    │
    └── 其他格式（.docx/.txt等）    → ❌ 不支持
```

**注意：** 此步骤仅处理发票文件。`.xlsx` / `.xls` 文件已在路径分流中走快捷路径，不会进入此处。

**判断 PDF 是否有文本层：** 尝试用 pdfplumber 提取文本，若首页文本长度 < 50 字符，视为扫描件。

**分类完成后告知用户：**
```
📂 文件分类完成：
- ✅ 文本提取（2个）：invoice_001.pdf, invoice_002.pdf
- 👁️ 视觉识别（1个）：receipt_scan.pdf
- ❌ 不支持  （1个）：报价单.docx

正在处理，请稍候...
```

**规则：**
- 有文本层的 PDF **优先处理**（准确率最高）
- 不支持的格式**不要中途提示**，统一记录到汇总
- 全部文件都不支持时，终止流程并告知原因

---

## Step 2：识别与填充

**Agent 动作：** 逐个处理文件，提取字段，生成 JSON，调用脚本填充 Excel。

**处理过程中不向用户逐条反馈**，全部完成后统一进入 Step 3。

### 2a. 文本提取（电子发票 PDF）

直接读取 PDF 文本内容，按字段映射规则提取。

**提取规则参考：** [reimbursement-field-mapping.md](reimbursement-field-mapping.md)
**费用类型判断：** [reimbursement-expense-types.md](reimbursement-expense-types.md)

**必须读取以上两个文档后再提取，禁止凭自身知识判断费用类型或金额。**

### 2b. 视觉识别（图片 / 扫描版 PDF）

使用当前多模态大模型的视觉能力直接识别发票内容，无需安装任何 OCR 模块。

**操作方式：**
1. 使用 Read 工具读取图片文件（支持 .jpg/.png/.jpeg），模型通过视觉能力识别内容
2. 对于扫描版 PDF，先转为图片再识别（转换方法参考 [reimbursement-pdf-conversion.md](reimbursement-pdf-conversion.md)）
3. 按与文本提取相同的字段映射规则输出结构化数据

**识别要点：**
- 重点关注：金额、日期、销售方、货物名称、发票号码
- 金额取值规则同文本提取：参考 [reimbursement-field-mapping.md](reimbursement-field-mapping.md)
- 费用类型判断同文本提取：参考 [reimbursement-expense-types.md](reimbursement-expense-types.md)
- 识别不确定的字段标注 `[待确认]`

### 2c. 生成 JSON 并填充

**重要：所有临时文件和输出文件必须放在工作目录（当前目录或用户指定目录），严禁写入 skill 安装目录。**

Agent 将所有识别结果直接写入工作目录下的 `invoices.json` 文件（格式参见 [reimbursement-field-mapping.md](reimbursement-field-mapping.md) 的 Schema 定义），一页多票时分别识别为独立条目，然后调用脚本：

```bash
# 在工作目录下执行（不要在 skill 目录中执行）
python <skill_dir>/scripts/reimbursement-fill-invoice.py \
  <skill_dir>/assets/reimbursement-template.xlsx \
  --from-file invoices.json \
  --output 报销单批量导入_已填充.xlsx
```

其中 `<skill_dir>` 是 cloudcc skill 的安装目录（可通过 `./bin/cloudcc` 的相对路径确定）。

**追加模式**（用户分批提供发票，需追加到已有 Excel 时使用 `--append`）：
```bash
python <skill_dir>/scripts/reimbursement-fill-invoice.py \
  报销单批量导入_已填充.xlsx \
  --from-file invoices.json \
  --append
```

**文件清理规则：**
- `invoices.json`：导入完成后可保留，方便后续追加
- `报销单批量导入_已填充.xlsx`：导入成功后可归档或删除
- **禁止**在 skill 目录下生成任何临时文件

**处理过程中的错误不中断**，统一记录到汇总。提取失败的文件归入"处理失败"列表。

**边界情况：** 若全部文件提取失败，Step 3 仍需展示（0 张成功），告知用户无可用数据。

---

## Step 3：汇总确认

**Agent 动作：** 统一展示处理结果，**必须等待用户确认**。

### 输出模板

```markdown
## 📊 处理结果汇总

📄 **Excel文件：** `{输出文件路径}`
（你可以打开此文件自行核对）

### ✅ 成功识别（X 张，合计 ¥XX,XXX.XX）

**低置信度项已用 ⚠️ 标记，请重点核对。**

| # | 原始文件名 | 发票号 | 金额 | 费用类型 | 报销类型 | 置信度 |
|---|-----------|--------|------|---------|---------|--------|
| 1 | 加油发票.pdf | 19825252 | ¥5,000.00 | 差旅费-其他交通费 | 日常费用 | ✅ |
| 2 | 地铁发票.pdf | 36538561 | ¥111.00 | 市内交通费 | 日常费用 | ✅ |
| 3 | ⚠️ 停车费.jpg | [待确认] | ¥200.00 | [待确认] | [待确认] | ⚠️ 0.3 |
| 4 | ⚠️ 境外机票.pdf | - | ¥1,595.00 | 差旅费-机票 | 销售费用 | ⚠️ 0.5 |

**置信度说明：**
- ✅ 1.0 / 0.8：大写金额与小写一致，或仅有价税合计小写
- ⚠️ < 0.8：仅"合计"行金额、多个候选值差异大、或缺少关键字段

### ⚠️ 处理失败（X 个）
| 文件名 | 原因 |
|--------|------|
| damaged.pdf | PDF内容损坏，无法提取 |

### ❌ 格式不支持（X 个）
| 文件名 | 原因 |
|--------|------|
| 报价单.docx | 仅支持 PDF 和图片文件 |

---
> 请确认以上数据是否正确。你可以：
> - 口述修改，如"第3条金额改为300"、"第4条费用类型改为招待费"
> - 对低置信度项说"全部确认"或逐条确认
> - 回复"确认导入"继续执行
```

### 汇总增强要求

1. **必须展示原始文件名**：方便用户对照检查哪张发票的数据可能有问题
2. **低置信度标记**：置信度 < 0.8 的条目用 ⚠️ 前缀标记，并在置信度列显示具体数值
3. **费用分类统计**（可选）：在汇总末尾添加按报销类型的分组统计
4. **修正对比**（如有修改）：如果用户要求修正金额，展示修正前后的对比

### 交互规则（必须遵守）

1. **必须等待用户回复**，不得自动继续
2. 用户口述修改 → Agent 修改后**重新展示整个汇总**，需再次等待确认
3. **完整路径**：口述修改影响 JSON 数据，需重新执行填充脚本更新 Excel
4. **快捷路径**：提示用户直接编辑 Excel 文件，修改后重新执行 `--summary`
5. 用户口述模糊时（如"那个金额不对"），Agent 应追问具体是哪条、改为多少
6. 用户说"确认导入" → 进入 Step 4
7. 用户说"取消" → 终止流程，已生成的中间文件保留并告知位置
8. **没有用户确认，绝不执行导入**

---

## Step 4：执行导入

**前置条件：** 用户已确认 Step 3 汇总数据。

**Agent 动作：**

```bash
cloudcc reimbursement import -f 报销单批量导入_已填充.xlsx
```

**结果展示：**

成功时：
```markdown
✅ **导入成功！**
- 成功：5 条
- 失败：0 条
- 报销单ID：BX20260610001
- 详情链接：https://app.cloudcc.com/reimbursement/detail/BX20260610001
```

部分失败时：
```markdown
⚠️ **导入完成（存在失败记录）**
- 成功：3 条
- 失败：2 条

❌ 错误详情：
1. 第8行：报销金额格式错误[abc]
2. 第10行：项目编号[P999]在系统中不存在

> 你可以修正 Excel 后重新执行导入，或联系管理员处理。
```

---

## 错误处理

| 错误 | 处理方式 |
|------|---------|
| 401 / Token 过期 | 重新登录：`cloudcc auth login` |
| 403 | 提示权限不足，联系管理员 |
| 500 | 稍后重试 |
| Excel 路径不存在 | 检查文件路径 |
| Python 脚本报错 | 检查依赖：`pip install -r scripts/requirements.txt` |

---

## 脚本资源

| 脚本 | 用途 | 使用方式 |
|------|------|--------|
| `scripts/reimbursement-fill-invoice.py` | 发票数据填充到模板 | `python scripts/reimbursement-fill-invoice.py <模板> --from-file <JSON>` |
| `scripts/reimbursement-validate-invoices.py` | 验证报销发票数据完整性 | `python scripts/reimbursement-validate-invoices.py invoices.json` |

### Windows 用户注意事项

如果遇到 `UnicodeEncodeError` 错误：
1. 确保使用 Python 3.8+
2. 设置环境变量：`set PYTHONIOENCODING=utf-8`
3. 或使用 PowerShell 运行：`$env:PYTHONIOENCODING='utf-8'; python script.py`

---

## 发票处理最佳实践

### 金额提取策略

系统按以下优先级尝试提取金额：

1. **增値税发票标准格式**：`价税合计（小写）¥XXX.XX`
2. **普通发票格式**：`合 计 ¥XXX.XX`
3. **机票行程单**：包含多个 CNY 的行，取最后一个値
4. **火车票等简单格式**：`价:XXX.XX` 或 `¥XXX.XX`
5. **文件名推断**：如"发票金额410.00元.pdf"

### 数据验证清单

导入前运行验证脚本检查数据：

```bash
python scripts/reimbursement-validate-invoices.py invoices.json
# ✅ 验证通过：5张发票，总金额 ¥2,109.20
# ⚠️ 警告：第2张发票金额较小 (¥87.00)，请确认
```

验证内容：必填字段完整性、格式正确性、金额合理性。

### 交互模板

**金额提取失败时**
```
📋 需要确认 - 第 {idx} 张发票
文件：{filename} | 发票号：{invoice_no} | 日期：{date}
❓ 无法自动提取金额，请选择：
1. 告诉实际金额  2. 回复"跳过"留空  3. 回复"查看原文"
```

**批量确认时**
```
📊 批量确认（{count} 张待确认）
| # | 文件名 | 发票号 | 建议金额 |
|---|--------|--------|------|
请回复："全部确认" / "修改第N条为XXX" / "查看详情"
```

---

## 附件管理功能

报销单支持上传和管理附件，包括发票原件、合同、证明文档等。

### 上传附件

**命令：**
```bash
cloudcc reimbursement upload-attachment -f <文件路径> -o <报销单ID或编号> [--output json]
```

**参数说明：**
- `-f, --file`：附件文件路径（必填）
- `-o, --order`：报销单ID或编号（必填）
- `--output`：输出格式，可选 `table`（默认）或 `json`（供Agent使用）

**示例：**
```bash
# 使用报销单编号上传
cloudcc reimbursement upload-attachment -f 发票.pdf -o 20260722547361

# 使用报销单ID上传
cloudcc reimbursement upload-attachment -f 合同扫描件.jpg -o a1320263834AA41i02R8
```

**响应示例（JSON格式）：**
```json
{
  "success": true,
  "attachmentId": "bda202671220719nYmse",
  "fileName": "发票",
  "suffix": "pdf",
  "fileSize": 1289743,
  "fileSizeText": "1.23 MB",
  "relatedId": "a1320263834AA41i02R8",
  "description": "报销单附件",
  "createdAt": ""
}
```

**Agent使用建议：**
- 始终使用 `--output json` 参数获取结构化数据
- 解析 `success` 字段判断是否成功
- 使用 `attachmentId` 进行后续操作

**限制条件：**
- 单个文件大小不超过 **100MB**
- 支持的文件类型：PDF、图片（JPG/PNG/JPEG）、Word、Excel等常见格式
- 必须已登录且Token有效
- 报销单必须存在

### 查询附件列表

**命令：**
```bash
cloudcc reimbursement list-attachments -o <报销单ID或编号> [--output json]
```

**参数说明：**
- `-o, --order`：报销单ID或编号（必填）
- `--output`：输出格式，可选 `table`（默认）或 `json`（供Agent使用）

**示例：**
```bash
cloudcc reimbursement list-attachments -o 20260722547361
```

**响应示例（JSON格式）：**
```json
{
  "success": true,
  "orderId": "20260722547361",
  "count": 3,
  "attachments": [
    {
      "index": 1,
      "fileName": "发票.pdf",
      "fileSize": 1289743,
      "fileSizeText": "1.23 MB",
      "attachmentId": "bda202671220719nYmse",
      "createdAt": ""
    },
    {
      "index": 2,
      "fileName": "合同扫描件.jpg",
      "fileSize": 2569472,
      "fileSizeText": "2.45 MB",
      "attachmentId": "bda20263613C5C1Rs5l9",
      "createdAt": ""
    }
  ]
}
```

**Agent使用建议：**
- 始终使用 `--output json` 参数获取结构化数据
- 解析 `success` 字段判断是否成功
- 通过 `count` 获取附件数量
- 遍历 `attachments` 数组处理每个附件

**特性：**
- 支持通过报销单ID或编号查询
- 自动过滤已删除的附件
- 按创建时间降序排列
- 文件大小自动格式化显示（B/KB/MB/GB）

### 典型使用场景

| 场景 | 操作 |
|------|------|
| 导入报销单后补充发票原件 | `upload-attachment -f 发票.pdf -o 报销单编号` |
| Agent程序化上传附件 | `upload-attachment -f 发票.pdf -o 报销单编号 --output json` |
| 查看某报销单的所有附件 | `list-attachments -o 报销单编号` |
| Agent程序化查询附件 | `list-attachments -o 报销单编号 --output json` |
| 批量上传多个附件 | 多次执行 `upload-attachment` 命令 |
| 验证附件是否上传成功 | 先上传，再执行 `list-attachments` 确认 |

### 注意事项

1. **文件大小限制**：超过100MB的文件会被拒绝上传
2. **认证要求**：必须先登录（`cloudcc auth login`）
3. **报销单存在性**：如果报销单不存在，会返回错误提示
4. **附件类型**：系统会自动识别文件类型，默认为 `attachment` 类型
5. **上传时间显示**：当前版本中上传时间可能显示为 N/A，这是已知问题

---

**版本：** v2.3
**最后更新：** 2026-07-22
