# -*- coding: utf-8 -*-
"""缓存状态命令"""

import typer
import os

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def cache():
    """查看缓存状态"""
    print_banner()

    typer.echo("=" * 60)
    typer.echo("  💾 缓存状态")
    typer.echo("=" * 60)
    typer.echo("")

    cache_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'cache')
    if os.path.exists(cache_dir):
        files = os.listdir(cache_dir)
        typer.echo(f"  缓存目录: {cache_dir}")
        typer.echo(f"  文件数量: {len(files)}")
        for f in files[:5]:
            path = os.path.join(cache_dir, f)
            size = os.path.getsize(path)
            typer.echo(f"    - {f}: {size} bytes")
    else:
        typer.echo("  缓存目录不存在")

    typer.echo("")
    typer.echo("=" * 60)
