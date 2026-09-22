# 认证模块

CloudCC CLI 仅支持**邮箱验证码登录**。

## 登录流程

```bash
# Step 1: 发送验证码
cloudcc auth send-code --email <邮箱地址>

# Step 2: 输入验证码登录
cloudcc auth login --email <邮箱地址> --code <验证码>
```

成功输出：
```
✓ Login successful! Token saved to system keyring
```

## 检查登录状态

```bash
cloudcc auth status
```

| 输出 | 含义 |
|------|------|
| `✓ Logged in` + `System Keyring (secure)` | Token 存在系统密钥链 |
| `✓ Logged in` + `Encrypted file (fallback mode)` | 降级为加密文件 |
| `✗ Not logged in` | 未登录，需执行登录流程 |

## 查看当前用户信息

```bash
cloudcc auth whoami
```

输出示例：
```
👤 Current User Info
  Email:        user@example.com
  Username:     张三
  ResourceType: 内部用户
  Region:       华东区
  Company:      云和恩默
  Roles:        SALES_REP, REGIONAL_MANAGER
```

字段说明：

| 字段 | 含义 |
|------|------|
| Email | 登录邮箱 |
| Username | 用户姓名 |
| ResourceType | 资源类型（内部用户/外部用户） |
| Region | 所属区域 |
| Company | 所属公司 |
| Roles | 角色列表 |

## 退出登录

```bash
cloudcc auth logout
```

## Token 过期处理

当命令返回以下错误时表示 Token 已过期：

```
token has expired. Please run 'cloudcc auth login' again
```

或：
```
❌ API Error (code: 401)
💡 Hint: Token已过期或无效，请重新登录
```

**处理步骤：**
1. Token 会被 CLI 自动清理
2. 提示用户需要重新登录
3. 引导用户走 send-code → login 两步流程

## 凭据存储架构

CLI 使用 `FallbackStore` 策略，所有平台优先使用系统密钥链：

```
FallbackStore
├── KeyringStore（优先）
│   ├── macOS    → Keychain Access
│   ├── Windows  → Credential Manager（凭据前缀 cloudcc-cli）
│   └── Linux    → Secret Service (GNOME Keyring / KDE KWallet)
└── EncryptedFileStore（降级）
    └── ~/.cloudcc/credentials.enc (AES-256-GCM)
```

### 配置文件位置

| 文件 | 位置 |
|------|------|
| 加密凭据（降级） | `~/.cloudcc/credentials.enc` |
| 配置文件 | `~/.cloudcc/config.json` |

## 自动认证检查规则

Agent 在执行任何 cloudcc 业务命令前，必须：

1. 先执行 `cloudcc auth status`
2. 已登录 → 继续执行
3. 未登录 → 询问邮箱 → `send-code` → 用户提供验证码 → `login`
4. 登录成功后继续执行原命令

**绝不在未认证状态下执行查询命令。**
