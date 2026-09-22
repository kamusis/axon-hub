# CloudCC Skill 故障排查指南

## 快速诊断流程图

```
开始
  ↓
执行 cloudcc auth status
  ↓
是否显示 "✓ Logged in"？
  ├─ 否 → 执行认证流程（见 auth.md）
  └─ 是 → 继续
  ↓
执行业务命令
  ↓
是否返回错误？
  ├─ 401 → Token过期，重新登录
  ├─ 403 → 权限不足，联系管理员
  ├─ 500 → 服务端异常，稍后重试
  └─ 其他 → 查看下方详细排查
```

## 常见错误代码对照表

| 错误代码 | 含义 | 解决方案 |
|---------|------|---------|
| 401 | 未授权 | Token过期，执行 `cloudcc auth login` |
| 403 | 禁止访问 | 权限不足，联系管理员授予权限 |
| 404 | 资源不存在 | 检查参数是否正确（如项目编号、活动ID） |
| 500 | 服务器内部错误 | 稍后重试，或联系技术支持 |
| FileNotFoundError | 文件不存在 | 检查文件路径，建议使用绝对路径 |
| UnicodeEncodeError | 编码错误 | 设置 `PYTHONIOENCODING=utf-8` 或使用 PowerShell |
| JSONDecodeError | JSON格式错误 | 检查 invoices.json 格式是否正确 |

## Windows 编码问题详解

### 症状
```
UnicodeEncodeError: 'gbk' codec can't encode character '\xa5'
```

### 原因
Windows 控制台默认使用 GBK 编码，而 Python 脚本输出 UTF-8 字符（如 ¥、✅）。

### 解决方案

**方案1：设置环境变量（推荐）**
```powershell
# PowerShell
$env:PYTHONIOENCODING='utf-8'
python scripts/reimbursement-fill-invoice.py ...
```

```cmd
# CMD
set PYTHONIOENCODING=utf-8
python scripts/reimbursement-fill-invoice.py ...
```

**方案2：使用脚本内置支持**
当前脚本已内置 UTF-8 编码支持，通常无需额外配置。

**方案3：重定向输出到文件**
```bash
python scripts/reimbursement-validate-invoices.py invoices.json > output.txt 2>&1
type output.txt
```

## 发票处理常见问题

### Q1: 金额提取失败，显示为 0

**可能原因：**
1. PDF 无文本层（扫描件）
2. 正则表达式不匹配
3. 发票格式特殊

**解决方法：**
1. 检查是否为扫描件：文本长度 < 50 字符
2. 手动查看提取的文本文件
3. 用户提供实际金额

**调试步骤：**
```bash
# 1. 提取文本
python -c "import pdfplumber; pdf=pdfplumber.open('invoice.pdf'); print(''.join([p.extract_text() or '' for p in pdf.pages]))" > invoice.txt

# 2. 查看文本内容
type invoice.txt

# 3. 手动构建 invoices.json
```

### Q2: 火车票文件找不到

**可能原因：**
文件名包含中文，路径编码问题

**解决方法：**
使用 PowerShell 列出文件：
```powershell
Get-ChildItem "D:\path\to\invoices" -Filter "*.pdf" | Select-Object Name
```

或使用 Python glob：
```python
import glob
files = glob.glob(r"D:\path\to\invoices\*.pdf")
for f in files:
    print(f)
```

### Q3: Excel 填充后金额为空

**可能原因：**
1. invoices.json 中 bxje 字段为 0 或缺失
2. 模板文件格式不正确

**解决方法：**
1. 运行验证脚本：`python scripts/reimbursement-validate-invoices.py invoices.json`
2. 检查 JSON 格式：
   ```json
   {
     "bxje": 1140.00,
     "fapiaohao": "26318781111033962073",
     ...
   }
   ```
3. 确保使用正确的模板文件

### Q4: 导入时提示字段错误

**可能原因：**
1. 费用类型不在系统允许列表中
2. 报销类型与费用类型不匹配
3. 日期格式错误

**解决方法：**
1. 查阅 [reimbursement-expense-types.md](reimbursement-expense-types.md) 确认费用类型
2. 查阅 [reimbursement-field-mapping.md](reimbursement-field-mapping.md) 确认字段映射
3. 确保日期格式为 YYYY-MM-DD

## 销售活动创建常见问题

### Q5: 创建活动时提示「找到多个匹配的联系人」

**可能原因：**
通过联系人姓名（如「张三」）存在重名，系统无法确定目标联系人。

**解决方法：**
使用联系人编号代替姓名：
```bash
# 先查询联系人获取编号
cloudcc customer contact query --keyword "张三" --output json
# 使用编号创建
cloudcc activity create --contact "2021111625446" ...
```

### Q6: 创建活动时提示「业务机会不存在」

**可能原因：**
1. 业务机会编号输入错误
2. 业务机会名称模糊匹配无结果
3. 该业务机会不在当前用户权限范围内

**解决方法：**
1. 确认业务机会编号是否正确
2. 使用 `cloudcc project opportunity query --keyword "关键词"` 搜索确认
3. 如确实不存在，需先在 Oracle CC 系统中创建业务机会

### Q7: 创建活动时提示「枚举值格式不正确」

**可能原因：**
`glcj`、`gxjmd`、`feedback`、`type` 等字段缺少括号内的完整描述。

**解决方法：**
必须使用完整格式，包含括号描述：
```bash
# 错误
--glcj "高层"
--type "电话"

# 正确
--glcj "高层(公司分管副总及以上)"
--type "电话沟通"
```

## 日志分析方法

### 启用详细日志

```bash
# Linux/macOS
export CLOUDCC_DEBUG=1
cloudcc activity query --date 本月

# Windows PowerShell
$env:CLOUDCC_DEBUG=1
cloudcc activity query --date 本月
```

### 日志位置
`~/.cloudcc/logs/cloudcc.log`

### 关键日志片段

**API 请求详情：**
```
DEBUG: API request to /api/v1/activity/query
DEBUG: Request body: {"pageNumber": 1, "pageSize": 10, ...}
```

**响应状态码：**
```
DEBUG: Response status: 200
DEBUG: Response body: {"items": [...], "total": 100}
```

**参数验证失败：**
```
ERROR: Validation failed: opKnx must be between 0 and 100
ERROR: Invalid date format: expected YYYY-MM-DD
```

## 性能优化建议

### 大数据集查询

当查询结果超过 1000 条时：

```bash
# 使用智能分页并导出到文件
cloudcc activity query --date 本月 --page-all --output json --output-file data.json

# 限制页数
cloudcc activity query --date 本月 --page-all --page-limit 10 --output json

# 调大每页数量减少请求次数
cloudcc activity query --date 本月 --page-all --page-size 200 --output json
```

### 批量发票处理

当处理超过 20 张发票时：

1. **分批处理**：每次处理 10-20 张
2. **使用缓存**：保存已识别的发票信息
3. **并行提取**：使用多线程并行提取文本（高级用户）

## 获取帮助

如果以上方法无法解决问题：

1. **检查文档**：
   - [auth.md](auth.md) - 认证问题
   - [activity.md](activity.md) - 销售活动查询与创建
   - [reimbursement-import.md](reimbursement-import.md) - 报销流程

2. **联系支持**：
   - 提供错误日志和复现步骤

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| 2.1.0 | 2026-06-15 | 新增 reimbursement-validate-invoices.py，修复 Windows 编码问题 |
| 2.0.0 | 2026-06-10 | 初始版本发布 |
