# -*- coding: utf-8 -*-
"""指数最近收益查询命令"""

import typer
from datetime import datetime

from . import index_app
from ..helpers import print_banner


def print_index_recent_performance(result: dict, limit: int = 20):
    """打印指数最近收益走势"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    code = result.get('code', '')
    days = result.get('days', 0)
    total_return = result.get('total_return', 0)
    data_count = result.get('data_count', 0)
    data = result.get('data', [])

    print()
    print(f"  📊 指数代码: {code}")
    print(f"  📅 最近 {days} 天")
    print(f"  📈 期间收益率: {total_return:+.2f}%")
    print(f"  📋 数据点数: {data_count}")
    print()

    if not data:
        print("  ℹ️  暂无数据")
        return

    # 显示最近的数据
    show = data[-limit:]  # 取最后几条（最新的数据）
    print(f"  最近 {min(limit, len(show))} 个交易日:")
    print()

    # 指数历史行情通常包含：日期, 开盘, 收盘, 最高, 最低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
    first_item = show[0] if show else {}
    if '收盘' in first_item or 'close' in first_item:
        # 标准指数行情格式
        print(f"  {'日期':<14}{'收盘':<10}{'开盘':<10}{'最高':<10}{'最低':<10}{'涨跌幅':<10}")
        print("  " + "-" * 64)
        for item in show:
            dt = str(item.get("日期", item.get("date", "")))[:12]
            close = item.get("收盘", item.get("close", "N/A"))
            open_p = item.get("开盘", item.get("open", "N/A"))
            high = item.get("最高", item.get("high", "N/A"))
            low = item.get("最低", item.get("low", "N/A"))
            change_pct = item.get("涨跌幅", item.get("change_pct", "N/A"))

            close_str = f"{close:.2f}" if isinstance(close, (int, float)) else str(close)
            open_str = f"{open_p:.2f}" if isinstance(open_p, (int, float)) else str(open_p)
            high_str = f"{high:.2f}" if isinstance(high, (int, float)) else str(high)
            low_str = f"{low:.2f}" if isinstance(low, (int, float)) else str(low)
            change_str = f"{change_pct:.2f}%" if isinstance(change_pct, (int, float)) else str(change_pct)

            print(f"  {dt:<14}{close_str:<10}{open_str:<10}{high_str:<10}{low_str:<10}{change_str:<10}")
    else:
        # 其他格式，遍历显示
        for item in show:
            parts = [f"{k}: {v}" for k, v in item.items()]
            print(f"  {' | '.join(parts)}")


@index_app.command("recent")
def recent(
    code: str = typer.Argument(..., help="6位指数代码"),
    days: int = typer.Option(30, "--days", "-d", help="查询天数（1-365，默认30）"),
    limit: int = typer.Option(20, "--limit", "-l", help="显示数据条数（默认20）"),
):
    """查询指数最近 N 天的收益走势

    示例:
        python cli.py index recent 000300 --days 60
        python cli.py index recent 000905 -d 90 -l 30
    """
    print_banner()

    from fund_tools import get_index_recent_performance

    print(f"📈 查询指数最近收益: {code}")
    print()

    result = get_index_recent_performance(code, days)

    print_index_recent_performance(result, limit=limit)

    print()
