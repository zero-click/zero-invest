# -*- coding: utf-8 -*-
"""沪深港通资金流历史趋势命令"""

import typer

from cli.capital_flow import cf_app
from cli.helpers import print_banner, _fmt_amount


def print_capital_flow_history(result: dict):
    """打印沪深港通资金流历史趋势"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get('data', {})
    direction = data.get('direction', '')
    days = data.get('days', 0)
    records = data.get('records', [])
    trend = data.get('trend_analysis', {})

    print(f"  📈 {direction}近{days}日资金流趋势")
    print("  " + "-" * 70)

    if not records:
        print("  ℹ️  暂无历史数据")
        return

    print(f"  {'日期':<14}{'成交净买额(亿)':<16}{'资金净流入(亿)':<16}")
    print("  " + "-" * 46)
    # 倒序显示（最新在前），最多显示最近 20 条
    for rec in reversed(records[-20:]):
        date = rec.get('date', 'N/A')
        net_buy = _fmt_amount(rec.get('net_buy_amount'))
        net_flow = _fmt_amount(rec.get('net_flow_amount'))
        print(f"  {date:<14}{net_buy:<16}{net_flow:<16}")

    if len(records) > 20:
        print(f"  ... 共 {len(records)} 条记录，仅显示最近 20 条")
    print()

    if trend:
        print("  📊 趋势分析")
        print("  " + "-" * 40)
        if trend.get('direction'):
            print(f"    整体趋势: {trend['direction']}")
        if trend.get('total_net_buy') is not None:
            print(f"    累计净买入: {_fmt_amount(trend['total_net_buy'])}")
        if trend.get('avg_daily_net_buy') is not None:
            print(f"    日均净买入: {_fmt_amount(trend['avg_daily_net_buy'])}")
        if trend.get('max_net_buy') is not None:
            print(f"    最大单日净买入: {_fmt_amount(trend['max_net_buy'])}")
        if trend.get('max_net_sell') is not None:
            print(f"    最大单日净卖出: {_fmt_amount(trend['max_net_sell'])}")
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
