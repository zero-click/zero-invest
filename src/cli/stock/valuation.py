# -*- coding: utf-8 -*-
"""估值概览命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def valuation(
    code: str = typer.Argument(..., help="股票代码"),
):
    """估值概览（PE/PB/PS/EV）"""
    print_banner()

    from fund_tools.stock import get_stock_spot, get_stock_financial_indicator

    typer.echo("=" * 60)
    typer.echo("  📊 估值概览")
    typer.echo("=" * 60)
    typer.echo("")

    # 获取实时行情
    spot = get_stock_spot(code)
    if spot['status'] != 'success':
        typer.echo(f"  ❌ {spot['message']}")
        raise typer.Exit(1)

    data = spot['data']

    typer.echo(f"  股票: {code} {data['名称']}")
    typer.echo("")
    typer.echo("  📈 估值指标")
    typer.echo("  " + "-" * 60)
    typer.echo(f"  市盈率(PE):  {data['市盈率']}")
    typer.echo(f"  市净率(PB):  {data['市净率']}")
    typer.echo(f"  总市值:      {data['总市值']}")
    typer.echo("")

    # 获取财务指标
    financial = get_stock_financial_indicator(code)
    if financial['status'] == 'success':
        fin_data = financial['data']
        typer.echo("  📊 财务指标")
        typer.echo("  " + "-" * 60)
        typer.echo(f"  ROE:        {fin_data.get('ROE', 'N/A')}")
        typer.echo(f"  毛利率:      {fin_data.get('毛利率', 'N/A')}")
        typer.echo(f"  净利率:      {fin_data.get('净利率', 'N/A')}")
        typer.echo(f"  营收增速:    {fin_data.get('营收增速', 'N/A')}")

    typer.echo("")
    typer.echo("=" * 60)
