# -*- coding: utf-8 -*-
"""十大重仓股命令"""

import typer

from cli.bond import bond_app
from cli.helpers import print_banner, get_current_year


@bond_app.command("top-holdings")
def top_holdings(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """十大重仓股"""
    from fund_tools import get_fund_top_holdings

    print_banner()
    print(f"💼 十大重仓股: {code}")
    print()

    holdings = get_fund_top_holdings(code, year=get_current_year())
    if holdings:
        for i, holding in enumerate(holdings[:10], 1):
            print(f"  {i}. {holding}")
    else:
        print("  ℹ️  暂无持仓数据")
