---
name: gzh-publish-remote
description: Publish formatted WeChat Official Account (微信公众号) HTML articles to the WeChat Draft Box from a local laptop with a dynamic IP by relaying through the whitelisted remote server (dev.mopheus.ai) using split-custody encryption (~/.config/gzh-publish-remote/secret.key locally + enc:... SQLite on the server). Always prefer this skill over gzh-publish when running on a local laptop (macOS/Windows) whenever the user asks to publish, sync, or push an article/HTML/blog to WeChat Official Account draft box (发布到公众号, 发布到公众号草稿箱, 同步到草稿箱, 发布微信草稿, publish to wechat).
---

# 微信公众号远程白名单跳板发布技能 (gzh-publish-remote)

专为**本地笔记本（动态 IP，不在微信公众号 IP 白名单内）**设计的公众号草稿一键发布技能。

## 核心安全架构（密文与密钥物理分离）

1. **远端白名单节点（`dev.mopheus.ai` / `163.44.99.140`）只存密文**：
   - 远端 SQLite（`wechat-mcp.db`）中的 `app_secret` 与 `access_token` 均以 `enc:U2FsdGVk...` AES 密文存储。
   - 远端服务器（含数据库、Agent 配置、环境变量）**不保存** `WECHAT_MCP_SECRET_KEY`。
2. **本机笔记本只存解密密钥，不存 `AppSecret`**：
   - 解密密钥保存在本机 `~/.config/gzh-publish-remote/secret.key`（权限 `0600`，不进 Git 仓库）。
   - 发布时由 `scripts/publish_remote.py` 读取本机密钥，通过 SSH 内存环境变量注入给远端短生命周期 `node` 进程完成解密与 API 调用，执行完毕后立即清理远端 `/tmp/gzh_pub_*` 临时目录。

---

## 一键执行命令

准备好经过 `gzh-design` 排版并校验通过的**纯净正文 HTML 文件**（严禁使用带 `_预览.html` 后缀的文件）后，直接执行：

```bash
python3 ~/.gemini/config/skills/gzh-publish-remote/scripts/publish_remote.py \
  --html "<纯净正文HTML绝对路径>" \
  --title "<文章标题，≤64字符>" \
  --author "Kamus" \
  --digest "<文章摘要，≤120字符>" \
  --cover "<可选：封面图本地路径或远程URL，默认自动取HTML内第一张图>"
```

### 脚本自动完成的 5 个步骤

1. **校验与提取图片**：校验 HTML 不含 `<!DOCTYPE>`/`<html>`/`<script>`，提取所有非 `mmbiz.qpic.cn` 的 `<img src="...">`（支持 `https://files.seeusercontent.com/...` 等外链自动下载与本地路径复制）。
2. **封面自动压缩**：若封面图大于 `900KB` 或非 JPEG 格式，自动调用 `sips` 压缩为高画质 JPEG，避免触发微信永久素材大小限制。
3. **SSH 白名单跳板上传（绕过本机 FakeIP 代理）**：默认使用 `-o HostName=163.44.99.140` 直连 `dev.mopheus.ai`，将暂存目录上传至 `/tmp/gzh_pub_<uuid>`。
4. **远端内存解密与微信 API 调用**：
   - `wechat_upload_img`：将正文所有配图转存至微信官方 CDN（`http://mmbiz.qpic.cn/...`）并替换 HTML `src`；
   - `wechat_permanent_media`：将封面图注册为永久素材，获取 `thumb_media_id`；
   - `wechat_draft`：推送草稿箱，开启评论（`needOpenComment: 1`）并展示封面（`showCoverPic: 1`）。
5. **回写与无痕清理**：将替换好 `mmbiz.qpic.cn` 的 HTML 同步回本机原 HTML 文件，`finally` 块自动执行 `rm -rf /tmp/gzh_pub_<uuid>`。

---

## 异常处理：当微信 AppSecret 重置或过期（`40125 invalid appsecret`）

如果需要更换公众号 `AppSecret`，**严禁要求用户在聊天窗口发送明文 `AppSecret`**。引导用户登录服务器执行一行加密录入命令（脚本结束后立即自删）：

```bash
WECHAT_MCP_SECRET_KEY="$(cat ~/.config/gzh-publish-remote/secret.key)"
```
（或在远端通过 `StorageManager.saveConfig({ appId: "<YOUR_WECHAT_APP_ID>", appSecret: "<NEW_SECRET>" })` 带 `WECHAT_MCP_SECRET_KEY` 加密写入 `wechat-mcp.db`）。
