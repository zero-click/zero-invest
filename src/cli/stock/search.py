# -*- coding: utf-8 -*-
"""个股搜索命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def search(
    keyword: str = typer.Argument(..., help="股票代码或名称关键词"),
):
    """搜索股票"""
    print_banner()

    from fund_tools.stock import search_stock

    result = search_stock(keyword)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    stocks = result['data']
    if not stocks:
        typer.echo(f"  ℹ️  未找到匹配的股票")
        return

    typer.echo(f"  📊 搜索结果: {keyword}")
    typer.echo("  " + "=" * 80)
    typer.echo(f"  {'代码':<10s} {'名称':<20s} {'最新价':<10s} {'涨跌幅':<10s} {'市值':<15s} {'PE':<8s} {'PB':<8s}")
    typer.echo("  " + "-" * 80)

    for stock in stocks[:20]:  # 最多显示20条
        typer.echo(
            f"  {stock['代码']:<10s} {stock['名称']:<20s} "
            f"{stock['最新价']:<10s} {stock['涨跌幅']:<10s} "
            f"{stock['市值']:<15s} {stock['市盈率-动态']:<8s} {stock['市净率']:<8s}"
        )
