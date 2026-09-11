# Mopheus Agent 头像底色与角色映射矩阵 (Color Palette Matrix)

为确保智能体在 Mopheus Web 界面（32×32px / 40×40px 极小尺寸列表与工单评论区）中**一眼即辨**，每个角色类型必须绑定专属的高对比度纯色平涂背景。

---

## 一、核心底色映射规范 (Role-to-Color Mapping)

| 智能体角色定位 | 英文角色名示例 | 推荐底色 | 色彩名称与情绪定位 | 典型核心道具 / 视觉隐喻 |
| :--- | :--- | :--- | :--- | :--- |
| **方案设计 / 架构提议** | `Proposer`, `Architect`, `Planner` | **暖阳亮黄** (`#FBBF24` / `#F59E0B`) | 阳光、构想、理性严谨 | 工程蓝图卷轴、三角尺、圆规 |
| **流程主持 / 共识归档** | `Moderator`, `Facilitator`, `Leader` | **鲜明宝蓝** (`#2563EB` / `#3B82F6`) | 稳重、协调、官方可信 | 会议麦克风、总结板夹、Checklist |
| **深度质询 / 安全质检** | `Griller`, `Security Inquisitor`, `Tester` | **活力珊瑚红** (`#EF4444` / `#F43F5E`) | 敏锐、警示、烈火淬炼 | 高倍放大镜、Bug 昆虫、代码字符 `<{}!#;[` |
| **技术布道 / 文档撰稿** | `Blog Writer`, `Doc Scribe`, `Technical Evangelist` | **薄荷翠绿** (`#10B981` / `#059669`) | 清新、创造、笔耕不辍 | 羽毛笔/钢笔、翻开的笔记本/文稿卷轴 |
| **运维监控 / 数据库巡检** | `SRE`, `DB Inspector`, `DevOps Bot` | **极客青蓝** (`#06B6D4` / `#0284C7`) | 敏捷、冷静、高可用保障 | 扳手、压力仪表盘、圆柱形数据库磁盘 |
| **发布交付 / 流水线网关** | `Release Agent`, `PR Gatekeeper`, `Delivery Bot` | **活力橘橙** (`#F97316` / `#EA580C`) | 动力、触发、通关放行 | 火箭发射扳机、质检验讫盖章、通关通行证 |
| **算法研究 / Prompt 专家** | `AI Researcher`, `Prompt Optimizer`, `Data Scientist` | **神秘紫罗兰** (`#8B5CF6` / `#7C3AED`) | 智慧、探索、神经认知 | 发光思考电灯泡、魔法水晶球、双螺旋算子 |
| **日常协理 / 团队看门狗** | `Daily Assistant`, `Watchdog`, `Issue Manager` | **温暖蜜桃/暖灰粉** (`#FB7185` / `#F472B6`) | 友善、贴心、敏捷守护 | 哨子、咖啡杯、便签备忘录、可爱警徽 |

---

## 二、底色与对比度铁律 (Contrast Rules)

1. **100% 纯色平涂 (Solid Flat Color)**：
   - 严禁添加线性渐变、径向渐变、光晕、颗粒杂点。
   - 严禁用暗色、深黑（#000000）、深铁灰作为底色。
2. **黑色纯墨线极高反差 (Black Ink Outlines)**：
   - 所有前景人物和道具一律采用粗细均匀的高反差黑白线描或墨线描边。
   - 保证缩减至 16px 时人物剪影轮廓仍然干净利落。
3. **团队内色系互斥 (Color Diversity per Team)**：
   - 同一个小队或工作区内的核心 Agent，底色绝不可重复撞色（如 Grill Team 锁定：黄+蓝+红 三原色组合，视觉辨识度达到 100%）。
