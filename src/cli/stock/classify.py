# -*- coding: utf-8 -*-
"""股票分类查询命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def classify(
    code: str = typer.Argument(..., help="股票代码"),
):
    """股票类型查询（本工具不预测类型）"""
    print_banner()

    from fund_tools.stock import classify_stock

    typer.echo("=" * 60)
    typer.echo("  🏷️  股票类型")
    typer.echo("=" * 60)
    typer.echo("")

    result = classify_stock(code)

    # 总是显示提示信息（即使是 error 状态）
    typer.echo(f"  股票: {code}")
    typer.echo("")
    typer.echo("  ⚠️  本工具是数据脚本，不预测股票类型。")
    typer.echo("")
    typer.echo("  请根据公司基本面自行判断后选择场景分析：")
    typer.echo("    ├─ scenario-a  稳定成长型（Forward PE / PEG）")
    typer.echo("    ├─ scenario-b  高速成长型（PS + FCF反算）")
    typer.echo("    └─ scenario-c  强周期型（DOI / EV/EBITDA / PB）")
    typer.echo("")

    typer.echo("=" * 60)
