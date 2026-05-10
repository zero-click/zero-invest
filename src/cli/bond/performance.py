# -*- coding: utf-8 -*-
"""基金业绩命令"""

import typer

from . import bond_app
from ..helpers import print_banner


@bond_app.command("performance")
def performance(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """基金业绩"""
    from fund_tools import get_fund_performance

    print_banner()
    print(f"📈 基金业绩: {code}")
    print()

    perf = get_fund_performance(code)
    if perf:
        for period, return_rate in perf.items():
            print(f"  {period}: {return_rate}")
    else:
        print("  ℹ️  暂无业绩数据")
