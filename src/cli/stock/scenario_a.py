# -*- coding: utf-8 -*-
"""场景A分析命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def scenario_a(
    code: str = typer.Argument(..., help="股票代码"),
):
    """场景A分析（稳定成长型：Forward PE / PEG）"""
    print_banner()

    from fund_tools.stock import analyze_scenario_a

    typer.echo(f"📊 场景A分析：稳定成长型")
    typer.echo("")
    typer.echo("=" * 60)

    result = analyze_scenario_a(code)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']

    typer.echo(f"  股票: {code} {data.get('股票名称', '')}")
    typer.echo("")

    typer.echo("  📈 估值指标")
    typer.echo("  " + "-" * 60)
    typer.echo(f"  市盈率-TTM:     {data.get('市盈率-TTM', 'N/A')}x")
    typer.echo(f"  营收增速:       {data.get('营收增速', 'N/A')}%")
    typer.echo(f"  PEG:            {data.get('PEG', 'N/A')}")
    typer.echo("")

    typer.echo("  🎯 估值判断")
    typer.echo("  " + "-" * 60)
    judgment = data.get('判断', '')
    if '低估' in judgment or '便宜' in judgment:
        typer.echo(f"  ✅ {judgment}")
    else:
        typer.echo(f"  ⚠️  {judgment}")

    typer.echo("=" * 60)
