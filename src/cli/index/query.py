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


def print_hk_index_spot(result: dict):
    """打印港股指数实时行情"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    data = result.get("data", [])
    source = result.get("source", "")
    note = result.get("data_delay_note", "")

    print(f"  数据源: {source} | 共 {len(data)} 个指数 | {note}")
    print()

    if not data:
        print("  ℹ️  暂无数据")
        return

    print(f"  {'代码':<10}{'名称':<16}{'最新价':<10}{'涨跌额':<10}{'涨跌幅':<10}{'今开':<10}{'最高':<10}{'最低':<10}")
    print("  " + "-" * 86)
    for item in data:
        code = str(item.get("代码", ""))
        name = str(item.get("名称", ""))[:14]
        price = item.get("最新价", "N/A")
        change = item.get("涨跌额", "N/A")
        pct = item.get("涨跌幅", "N/A")
        open_v = item.get("今开", "N/A")
        high = item.get("最高", "N/A")
        low = item.get("最低", "N/A")

        price_s = f"{price:.2f}" if isinstance(price, (int, float)) else str(price)
        change_s = f"{change:.2f}" if isinstance(change, (int, float)) else str(change)
        pct_s = f"{pct:.2f}%" if isinstance(pct, (int, float)) else str(pct)
        open_s = f"{open_v:.2f}" if isinstance(open_v, (int, float)) else str(open_v)
        high_s = f"{high:.2f}" if isinstance(high, (int, float)) else str(high)
        low_s = f"{low:.2f}" if isinstance(low, (int, float)) else str(low)

        print(f"  {code:<10}{name:<16}{price_s:<10}{change_s:<10}{pct_s:<10}{open_s:<10}{high_s:<10}{low_s:<10}")
    print()


@index_app.command("query")
def query(
    code: str = typer.Argument("", help="6位指数代码"),
    detail: bool = typer.Option(False, "--detail", "-d",
                                help="显示完整信息（额外包含估值和风险分析）"),
    hk: bool = typer.Option(False, "--hk", help="查询港股指数实时行情"),
):
    """查看指数信息

    内地指数：需指定 CODE，显示基本信息、当前值、业绩（支持 --detail 展开估值和风险）
    港股指数（--hk）：无需 CODE，显示港股主要指数实时行情

    示例:
      python cli.py index query 000001         # 查询沪深300
      python cli.py index query 000001 --detail # 含估值+风险
      python cli.py index query --hk            # 港股指数行情
    """
    print_banner()

    if hk:
        from fund_tools import get_hk_index_spot

        print(f"📊 港股指数实时行情")
        print()

        result = get_hk_index_spot()
        print_hk_index_spot(result)
    elif not code:
        print("  ❌ 查询内地指数需要指定指数代码")
        print("  示例: python cli.py index query 000001")
        print("  港股: python cli.py index query --hk")
        raise typer.Exit(code=1)
    else:
        from fund_tools import (
            get_index_query,
            get_index_query_window,
            get_index_valuation,
            get_index_risk,
        )

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
