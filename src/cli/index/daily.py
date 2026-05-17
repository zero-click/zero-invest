# -*- coding: utf-8 -*-
"""港股指数日K历史行情命令"""

import typer

from . import index_app
from ..helpers import print_banner


def print_hk_index_daily(result: dict, days: int = 30):
    """打印港股指数历史行情"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get("data", [])
    source = result.get("source", "")

    print(f"  数据源: {source} | 共 {len(data)} 条记录")
    print()

    if not data:
        print("  ℹ️  暂无数据")
        return

    show = data[:days]
    print(f"  {'日期':<14}{'开盘':<12}{'最高':<12}{'最低':<12}{'收盘':<12}{'成交量':<14}")
    print("  " + "-" * 76)
    for item in show:
        dt = str(item.get("date", item.get("日期", "")))[:12]
        open_v = item.get("open", item.get("开盘", "N/A"))
        high = item.get("high", item.get("最高", "N/A"))
        low = item.get("low", item.get("最低", "N/A"))
        close = item.get("close", item.get("收盘", "N/A"))
        vol = item.get("volume", item.get("成交量", "N/A"))

        def _fmt(v):
            return f"{v:.2f}" if isinstance(v, (int, float)) else str(v)

        print(f"  {dt:<14}{_fmt(open_v):<12}{_fmt(high):<12}{_fmt(low):<12}{_fmt(close):<12}{_fmt(vol):<14}")
    print()


@index_app.command("daily")
def daily(
    symbol: str = typer.Argument(..., help="港股指数代码（如 CES100）"),
    days: int = typer.Option(30, "--days", "-d", help="显示天数（1-365）"),
):
    """查询港股指数历史行情（日K）"""
    from fund_tools import get_hk_index_daily

    print_banner()
    print(f"📈 港股指数 {symbol} 历史行情（最近 {days} 天）")
    print()

    result = get_hk_index_daily(symbol=symbol, days=days)
    print_hk_index_daily(result, days=days)
