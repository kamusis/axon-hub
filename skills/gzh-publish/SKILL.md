---
name: gzh-publish
description: Publish formatted HTML or Markdown articles directly to WeChat Official Account (微信公众号) Draft Box using wechat-official-account-mcp. Automatically extracts metadata, downloads external images, uploads content images via wechat_upload_img, replaces <img> src with WeChat mmbiz CDN URLs to prevent broken images/anti-hotlinking, uploads cover images via wechat_permanent_media to acquire thumb_media_id, and creates WeChat drafts via wechat_draft. Use whenever the user asks to publish, sync, or push an article/HTML/blog to WeChat Official Account draft box (发布到公众号, 同步到草稿箱, 发布微信草稿, publish to wechat).
---

# 微信公众号草稿发布技能 (gzh-publish)

使用 `wechat-official-account-mcp` 工具链，将本地排版好的**纯净 HTML** 或 Markdown 文章一键推送到微信公众号草稿箱。

解决微信平台核心限制：
- **微信防盗链白名单机制**：外链图片在微信文章中会被拦截显示为空白。本技能自动通过 `wechat_upload_img` 将所有正文图片转存到微信官方 CDN（`http://mmbiz.qpic.cn/...`）并替换 HTML 中的引用地址。
- **永久封面素材绑定**：自动将文章题图/封面图通过 `wechat_permanent_media` 上传为永久图片素材，获取 `thumb_media_id` 注入草稿。

---

## 🛠️ 所需 MCP 工具速查

| 步骤 | MCP 工具 | 操作 (`action`) | 参数 | 作用 |
|---|---|---|---|---|
| **正文图片转存** | `wechat_upload_img` | `upload` | `file_path: string` | 上传正文图片到微信图床，返回 `url`（不占素材库配额） |
| **封面素材注册** | `wechat_permanent_media` | `add` | `type: "image"`, `file_path: string` | 上传封面图，返回永久 `media_id`（用于 `thumb_media_id`） |
| **临时素材备用** | `wechat_media_upload` | `upload` | `type: "image"`, `file_path: string` | 临时素材（3天有效） |
| **创建草稿** | `wechat_draft` | `add` | `articles: Article[]` | 将处理后的纯净 HTML 推送到公众号草稿箱 |
| **查询草稿** | `wechat_draft` | `list` / `get` | `offset: 0, count: 10` / `media_id: string` | 检查草稿创建状态与详情 |

---

## 📋 执行标准流水线 (Pipeline)

### 第 1 步：定位输入源与元数据提取

从用户指定的文章（`.md` 或 `_排版_*.html`）中提取以下信息：
1. **HTML 正文**：必须使用**不带预览字样的纯净正文 HTML 文件**（如 `..._排版_橄榄手记(olive-journal).html`）。严禁使用带 `_预览.html` 的文件（包含 `<!DOCTYPE>`、`<html>`、`<script>` 会导致接口报错）。
2. **文章标题 (`title`)**：从 Markdown `# 标题` 或 Frontmatter `title` 提取，长度 ≤ 64 字符。
3. **作者署名 (`author`)**：从 Frontmatter `author` 提取（如 `Mopheus Team` / `Kamus`），长度 ≤ 8 字符（微信限制）。
4. **文章摘要 (`digest`)**：从 Frontmatter `summary`/`description` 或文章开头导读提取，长度 ≤ 120 字符。
5. **封面图路径 (`cover_image`)**：从 Frontmatter `cover` 或文章第一张题图提取（本地路径或远程 URL）。

---

### 第 2 步：扫描并下载正文中的所有图片

1. 扫描 HTML 中所有的 `<img ... src="(.*?)" ...>` 标签。
2. 针对每一个图片来源：
   - **如果为远程外链**（如 `https://files.seeusercontent.com/...` 或 GitHub URL）：
     - 自动在本地临时目录（如 `scratch/wechat_images/`）下下载并保存为本地文件（如 `img_0.jpg`）。
   - **如果为本地绝对/相对路径**：
     - 解析为本地文件的绝对路径。

---

### 第 3 步：正文图片转存与 HTML 地址替换 (`wechat_upload_img`)

针对正文中的每一张本地图片：
1. 调用 MCP 工具 **`wechat_upload_img`**：
   ```json
   {
     "action": "upload",
     "file_path": "C:\\path\\to\\local\\img_0.jpg"
   }
   ```
2. 从返回结果中提取微信 CDN 链接：
   ```json
   {
     "url": "http://mmbiz.qpic.cn/sz_mmbiz_jpg/xxxx/0"
   }
   ```
3. 将 HTML 中原始的 `src="..."` 精确替换为微信的 `url`。

---

### 第 4 步：上传封面图获取 `thumb_media_id` (`wechat_permanent_media`)

微信草稿箱强制要求每篇文章必须绑定一个封面素材 ID：
1. 如果用户未单独提供已有 `thumb_media_id`，取文章题图/封面图的本地文件路径。
2. 调用 MCP 工具 **`wechat_permanent_media`**：
   ```json
   {
     "action": "add",
     "type": "image",
     "file_path": "C:\\path\\to\\local\\cover.jpg"
   }
   ```
3. 从返回结果中提取 `media_id`：
   ```json
   {
     "media_id": "ABC123xyz_thumb_media_id",
     "url": "http://mmbiz.qpic.cn/..."
   }
   ```

---

### 第 5 步：推送公众号草稿箱 (`wechat_draft`)

组装最终 Payload 并调用 MCP 工具 **`wechat_draft`**：

```json
{
  "action": "add",
  "articles": [
    {
      "title": "Mopheus Runtime 深度剖析：从单兵 CLI 到企业运行时",
      "author": "Mopheus",
      "digest": "如何通过 Adapter 抽象、零配置探测、标签调度与多层资源守卫，将各类 Provider CLI 转化为企业级智能体运行时。",
      "content": "<section style=... (替换完 mmbiz 图片后的纯净 HTML) ...></section>",
      "thumb_media_id": "ABC123xyz_thumb_media_id",
      "need_open_comment": 1,
      "only_fans_can_comment": 0
    }
  ]
}
```

---

### 第 6 步：交付确认

推送成功后，向用户汇报：
1. **草稿 Media ID**（`media_id`）；
2. **文章标题、作者与摘要**；
3. **转存图片统计**：成功转存替换的图片数量与对应微信 CDN 列表；
4. **提示**：用户可直接登录微信公众号后台（mp.weixin.qq.com）在「草稿箱」中查看、预览与下发群发。

---

## ⚠️ 避坑铁律 (Gotchas)

1. **必须用纯净 HTML 片段**：
   - 严禁传入 `<!DOCTYPE html>`、`<html>`、`<head>`、`<body>` 或 `<script>` 标签，微信后端 API 会直接校验失败。
2. **严禁遗漏外链转存**：
   - 即使正文 HTML 在浏览器预览中能正常看到图片，**如果不经 `wechat_upload_img` 换成 `mmbiz.qpic.cn`，直接发到公众号上 100% 会变成裂图或空白**。
3. **作者名长度限制**：
   - 微信官方限制 `author` 字段最大长度为 **8 个中文字符（或 16 个英文字符）**。如果名字过长（如 `Mopheus Architecture Team`），需自动截断为 `Mopheus` 或 `Mopheus团队`。
4. **标题长度限制**：
   - 微信官方限制 `title` 字段最大长度为 **64 个字符**。
