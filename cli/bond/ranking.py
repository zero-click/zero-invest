# -*- coding: utf-8 -*-
"""基金排行榜命令"""

from typing import Optional

import typer

from cli.bond import bond_app
from cli.helpers import print_banner


@bond_app.command("ranking")
def ranking(
    fund_type: str = typer.Option(
        "全部", "--type", "-t",
        help="基金类型（默认: 全部）",
    ),
    top: int = typer.Option(10, "--top", "-n", help="显示前N名（默认: 10）"),
):
    """查看基金排行榜"""
    from fund_tools import get_fund_rankings

    _valid_types = ["全部", "股票型", "混合型", "债券型", "指数型", "QDII", "FOF"]
    if fund_type not in _valid_types:
        print(f"  ❌ 无效的基金类型: {fund_type}，可选: {', '.join(_valid_types)}")
        raise typer.Exit(code=1)

    print_banner()
    print(f"🏆 基金排行榜 - {fund_type}")
    print()

    rankings = get_fund_rankings(fund_type, top=top)
    print(f"  {'排名':<6}{'基金代码':<12}{'基金名称':<25}{'近1年收益率':<12}")
    print("  " + "-" * 60)
    for i, fund in enumerate(rankings, 1):
        print(f"  {i:<6}{fund['基金代码']:<12}{fund['基金简称']:<25}{fund['近1年']:<12}")
