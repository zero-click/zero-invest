# -*- coding: utf-8 -*-
"""场景C分析命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def scenario_c(
    code: str = typer.Argument(..., help="股票代码"),
):
    """场景C分析（强周期型：DOI/EV/EBITDA/PB）"""
    print_banner()

    from fund_tools.stock import analyze_scenario_c

    typer.echo(f"📊 场景C分析：强周期型")
    typer.echo("")
    typer.echo("=" * 60)

    result = analyze_scenario_c(code)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']

    typer.echo(f"  股票: {code} {data.get('股票名称', '')}")
    typer.echo("")

    typer.echo("  📨 周期位置判定")
    typer.echo("  " + "-" * 60)
    typer.echo(f"  PB:  {data.get('PB', 'N/A')}")
    typer.echo("")

    note = data.get('说明', '')
    if note:
        typer.echo(f"  ℹ️  {note}")

    typer.echo("=" * 60)
