# -*- coding: utf-8 -*-
"""基金搜索命令"""

import typer

from . import bond_app
from ..helpers import print_banner


def print_fund_search_results(results: list, show_all: bool = False):
    """美式打印基金搜索结果"""
    if not results:
        print("  ℹ️  未找到匹配的基金")
        return

    count = len(results)
    display_count = count if show_all else min(10, count)

    print(f"  查找到 {count} 只基金 (显示前 {display_count} 只):")
    print()
    print(f"  {'序号':<6}{'基金代码':<12}{'基金名称':<25}{'基金类型':<20}")
    print("  " + "-" * 65)

    for i, fund in enumerate(results[:display_count], 1):
        code = fund.get('基金代码', '')
        name = fund.get('基金简称', '')
        fund_type = fund.get('基金类型', '')

        # 截断过长的名称
        if len(name) > 23:
            name = name[:20] + '...'

        print(f"  {i:<6}{code:<12}{name:<25}{fund_type:<20}")

    if count > display_count:
        print(f"  ... 还有 {count - display_count} 只基金")


@bond_app.command("search")
def search(
    keyword: str = typer.Argument(..., help="搜索关键词（基金代码/名称/拼音）"),
    show_all: bool = typer.Option(False, "--all", "-a", help="显示所有结果"),
):
    """搜索基金"""
    from fund_tools import search_funds

    print_banner()
    print(f"🔍 搜索基金: {keyword}")
    print()

    result = search_funds(keyword)

    if result.get('status') == 'error':
        print(f"  ❌ {result['message']}")
    elif result.get('count') == 0:
        print(f"  ℹ️  未找到与 '{keyword}' 相关的基金")
    else:
        print_fund_search_results(result['data'], show_all=show_all)
