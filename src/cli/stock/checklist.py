# -*- coding: utf-8 -*-
"""准入检查命令"""

import typer

from . import stock_app
from ..helpers import print_banner


@stock_app.command()
def checklist(
    code: str = typer.Argument(..., help="股票代码"),
    stock_type: str = typer.Option("a", "--type", "-t", help="股票类型：a=稳定成长型, b=高速成长型, c=强周期型"),
):
    """个股准入检查（需指定股票类型）"""
    print_banner()

    from fund_tools.stock import get_stock_checklist, get_stock_spot

    typer.echo("=" * 60)
    typer.echo("  📋 个股买入决策流水表")
    typer.echo("=" * 60)
    typer.echo("")

    # 获取基本信息
    spot = get_stock_spot(code)
    if spot['status'] != 'success':
        typer.echo(f"  ❌ {spot['message']}")
        raise typer.Exit(1)

    data = spot['data']
    typer.echo(f"  股票: {code} {data.get('名称', '')}")
    typer.echo("")

    # 类型映射
    type_names = {
        "a": "稳定成长型（Forward PE / PEG）",
        "b": "高速成长型（PS + FCF反算）",
        "c": "强周期型（DOI / EV/EBITDA / PB）",
    }

    typer.echo("  0. 股票类型（用户指定）")
    typer.echo("  " + "-" * 60)
    typer.echo(f"  类型: {type_names.get(stock_type, stock_type)}")
    typer.echo("")

    # 获取场景分析
    result = get_stock_checklist(code, stock_type)

    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    # 1. 场景分析结果
    typer.echo("  1. 场景分析")
    typer.echo("  " + "-" * 60)
    analysis = result.get('analysis', {})
    if analysis.get('status') == 'success':
        analysis_data = analysis.get('data', {})
        typer.echo(f"  场景: {analysis_data.get('股票名称', 'N/A')}")
        if 'PEG' in analysis_data:
            typer.echo(f"  PEG: {analysis_data.get('PEG', 'N/A')}")
        if '市盈率-TTM' in analysis_data:
            typer.echo(f"  市盈率-TTM: {analysis_data.get('市盈率-TTM', 'N/A')}")
    else:
        typer.echo(f"  ⚠️  {analysis.get('message', '分析失败')}")
    typer.echo("")

    # 2. 准入签字
    typer.echo("  5. 准入签字")
    typer.echo("  " + "-" * 60)
    typer.echo("  ☐ 1. 股票类型已由用户指定")
    typer.echo("  ☐ 2. 已通过对应场景的估值路径")
    typer.echo("  ☐ 3. 市值反算正常（如适用）")
    typer.echo("  ☐ 4. 明确归零风险")
    typer.echo("")

    typer.echo("=" * 60)
