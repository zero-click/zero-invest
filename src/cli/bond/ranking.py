# -*- coding: utf-8 -*-
"""基金排行榜命令"""

from typing import Optional

import typer

from . import bond_app
from ..helpers import print_banner


@bond_app.command("ranking")
def ranking(
    fund_type: str = typer.Option(
        "全部", "--type", "-t",
        help="基金类型（默认: 全部）",
    ),
    top: int = typer.Option(10, "--top", "-n", help="显示前N名（默认: 10）"),
    hk: bool = typer.Option(False, "--hk", help="查看香港基金排行"),
):
    """查看基金排行榜"""
    print_banner()

    if hk:
        from fund_tools import get_hk_fund_rankings

        print(f"🏆 香港基金排行榜")
        print()

        result = get_hk_fund_rankings(sort_by="近1年", limit=top)

        if result.get("status") == "error":
            print(f"  ❌ {result.get('message', '查询失败')}")
            return

        data = result.get("data", [])
        if not data:
            print("  ℹ️  暂无数据")
            return

        print(f"  {'排名':<6}{'基金代码':<12}{'基金简称':<24}{'近1周':<10}{'近1月':<10}{'近3月':<10}{'近1年':<10}{'成立来':<10}")
        print("  " + "-" * 90)
        for i, item in enumerate(data, 1):
            code = str(item.get("基金代码", ""))
            name = str(item.get("基金简称", ""))[:22]
            vals = []
            for key in ["近1周", "近1月", "近3月", "近1年", "成立来"]:
                v = item.get(key)
                vals.append(f"{v:.2f}" if v is not None else "N/A")
            print(f"  {i:<6}{code:<12}{name:<24}" + "".join(f"{v:<10}" for v in vals))
        print()
    else:
        from fund_tools import get_fund_rankings

        from fund_tools.core import VALID_FUND_TYPES
        if fund_type not in VALID_FUND_TYPES:
            print(f"  ❌ 无效的基金类型: {fund_type}，可选: {', '.join(VALID_FUND_TYPES)}")
            raise typer.Exit(code=1)

        print(f"🏆 基金排行榜 - {fund_type}")
        print()

        rankings = get_fund_rankings(fund_type, top=top)
        print(f"  {'排名':<6}{'基金代码':<12}{'基金名称':<25}{'近1年收益率':<12}")
        print("  " + "-" * 60)
        for i, fund in enumerate(rankings, 1):
            print(f"  {i:<6}{fund['基金代码']:<12}{fund['基金简称']:<25}{fund['近1年']:<12}")
