# log-analysis

Windows 原生日志分析工具集，不依赖 WSL。

## 脚本列表

| 脚本 | 用途 |
|------|------|
| `scripts/log_grep.py` | 关键词上下文搜索（类似 `grep -C`） |
| `scripts/log_time_stats.py` | 关键词频次统计 + Top N 输出 |

## 使用前提

- Python 3.x（已装在 `C:\Users\kamus\.workbuddy\binaries\python\versions\3.13.12\python.exe`）
- 日志文件默认以 UTF-8 读取，自动降级处理乱码

## 使用方法

### 1. log_grep.py — 关键词上下文搜索

```powershell
# 单关键词
python C:\Users\kamus\.workbuddy\skills\log-analysis\scripts\log_grep.py "shutdown" app.log

# 多关键词（正则风格，| 分隔）
python C:\Users\kamus\.workbuddy\skills\log-analysis\scripts\log_grep.py "shutdown|ERROR|FATAL" app.log

# 从 stdin 接收（配合管道）
Get-Content app.log -Tail 10000 | python C:\Users\kamus\.workbuddy\skills\log-analysis\scripts\log_grep.py "xlog|error"
```

**输出示例**：命中的每处会打印前后共 10 行上下文，方便定位问题现场。

### 2. log_time_stats.py — 关键词频次统计

```powershell
# 统计默认关键词（ERROR, WARN, FATAL, exception, failed, timeout）
python C:\Users\kamus\.workbuddy\skills\log-analysis\scripts\log_time_stats.py app.log

# 自定义关键词
python C:\Users\kamus\.workbuddy\skills\log-analysis\scripts\log_time_stats.py app.log ERROR WARNING exception
```

**输出示例**：每个关键词显示出现频次 Top 10 的行，并输出总命中率。

## 配合 Windows 内置 tar 解压

```powershell
# 解压 .tar.gz
tar -xzf C:\path\to\mogdb_log_26.tar.gz -C C:\output\

# 解压 .rar（需 7-Zip）
& "C:\Users\kamus\scoop\apps\7zip\current\7z.exe" x "C:\path\to\042621.rar" "-oC:\output\" -y
```