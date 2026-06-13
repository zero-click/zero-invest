# -*- coding: utf-8 -*-
"""持仓状态命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def status(
    code: str = typer.Argument(..., help="股票代码"),
):
    """持仓状态检查"""
    print_banner()

    typer.echo("=" * 60)
    typer.echo("  📊 持仓状态检查")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo(f"  股票: {code}")
    typer.echo("")
    typer.echo("  当前持仓:")
    typer.echo("    └─ 需要本地持仓数据支持")
    typer.echo("")
    typer.echo("  ℹ️  此功能需要持仓数据库，待实现")
    typer.echo("=" * 60)
