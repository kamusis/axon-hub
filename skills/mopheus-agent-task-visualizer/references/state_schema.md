# State Record Schema (`state_record.json`)

## 目的
记录工作区中已完成解析和统计的 Agent Task ID，实现增量采集与计算。对于已进入终态（`completed`、`failed`、`cancelled`）的历史任务，后续执行时直接复用本地缓存，无需重复调用 API 或再次解析海量 transcript 消息。

## 结构说明
```json
{
  "workspace_slug": "dev",
  "workspace_id": "97e68228-40ea-4c57-8fb6-788ec6e19642",
  "last_synced_at": "2026-08-26T13:50:00Z",
  "total_tasks_tracked": 342,
  "processed_task_ids": {
    "<agent_task_uuid>": {
      "status": "completed",
      "terminal": true,
      "processed_at": "2026-08-26T12:00:00Z",
      "started_at": "2026-08-26T11:58:10Z",
      "completed_at": "2026-08-26T12:00:00Z",
      "messages_count": 34,
      "usage_count": 1
    }
  },
  "active_task_ids": [
    "<running_or_queued_task_uuid>"
  ]
}
```
