# -*- coding: utf-8 -*-
"""北向资金板块排行命令"""

from typing import Annotated, Optional

import typer

from . import cf_app
from ..helpers import print_banner, _fmt_amount


def print_northbound_sector_rank(result: dict):
    """打印北向资金板块排行"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get('data', {})
    direction = data.get('direction', '')
    indicator = data.get('indicator', '')
    board_type = data.get('board_type', '')

    items = data.get('items', [])
    if not items:
        print("  ℹ️  暂无排行数据（非交易日可能无数据）")
        return

    print(f"  🏆 {direction} {board_type}排行（{indicator}资金）")
    print("  " + "-" * 80)
    print(f"  {'排名':<6}{'板块名称':<18}{'涨跌幅%':<10}{'净买额(亿)':<14}{'净流入(亿)':<14}{'上涨数':<8}{'下跌数':<8}")
    print("  " + "-" * 80)
    for i, item in enumerate(items, 1):
        name = item.get('name', 'N/A')
        change = item.get('change_pct', 'N/A')
        net_buy = _fmt_amount(item.get('net_buy_amount'))
        net_flow = _fmt_amount(item.get('net_flow_amount'))
        up = item.get('up_count', 'N/A')
        down = item.get('down_count', 'N/A')
        print(f"  {i:<6}{name:<18}{str(change):<10}{net_buy:<14}{net_flow:<14}{str(up):<8}{str(down):<8}")
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
    direction: Annotated[
        str,
        typer.Option("--direction", "-d", help="资金方向",
                      case_sensitive=False),
    ] = "北向",
    top: int = typer.Option(15, "--top", "-n", help="显示前N名（默认: 15，最大 50）"),
):
    """北向资金板块排行"""
    from fund_tools import get_northbound_sector_rank

    # 参数校验（等价于原 argparse choices）
    _valid_indicators = ["今日", "3日", "5日", "10日", "1月", "1季", "1年"]
    _valid_board_types = ["行业板块", "概念板块"]
    _valid_directions = ["北向", "沪股通", "深股通"]

    if indicator not in _valid_indicators:
        print(f"  ❌ 无效的指标周期: {indicator}，可选: {', '.join(_valid_indicators)}")
        raise typer.Exit(code=1)
    if board_type not in _valid_board_types:
        print(f"  ❌ 无效的板块类型: {board_type}，可选: {', '.join(_valid_board_types)}")
        raise typer.Exit(code=1)
    if direction not in _valid_directions:
        print(f"  ❌ 无效的资金方向: {direction}，可选: {', '.join(_valid_directions)}")
        raise typer.Exit(code=1)

    print_banner()
    print(f"🏆 北向资金板块排行: {direction} {board_type}({indicator})")
    print()

    result = get_northbound_sector_rank(
        indicator=indicator,
        board_type=board_type,
        direction=direction,
        top_n=top,
    )
    print_northbound_sector_rank(result)
