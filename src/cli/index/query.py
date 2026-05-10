# -*- coding: utf-8 -*-
"""指数查询命令"""

import typer

from . import index_app
from ..helpers import print_banner


def print_index_query(details: dict):
    """打印指数查询数据（基本信息 + 当前值 + 业绩表现）"""
    if details.get('status') == 'error':
        print(f"  ❌ {details.get('message')}")
        return

    print()
    print("  📊 基本信息")
    print("  " + "-" * 60)
    print(f"  指数代码:  {details.get('代码', '')}")
    print(f"  指数名称:  {details.get('名称', '')}")
    print(f"  指数分类:  {details.get('分类', '')}")
    print(f"  指数类别:  {details.get('指数类别', '')}")
    print(f"  发布日期:  {details.get('发布日期', 'N/A')}")

    print()
    print("  💹 当前值")
    print("  " + "-" * 60)
    print(f"  收盘点位:  {details.get('收盘点位', 'N/A')}")
    print(f"  日期:  {details.get('日期', 'N/A')}")
    print(f"  涨跌幅:  {details.get('涨跌幅', 'N/A')}%")

    # 业绩表现
    print()
    print("  📈 业绩表现")
    print("  " + "-" * 60)
    performance_items = [
        ("1周_收益率", "1周"),
        ("1月_收益率", "1月"),
        ("3月_收益率", "3月"),
        ("6月_收益率", "6月"),
        ("1年_收益率", "1年"),
        ("3年_收益率", "3年"),
        ("今年收益率", "今年"),
    ]
    for key, label in performance_items:
        value = details.get(key)
        if value is not None:
            print(f"  {label}收益率:  {value}%")
        else:
            print(f"  {label}收益率:  N/A")


@index_app.command("query")
def query(
    code: str = typer.Argument(..., help="6位指数代码"),
    detail: bool = typer.Option(False, "--detail", "-d",
                                help="显示完整信息（额外包含估值和风险分析）"),
):
    """查看指数查询信息（基本信息、当前值、业绩）"""
    from fund_tools import (
        get_index_query,
        get_index_query_window,
        get_index_valuation,
        get_index_risk,
    )

    print_banner()
    print(f"📊 查询指数: {code}")
    print()

    # 复用历史数据，避免重复网络调用
    from fund_tools.index import fetch_index_history_data, _get_index_context

    index_info = _get_index_context(code)
    if detail:
        # 使用时间窗口获取历史数据
        query_start_date, query_end_date = get_index_query_window()
        df_hist = fetch_index_history_data(
            code,
            start_date=query_start_date,
            end_date=query_end_date
        )
    else:
        df_hist = None

    query_result = get_index_query(code, df_hist=df_hist, index_info=index_info)
    print_index_query(query_result)

    if detail and query_result.get("status") == "success":
        valuation = get_index_valuation(code, df_hist=df_hist, index_info=index_info)
        from .valuation import print_index_valuation
        print_index_valuation(valuation)

        risk_result = get_index_risk(code, df_hist=df_hist)
        from .risk import print_index_risk
        print_index_risk(risk_result)
