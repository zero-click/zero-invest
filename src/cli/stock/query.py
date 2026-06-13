# -*- coding: utf-8 -*-
"""个股查询命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def query(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询股票基本信息"""
    print_banner()

    from fund_tools.stock import get_stock_spot

    result = get_stock_spot(code)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']

    typer.echo(f"📊 查询股票: {code}")
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("  📋 基本信息")
    typer.echo("  " + "-" * 60)
    typer.echo(f"  股票代码:  {data['代码']}")
    typer.echo(f"  股票名称:  {data['名称']}")
    typer.echo(f"  当前价格:  {data['最新价']}元")
    typer.echo(f"  涨跌幅:    {data['涨跌幅']}%")
    typer.echo(f"  涨跌额:    {data['涨跌额']}元")
    typer.echo(f"  总市值:    {data['总市值']}")
    typer.echo(f"  流通市值:  {data['流通市值']}")
    typer.echo(f"  市盈率:    {data['市盈率']}")
    typer.echo(f"  市净率:    {data['市净率']}")
    typer.echo("=" * 60)
