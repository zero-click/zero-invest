# -*- coding: utf-8 -*-
"""沪深港通资金流历史趋势命令"""

import typer

from . import cf_app
from ..helpers import print_banner, _fmt_amount


def print_capital_flow_history(result: dict):
    """打印沪深港通资金流历史趋势"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    direction = result.get('direction', '')
    days = result.get('days', 0)
    records = result.get('data', [])
    summary = result.get('summary', {})

    print(f"  📈 {direction}近{days}日资金流趋势")
    print("  " + "-" * 70)

    if not records:
        print("  ℹ️  暂无历史数据")
        return

    print(f"  {'日期':<14}{'成交净买额(亿)':<16}{'买入成交额(亿)':<16}{'卖出成交额(亿)':<16}")
    print("  " + "-" * 62)
    # 倒序显示（最新在前），最多显示最近 20 条
    for rec in reversed(records[-20:]):
        date = rec.get('date', 'N/A')
        net_buy = _fmt_amount(rec.get('net_buy'))
        buy_amount = _fmt_amount(rec.get('buy_amount'))
        sell_amount = _fmt_amount(rec.get('sell_amount'))
        print(f"  {date:<14}{net_buy:<16}{buy_amount:<16}{sell_amount:<16}")

    if len(records) > 20:
        print(f"  ... 共 {len(records)} 条记录，仅显示最近 20 条")
    print()

    if summary:
        print("  📊 趋势分析")
        print("  " + "-" * 40)
        if summary.get('trend'):
            print(f"    整体趋势: {summary['trend']}")
        if summary.get('cumulative_net_buy') is not None:
            print(f"    累计净买入: {_fmt_amount(summary['cumulative_net_buy'])}")
        if summary.get('daily_avg_net_buy') is not None:
            print(f"    日均净买入: {_fmt_amount(summary['daily_avg_net_buy'])}")
        if summary.get('max_daily_inflow'):
            inflow = summary['max_daily_inflow']
            print(f"    最大单日流入: {_fmt_amount(inflow.get('value'))} ({inflow.get('date', '')})")
        if summary.get('max_daily_outflow'):
            outflow = summary['max_daily_outflow']
            print(f"    最大单日流出: {_fmt_amount(outflow.get('value'))} ({outflow.get('date', '')})")
        print()


@cf_app.command("history")
def history(
    direction: str = typer.Option(
        "北向", "--direction", "-d",
        help="资金方向（默认: 北向）",
    ),
    days: int = typer.Option(30, "--days", "-n", help="查询天数（默认: 30，最大 365）"),
):
    """沪深港通资金流历史趋势"""
    from fund_tools import get_capital_flow_history

    _valid_directions = ["北向", "沪股通", "深股通", "南向", "港股通沪", "港股通深"]
    if direction not in _valid_directions:
        print(f"  ❌ 无效的资金方向: {direction}，可选: {', '.join(_valid_directions)}")
        raise typer.Exit(code=1)

    print_banner()
    print(f"📈 沪深港通资金流历史: {direction} 近{days}日")
    print()

    result = get_capital_flow_history(direction=direction, days=days)
    print_capital_flow_history(result)
