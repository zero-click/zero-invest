# -*- coding: utf-8 -*-
"""准入检查命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def checklist(
    code: str = typer.Argument(..., help="股票代码"),
):
    """个股准入完整检查（附录A流水表）"""
    print_banner()

    from fund_tools.stock import get_stock_checklist

    result = get_stock_checklist(code)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    classify_result = result.get('classify', {})
    analysis = result.get('analysis', {})

    typer.echo("=" * 60)
    typer.echo("  📋 个股买入决策流水表")
    typer.echo("=" * 60)
    typer.echo("")

    # 0. 股票类型预分类
    typer.echo("  0. 股票类型预分类")
    typer.echo("  " + "-" * 60)
    typer.echo(f"  股票: {code}")
    typer.echo(f"  类型: {classify_result.get('type', 'N/A')}")
    typer.echo(f"  理由: {classify_result.get('reason', 'N/A')}")
    typer.echo("")

    # 1. 场景分析结果
    typer.echo("  1. 场景分析")
    typer.echo("  " + "-" * 60)
    if analysis.get('status') == 'success':
        data = analysis.get('data', {})
        typer.echo(f"  场景: {data.get('scenario', 'N/A')}")
        typer.echo(f"  类型: {data.get('type', 'N/A')}")
        if 'PEG' in data:
            typer.echo(f"  PEG: {data.get('PEG', 'N/A')}")
    else:
        typer.echo(f"  ⚠️  {analysis.get('message', '分析失败')}")
    typer.echo("")

    # 2. 准入签字
    typer.echo("  5. 准入签字")
    typer.echo("  " + "-" * 60)
    typer.echo("  ☑ 1. 股票类型预分类已完成")
    typer.echo("  ☐ 2. 已通过对应场景的估值路径")
    typer.echo("  ☐ 3. 市值反算正常（如适用）")
    typer.echo("  ☐ 4. 明确归零风险")
    typer.echo("")

    typer.echo("=" * 60)
