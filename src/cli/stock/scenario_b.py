# -*- coding: utf-8 -*-
"""场景B分析命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def scenario_b(
    code: str = typer.Argument(..., help="股票代码"),
):
    """场景B分析（成长/亏损型：PS + FCF反算）"""
    print_banner()

    from fund_tools.stock import analyze_scenario_b

    typer.echo(f"📊 场景B分析：高速成长/亏损型")
    typer.echo("")
    typer.echo("=" * 60)

    result = analyze_scenario_b(code)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']

    typer.echo(f"  股票: {code} {data.get('股票名称', '')}")
    typer.echo("")

    typer.echo("  📈 PS估值")
    typer.echo("  " + "-" * 60)
    typer.echo(f"  PS:      {data.get('PS', 'N/A')}")
    typer.echo(f"  营收增速:  {data.get('营收增速', 'N/A')}%")
    typer.echo(f"  毛利率:   {data.get('毛利率', 'N/A')}%")
    typer.echo("")

    note = data.get('说明', '')
    if note:
        typer.echo(f"  ℹ️  {note}")

    typer.echo("=" * 60)
