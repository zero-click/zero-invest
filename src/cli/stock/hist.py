# -*- coding: utf-8 -*-
"""历史行情命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def hist(
    code: str = typer.Argument(..., help="股票代码"),
    days: int = typer.Option(30, "--days", "-d", help="查询天数"),
):
    """查询历史K线/区间涨跌"""
    print_banner()

    from fund_tools.stock import get_stock_hist

    result = get_stock_hist(code, days)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    df = result['data']
    stats = result['stats']

    typer.echo(f"📈 最近{days}日价格走势")
    typer.echo("")
    typer.echo("=" * 80)
    typer.echo("  📊 历史行情")
    typer.echo("  " + "-" * 80)

    # 显示最近10条
    recent = df.tail(10)[['日期', '开盘', '收盘', '最高', '最低', '涨跌幅', '成交量']]
    for _, row in recent.iterrows():
        typer.echo(f"  {row['日期']}  {row['开盘']:.2f}   {row['收盘']:.2f}   "
                   f"{row['最高']:.2f}   {row['最低']:.2f}   {row['涨跌幅']:.2f}%")

    typer.echo("")
    typer.echo("  📊 统计摘要")
    typer.echo("  " + "-" * 80)
    typer.echo(f"  期间涨跌: {stats['期间涨跌幅']:.2f}%")
    typer.echo(f"  30日高点: {stats['30日高点']:.2f}元")
    typer.echo(f"  当前回撤: {stats['当前回撤']:.2f}%")
    typer.echo(f"  最大回撤: {stats['最大回撤']:.2f}%")
    typer.echo(f"  年化波动率: {stats['年化波动率']:.2f}%")
    typer.echo("=" * 60)
