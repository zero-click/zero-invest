# -*- coding: utf-8 -*-
"""基金最近收益查询命令"""

import typer
from datetime import datetime

from . import bond_app
from ..helpers import print_banner


def print_recent_performance(result: dict, limit: int = 20):
    """打印最近收益走势"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    code = result.get('code', '')
    days = result.get('days', 0)
    total_return = result.get('total_return', 0)
    data_count = result.get('data_count', 0)
    data = result.get('data', [])

    print()
    print(f"  📊 基金代码: {code}")
    print(f"  📅 最近 {days} 天")
    print(f"  📈 期间收益率: {total_return:+.2f}%")
    print(f"  📋 数据点数: {data_count}")
    print()

    if not data:
        print("  ℹ️  暂无数据")
        return

    # 显示最近的数据
    show = data[:limit]
    print(f"  最近 {min(limit, len(show))} 个交易日:")
    print()

    # 根据数据格式显示
    first_item = show[0]
    if '净值日期' in first_item or '日期' in first_item:
        # 基金净值格式
        print(f"  {'日期':<14}{'单位净值':<14}{'累计净值':<14}{'日增长率':<10}")
        print("  " + "-" * 52)
        for item in show:
            dt = str(item.get("净值日期", item.get("日期", "")))[:12]
            nav = item.get("单位净值", item.get("净值", "N/A"))
            acc = item.get("累计净值", "N/A")
            growth = item.get("日增长率", "N/A")

            nav_str = f"{nav:.4f}" if isinstance(nav, (int, float)) else str(nav)
            acc_str = f"{acc:.4f}" if isinstance(acc, (int, float)) else str(acc)
            g_str = f"{growth:.2f}%" if isinstance(growth, (int, float)) else str(growth)

            print(f"  {dt:<14}{nav_str:<14}{acc_str:<14}{g_str:<10}")
    else:
        # 其他格式，遍历显示
        for item in show:
            parts = [f"{k}: {v}" for k, v in item.items()]
            print(f"  {' | '.join(parts)}")


@bond_app.command("recent")
def recent(
    code: str = typer.Argument(..., help="6位基金代码"),
    days: int = typer.Option(30, "--days", "-d", help="查询天数（1-365，默认30）"),
    limit: int = typer.Option(20, "--limit", "-l", help="显示数据条数（默认20）"),
):
    """查询基金最近 N 天的收益走势

    示例:
        python cli.py bond recent 005561 --days 60
        python cli.py bond recent 005561 -d 90 -l 30
    """
    print_banner()

    from fund_tools import get_fund_recent_performance

    print(f"📈 查询基金最近收益: {code}")
    print()

    result = get_fund_recent_performance(code, days)

    print_recent_performance(result, limit=limit)

    print()
