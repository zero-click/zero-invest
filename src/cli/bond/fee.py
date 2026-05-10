# -*- coding: utf-8 -*-
"""费用明细命令"""

import typer

from . import bond_app
from ..helpers import print_banner


def print_fee_details(result: dict):
    """打印费用明细"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    fees = result.get('fee_details', {})
    if not fees:
        print("  ℹ️  暂无费用数据")
        return

    # 运作费用
    print("  💰 运作费用")
    print("  " + "-" * 60)
    if '管理费率' in fees:
        print(f"    管理费率: {fees['管理费率']}")
    if '托管费率' in fees:
        print(f"    托管费率: {fees['托管费率']}")
    print()

    # 认购/申购费率
    if '申购费率' in fees and fees['申购费率']:
        print("  📥 申购费率")
        print("  " + "-" * 60)
        for fee in fees['申购费率']:
            amount = fee.get('适用金额', '---')
            rate = fee.get('申购费率', 'N/A')
            print(f"    {amount:<15s} {rate}")
        print()

    # 赎回费率
    if '赎回费率' in fees and fees['赎回费率']:
        print("  📤 赎回费率")
        print("  " + "-" * 60)
        for fee in fees['赎回费率']:
            period = fee.get('适用期限', 'N/A')
            rate = fee.get('赎回费率', 'N/A')
            print(f"    {period:<20s} {rate}")
        print()


@bond_app.command("fee")
def fee(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """费用明细"""
    from fund_tools import get_fund_fee_details

    print_banner()
    print(f"💰 费用明细: {code}")
    print()

    result = get_fund_fee_details(code)
    print_fee_details(result)
