---
name: qq-history-export
description: 在 Windows 环境下免安装一站式自动探测、只读提取内存密钥、解密 QQ NT（QQ.exe / Tencent Files / nt_msg.db）本地数据库，并按好友 QQ 号、群号、备注名或昵称检索与导出聊天记录。当用户提到“导出QQ聊天记录”、“备份QQ记录”、“导出跟某人的QQ记录”、“解密QQ数据库”、“读取QQ本地消息”、“分析QQ群聊讨论”时使用。要求 QQ 正在运行且已登录。
agent_created: true
---

# QQ NT (9.x+) 本地聊天记录解密与消息检索

针对 Windows 本机上运行的 **QQ NT（QQ.exe / QQ 9.x+ 架构）**，提供零第三方依赖（纯标准库 Python + 独立静态扫描器）的聊天记录导出流程。

流程：`探测环境与数据目录 → 内存只读提密钥解密 → 按 QQ号/备注/群名检索导出`。

---

## 核心脚本清单

- `scripts/find_qq.py` — 自动探测运行中的 QQ 进程、数据根目录及活跃登录账号
- `scripts/decrypt_qq.py` — 调用内置非侵入式扫描器从内存提取密钥并解密数据库到明文 SQLite
- `scripts/query_qq_messages.py` — 按目标 QQ 号/备注/昵称/群号及关键词与时间窗检索，并输出 TXT / JSON / CSV

工具二进制文件位于 `bin/x_key_scanner.exe`（开源项目 [QQBackup/x_key_scanner](https://github.com/QQBackup/x_key_scanner)，只读扫描，不注入，不改动 QQ 进程）。

---

## 1. 环境与账号探测

确保 QQ 保持运行且已登录：

```bash
python scripts/find_qq.py
```

- 输出当前运行的 `QQ.exe` 进程 PID、内存占用与版本；
- 扫描系统所有可能的 `Tencent Files` 数据根目录（如 `D:\Documents\Tencent Files`）；
- 列出各账号的 `nt_msg.db` 路径、大小与最近写入时间，标出当前最活跃账号。

---

## 2. 内存密钥提取与数据库解密

```bash
python scripts/decrypt_qq.py --output decrypted
```

- 自动扫描运行中 `QQ.exe` 进程内存获取 16 字节 SQLCipher 4 密钥；
- 去除 `nt_msg.db` 等前置 1024 字节腾讯私有 Header；
- 合并 `-wal` 预写日志（确保刚收发的新消息不丢失）；
- 产出明文 SQLite 数据库到 `decrypted/<uin>/`（如 `nt_msg.db`, `profile_info.db`, `group_info.db` 等）；
- 自动验证明文数据库表行数。

> 若密钥扫描耗时或未匹配，可加上 `--strong` 启用强力扩散扫描模式。

---

## 3. 消息检索与多格式导出

```bash
# 1) 查看最近活跃会话排行（不导出正文）
python scripts/query_qq_messages.py --decrypted-dir decrypted --list

# 2) 导出与指定好友或群聊的全部记录（直接输入对方 QQ 号、好友备注或昵称）
python scripts/query_qq_messages.py --decrypted-dir decrypted \
  --session "12345678" --out-dir out_12345678

# 3) 按关键词与时间范围筛选导出
python scripts/query_qq_messages.py --decrypted-dir decrypted \
  --session "工作群" --keywords "上线,发布,故障" \
  --since 2026-01-01 --until 2026-06-30 --out-dir out_work
```

### 产出物

- `<out-dir>/digest.txt`：按会话分组、时间正序排列的对话文本摘录（含发言人与时间戳，供 AI 阅读与总结）；
- `<out-dir>/matches.json`：全量结构化结果，包含完整时间戳、发送者与正文；
- `<out-dir>/chat.csv`：带 UTF-8 BOM 编码的表格，可直接用 Excel 双击打开筛选。

默认 `--max-per-session 0` 为全量无截断导出。

---

## 4. 数据库结构参考

解密后的 `nt_msg.db` 为标准明文 SQLite：

| 表名 | 含义与关键列 |
|---|---|
| `c2c_msg_table` | 好友私聊消息表。<br>`40001`: 消息 ID<br>`40050`: Unix 时间戳<br>`40013`: 方向 (1=发送, 0=接收)<br>`40030`: 对方 QQ 号 (`peer_qq`)<br>`40033`: 发送者 QQ 号 (`sender_qq`)<br>`40090`: 发送者昵称<br>`40800`: Protobuf 格式消息体 (含富文本、图片、表情等) |
| `group_msg_table` | 群聊消息表。<br>`40001`: 消息 ID<br>`40050`: Unix 时间戳<br>`40030`: 群号 (`group_code`)<br>`40033`: 发送者 QQ 号<br>`40090`: 发送者群名片/昵称<br>`40800`: Protobuf 消息体 |
| `recent_contact_v3_table` | 最近联系人与会话元数据表。<br>`40021`: 会话 peer UID / 群号<br>`40030`: 对方 QQ 号 / 群号<br>`40093`: 会话显示名称<br>`40094`: 昵称<br>`40095`: 备注名 |

### 消息体 Protobuf 结构简要说明
字段 `40800` 中，消息正文字段为 `45101`（UTF-8 编码文本）。脚本内置递归 Wire 解码器，自动提取纯文本、识别 `[Image]`、`[File: <filename>]` 与 `[Sticker]`。

---

## 5. 故障排查

| 现象 | 原因 | 处理建议 |
|---|---|---|
| `No running QQ.exe process detected` | QQ 未启动或当前不是 NTQQ | 启动 QQ 9.x 并登录；旧版 QQ (9.7 之前) 不适用本工具 |
| 密钥扫描提示未管理员运行 | Windows 进程保护/权限受限 | 以管理员身份打开终端重新执行解密步骤 |
| 搜好友 QQ 号无结果 | 会话 ID 或 peer UID 匹配未覆盖 | 脚本已支持直接传 QQ 号、备注、昵称与 UID；可先跑 `--list` 查看所有会话 ID |
| 消息正文含有 `[Image]` 或 `[File]` | 该条消息为多媒体内容 | 正常现象；富文本附件在原库中存为哈希路径，文本已正常提取 |

---

## 6. 合规与安全边界

仅限用户本机、用户自己的账号、且用户明确要求时操作。本工具对 QQ 进程为只读访问，不读取未授权数据，不上传任何内容到云端或第三方。
