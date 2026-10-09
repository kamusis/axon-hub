---
name: wechat-history-export
description: 在 Windows 环境下一站式自动探测、提取密钥、解密微信 4.x（Weixin.exe / xwechat_files）本地数据库，并精确检索与导出单人或群聊的完整聊天记录。当用户提到“导出微信聊天记录”、“备份微信记录”、“导出跟某人的微信记录”、“解密微信数据库”、“读取微信本地消息”、“分析群聊讨论”、“微信数据导出”、“wechat export”、“wechat chat history”时必须使用此技能。支持微信号、备注名、昵称自动模糊解析与无条数截断导出。微信 3.x（WeChat.exe）不适用，需改用旧版 pywxdump。
---

# 微信 4.x 聊天记录导出与检索 (wechat-history-export)

用于在 Windows 平台直接提取运行中微信 4.x 的本地数据库，并导出指定联系人或群聊的完整聊天记录（支持微信号、备注名、昵称输入，输出易读文本、JSON 与 Excel 兼容 CSV）。

## 核心特性

- **零第三方依赖**：纯 Python 3.10+ 标准库（sqlite3、ctypes 调用系统 `bcrypt.dll`、hashlib），无需安装 `pycryptodome` 或外部 C 扩展。
- **全自动身份对齐**：支持直接输入用户的“微信号”（如 `jp0127lily`）、“备注名”（如“张三”）或“微信昵称”，脚本自动关联 `contact.db` 反查内部 `username`。
- **无静默截断**：默认全量导出目标会话的历史记录（不设 400 条上限限制）。
- **全分片合并检索**：自动遍历并去重合并 `message_fts_v4_0` ~ `message_fts_v4_3` 全部分片，杜绝漏扫消息。
- **多格式输出**：同时产出排版时间线文本（`digest.txt`）、结构化数据（`matches.json`）及表格（`chat.csv`）。

---

## 执行前提

1. **操作系统**：Windows 10/11。
2. **环境要求**：Python 3.10+。
3. **关键条件**：**必须保持微信处于登录且运行状态**（微信 4.1+ 内存中无常驻明文密钥，密钥仅在运行时作为内存对象临时存在，退出即失效）。

---

## 标准操作流程 (4 步)

所有脚本均位于本技能的 `scripts/` 目录下。

### 步骤 1 · 环境探测与路径定位

运行探测脚本，自动识别微信主进程 `Weixin.exe`、版本号及当前登录账号的数据库目录：

```powershell
python "<SKILL_DIR>/scripts/find_wechat.py"
```

- 确认输出的 `Weixin.exe` PID 与 `--db-dir` 路径（通常为 `D:\xwechat_files\<wxid>\db_storage`）。

### 步骤 2 · 提取密钥并解密数据库 (一步完成)

使用内置的 `wcdb_key_tool_windows.py`，通过 Windows CNG 内存扫描提取密钥并解密出明文 SQLite：

```powershell
python "<SKILL_DIR>/scripts/wcdb_key_tool_windows.py" extract `
  --db-dir "<步骤1输出的 db_storage 路径>" `
  --output ".\decrypted" `
  --decrypt
```

- **预期结果**：约 26 个数据库 100% 成功解密并存入当前目录的 `decrypted/` 文件夹中。

### 步骤 3 · 检索与导出目标聊天记录

#### 场景 A：导出指定单人或群聊的全部记录（最常用）

直接传入好友的微信号、备注名或原始 ID：

```powershell
python "<SKILL_DIR>/scripts/query_messages.py" `
  --decrypted-dir ".\decrypted" `
  --session "<微信号 或 备注名 或 昵称>" `
  --out-dir ".\out_<联系人>"
```

> **示例**：
> `python "<SKILL_DIR>/scripts/query_messages.py" --decrypted-dir ".\decrypted" --session "jp0127lily" --out-dir ".\out_jp0127lily"`

#### 场景 B：按关键词与时间范围过滤导出

```powershell
python "<SKILL_DIR>/scripts/query_messages.py" `
  --decrypted-dir ".\decrypted" `
  --session "<联系人>" `
  --keywords "发票,报销,项目" `
  --since 2026-01-01 `
  --until 2026-10-09 `
  --out-dir ".\out_filter"
```

#### 场景 C：查看所有活跃会话排行榜（不导出正文）

```powershell
python "<SKILL_DIR>/scripts/query_messages.py" `
  --decrypted-dir ".\decrypted" `
  --list `
  --top 20
```

### 步骤 4 · 查看产出物与清理敏感数据

导出文件存放在指定的输出目录中：
- `digest.txt`：时间升序排版的易读文本，包含时间戳、发言人角色与正文。
- `chat.csv`：带 UTF-8 BOM 的表格文件，可直接双击用 Excel 打开分析。
- `matches.json`：完整结构化 JSON，供二次开发或大模型深入分析。

> **安全清理**：导出完成后，若无需继续查询其他联系人，请删除 `decrypted/` 临时文件夹，避免本地明文存储微信完整数据库。

---

## 技术架构与避坑指南

1. **微信 4.1+ 密钥机制**：
   微信 4.x 不再常驻明文 `x'...'` 密钥，老旧工具（如 `pywxdump`）直接内存搜索十六进制必定 0 命中。本工具定位 `Config.Cipher` 对象链并结合 27 字节掩码 XOR 解密提取 raw key，完全兼容 4.1.x。
2. **正文分片机制**：
   微信 4.x 正文表拆分在 `message_fts_v4_0` ~ `message_fts_v4_3` 四个分片中。单查第一张表会丢失超过 80% 的消息，本技能脚本强制全分片遍历聚合。
3. **ID 与名称映射**：
   FTS 库中的会话与发言人 ID 对应 `message_fts.db` 的 `name2id` 表；用户显示名认准 `contact.db` 的 `remark` 与 `nick_name`，不得误用 `session.db` 的 `summary`（那是最后一条消息预览）。

---

## 故障排查

| 现象 | 根因分析 | 解决方案 |
|---|---|---|
| `找不到 Weixin.exe` | 微信未启动或为 3.x 旧版 | 启动并登录微信 4.x（主进程名为 `Weixin.exe`） |
| `extract 命中 0` | 微信未登录或权限不足 | 确保以管理员权限执行终端，且微信处于已登录状态 |
| `未找到 *fts*.db` | 解密路径未生成或失败 | 确认步骤 2 带有 `--decrypt` 参数且解密无报错 |
| `导出记录为 0 条` | 联系人名称输错 | 先执行 `--list` 查看目标联系人的准确名称或微信号 |
