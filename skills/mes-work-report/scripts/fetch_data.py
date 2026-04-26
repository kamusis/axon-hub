#!/usr/bin/env python3
"""
MES 报工数据拉取脚本 — 纯数据层，输出 JSON，不生成 HTML。
用法：
  python3 fetch_data.py \
    --team-ids 2,3,23,19 \
    --team-names "东西大区1部,东西大区2部,东西大区4部,东西大区5部" \
    --from 2026-04-21 \
    --to 2026-04-23 \
    --output /path/to/data.json
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import date, timedelta


def run_mes(cmd: list[str]) -> dict | list:
    """执行 mes 命令并返回 JSON 结果（dict 或 list）。"""
    full_cmd = ["mes", "-o", "json"] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"[ERROR] mes 命令输出无法解析: {result.stdout[:200]}", file=sys.stderr)
        return []


def get_work_dates(from_date: str, to_date: str) -> list[str]:
    """返回日期范围内的工作日列表（排除周末）。"""
    start = date.fromisoformat(from_date)
    end = date.fromisoformat(to_date)
    result = []
    cur = start
    while cur <= end:
        if cur.weekday() < 5:
            result.append(cur.isoformat())
        cur += timedelta(days=1)
    return result


def fetch_team_members(team_id: int) -> list[dict]:
    """获取指定团队的成员列表（userId + employeeName）。"""
    data = run_mes(["util", "list-members", "--team-id", str(team_id)])
    return data if isinstance(data, list) else []


def fetch_summary(team_id: int, from_date: str, to_date: str) -> list[dict]:
    """获取指定团队在时间范围内的报工 summary（含成员明细）。"""
    data = run_mes(["statistics", "summary", "--team-id", str(team_id), "--from", from_date, "--to", to_date])
    if isinstance(data, dict):
        return data.get("operateCallBackObj", [])
    return []


def fetch_list_by_user(user_id: int, from_date: str, to_date: str) -> list[dict]:
    """通过 statistics list 获取某用户的报工记录列表（用于聚合每日工时和记录数）。"""
    all_records = []
    page = 1
    while True:
        data = run_mes([
            "statistics", "list",
            "--executor-id", str(user_id),
            "--from", from_date,
            "--to", to_date,
            "--page", str(page),
            "--page-size", "100",
        ])
        items = _extract_list(data)
        has_next = False
        if isinstance(data, dict):
            has_next = data.get("hasNextPage", False)
        if not items:
            break
        all_records.extend(items)
        if not has_next or len(items) < 100:
            break
        page += 1
    return all_records


def fetch_articles(team_id: int, from_date: str, to_date: str) -> list[dict]:
    """获取指定团队的文档列表。"""
    start_time = f"{from_date} 00:00:00"
    end_time = f"{to_date} 23:59:59"
    all_articles = []
    page = 1
    while True:
        data = run_mes([
            "article", "list",
            "--team-id", str(team_id),
            "--start-time", start_time,
            "--end-time", end_time,
            "--mode", "manage",
            "--page", str(page),
            "--page-size", "50",
        ])
        if isinstance(data, dict):
            items = data.get("list", data.get("operateCallBackObj", data.get("data", [])))
        elif isinstance(data, list):
            items = data
        else:
            break
        if not items:
            break
        all_articles.extend(items)
        if len(items) < 50:
            break
        page += 1
    return all_articles


def fetch_scores(team_id: int, month: str) -> list[dict]:
    """获取指定团队的报工质量评分。"""
    all_scores = []
    page = 1
    while True:
        data = run_mes([
            "dashboard", "score", "list",
            "--team-id", str(team_id),
            "--month", month,
            "--page", str(page),
            "--page-size", "50",
        ])
        if isinstance(data, dict):
            page_data = data.get("operateCallBackObj", {})
            if isinstance(page_data, dict):
                items = page_data.get("list", [])
                has_next = page_data.get("hasNextPage", False)
            elif isinstance(page_data, list):
                items = page_data
                has_next = False
            else:
                items = []
                has_next = False
        elif isinstance(data, list):
            items = data
            has_next = False
        else:
            break
        all_scores.extend(items)
        if not has_next or not items:
            break
        page += 1
    return all_scores


def _extract_list(data) -> list[dict]:
    """从各种 mes 返回格式中提取列表。"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # 常见结构：{list: [...]} / {operateCallBackObj: {list: [...]}} / {operateCallBackObj: [...]} / {data: [...]}
        for key in ("list", "operateCallBackObj", "data"):
            val = data.get(key)
            if isinstance(val, list):
                return val
            if isinstance(val, dict):
                inner = val.get("list")
                if isinstance(inner, list):
                    return inner
    return []


def fetch_service_requests(person_ids: list[int], from_date: str, to_date: str) -> list[dict]:
    """获取指定人员在时间范围内的服务请求列表。person_ids 为空时拉全量。"""
    start_time = f"{from_date} 00:00:00"
    end_time = f"{to_date} 23:59:59"
    all_items = []
    # 按人员分批拉取（避免全量查询）
    if person_ids:
        for pid in person_ids:
            data = run_mes([
                "service", "request", "list",
                "--person-id", str(pid),
                "--start-time", start_time,
                "--end-time", end_time,
                "--page-size", "100",
            ])
            all_items.extend(_extract_list(data))
    else:
        data = run_mes([
            "service", "request", "list",
            "--start-time", start_time,
            "--end-time", end_time,
            "--page-size", "100",
        ])
        all_items.extend(_extract_list(data))
    return all_items


def fetch_service_stats() -> dict:
    """获取全局服务统计卡片（待处理咨询/工单/计划/未关闭工单数）。"""
    data = run_mes(["dashboard", "service"])
    return data if isinstance(data, dict) else {}


def fetch_task_table(from_date: str, to_date: str) -> list[dict]:
    """获取部门工时分布表。"""
    data = run_mes([
        "dashboard", "task-table",
        "--from", from_date,
        "--to", to_date,
    ])
    if isinstance(data, dict):
        return data.get("operateCallBackObj", data.get("data", []))
    return data if isinstance(data, list) else []


def weekday_cn(d: str) -> str:
    wds = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return wds[date.fromisoformat(d).weekday()]


def main():
    parser = argparse.ArgumentParser(description="拉取 MES 报工数据并输出 JSON")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--team-ids", help="多团队逗号分隔，如 2,3,23,19")
    group.add_argument("--team-id", type=int, help="单团队 ID")

    parser.add_argument("--team-names", help="对应团队名称，逗号分隔")
    parser.add_argument("--team-name", help="单团队名称")
    parser.add_argument("--from", dest="from_date", required=True, help="开始日期 YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="结束日期 YYYY-MM-DD")
    parser.add_argument("--std-hours-per-day", type=float, default=8.0, help="每日标准工时，默认 8")
    parser.add_argument("--output", required=True, help="输出 JSON 文件路径")
    parser.add_argument("--fetch-extra", action="store_true", help="是否拉取额外数据（文档、质量评分、服务请求）")

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

    work_dates = get_work_dates(args.from_date, args.to_date)
    work_days = len(work_dates)
    std_per_day = args.std_hours_per_day
    std_total = work_days * std_per_day
    month_str = args.from_date[:7]  # YYYY-MM

    print(f"[INFO] 拉取数据：{team_names}，周期 {args.from_date} ~ {args.to_date}，{work_days} 个工作日")

    # ─── 主数据：各团队 summary + 成员每日工时 ───
    teams_data = []
    all_team_member_ids = set()  # 收集所有团队成员 userId，用于服务请求筛选

    for tid, tname in zip(team_ids, team_names):
        print(f"[INFO] 拉取 {tname}（team-id={tid}）成员列表...")
        team_member_list = fetch_team_members(tid)
        team_member_ids = {m["userId"] for m in team_member_list if m.get("userId")}
        all_team_member_ids.update(team_member_ids)
        print(f"       {len(team_member_list)} 名成员")

        print(f"[INFO] 拉取 {tname} summary...")
        members = fetch_summary(tid, args.from_date, args.to_date)
        print(f"       {len(members)} 名成员有报工记录，获取每日工时...")

        # 已报工成员 userId 集合
        reported_user_ids = {m.get("userId") for m in members if m.get("userId")}

        # 识别未报工人员
        unreported_members = [
            {"name": m.get("employeeName", ""), "userId": m.get("userId")}
            for m in team_member_list
            if m.get("userId") and m.get("userId") not in reported_user_ids
        ]

        member_stats = []
        team_total = 0
        team_full_count = 0
        team_overtime = 0
        team_pre = 0
        team_after = 0
        team_internal = 0
        team_doc_count = 0
        team_score_sum = 0
        team_score_count = 0

        for m in members:
            total = round(m.get("totalTaskTime", 0) or 0, 1)
            pre = round(m.get("preTaskTime", 0) or 0, 1)
            after = round(m.get("afterTaskTime", 0) or 0, 1)
            internal = round(m.get("internalTaskTime", 0) or 0, 1)
            overtime = round(m.get("overTaskTime", 0) or 0, 1)
            doc = m.get("docCount", 0) or 0
            score = m.get("operationStandardScore", 0) or 0

            team_total += total
            team_overtime += overtime
            team_pre += pre
            team_after += after
            team_internal += internal
            team_doc_count += doc
            if score > 0:
                team_score_sum += score
                team_score_count += 1
            if total >= std_total:
                team_full_count += 1

            # 通过 statistics list 按日聚合（修复 calendar 无法查他人数据的问题）
            daily = {}
            record_count = 0
            if m.get("userId"):
                records = fetch_list_by_user(m["userId"], args.from_date, args.to_date)
                record_count = len(records)
                for r in records:
                    # 日期优先从 start 字段取，兼容 taskDate
                    raw_date = r.get("taskDate") or r.get("start") or ""
                    d = raw_date[:10]
                    h = round(r.get("taskTime", 0) or 0, 1)
                    if d:
                        daily[d] = daily.get(d, 0) + h

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
                "recordCount": record_count,
                "daily": daily,
                "shortage": round(std_total - total, 1) if total < std_total else 0,
                "full": total >= std_total,
            })

        n = len(members)
        teams_data.append({
            "teamId": tid,
            "teamName": tname,
            "memberCount": len(team_member_list),
            "reportedMemberCount": n,
            "totalHours": round(team_total, 1),
            "avgHours": round(team_total / n, 2) if n > 0 else 0,
            "fullCount": team_full_count,
            "fullRate": round(team_full_count / n * 100, 1) if n > 0 else 0,
            "overtimeHours": round(team_overtime, 1),
            "preHours": round(team_pre, 1),
            "afterHours": round(team_after, 1),
            "internalHours": round(team_internal, 1),
            "docCount": team_doc_count,
            "avgScore": round(team_score_sum / team_score_count, 1) if team_score_count > 0 else 0,
            "members": sorted(member_stats, key=lambda x: -x["total"]),
            "unreportedMembers": sorted(unreported_members, key=lambda x: x["name"]),
        })
        print(f"       完成：总工时 {team_total}h，人均 {team_total/max(n,1):.1f}h")

    output = {
        "meta": {
            "fromDate": args.from_date,
            "toDate": args.to_date,
            "workDays": work_days,
            "workDates": work_dates,
            "stdHoursPerDay": std_per_day,
            "stdHoursTotal": std_total,
            "teamNames": team_names,
            "generatedAt": f"{args.from_date} {args.to_date}",
        },
        "teams": teams_data,
    }

    # ─── 额外数据：文档、质量评分、服务请求、服务统计、工时分布表 ───
    if args.fetch_extra:
        print("[INFO] 拉取额外数据...")

        # 文档统计
        articles_all = []
        for tid, tname in zip(team_ids, team_names):
            print(f"       文档: {tname}...")
            arts = fetch_articles(tid, args.from_date, args.to_date)
            for a in arts:
                articles_all.append({
                    "teamName": tname,
                    "teamId": tid,
                    "title": a.get("title", ""),
                    "author": a.get("employeeName", "") or a.get("createdByName", ""),
                    "authorId": a.get("createdBy"),
                    "createTime": a.get("createdTime", "") or a.get("createTime", ""),
                })
        output["articles"] = articles_all

        # 质量评分
        scores_all = []
        for tid, tname in zip(team_ids, team_names):
            print(f"       质量评分: {tname}...")
            scores = fetch_scores(tid, month_str)
            for s in scores:
                scores_all.append({
                    "teamName": tname,
                    "teamId": tid,
                    **s,
                })
        output["scores"] = scores_all

        # 服务请求（按团队成员范围筛选）
        print(f"       服务请求（筛选 {len(all_team_member_ids)} 名成员）...")
        services = fetch_service_requests(list(all_team_member_ids), args.from_date, args.to_date)
        output["serviceRequests"] = services

        # 全局服务统计
        print(f"       服务统计卡片...")
        svc_stats = fetch_service_stats()
        output["serviceStats"] = svc_stats

        # 部门工时分布表
        print(f"       工时分布表...")
        task_table = fetch_task_table(args.from_date, args.to_date)
        # 只保留目标团队的数据
        target_team_ids_set = set(team_ids)
        output["taskTable"] = [r for r in task_table if r.get("teamId") in target_team_ids_set]

    # 写出 JSON
    output_path = os.path.expanduser(args.output)
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] 数据已输出：{output_path}")


if __name__ == "__main__":
    main()
