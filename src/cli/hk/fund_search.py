# -*- coding: utf-8 -*-
"""香港基金搜索命令"""

import typer

from . import hk_app
from ..helpers import print_banner


@hk_app.command("fund-search")
def fund_search(
    keyword: str = typer.Argument(..., help="搜索关键字"),
):
    """搜索香港基金（按代码或名称）"""
    from fund_tools import search_hk_funds

    print_banner()
    print(f"🔍 搜索香港基金: {keyword}")
    print()

    result = search_hk_funds(keyword)

    if result.get("status") == "error":
        print(f"  ❌ {result.get('message', '搜索失败')}")
        return

    data = result.get("data", [])
    if not data:
        print("  ℹ️  未找到匹配的香港基金")
        return

    print(f"  找到 {len(data)} 只基金:")
    print()
    print(f"  {'基金代码':<10}{'基金简称':<30}{'近1年':<10}")
    print("  " + "-" * 50)
    for item in data:
        code = str(item.get("基金代码", ""))
        name = str(item.get("基金简称", ""))[:28]
        v = item.get("近1年")
        v_str = f"{v:.2f}" if v is not None else "N/A"
        print(f"  {code:<10}{name:<30}{v_str:<10}")
    print()
