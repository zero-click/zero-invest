# -*- coding: utf-8 -*-
"""香港基金排行命令"""

import typer

from . import hk_app
from ..helpers import print_banner


@hk_app.command("fund-ranking")
def fund_ranking(
    sort_by: str = typer.Option("近1年", "--sort", "-s", help="排序字段"),
    limit: int = typer.Option(20, "--limit", "-n", help="返回数量"),
):
    """香港基金排行榜"""
    from fund_tools import get_hk_fund_rankings

    print_banner()
    print(f"🏆 香港基金排行榜（按 {sort_by} 排序，前 {limit} 名）")
    print()

    result = get_hk_fund_rankings(sort_by=sort_by, limit=limit)

    if result.get("status") == "error":
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get("data", [])
    if not data:
        print("  ℹ️  暂无数据")
        return

    print(f"  {'基金代码':<10}{'基金简称':<24}{'近1周':<10}{'近1月':<10}{'近3月':<10}{'近1年':<10}{'成立来':<10}")
    print("  " + "-" * 84)
    for item in data:
        code = str(item.get("基金代码", ""))
        name = str(item.get("基金简称", ""))[:22]
        vals = []
        for key in ["近1周", "近1月", "近3月", "近1年", "成立来"]:
            v = item.get(key)
            vals.append(f"{v:.2f}" if v is not None else "N/A")
        print(f"  {code:<10}{name:<24}" + "".join(f"{v:<10}" for v in vals))
    print()
