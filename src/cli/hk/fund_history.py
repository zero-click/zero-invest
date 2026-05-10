# -*- coding: utf-8 -*-
"""香港基金历史净值命令"""

import typer

from . import hk_app
from ..helpers import print_banner


@hk_app.command("fund-history")
def fund_history(
    code: str = typer.Argument(..., help="基金代码（6位）"),
    history_type: str = typer.Option(
        "历史净值明细", "--type", "-t",
        help="查询类型: 历史净值明细 / 分红送配详情",
    ),
    limit: int = typer.Option(20, "--limit", "-n", help="显示条数"),
):
    """查询香港基金历史净值或分红送配"""
    from fund_tools import get_hk_fund_history

    print_banner()
    print(f"📈 香港基金 {code} — {history_type}")
    print()

    result = get_hk_fund_history(code=code, history_type=history_type)

    if result.get("status") == "error":
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get("data", [])
    name = result.get("name", "")
    count = result.get("count", 0)
    print(f"  基金: {name} ({code})")
    print(f"  共 {count} 条记录，显示最近 {min(limit, count)} 条:")
    print()

    if not data:
        print("  ℹ️  暂无数据")
        return

    # 根据类型选择显示列
    show = data[:limit]
    if history_type == "历史净值明细":
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
        # 分红送配详情 — 直接打印字典
        for item in show:
            parts = [f"{k}: {v}" for k, v in item.items()]
            print(f"  {' | '.join(parts)}")
    print()
