# Mopheus Agent Task 数据持久化与跨任务共享设计

本文档详细说明 `mopheus-agent-task-visualizer` 技能中的数据持久化架构、跨任务状态共享原理以及多节点扩展规范。

---

## 1. 核心文件与定位规则

技能运行过程中产生三类数据资产：
1. **增量状态文件 (`state_record.json`)**：记录全量历史已同步的 Task ID，打标已终态（completed/failed/cancelled）任务以实现零重复拉取。
2. **Stage 结构化指标 (`stage_tasks.json`)**：对原始 transcript（Thinking、tool:* 调用、Token）进行深度清洗聚合后的多维数据集。
3. **原始转录缓存 (`raw_tasks/<task_id>.json`)**：本地原始消息与用量缓存。

### 路径解析优先级（按序回落）：
```
1. 命令行参数: --data-dir <path>
2. 环境变量:   $MOPHEUS_ANALYTICS_DATA_DIR 或 $MOPHEUS_DATA_DIR
3. 默认共享目录: ~/.mopheus/analytics/<workspace_slug>/
```

---

## 2. 为什么默认路径能天然实现跨 Agent Task 共享？

### Mopheus 任务执行生命周期
1. **Daemon 临时沙箱隔离**：Mopheus Daemon 调度执行单个 Agent Task 时，会为该 Task 分配临时工作区目录（例如 `/home/user/mopheus_workspace/<workspace_id>/<task_id_prefix>/workdir`）。当 Task 结束并经过 TTL 后，Daemon GC 会自动回收该临时目录。
2. **宿主机全局持久层**：宿主机用户主目录（`~/.mopheus/`）属于全局持久存储层，不受单个 Task 沙箱回收的影响。
3. **跨智能体执行协同**：
   - **今天**：由 Agent A（如 Dev-Griller）定时执行，状态写入 `~/.mopheus/analytics/dev/state_record.json`，缓存全部历史任务。
   - **明天**：由 Agent B（如 Daily Assistant / 定时 Cron 智能体）执行，默认自动读取宿主机同一份 `state_record.json`，仅增量拉取过去 24 小时新产生的任务，秒级更新 `stage_tasks.json`。

---

## 3. 分布式 / 多节点 Daemon 共享规范

若定时智能体分散调度在多个不同的 Daemon 节点机上：
1. **挂载网络存储卷 (NFS / EFS / CIFS)**：
   在 Daemon 启动环境配置：
   ```bash
   export MOPHEUS_ANALYTICS_DATA_DIR="/mnt/shared_storage/mopheus_analytics"
   ```
2. **Git 仓库内部归档**：
   通过参数绑定到特定 Git 代码仓目录：`--data-dir ./reports/analytics`。
