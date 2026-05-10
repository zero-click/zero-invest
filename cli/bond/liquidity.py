# -*- coding: utf-8 -*-
"""流动性信息命令"""

import typer

from cli.bond import bond_app
from cli.helpers import print_banner


def print_liquidity_info(result: dict):
    """打印流动性信息"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    info = result.get('liquidity_info', {})
    if not info:
        print("  ℹ️  暂无流动性数据")
        return

    # 申赎状态
    print("  🔄 申赎状态")
    print("  " + "-" * 60)
    print(f"    基金状态: {info.get('基金状态', 'N/A')}")
    if '申购状态' in info:
        print(f"    申购状态: {info['申购状态']}")
    if '赎回状态' in info:
        print(f"    赎回状态: {info['赎回状态']}")
    print()

    # 交易规则
    print("  📋 交易规则")
    print("  " + "-" * 60)
    print(f"    交易场所: {info.get('交易场所', 'N/A')}")
    print(f"    申赎时间: {info.get('申赎时间', 'N/A')}")
    print(f"    最低申购: {info.get('最低申购金额', 'N/A')}")
    print(f"    申购确认: {info.get('申购确认时间', 'N/A')}")
    print(f"    赎回到账: {info.get('赎回到账时间', 'N/A')}")
    print()


@bond_app.command("liquidity")
def liquidity(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """流动性信息"""
    from fund_tools import get_fund_liquidity_info

    print_banner()
    print(f"💧 流动性信息: {code}")
    print()

    result = get_fund_liquidity_info(code)
    print_liquidity_info(result)
