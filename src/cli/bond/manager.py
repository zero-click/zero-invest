# -*- coding: utf-8 -*-
"""基金经理查询命令"""

import typer

from . import bond_app
from ..helpers import print_banner


@bond_app.command("manager")
def manager(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """查询基金经理深度信息"""
    from fund_tools import get_fund_manager_details
    from .query import print_fund_details

    print_banner()
    print(f"👤 查询基金经理: {code}")
    print()

    manager = get_fund_manager_details(code)
    if manager.get('status') == 'success':
        print_fund_details({'manager_details': manager})
    else:
        print(f"  ❌ {manager.get('message', '查询失败')}")
