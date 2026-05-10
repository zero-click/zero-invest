# -*- coding: utf-8 -*-
"""指数搜索命令"""

import typer

from cli.index import index_app
from cli.helpers import print_banner


def print_index_search_results(results: list, show_all: bool = False):
    """打印指数搜索结果"""
    if not results:
        print("  ℹ️  未找到匹配的指数")
        return

    count = len(results)
    display_count = count if show_all else min(15, count)

    print(f"  查找到 {count} 个指数 (显示前 {display_count} 个):")
    print()
    print(f"  {'序号':<6}{'代码':<10}{'名称':<20}{'分类':<12}{'指数类别':<10}")
    print("  " + "-" * 70)

    for i, idx in enumerate(results[:display_count], 1):
        code = idx.get('code', '')
        name = idx.get('name', '')
        category = idx.get('category', '')
        index_class = idx.get('index_class', '')

        # 截断过长的名称
        if len(name) > 18:
            name = name[:15] + '...'

        print(f"  {i:<6}{code:<10}{name:<20}{category:<12}{index_class:<10}")

    if count > display_count:
        print(f"  ... 还有 {count - display_count} 个指数")


@index_app.command("search")
def search(
    keyword: str = typer.Argument(..., help="搜索关键词（指数代码/名称）"),
    show_all: bool = typer.Option(False, "--all", "-a", help="显示所有结果"),
):
    """搜索指数"""
    from fund_tools import search_indices_all

    print_banner()
    print(f"🔍 搜索指数: {keyword}")
    print()

    results = search_indices_all(keyword)

    if not results:
        print(f"  ℹ️  未找到与 '{keyword}' 相关的指数")
    else:
        print_index_search_results(results, show_all=show_all)
