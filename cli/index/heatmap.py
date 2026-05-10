# -*- coding: utf-8 -*-
"""指数估值热力图命令"""

import typer

from cli.index import index_app
from cli.helpers import print_banner


def print_index_heatmap(result: dict, limit: int = 30):
    """打印指数估值热力图"""
    from fund_tools import format_heatmap_table

    if not result or result.get("total", 0) == 0:
        print("  ℹ️  未获取到热力图数据")
        return
    print(format_heatmap_table(result, limit=limit))


@index_app.command("heatmap")
def heatmap(
    heatmap_category: str = typer.Option("全部", "--category", help="分类筛选（默认: 全部）"),
    sort_by: str = typer.Option(
        "pe", "--sort-by",
        help="排序字段（默认: pe）",
    ),
    limit: int = typer.Option(30, "--limit", help="显示条数（默认: 30）"),
    use_csrc: bool = typer.Option(False, "--CSRC", help="改为输出证监会行业静态PE热力图"),
):
    """查看指数估值热力图"""
    from fund_tools import get_valuation_heatmap, get_csrc_valuation_heatmap

    print_banner()
    report_name = "证监会行业静态PE热力图" if use_csrc else "指数估值热力图"
    print(f"📈 查询{report_name}: 分类={heatmap_category} 排序={sort_by}")
    print()

    if use_csrc:
        result = get_csrc_valuation_heatmap(category=heatmap_category, sort_by=sort_by)
    else:
        result = get_valuation_heatmap(category=heatmap_category, sort_by=sort_by)
    print_index_heatmap(result, limit=limit)
