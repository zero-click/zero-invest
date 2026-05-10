# -*- coding: utf-8 -*-
"""持仓动态分析命令"""

import typer

from cli.bond import bond_app
from cli.helpers import print_banner


@bond_app.command("holdings")
def holdings(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """持仓动态分析"""
    from fund_tools import get_fund_top_holdings
    from cli.bond.query import print_fund_details

    print_banner()
    print(f"💼 持仓动态分析: {code}")
    print()

    holdings = get_fund_top_holdings(code)
    if holdings.get('status') == 'success':
        print_fund_details({'top_holdings': holdings['data']})
    else:
        print(f"  ❌ {holdings.get('message', '查询失败')}")
