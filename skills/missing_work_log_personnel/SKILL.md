---
name: missing_work_log_personnel
description: Immediately generate "missing work log personnel" analysis report. Compare active_employee_list.xlsx and work_logs.xlsx to identify personnel who haven't submitted work logs. Must directly invoke this skill when users ask "who hasn't submitted work logs", "check work log completeness".
---

# 执行指令：漏报人员分析

当此技能被触发时，Agent 必须按照以下步骤**立即执行**：

## 第一步：环境预检
1. **依赖检查**：运行 `python3 -c "import pandas, openpyxl; print('Ready')"`。
2. **输入确认**：确认当前工作目录下存在必要的 Excel 输入文件。

## 第二步：运行分析脚本 (动态路径)
Agent 必须运行该技能文件夹内的 `generate.py` 脚本。**注意**：
- 必须使用脚本在文件系统中的**绝对路径**以确保在任何目录下均可执行。
- 必须通过 `--output .` 参数将结果生成在用户**当前工作目录**中。

**执行逻辑：**
- 运行：`python3 <技能绝对路径>/generate.py --output .`

## 第三步：输出确认与详细汇总
1. **确认位置**：告知用户报告已生成在当前工作目录。
2. **详细汇报**：
   - **统计数据**：在职总人数、已报工人数、漏报人数。
   - **处理细节**：已对比名单、已排除 7 位特定高层人员、统计了时间跨度。

## 过滤规则
- **默认排除人员**：张乐奕、杨廷琨、黄宸宁、李华、李海清、李轶楠、章芋文。
