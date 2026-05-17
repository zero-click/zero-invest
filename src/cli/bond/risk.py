# -*- coding: utf-8 -*-
"""风险指标命令"""

import typer

from . import bond_app
from ..helpers import print_banner


@bond_app.command("risk")
def risk(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """风险指标"""
    from fund_tools import get_fund_risk_metrics

    print_banner()
    print(f"⚠️  风险指标: {code}")
    print()

    risk = get_fund_risk_metrics(code)
    if risk:
        for key, value in risk.items():
            print(f"  {key}: {value}")
    else:
        print("  ℹ️  暂无风险数据")
