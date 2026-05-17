# -*- coding: utf-8 -*-
"""资产配置结构命令"""

from typing import Optional

import typer

from . import bond_app
from ..helpers import print_banner, get_current_year


@bond_app.command("allocation")
def allocation(
    code: str = typer.Argument(..., help="6位基金代码"),
    year: Optional[str] = typer.Option(None, "--year", "-y", help="年份（默认: 当前年份）"),
):
    """资产配置结构"""
    from fund_tools import get_fund_asset_allocation

    print_banner()
    print(f"🎯 资产配置结构: {code}")
    print()

    y = year or get_current_year()
    result = get_fund_asset_allocation(code, year=y)
    if result.get('status') == 'success':
        data = result.get('data', {})
        if isinstance(data, dict):
            for key, value in data.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {data}")
    else:
        print(f"  ❌ {result.get('message', '查询失败')}")
