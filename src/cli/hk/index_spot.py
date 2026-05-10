# -*- coding: utf-8 -*-
"""港股指数实时行情命令"""

import typer

from . import hk_app
from ..helpers import print_banner


@hk_app.command("index-spot")
def index_spot():
    """港股指数实时行情"""
    from fund_tools import get_hk_index_spot

    print_banner()
    print("📊 港股指数实时行情")
    print()

    result = get_hk_index_spot()

    if result.get("status") == "error":
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get("data", [])
    source = result.get("source", "")
    note = result.get("data_delay_note", "")

    print(f"  数据源: {source} | 共 {len(data)} 个指数 | {note}")
    print()

    if not data:
        print("  ℹ️  暂无数据")
        return

    print(f"  {'代码':<10}{'名称':<16}{'最新价':<10}{'涨跌额':<10}{'涨跌幅':<10}{'今开':<10}{'最高':<10}{'最低':<10}")
    print("  " + "-" * 86)
    for item in data:
        code = str(item.get("代码", ""))
        name = str(item.get("名称", ""))[:14]
        price = item.get("最新价", "N/A")
        change = item.get("涨跌额", "N/A")
        pct = item.get("涨跌幅", "N/A")
        open_v = item.get("今开", "N/A")
        high = item.get("最高", "N/A")
        low = item.get("最低", "N/A")

        price_s = f"{price:.2f}" if isinstance(price, (int, float)) else str(price)
        change_s = f"{change:.2f}" if isinstance(change, (int, float)) else str(change)
        pct_s = f"{pct:.2f}%" if isinstance(pct, (int, float)) else str(pct)
        open_s = f"{open_v:.2f}" if isinstance(open_v, (int, float)) else str(open_v)
        high_s = f"{high:.2f}" if isinstance(high, (int, float)) else str(high)
        low_s = f"{low:.2f}" if isinstance(low, (int, float)) else str(low)

        print(f"  {code:<10}{name:<16}{price_s:<10}{change_s:<10}{pct_s:<10}{open_s:<10}{high_s:<10}{low_s:<10}")
    print()
