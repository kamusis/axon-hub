---
name: grill-consensus-doc
description: "编写与归档 Grill 对抗研讨终版《架构共识实施文档》。当 Grill 流程主持人（Grill Moderator / Team Leader）在决策树推演闭环时触发。强制在文档首部前置‘Grill 核心价值与盲区规避对比’章节，基于标准实施模板提炼系统架构方案、状态机流转、数据模型与并发控制、CLI/UI 契约及全层级测试矩阵，并将生成的 .md 文件作为工单附件上传归档。"
---

# Grill 架构共识实施文档编写规约 (Grill Architecture Consensus Document Specification)

用于指导 Grill Team 流程主持人（Grill Moderator）在多智能体对抗研讨闭环后，将全过程的技术决策与盲区质询提炼为权威的《架构共识实施文档》，作为后续工程落地的唯一实施基准。

---

## 核心原则 (Core Principles)

1. **价值强制前置 (Value Upfront)**：
   - Grill 的核心价值在于**在编写一行代码之前，消灭灾难性的隐性生产盲区**。
   - 必须在文档第一章强制放置《Grill 核心价值与盲区规避对比表》，突出展示“若无 Grill 盲目开发会遗漏什么、带来何种生产级故障，以及 Grill 最终锁定的稳固设计”。
2. **规范模板驱动 (Template-Driven SSOT)**：
   - 严禁随意发挥章节排版。必须直接读取并完整遵循本技能附带的标准模板：
     `references/consensus_blueprint_template.md`
   - 所有技术决策必须是经双方确认的闭环事实，严禁残留未决歧义（To Be Decided）。
3. **实体落盘与附件上传 (Physical Markdown Artifact & Ticket Attachment)**：
   - 终稿必须先在本地保存为 `<核心需求名称>_架构共识实施文档.md`。
   - 必须通过 CLI 命令 `mopheus ticket comment add <ticket-id> --attachment <file-path>` 挂载至工单附件区，作为后续开发实施的权威蓝图。

---

## 流程主持人 (Leader) 执行 SOP

当 Griller 与 Proposer 完成所有质询，Griller 声明“决策树推演闭环”时，Leader 必须依次执行：

### 1. 加载实施文档标准模板
读取本技能的模板文件：
`references/consensus_blueprint_template.md`

模板固定包含以下 6 大通用核心章节：
- **一、【价值前置】Grill 核心价值与盲区规避对比**（表格呈现初始需求设想、质询出的隐性盲区、潜在生产/返工风险、终版共识决策）
- **二、核心架构方案与防范矩阵**（链路交互拓扑、不可突破的技术红线、边界异常与降级退化矩阵）
- **三、状态机与生命周期流转（若适用）**（领域实体与运行状态枚举、状态跃迁与非法拦截跳转表、生命周期与异常恢复兜底；不涉及状态机时说明生命周期机制或标注不适用）
- **四、数据模型变更与并发控制**（遵循 AGENTS.md：无 FK/CHECK、带 workspace_id 与索引、COMMENT ON 注释；明确并发模型 CAS/锁机制、幂等保障与 RBAC 权限隔离）
- **五、接口、CLI 与前端 UI 交付契约**（CLI 优先命令族、REST API camelCase 规范与标准响应体、UI AlertDialog 防误触与 i18n useT 国际化）
- **六、全层级质量与测试验收矩阵**（单测核心分支、Service 事务与并发用例、Playwright E2E 验收规范及异常边界场景）

### 2. 提炼并填充实施内容
1. 对比原工单需求背景与对抗全过程，提取 3~5 项最具代表性的隐患规避事实填入第 1 章价值对比表。
2. 将双方确认的架构选型、参数基线、状态枚举、数据表变更及测试用例完整填入对应章节。
3. 去除文件名特殊字符，将完成的 Markdown 内容写入本地文件：
   `<核心需求名称>_架构共识实施文档.md`

### 3. 上传工单附件归档
```bash
mopheus ticket comment add <ticket-id> \
  --attachment "<核心需求名称>_架构共识实施文档.md" \
  --content "【架构共识实施文档归档】已将本次 Grill 对抗研讨最终达成的全部技术共识与工程决策整理成终版规范文档，并作为附件上传至工单，供后续工程落地直接依循。"
```

### 4. 流转工单状态
```bash
mopheus ticket status <ticket-id> in_review
```
> 💡 **说明**：Grill 流程完成方案设计评审共识达成后，工单状态默认设为 `in_review`，供后续排期或具体开发测试继续流转。
