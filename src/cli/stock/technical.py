# -*- coding: utf-8 -*-
"""技术指标查询命令"""

import typer
from src.fund_tools.stock import get_stock_hist
from src.cli.helpers import print_banner

technical_app = typer.Typer(help="技术指标查询")


@technical_app.command()
def technical(
    code: str = typer.Argument(..., help="股票代码"),
    days: int = typer.Option(252, help="查询天数"),
):
    """查询技术指标（200日MA、52周高低、RSI等）"""
    print_banner("技术指标分析")

    result = get_stock_hist(code, days=days)
    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    stats = result.get('stats', {})

    typer.echo(f"  股票代码: {code}")
    typer.echo("")
    typer.echo("【基础统计】")
    typer.echo(f"  期间涨跌幅: {stats.get('期间涨跌幅', 'N/A'):.2f}%")
    typer.echo(f"  年化波动率: {stats.get('年化波动率', 'N/A'):.2f}%")
    typer.echo(f"  最大回撤: {stats.get('最大回撤', 'N/A'):.2f}%")
    typer.echo(f"  当前回撤: {stats.get('当前回撤', 'N/A'):.2f}%")
    typer.echo("")
    typer.echo("【技术指标】")
    typer.echo(f"  RSI(14): {stats.get('RSI(14)', 'N/A'):.2f}" if stats.get('RSI(14') is not None else "  RSI(14): N/A")

    if '200日均线' in stats:
        typer.echo(f"  200日均线: {stats.get('200日均线', 'N/A'):.2f}")
        typer.echo(f"  200日均线乖离率: {stats.get('200日均线乖离率', 'N/A'):.2f}%")

    if '52周最高' in stats:
        typer.echo(f"  52周最高: {stats.get('52周最高', 'N/A'):.2f}")
        typer.echo(f"  52周最低: {stats.get('52周最低', 'N/A'):.2f}")
        typer.echo(f"  52周涨幅: {stats.get('52周涨幅', 'N/A'):.2f}%")
        typer.echo(f"  距52周高点距离: {stats.get('距52周高点距离', 'N/A'):.2f}%")
