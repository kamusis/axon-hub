#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报销发票数据验证脚本

验证 invoices.json 的数据完整性和合理性，提前发现潜在问题。

用法：
  python reimbursement-validate-invoices.py invoices.json
  
输出示例：
  ✓ 验证通过：5张发票，总金额 ¥2,109.20
  ⚠️ 警告：第2张发票金额较小 (¥87.00)，请确认
  ✗ 错误：第3张发票缺少发票号码
"""

import sys
import json
import re
from pathlib import Path

# Windows 编码修复：确保 stdout/stderr 使用 UTF-8
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
    except Exception:
        pass  # 如果失败，静默忽略，继续执行


def validate_invoice(inv, idx):
    """
    验证单张发票的数据
    
    Returns:
        tuple: (errors_list, warnings_list)
    """
    errors = []
    warnings = []
    
    # === 必填字段检查 ===
    if not inv.get('fapiaohao') or inv['fapiaohao'].strip() == '':
        errors.append(f"第{idx}张：缺少发票号码")
    
    if not inv.get('bxje') or inv['bxje'] <= 0:
        errors.append(f"第{idx}张：金额无效 ({inv.get('bxje', '空')})")
    
    if not inv.get('qsrq'):
        errors.append(f"第{idx}张：缺少起始日期")
    
    if not inv.get('jsrq'):
        errors.append(f"第{idx}张：缺少结束日期")
    
    if not inv.get('bxlx'):
        errors.append(f"第{idx}张：缺少报销类型")
    
    if not inv.get('fylx'):
        errors.append(f"第{idx}张：缺少费用类型")
    
    if not inv.get('fysm'):
        errors.append(f"第{idx}张：缺少费用说明")
    
    # === 格式验证 ===
    if inv.get('fapiaohao'):
        # 发票号应为18-20位数字
        if not re.match(r'^\d{18,20}$', inv['fapiaohao']):
            warnings.append(f"第{idx}张：发票号格式异常 ({inv['fapiaohao']})")
    
    # 日期格式应为 YYYY-MM-DD
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if inv.get('qsrq') and not re.match(date_pattern, inv['qsrq']):
        warnings.append(f"第{idx}张：起始日期格式错误 ({inv['qsrq']})")
    
    if inv.get('jsrq') and not re.match(date_pattern, inv['jsrq']):
        warnings.append(f"第{idx}张：结束日期格式错误 ({inv['jsrq']})")
    
    # === 合理性检查 ===
    amount = inv.get('bxje', 0)
    
    # 金额过大警告
    if amount > 10000:
        warnings.append(f"第{idx}张：金额异常大 (¥{amount:,.2f})，请确认")
    
    # 金额过小警告（可能是提取失败）
    if 0 < amount < 10:
        warnings.append(f"第{idx}张：金额异常小 (¥{amount:.2f})，可能是提取失败")
    
    # 费用类型与金额匹配检查
    fylx = inv.get('fylx', '')
    if '机票' in fylx and amount < 500:
        warnings.append(f"第{idx}张：机票金额偏低 (¥{amount:.2f})")
    
    if '住宿' in fylx and amount < 100:
        warnings.append(f"第{idx}张：住宿金额偏低 (¥{amount:.2f})")
    
    if '市内交通' in fylx and amount > 500:
        warnings.append(f"第{idx}张：市内交通费偏高 (¥{amount:.2f})")
    
    # 报销类型与费用类型匹配
    bxlx = inv.get('bxlx', '')
    if bxlx == '日常费用' and '差旅费' in fylx:
        warnings.append(f"第{idx}张：日常费用包含差旅费，建议改为销售费用")
    
    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("用法：python reimbursement-validate-invoices.py <invoices.json文件路径>")
        print("\n示例：")
        print("  python reimbursement-validate-invoices.py invoices.json")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f" 错误：文件不存在：{input_file}")
        sys.exit(1)
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            invoices = json.load(f)
    except json.JSONDecodeError as e:
        print(f"✗ 错误：JSON 格式错误：{e}")
        sys.exit(1)
    
    if not isinstance(invoices, list):
        print("✗ 错误：JSON 根元素应为数组")
        sys.exit(1)
    
    if len(invoices) == 0:
        print("⚠️ 警告：发票列表为空")
        sys.exit(0)
    
    # 验证所有发票
    all_errors = []
    all_warnings = []
    total_amount = 0
    
    for idx, inv in enumerate(invoices, 1):
        errors, warnings = validate_invoice(inv, idx)
        all_errors.extend(errors)
        all_warnings.extend(warnings)
        total_amount += inv.get('bxje', 0)
    
    # 输出结果
    print(f"\n{'='*60}")
    print(f"📊 发票验证报告")
    print(f"{'='*60}")
    print(f"文件：{input_file}")
    print(f"发票数量：{len(invoices)} 张")
    print(f"合计金额：¥{total_amount:,.2f}")
    print()
    
    if all_errors:
        print(f"✗ 发现 {len(all_errors)} 个错误：")
        for err in all_errors:
            print(f"  • {err}")
        print()
    
    if all_warnings:
        print(f"️ 发现 {len(all_warnings)} 个警告：")
        for warn in all_warnings:
            print(f"  • {warn}")
        print()
    
    if not all_errors and not all_warnings:
        print(f"✅ 验证通过！所有发票数据完整且合理。")
    elif not all_errors:
        print(f"✅ 无致命错误，但有 {len(all_warnings)} 个警告需要确认。")
    else:
        print(f"❌ 存在 {len(all_errors)} 个错误，请先修复后再导入。")
    
    print(f"{'='*60}\n")
    
    # 返回退出码
    if all_errors:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
