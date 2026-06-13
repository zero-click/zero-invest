# -*- coding: utf-8 -*-
"""退出评估命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def exit_eval(
    code: str = typer.Argument(..., help="股票代码"),
):
    """退出评估"""
    print_banner()

    typer.echo("=" * 60)
    typer.echo("  🚪 退出评估")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo(f"  股票: {code}")
    typer.echo("")
    typer.echo("  ℹ️  此功能需要财报和持仓历史，待实现")
    typer.echo("=" * 60)
