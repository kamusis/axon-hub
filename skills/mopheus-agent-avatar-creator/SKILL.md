---
name: mopheus-agent-avatar-creator
description: "为 Mopheus 智能体（Agent）设计并生成极简 Sketch 漫画风专属头像（Avatar）。针对 Web UI 列表与评论区 32×32px 极小尺寸场景优化，严格执行高反差粗墨线手绘、生动卡通五官、高度象征性极简道具、以及角色间绝对互斥的鲜明高饱和纯色背景，彻底避免界面缩略图发黑糊团。"
---

# Mopheus Agent 头像生成规约 (Mopheus Agent Avatar Creator)

用于为 Mopheus 工作区内的各类智能体（Agent）设计并批量生成风格统一、辨识度极高的**极简 Sketch 漫画风**专属头像。

---

## 一、核心视觉红线 (Visual Non-negotiables)

在 Mopheus Web 界面中，Agent 头像主要展示在侧边栏、表格行（`h-8 w-8` / `32×32px`）以及工单评论流中。**极小尺寸下的瞬时辨识度是唯一最高准则**：

1. **绝对禁止复杂 3D 渲染与暗色杂影**：
   - 严禁赛博朋克深黑铠甲、机械金属反光、复杂光影渐变。此类图像缩放至 32px 时会缩成“一团黑”，丧失所有辨识度。
2. **极简黑白墨线漫画风 (Minimalist Ink Sketch Comic Style)**：
   - 采用粗细均匀、干净利落的高反差黑白线描手绘涂鸦风（Doodle / Comic Sketch）。
   - 线条果断，留白充足，轮廓清晰。
3. **生动具象的人物五官 (Expressive Cartoon Facial Features)**：
   - 必须具备可爱生动的漫画眼睛、眉毛、清爽发型与契合角色性格的表情（微笑、敏锐、好奇、沉稳）。
   - **严禁无面人（Faceless Mannequin）或死板机械指示图**。
4. **角色间绝对互斥的高对比纯色平涂底色 (Distinct Flat Solid Backgrounds)**：
   - 必须是 100% 纯色背景，无渐变、无杂斑、无暗角。
   - 同一小队或工作区内的核心角色，底色**严禁撞色**，让用户通过背景色彩一眼区分 Agent 身份。
5. **1~2 项极具象征性的大道具 (Iconic Props)**：
   - 道具必须大而醒目，强化角色职业隐喻，杜绝细碎杂乱零件。

---

## 二、底色与角色视觉隐喻标准

详细映射查阅：[`references/color_palette_matrix.md`](references/color_palette_matrix.md)

- 方案设计 / 架构提案（`Proposer` / `Architect`）：**暖阳亮黄**（Sunny Amber `#F59E0B`），手持图纸卷轴与三角绘图尺。
- 流程主持 / 总结归档（`Moderator` / `Leader`）：**鲜明宝蓝**（Cobalt Blue `#2563EB`），手持演讲麦克风与总结 Checklist 板夹。
- 深度质询 / 缺陷排查（`Griller` / `Tester`）：**活力珊瑚红**（Coral Red `#EF4444`），手持高倍放大镜排查 Bug 与代码异常 `<{}!#;[`。
- 技术布道 / 文档撰稿（`Writer` / `Scribe`）：**薄荷翠绿**（Mint Emerald `#10B981`），手持羽毛笔伏案书写。
- 运维保障 / 数据库巡检（`SRE` / `DBA`）：**极客青蓝**（Cyan `#06B6D4`），手持机械扳手与数据库仪表盘。
- 发布交付 / 流水线网关（`Release Agent` / `Gatekeeper`）：**活力橘橙**（Tangerine `#F97316`），手持放行盖章与发射扳机。

---

## 三、标准执行工作流 (Standard Workflow)

### 1. 确定角色特征与底色
明确目标 Agent 的职责定位、性格气质，从调色板矩阵中选定尚未被占用的纯色平涂背景。

### 2. 注入风格基准参考图 (Reference Conditioning)
若当前小队已有经过用户确认的基准头像（如 `Proposer_avatar.jpg`），在调用 `generate_image` 时**必须传入 `ImagePaths` 包含该参考图**，以确保线条粗细、头身比例、五官画风成套统一。

### 3. 生成头像图片
- 工具：`generate_image`
- 参数：`AspectRatio: "1:1"`，`ImageName: "sketch_avatar_<role>"`
- Prompt 骨架：
```text
A minimalist line sketch comic avatar in the exact same cartoon doodle art style as the reference image, on a solid flat bright [COLOR] background. Features a friendly, expressive [CHARACTER_PERSONA] with cute expressive comic eyes, neat stylized hair, and an engaging [EXPRESSION]. The character is a [ROLE_DESCRIPTION], holding [ICONIC_PROP_1] and [ICONIC_PROP_2]. Bold clean black ink doodle outlines, completely flat bright solid [COLOR] backdrop, zero 3D rendering, no dark shadows, high contrast designed for tiny 32x32 profile icon display.
```
（具体各角色成熟 Prompts 见 [`references/prompt_examples.md`](references/prompt_examples.md)）

### 4. 交付与落盘规范
1. **本地交付目录（默认）**：
   将生成的图片规范命名并复制至用户下载目录，方便在 Web 界面中通过文件选择器直接拖拽上传：
   `C:\Users\kamus\Downloads\mopheus_avatars\<Role_Name>_avatar.jpg`
2. **CLI 自动绑定（若用户明确要求代为上传）**：
   ```bash
   mopheus agent avatar <agent-id> --file "C:\Users\kamus\Downloads\mopheus_avatars\<Role_Name>_avatar.jpg"
   ```
