# -*- coding: utf-8 -*-
"""指数候选基金池命令"""

import typer

from cli.index import index_app
from cli.helpers import print_banner


def print_index_candidate_funds(result: dict, show_all: bool = False):
    """打印指数候选基金池"""
    if result.get("status") == "error":
        print(f"  ❌ {result.get('message')}")
        return

    index_info = result.get("index", {})
    funds = result.get("funds", [])
    count = result.get("count", len(funds))
    display_count = count if show_all else min(20, count)

    print(f"  指数: {index_info.get('name', '')} ({index_info.get('code', '')})")
    print(f"  候选基金数量: {count} (显示 {display_count})")
    aliases = result.get("aliases", [])
    if aliases:
        print(f"  匹配关键词: {', '.join(aliases[:8])}")
    print()

    if not funds:
        print("  ℹ️  未找到候选基金")
        return

    print(f"  {'序号':<6}{'基金代码':<10}{'基金名称':<24}{'跟踪方式':<10}{'手续费':<8}")
    print("  " + "-" * 80)
    for i, item in enumerate(funds[:display_count], 1):
        code = str(item.get("基金代码", ""))
        name = str(item.get("基金名称", ""))
        track = str(item.get("跟踪方式", ""))
        fee = str(item.get("手续费", ""))
        if len(name) > 22:
            name = name[:19] + "..."
        print(f"  {i:<6}{code:<10}{name:<24}{track:<10}{fee:<8}")

    if count > display_count:
        print(f"  ... 还有 {count - display_count} 只基金")


@index_app.command("listfund")
def listfund(
    code: str = typer.Argument(..., help="6位指数代码"),
    show_all: bool = typer.Option(False, "--all", "-a", help="显示所有候选基金"),
):
    """查看指数候选基金池"""
    from fund_tools import get_index_candidate_funds

    print_banner()
    print(f"📋 查询指数候选基金池: {code}")
    print()

    result = get_index_candidate_funds(code)
    print_index_candidate_funds(result, show_all=show_all)
