#!/usr/bin/env python3
"""
MES 报工统计 HTML 报告生成器
用法：
  python3 generate_report.py \
    --team-ids 2,3,23,19 \
    --team-names "东西大区1部,东西大区2部,东西大区4部,东西大区5部" \
    --from 2026-04-14 \
    --to 2026-04-17 \
    --work-days 4 \
    --title "东西大区四团队报工分析" \
    --output /path/to/report.html

单团队模式（只需 --team-id）：
  python3 generate_report.py \
    --team-id 23 \
    --team-name "东西大区4部" \
    --from 2026-04-14 \
    --to 2026-04-17 \
    --work-days 4 \
    --output /path/to/report.html
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, date, timedelta
from collections import defaultdict

# ─── 颜色主题 ────────────────────────────────────────────────
TEAM_COLORS = ["#f59e0b", "#10b981", "#3b82f6", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"]


def run_mes(cmd: list[str]) -> dict:
    """执行 mes 命令并返回 JSON 结果。"""
    full_cmd = ["mes", "-o", "json"] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"[ERROR] mes 命令输出无法解析: {result.stdout[:200]}", file=sys.stderr)
        return {}


def fetch_summary(team_id: int, from_date: str, to_date: str) -> list[dict]:
    """获取指定团队在时间范围内的报工 summary。"""
    data = run_mes(["statistics", "summary", "--team-id", str(team_id), "--from", from_date, "--to", to_date])
    return data.get("operateCallBackObj", [])


def fetch_calendar(user_id: int, from_date: str, to_date: str) -> dict:
    """获取用户每日报工日历，返回 {date_str: hours} 映射。"""
    data = run_mes(["statistics", "calendar", "--user-id", str(user_id), "--from", from_date, "--to", to_date])
    items = data.get("operateCallBackObj", [])
    result = {}
    for item in items:
        d = item.get("date", "")[:10]
        result[d] = round(item.get("taskTime", 0) or 0, 1)
    return result


def get_work_dates(from_date: str, to_date: str) -> list[str]:
    """返回日期范围内的工作日列表（排除周末）。"""
    start = date.fromisoformat(from_date)
    end = date.fromisoformat(to_date)
    result = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:  # 0-4 是周一到周五
            result.append(cur.isoformat())
        cur += timedelta(days=1)
    return result


def analyze_team(members: list[dict], from_date: str, to_date: str, work_days: int, std_hours_per_day: float = 8.0) -> dict:
    """分析一个团队的报工数据，返回统计摘要。"""
    std_total = work_days * std_hours_per_day
    team_total = 0
    full_count = 0
    overtime_total = 0
    pre_total = 0
    after_total = 0
    internal_total = 0
    doc_total = 0
    score_sum = 0
    score_count = 0
    member_stats = []

    work_dates = get_work_dates(from_date, to_date)

    for m in members:
        total = round(m.get("totalTaskTime", 0) or 0, 1)
        pre = round(m.get("preTaskTime", 0) or 0, 1)
        after = round(m.get("afterTaskTime", 0) or 0, 1)
        internal = round(m.get("internalTaskTime", 0) or 0, 1)
        overtime = round(m.get("overTaskTime", 0) or 0, 1)
        doc = m.get("docCount", 0) or 0
        score = m.get("operationStandardScore", 0) or 0

        team_total += total
        overtime_total += overtime
        pre_total += pre
        after_total += after
        internal_total += internal
        doc_total += doc
        if score > 0:
            score_sum += score
            score_count += 1
        if total >= std_total:
            full_count += 1

        # 获取每日工时
        daily = {}
        if m.get("userId"):
            daily = fetch_calendar(m["userId"], from_date, to_date)

        member_stats.append({
            "name": m.get("userName", ""),
            "userId": m.get("userId"),
            "city": m.get("workCity") or "",
            "total": total,
            "pre": pre,
            "after": after,
            "internal": internal,
            "overtime": overtime,
            "doc": doc,
            "score": score,
            "records": 0,  # summary 中没有记录数，可选填
            "daily": daily,
            "shortage": round(std_total - total, 1) if total < std_total else 0,
            "excess": round(total - std_total, 1) if total >= std_total else 0,
            "full": total >= std_total,
        })

    n = len(members)
    avg_hours = round(team_total / n, 2) if n > 0 else 0
    full_rate = round(full_count / n * 100, 1) if n > 0 else 0
    avg_score = round(score_sum / score_count, 1) if score_count > 0 else 0

    return {
        "memberCount": n,
        "totalHours": round(team_total, 1),
        "avgHours": avg_hours,
        "fullCount": full_count,
        "fullRate": full_rate,
        "overtimeHours": round(overtime_total, 1),
        "preHours": round(pre_total, 1),
        "afterHours": round(after_total, 1),
        "internalHours": round(internal_total, 1),
        "docCount": doc_total,
        "avgScore": avg_score,
        "members": sorted(member_stats, key=lambda x: -x["total"]),
        "stdHours": std_total,
        "workDates": work_dates,
    }


def color_daily(h: float, std: float) -> str:
    """根据单日工时返回背景颜色 style 片段。"""
    if h == 0:
        return "background:#f3f4f6;color:#9ca3af"
    elif h >= std:
        return "background:#bbf7d0;color:#065f46"
    elif h >= std * 0.6:
        return "background:#fef08a;color:#713f12"
    else:
        return "background:#fecaca;color:#7f1d1d"


def format_hours_badge(h: float, std: float) -> str:
    """返回工时标签 HTML。"""
    if h >= std:
        color = "#065f46"
        bg = "#d1fae5"
    else:
        color = "#991b1b"
        bg = "#fee2e2"
    return f'<span style="background:{bg};color:{color};padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600">{h}h</span>'


def format_rate_badge(rate: float) -> str:
    if rate >= 80:
        return f'<span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600">{rate}%</span>'
    else:
        return f'<span style="background:#fee2e2;color:#991b1b;padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600">{rate}%</span>'


def weekday_cn(d: str) -> str:
    wds = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return wds[date.fromisoformat(d).weekday()]


# ─── HTML 生成 ────────────────────────────────────────────────
def render_team_detail_table(team_name: str, stats: dict, color: str, std_per_day: float) -> str:
    work_dates = stats["workDates"]
    date_headers = "".join(
        f"<th style='text-align:center'>{d[5:]} ({weekday_cn(d)})</th>" for d in work_dates
    )
    rows = ""
    for m in stats["members"]:
        daily_cells = ""
        for d in work_dates:
            h = m["daily"].get(d, 0)
            style = color_daily(h, std_per_day)
            daily_cells += f"<td style='text-align:center;{style};font-weight:600;font-size:13px;padding:6px 4px'>{h}</td>"

        ot_cell = f"<td><span style='color:#ef4444;font-weight:600'>{m['overtime']}h</span></td>" if m["overtime"] > 0 else "<td>0.0h</td>"

        rows += f"""<tr>
          <td><b>{m['name']}</b>{' <small style="color:#6b7280">'+m['city']+'</small>' if m['city'] else ''}</td>
          <td>{format_hours_badge(m['total'], stats['stdHours'])}</td>
          {daily_cells}
          <td>{m['pre']}h</td><td>{m['after']}h</td><td>{m['internal']}h</td>
          {ot_cell}
        </tr>"""

    return f"""
<div class="sub-title" style="border-color:{color}">{team_name}</div>
<table style="margin-bottom:12px">
  <thead><tr>
    <th>姓名</th><th>总工时</th>{date_headers}
    <th>售前</th><th>售后</th><th>内部</th><th>加班</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>"""


def render_shortage_list(team_name: str, stats: dict, std_per_day: float) -> str:
    shortage_members = [m for m in stats["members"] if m["shortage"] > 0]
    if not shortage_members:
        return f"<p style='color:#065f46;font-size:13px;padding:8px'>✅ {team_name} 全员工时达标</p>"
    items = ""
    for m in shortage_members:
        items += f"""<div class="shortage-item">
          <b>{m['name']}</b> — 报工 {m['total']}h，缺口 <span style="color:#ef4444;font-weight:700">-{m['shortage']}h</span>
          <div class="shortage-detail">{m['city'] or '未知城市'}</div>
        </div>"""
    return f"<div class='sub-title' style='font-size:13px;margin:8px 0'>{team_name}（{len(shortage_members)}人不达标）</div>{items}"


def render_overview_cards(team_names: list[str], team_stats_list: list[dict], colors: list[str]) -> str:
    cards = ""
    for i, (name, stats) in enumerate(zip(team_names, team_stats_list)):
        color = colors[i % len(colors)]
        rank_class = ["rank-1", "rank-2", "rank-3", "rank-4"][min(i, 3)]
        cards += f"""
    <div class="card" style="border-color:{color}">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <span style="font-size:15px;font-weight:700;color:{color}">{name}</span>
        <span class="rank-badge {rank_class}">{i+1}</span>
      </div>
      <div class="metric" style="color:{color}">{stats['avgHours']}<small style="font-size:14px">h</small></div>
      <div class="metric-label">人均工时（共{stats['memberCount']}人）</div>
      <div style="margin-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12px">
        <div>总工时 <b>{stats['totalHours']}h</b></div>
        <div>满勤率 {format_rate_badge(stats['fullRate'])}</div>
        <div>加班 <b>{stats['overtimeHours']}h</b></div>
        <div>文档 <b>{stats['docCount']}</b> 篇</div>
      </div>
    </div>"""
    return f'<div class="team-card">{cards}</div>'


def render_summary_table(team_names: list[str], team_stats_list: list[dict]) -> str:
    rows = ""
    for name, s in zip(team_names, team_stats_list):
        avg_h = s["avgHours"]
        avg_badge = format_hours_badge(avg_h, s["stdHours"] / max(len(s["workDates"]), 1) * len(s["workDates"]))
        ot = f'<span style="color:#ef4444;font-weight:600">{s["overtimeHours"]}h</span>' if s["overtimeHours"] > 0 else f'{s["overtimeHours"]}h'
        rows += f"""<tr>
          <td><b>{name}</b></td>
          <td style="text-align:center">{s['memberCount']}</td>
          <td><b>{s['totalHours']}h</b></td>
          <td>{avg_badge}</td>
          <td style="text-align:center">{s['fullCount']}</td>
          <td>{format_rate_badge(s['fullRate'])}</td>
          <td>{s['preHours']}h</td><td>{s['afterHours']}h</td>
          <td>{s['internalHours']}h</td>
          <td>{ot}</td>
          <td style="text-align:center">{s['docCount']}</td>
          <td style="text-align:center">{s['avgScore']}</td>
        </tr>"""
    return f"""
<table><thead><tr>
  <th>团队</th><th>人数</th><th>总工时</th><th>人均工时</th>
  <th>满勤人数</th><th>满勤率</th><th>售前</th><th>售后</th>
  <th>内部</th><th>加班</th><th>文档</th><th>操作标准均分</th>
</tr></thead><tbody>{rows}</tbody></table>"""


def generate_html(
    title: str,
    period_str: str,
    std_hours_per_week: float,
    team_names: list[str],
    team_stats_list: list[dict],
    std_per_day: float = 8.0,
) -> str:
    colors = TEAM_COLORS[: len(team_names)]

    overview_cards = render_overview_cards(team_names, team_stats_list, colors)
    summary_table = render_summary_table(team_names, team_stats_list)

    detail_tables = ""
    for name, stats, color in zip(team_names, team_stats_list, colors):
        detail_tables += render_team_detail_table(name, stats, color, std_per_day)

    shortage_sections = ""
    for name, stats in zip(team_names, team_stats_list):
        shortage_sections += render_shortage_list(name, stats, std_per_day)

    work_days = len(team_stats_list[0]["workDates"]) if team_stats_list else 0
    std_total = work_days * std_per_day

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} {period_str}</title>
<style>
  * {{box-sizing:border-box;margin:0;padding:0;}}
  body {{font-family:'PingFang SC','Microsoft YaHei',sans-serif;background:#f0f4f8;color:#1f2937;}}
  .container {{max-width:1200px;margin:0 auto;padding:20px;}}
  .header {{background:linear-gradient(135deg,#1e3a5f 0%,#2563eb 100%);color:white;padding:32px;border-radius:16px;margin-bottom:24px;}}
  .header h1 {{font-size:24px;font-weight:700;margin-bottom:8px;}}
  .header p {{font-size:14px;opacity:0.85;}}
  .section {{background:white;border-radius:12px;padding:24px;margin-bottom:24px;box-shadow:0 2px 8px rgba(0,0,0,0.06);}}
  .section-title {{font-size:18px;font-weight:700;color:#1e3a5f;margin-bottom:18px;padding-bottom:10px;border-bottom:2px solid #e5e7eb;display:flex;align-items:center;gap:8px;}}
  .section-title .icon {{font-size:20px;}}
  table {{width:100%;border-collapse:collapse;font-size:13px;}}
  th {{background:#f8fafc;color:#374151;font-weight:600;padding:10px 12px;text-align:left;border-bottom:2px solid #e5e7eb;white-space:nowrap;}}
  td {{padding:8px 12px;border-bottom:1px solid #f3f4f6;}}
  tr:hover td {{background:#f8fafc;}}
  .team-card {{display:grid;grid-template-columns:repeat(2,1fr);gap:16px;margin-bottom:20px;}}
  @media(min-width:900px){{.team-card{{grid-template-columns:repeat({min(len(team_names), 4)},1fr);}}}}
  .card {{background:#f8fafc;border-radius:10px;padding:16px;border-left:4px solid;}}
  .metric {{font-size:28px;font-weight:800;margin:4px 0;}}
  .metric-label {{font-size:12px;color:#6b7280;}}
  .rank-badge {{display:inline-block;width:28px;height:28px;border-radius:50%;text-align:center;line-height:28px;font-weight:700;font-size:14px;}}
  .rank-1{{background:#fbbf24;color:white;}} .rank-2{{background:#9ca3af;color:white;}} .rank-3{{background:#b45309;color:white;}} .rank-4{{background:#6b7280;color:white;}}
  .shortage-item {{padding:8px 12px;background:#fff7ed;border-left:3px solid #f59e0b;margin:4px 0;border-radius:4px;font-size:13px;}}
  .shortage-detail {{font-size:12px;color:#6b7280;margin-top:4px;}}
  .sub-title {{font-size:15px;font-weight:600;color:#374151;margin:16px 0 10px;padding-left:8px;border-left:3px solid #3b82f6;}}
  .stat-badge {{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;}}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>🏢 {title} · 报工综合分析</h1>
  <p>统计周期：{period_str}（共{work_days}个工作日）&nbsp;&nbsp;|&nbsp;&nbsp;标准工时：{int(std_total)}h/人·周期</p>
  <p style="margin-top:6px;opacity:0.7;font-size:12px">生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>

<!-- 一、核心指标 -->
<div class="section">
  <div class="section-title"><span class="icon">📊</span> 一、团队核心指标对比</div>
  {overview_cards}
  {summary_table}
</div>

<!-- 二、成员工时明细 -->
<div class="section">
  <div class="section-title"><span class="icon">👤</span> 二、成员工时明细 & 每日工时</div>
  {detail_tables}
</div>

<!-- 三、报工不足 -->
<div class="section">
  <div class="section-title"><span class="icon">⚠️</span> 三、报工不足预警（< {int(std_total)}h）</div>
  {shortage_sections}
</div>

</div>
</body>
</html>"""


# ─── 主入口 ────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="生成 MES 报工统计 HTML 报告")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--team-ids", help="多团队逗号分隔，如 2,3,23,19")
    group.add_argument("--team-id", type=int, help="单团队 ID")

    parser.add_argument("--team-names", help="对应团队名称，逗号分隔，顺序与 team-ids 一致")
    parser.add_argument("--team-name", help="单团队名称")
    parser.add_argument("--from", dest="from_date", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--work-days", type=int, help="工作日天数，不传则自动从日期推算")
    parser.add_argument("--std-hours-per-day", type=float, default=8.0, help="每日标准工时，默认 8")
    parser.add_argument("--title", default="", help="报告标题（不含日期）")
    parser.add_argument("--output", required=True, help="输出 HTML 文件路径")

    args = parser.parse_args()

    # 整理团队列表
    if args.team_id:
        team_ids = [args.team_id]
        team_names = [args.team_name or f"团队{args.team_id}"]
    else:
        team_ids = [int(x.strip()) for x in args.team_ids.split(",")]
        if args.team_names:
            team_names = [x.strip() for x in args.team_names.split(",")]
        else:
            team_names = [f"团队{tid}" for tid in team_ids]

    # 工作日天数
    if args.work_days:
        work_days = args.work_days
    else:
        work_dates = get_work_dates(args.from_date, args.to_date)
        work_days = len(work_dates)

    std_per_day = args.std_hours_per_day
    std_total = work_days * std_per_day
    period_str = f"{args.from_date} — {args.to_date}"
    title = args.title or ("、".join(team_names))

    print(f"[INFO] 开始拉取数据：{team_names}，周期 {period_str}，标准工时 {std_total}h")

    # 拉取各团队数据
    team_stats_list = []
    for i, (tid, tname) in enumerate(zip(team_ids, team_names)):
        print(f"[INFO] 拉取 {tname}（team-id={tid}）...")
        members = fetch_summary(tid, args.from_date, args.to_date)
        print(f"       共 {len(members)} 名成员，获取每日工时中...")
        stats = analyze_team(members, args.from_date, args.to_date, work_days, std_per_day)
        team_stats_list.append(stats)
        print(f"       完成：总工时 {stats['totalHours']}h，人均 {stats['avgHours']}h，满勤率 {stats['fullRate']}%")

    # 按人均工时排序（降序）
    combined = sorted(zip(team_names, team_stats_list), key=lambda x: -x[1]["avgHours"])
    team_names = [x[0] for x in combined]
    team_stats_list = [x[1] for x in combined]

    # 生成 HTML
    print("[INFO] 生成 HTML 报告...")
    html = generate_html(title, period_str, std_total, team_names, team_stats_list, std_per_day)

    output_path = os.path.expanduser(args.output)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[OK] 报告已生成：{output_path}")


if __name__ == "__main__":
    main()
