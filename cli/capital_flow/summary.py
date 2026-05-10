# -*- coding: utf-8 -*-
"""沪深港通资金流总览命令"""

import typer

from cli.capital_flow import cf_app
from cli.helpers import print_banner, _fmt_amount


def print_capital_flow_summary(result: dict):
    """打印沪深港通资金流总览"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get('data', {})
    direction = data.get('direction', '')
    summary = data.get('summary', {})

    print(f"  📊 {direction}资金流总览")
    print("  " + "-" * 60)
    for key, value in summary.items():
        print(f"    {key}: {value}")
    print()

    items = data.get('items', [])
    if not items:
        print("  ℹ️  暂无明细数据")
        return

    # 动态列宽
    print(f"  {'板块':<12}{'成交净买额':<16}{'资金净流入':<16}{'当日资金余额':<16}")
    print("  " + "-" * 60)
    for item in items:
        name = item.get('板块', 'N/A')
        net_buy = _fmt_amount(item.get('成交净买额'))
        net_flow = _fmt_amount(item.get('资金净流入'))
        balance = _fmt_amount(item.get('当日资金余额'))
        print(f"  {name:<12}{net_buy:<16}{net_flow:<16}{balance:<16}")
    print()


@cf_app.command("summary")
def summary():
    """沪深港通资金流总览（返回所有方向数据）"""
    from fund_tools import get_capital_flow_summary

    print_banner()
    print("💰 沪深港通资金流总览")
    print()

    result = get_capital_flow_summary()
    print_capital_flow_summary(result)
