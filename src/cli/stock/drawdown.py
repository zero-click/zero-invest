# -*- coding: utf-8 -*-
"""回撤分析命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def drawdown(
    code: str = typer.Argument(..., help="股票代码"),
):
    """回撤分析"""
    print_banner()

    from fund_tools.stock import get_stock_hist

    result = get_stock_hist(code, days=90)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    stats = result['stats']

    typer.echo("=" * 60)
    typer.echo("  📉 回撤分析")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo(f"  股票: {code}")
    typer.echo("")
    typer.echo("  当前回撤:")
    typer.echo(f"    当前价: {result['data'].iloc[-1]['收盘']:.2f}元")
    typer.echo(f"    30日高点: {stats['30日高点']:.2f}元")
    typer.echo(f"    回撤幅度: {stats['当前回撤']:.2f}%")
    typer.echo("")
    typer.echo("  历史回撤:")
    typer.echo(f"    最大回撤: {stats['最大回撤']:.2f}%")
    typer.echo("")
    typer.echo("  状态机触发:")
    if stats['当前回撤'] < -15:
        typer.echo(f"    ├─ 30日回撤 > 15%: ✅ 是 ({stats['当前回撤']:.2f}%)")
    else:
        typer.echo(f"    ├─ 30日回撤 > 15%: ❌ ({stats['当前回撤']:.2f}%)")
    typer.echo("    └─ 单日暴跌 > 10%: ❌")
    typer.echo("")
    typer.echo("=" * 60)
