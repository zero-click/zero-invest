# -*- coding: utf-8 -*-
"""北向资金板块排行命令"""

from typing import Annotated

import typer

from . import cf_app
from ..helpers import print_banner, _fmt_amount


def print_northbound_sector_rank(result: dict):
    """打印北向资金板块排行"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    board_type = result.get('board_type', '')
    indicator = result.get('indicator', '')
    report_date = result.get('report_date', '')
    items = result.get('data', [])

    if not items:
        print("  ℹ️  暂无排行数据（非交易日可能无数据）")
        return

    print(f"  🏆 北向资金{board_type}排行（{indicator}，报告期: {report_date}）")
    print("  " + "-" * 90)
    print(f"  {'排名':<6}{'板块名称':<14}{'涨跌幅%':<10}{'持股市值(亿)':<14}{'占板块比%':<12}{'增持市值(亿)':<14}{'增持增幅%':<12}")
    print("  " + "-" * 90)
    for item in items:
        rank = item.get('rank', '')
        name = item.get('name', 'N/A')
        change = item.get('change_pct', 'N/A')
        holding_mcap = _fmt_amount(item.get('holding_market_cap'))
        holding_ratio = item.get('holding_ratio')
        increase_mcap = _fmt_amount(item.get('increase_market_cap'))
        increase_change = item.get('increase_market_cap_change')

        holding_ratio_str = f"{holding_ratio:.2f}" if holding_ratio is not None else "N/A"
        increase_change_str = f"{increase_change:.2f}" if increase_change is not None else "N/A"

        print(f"  {rank:<6}{name:<14}{str(change):<10}{holding_mcap:<14}{holding_ratio_str:<12}{increase_mcap:<14}{increase_change_str:<12}")
    print()


@cf_app.command("sector-rank")
def sector_rank(
    indicator: Annotated[
        str,
        typer.Option("--indicator", "-i", help="资金指标周期",
                      case_sensitive=False),
    ] = "今日",
    board_type: Annotated[
        str,
        typer.Option("--board-type", "-b", help="板块类型",
                      case_sensitive=False),
    ] = "行业板块",
    top: int = typer.Option(15, "--top", "-n", help="显示前N名（默认: 15，最大 50）"),
):
    """北向资金板块排行"""
    from fund_tools import get_northbound_sector_rank

    # 参数校验
    _valid_indicators = ["今日", "3日", "5日", "10日", "1月", "1季", "1年"]
    _valid_board_types = ["行业板块", "概念板块"]

    if indicator not in _valid_indicators:
        print(f"  ❌ 无效的指标周期: {indicator}，可选: {', '.join(_valid_indicators)}")
        raise typer.Exit(code=1)
    if board_type not in _valid_board_types:
        print(f"  ❌ 无效的板块类型: {board_type}，可选: {', '.join(_valid_board_types)}")
        raise typer.Exit(code=1)

    print_banner()
    print(f"🏆 北向资金板块排行: {board_type}({indicator})")
    print()

    result = get_northbound_sector_rank(
        indicator=indicator,
        board_type=board_type,
        top_n=top,
    )
    print_northbound_sector_rank(result)
