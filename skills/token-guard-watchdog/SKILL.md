---
name: token-guard-watchdog
description: "周期性巡检工作区内正在运行的 Agent Tasks，检测死循环、Subagent 生命周期死锁及高频异常 Token 消耗，执行旁路中断熔断并创建工单记录。"
---

# Token Guard Watchdog (智能体死循环巡检看门狗)

## 概述

此 Skill 用于周期性巡检 Mopheus 工作区中所有正在运行（`running`）的 Agent Tasks。当检测到特定死循环特征（例如 Subagent 生命周期续接死锁 `subagent-lifecycle-wait`、连续无脑重复输出、或高频停滞无工具调用）时，自动执行旁路熔断（`mop agent-task cancel`），并创建事故工单进行告警与审计记录。

## 执行方式

运行内置的巡检脚本 `scripts/patrol.py`：

```bash
python scripts/patrol.py
```

### 可选参数

- `--workspace-id <uuid>`: 指定工作区 ID（默认使用当前环境活跃工作区）。
- `--profile <name>`: 指定 Mopheus 配置 profile。
- `--dry-run`: 仅检测与输出报告，不执行真实取消和工单创建。

## 判定规则

1. **Subagent 生命周期续接死锁 (Subagent Lifecycle Wait Loop)**：
   - 任务消息中包含 `Wait for the pending subagents to complete` 或 `subagent-lifecycle-wait` 续接指令重复出现 ≥ 3 次。
2. **完全相同文本重复死循环 (Identical Output Loop)**：
   - 连续 ≥ 4 次生成完全一致的相同文本回复，且无状态推进。
3. **高频高事件数停滞 (High Volume Repetition Runaway)**：
   - 任务总事件数已达 100+，且近期工具调用完全停滞、文本重复率极高。

## 熔断与告警流程

1. **旁路熔断**：调用 `mop agent-task cancel <task-id>` 强制终止任务。
2. **记录工单**：调用 `mop ticket create` 创建高优先级（Priority 1）的事故记录工单，附带诊断详情与样例内容。
3. **关联通知**：若原任务有关联工单，在原工单下方追加评论通知负责人。
4. **正常结束**：若未发现异常任务，静默退出，不产生多余噪音和工单。
