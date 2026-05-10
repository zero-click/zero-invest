# -*- coding: utf-8 -*-
"""基金评级命令"""

import typer

from cli.bond import bond_app
from cli.helpers import print_banner


@bond_app.command("rating")
def rating(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """查询基金评级"""
    from fund_tools import get_fund_rating

    print_banner()
    print(f"⭐ 查询基金评级: {code}")
    print()

    rating = get_fund_rating(code)
    if rating.get('status') == 'success':
        ratings = rating.get('ratings')
        if ratings:
            for key, value in ratings.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {rating.get('message', '暂无评级数据')}")
    else:
        print(f"  ❌ {rating.get('message', '查询失败')}")
