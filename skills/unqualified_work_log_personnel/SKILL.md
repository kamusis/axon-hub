---
name: unqualified_work_log_personnel
description: Immediately generate "unqualified work log personnel" analysis report. Filter vague descriptions from work_logs.xlsx and associate with supervisors. Must directly invoke this skill when users ask "generate unqualified report", "audit work log quality".
---

# 执行指令：报工质量审计

当此技能被触发时，Agent 必须按照以下步骤**立即执行**：

## 第一步：环境与规则预检
1. **依赖检查**：运行 `python3 -c "import pandas, openpyxl; print('Ready')"`。
2. **规则加载**：必须读取**本技能文件夹下**的 `rules.json` 以获取当前审计规则。

## 第二步：运行生成脚本 (动态路径)
Agent 必须运行该技能文件夹内的 `generate.py` 脚本。**注意**：
- 必须使用脚本在文件系统中的**绝对路径**以确保在任何目录下均可执行。
- 必须通过 `--output-dir .` 参数将结果生成在用户**当前工作目录**中。

**执行逻辑：**
- 运行：`python3 <技能绝对路径>/generate.py --output-dir .`
- 如果用户指定了文件：加上 `--report-file` 等对应参数。

## 第三步：输出确认与详细汇总
1. **确认位置**：告知用户报告已生成在当前工作目录。
2. **详细汇报**：
   - **统计数据**：处理条数、发现不合格条数。
   - **执行细节**：确认已完成筛选、关联主管、排序、排除 7 位特定高层人员。
   - **日期区间**：报告覆盖的具体时间跨度。

## 审计逻辑参考
- **规则配置**：详见同目录 `rules.json`。
- **高层排除**：张乐奕、杨廷琨、黄宸宁、李华、李海清、李轶楠、章芋文。
