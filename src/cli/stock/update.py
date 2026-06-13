# -*- coding: utf-8 -*-
"""数据更新命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def update():
    """更新股票数据库"""
    print_banner()

    typer.echo("=" * 60)
    typer.echo("  🔄 更新股票数据库")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo("  ℹ️  数据通过 akshare 实时获取，无需本地数据库")
    typer.echo("=" * 60)
