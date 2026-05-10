# -*- coding: utf-8 -*-
"""批量查询指数详情命令"""

from typing import List

import typer

from cli.index import index_app
from cli.helpers import print_banner
from cli.index.query import print_index_query
from cli.index.valuation import print_index_valuation


def print_index_details(details: dict):
    """打印指数完整详情（兼容旧命令）"""
    print_index_query(details)
    if details.get('status') == 'error':
        return
    print_index_valuation(details)


@index_app.command("batch")
def batch(
    codes: List[str] = typer.Argument(..., help="指数代码列表（多个代码用空格分隔）"),
):
    """批量查询指数详情"""
    from fund_tools import get_index_details_batch

    print_banner()
    print(f"📊 批量查询指数详情: {' '.join(codes)}")
    print()

    results = get_index_details_batch(codes)

    for code, details in results.items():
        print(f"  === {code} ===")
        print_index_details(details)
        print()
