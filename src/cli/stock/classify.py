# -*- coding: utf-8 -*-
"""股票分类命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def classify(
    code: str = typer.Argument(..., help="股票代码"),
):
    """股票类型预分类"""
    print_banner()

    from fund_tools.stock import classify_stock

    result = classify_stock(code)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    typer.echo("=" * 60)
    typer.echo("  🏷️  股票类型预分类")
    typer.echo("=" * 60)
    typer.echo("")
    typer.echo(f"  股票: {code}")
    typer.echo("")
    typer.echo(f"  类型判定: {result['type']}")
    typer.echo("")
    typer.echo("  判定依据:")
    typer.echo(f"  └─ {result['reason']}")
    typer.echo("")

    type_map = {
        "稳定成长型": "✅ 场景A（Forward PE / PEG 有效）",
        "强周期型": "✅ 场景C（DOI/EV/EBITDA/PB）",
        "生态垄断型": "⚠️  场景B + 垄断溢价检查",
    }

    hint = type_map.get(result['type'], "请手动判断适用场景")
    typer.echo(f"  估值工具适配: {hint}")
    typer.echo("")
    typer.echo("=" * 60)
