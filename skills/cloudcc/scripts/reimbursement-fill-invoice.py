#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
发票数据填充脚本 — 支持新建、追加、汇总三种模式

用法：
  # 新建模式（默认）
  python reimbursement-fill-invoice.py <模板文件> --from-file <JSON文件路径>
  python reimbursement-fill-invoice.py <模板文件> '[{"qsrq":"2024-05-27","bxje":111.00}]'

  # 追加模式
  python reimbursement-fill-invoice.py <模板文件> --from-file <JSON> --append

  # 汇总模式（对已有文件生成汇总，不修改文件）
  python reimbursement-fill-invoice.py <已填充文件> --summary

  # 输出到指定路径
  python reimbursement-fill-invoice.py <模板> --from-file data.json --output result.xlsx
"""

import sys
import json
import os
from pathlib import Path

# Windows 编码修复：确保 stdout/stderr 使用 UTF-8
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except Exception:
        pass  # 如果失败，静默忽略，继续执行


def find_first_empty_row(ws, data_start=7, max_check=506):
    """检测数据区第一个空行"""
    for row in range(data_start, max_check + 1):
        is_empty = True
        for col in range(1, 13):
            if ws.cell(row=row, column=col).value is not None:
                is_empty = False
                break
        if is_empty:
            return row
    return None


def get_api_col_map(ws, max_col=20):
    """从第2行读取API名称，返回 {api_name: col} 和 {col: api_name}"""
    api_to_col = {}
    col_to_api = {}
    for col in range(1, max_col + 1):
        api_name = ws.cell(row=2, column=col).value
        if api_name:
            api_to_col[api_name] = col
            col_to_api[col] = api_name
        else:
            break
    return api_to_col, col_to_api


def fill_invoice_to_template(template_path, invoice_data_list,
                            output_path=None, append=False):
    """
    将发票数据填充到模板，完成后打印汇总。

    Returns:
        (output_path, summary_dict)
        summary_dict: {
            "count": 有效票数,
            "skipped": 跳过数,
            "total": 合计金额,
            "details": [{"row":行号,"fapiaohao":"...","bxje":金额,...}, ...]
        }
    """
    try:
        import openpyxl
    except ImportError:
        print("错误：需要安装 openpyxl 库")
        print("请运行：pip install openpyxl")
        sys.exit(1)

    if not os.path.exists(template_path):
        print(f"错误：模板文件不存在：{template_path}")
        sys.exit(1)

    wb = openpyxl.load_workbook(template_path)
    ws = wb['批量导入']
    api_to_col, col_to_api = get_api_col_map(ws)

    # 获取字段的列的索引
    def col_of(api):
        return api_to_col.get(api)

    # 确定起始行
    if append:
        start_row = find_first_empty_row(ws)
        if start_row is None:
            print("错误：数据区已满（506行），无法追加")
            sys.exit(1)
        print(f"追加模式：从第{start_row}行开始填充")
    else:
        start_row = 7
        print("新建模式：从第7行开始填充（清空第7行起数据区）")
        # 清空数据区
        for row in range(7, 507):
            for col in range(1, 13):
                ws.cell(row=row, column=col).value = None

    # 字段映射（API名称 → 数据键名）
    field_mapping = [
        ('qsrq', 'qsrq'),
        ('jsrq', 'jsrq'),
        ('bxlx', 'bxlx'),
        ('fylx', 'fylx'),
        ('fysm', 'fysm'),
        ('bxje', 'bxje'),
        ('fapiaohao', 'fapiaohao'),
        ('xmmc', 'xmmc'),
        ('xshdbh', 'xshdbh'),
        ('bgd', 'bgd'),
        ('ccsqv1', 'ccsqv1'),
        ('wpgzsq', 'wpgzsq'),
    ]

    # 填充数据
    details = []
    for idx, invoice_data in enumerate(invoice_data_list):
        row = start_row + idx
        if row > 506:
            print(f"警告：数据超出500行限制，已截断（填充 {idx} 条）")
            break

        row_data = {"row": row}
        for api_name, data_key in field_mapping:
            if data_key in invoice_data and api_name in api_to_col:
                col = api_to_col[api_name]
                value = invoice_data[data_key]
                if value is not None and value != "":
                    ws.cell(row=row, column=col, value=value)
                    row_data[data_key] = value
        details.append(row_data)

    # 保存文件
    if output_path is None:
        base_name = os.path.splitext(template_path)[0]
        output_path = f"{base_name}_已填充.xlsx"

    wb.save(output_path)

    # 计算汇总
    total = sum(d.get('bxje', 0) or 0 for d in details)
    count = len(details)

    # 打印内部汇总
    print(f"\n{'='*50}")
    print(f"✅ 填充完成")
    print(f"{'='*50}")
    print(f"输出文件：{output_path}")
    print(f"填充范围：第{start_row}行 至 第{start_row + count - 1}行")
    print(f"有效票据：{count} 张")
    print(f"合计金额：¥{total:,.2f}")
    print()
    print("明细：")
    print(f"  {'#':<4} {'发票号':<14} {'金额':>14}  {'费用类型':<20}  来源/说明")
    print(f"  {'-'*70}")
    for d in details:
        r = d.get('row', '?')
        fh = d.get('fapiaohao', '') or '-'
        je = d.get('bxje', 0) or 0
        fl = d.get('fylx', '') or '-'
        sm = (d.get('fysm', '') or '')[:20]
        print(f"  {r:<4} {fh:<14} {je:>14,.2f}  {fl:<20}  {sm}")
    print(f"{'='*50}")

    summary = {"count": count, "total": total, "details": details, "output": output_path}
    return output_path, summary


def print_file_summary(file_path):
    """
    读取已有填充文件，打印汇总信息（不修改文件）。
    用于 --summary 模式。
    """
    try:
        import openpyxl
    except ImportError:
        print("错误：需要安装 openpyxl 库")
        sys.exit(1)

    if not os.path.exists(file_path):
        print(f"错误：文件不存在：{file_path}")
        sys.exit(1)

    wb = openpyxl.load_workbook(file_path, data_only=True)
    ws = wb['批量导入']
    api_to_col, col_to_api = get_api_col_map(ws)

    col_fapiaohao = api_to_col.get('fapiaohao')
    col_bxje       = api_to_col.get('bxje')
    col_fylx       = api_to_col.get('fylx')
    col_fysm       = api_to_col.get('fysm')
    col_qsrq       = api_to_col.get('qsrq')

    details = []
    total = 0.0
    skipped = 0

    for row in range(7, 507):
        bxje = ws.cell(row=row, column=col_bxje).value if col_bxje else None
        if bxje is None:
            # 检查该行是否完全为空
            has_any = any(ws.cell(row=row, column=c).value for c in range(1, 13))
            if not has_any:
                break  # 到达空行，停止
            skipped += 1
            continue

        fh  = ws.cell(row=row, column=col_fapiaohao).value if col_fapiaohao else ''
        fylx = ws.cell(row=row, column=col_fylx).value if col_fylx else ''
        fysm = ws.cell(row=row, column=col_fysm).value if col_fysm else ''
        qsrq = ws.cell(row=row, column=col_qsrq).value if col_qsrq else ''

        try:
            amount = float(bxje)
        except (TypeError, ValueError):
            amount = 0.0

        total += amount
        details.append({
            "row": row,
            "fapiaohao": fh,
            "bxje": amount,
            "fylx": fylx,
            "fysm": fysm,
            "qsrq": str(qsrq)[:10] if qsrq else '',
        })

    # 打印汇总
    print()
    print(f"📊 文件汇总：{os.path.basename(file_path)}")
    print(f"{'='*60}")
    print(f"  有效票据：{len(details)} 张")
    if skipped > 0:
        print(f"  空行/跳过：{skipped} 行")
    print(f"  合计金额：¥{total:,.2f}")
    print()
    if details:
        print(f"  {'#':<4} {'发票号':<16} {'金额':>14}  {'费用类型':<18}  日期")
        print(f"  {'-'*72}")
        for d in details:
            print(f"  {d['row']:<4} {str(d['fapiaohao']):<16} {d['bxje']:>14,.2f}  {str(d['fylx']):<18}  {d['qsrq']}")
    else:
        print("  （无有效数据）")
    print(f"{'='*60}")
    print()

    return {"count": len(details), "total": total, "details": details}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='发票数据填充到报销单模板 + 文件汇总工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 从 JSON 文件新建填充
  python fill_invoice.py 模板.xlsx --from-file data.json

  # 追加模式
  python fill_invoice.py 已填充.xlsx --from-file data.json --append

  # 对已填充文件生成汇总（不修改文件）
  python fill_invoice.py 已填充.xlsx --summary

  # 指定输出路径
  python fill_invoice.py 模板.xlsx --from-file data.json --output 结果.xlsx
        """
    )
    parser.add_argument('file', help='模板文件 或 已填充的Excel文件')
    parser.add_argument('data_json', nargs='?', help='发票数据JSON字符串（与--from-file互斥）')
    parser.add_argument('--from-file', '-f', help='从JSON文件读取发票数据')
    parser.add_argument('--append', '-a', action='store_true',
                        help='追加模式（不覆盖已有数据，从第一个空行开始）')
    parser.add_argument('--output', '-o', help='输出文件路径（可选）')
    parser.add_argument('--summary', '-s', action='store_true',
                        help='仅汇总模式：读取已有文件并打印汇总，不修改文件')

    args = parser.parse_args()

    # 汇总模式：只读，不填充
    if args.summary:
        print_file_summary(args.file)
        return

    # 填充模式：需要发票数据
    if not args.from_file and not args.data_json:
        parser.print_help()
        print("\n错误：填充模式需要发票数据。请使用 --from-file 或传入 JSON 字符串。")
        print("       如果只想查看已有文件的汇总，请加 --summary 参数。")
        sys.exit(1)

    # 读取发票数据
    if args.from_file:
        with open(args.from_file, 'r', encoding='utf-8') as f:
            invoice_data_list = json.load(f)
    else:
        try:
            invoice_data_list = json.loads(args.data_json)
        except json.JSONDecodeError:
            print("错误：无法解析JSON数据")
            sys.exit(1)

    # 确保是列表
    if isinstance(invoice_data_list, dict):
        invoice_data_list = [invoice_data_list]

    if len(invoice_data_list) == 0:
        print("错误：发票数据为空")
        sys.exit(1)

    _, summary = fill_invoice_to_template(
        args.file,
        invoice_data_list,
        output_path=args.output,
        append=args.append
    )

    # 同时输出 JSON 格式汇总到 stderr（供程序化读取）
    print(json.dumps({"summary": summary}, ensure_ascii=False, default=str),
          file=sys.stderr)


if __name__ == '__main__':
    main()
