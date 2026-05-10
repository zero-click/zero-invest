# -*- coding: utf-8 -*-
"""指数估值命令"""

import typer

from cli.index import index_app
from cli.helpers import print_banner


def print_index_valuation(details: dict):
    """打印指数估值数据"""
    if details.get('status') == 'error':
        print(f"  ❌ {details.get('message')}")
        return

    # 估值数据
    print()
    print("  💰 估值数据")
    print("  " + "-" * 60)
    pe = details.get('PE_TTM')
    pb = details.get('PB')
    if pe is not None:
        print(f"  PE-TTM:  {pe}")
    if pb is not None:
        print(f"  PB:  {pb}")

    # 股息率
    div_yield_1 = details.get('股息率1')
    div_yield_2 = details.get('股息率2')
    if div_yield_1 is not None or div_yield_2 is not None:
        print()
        print("  💵 股息率")
        print("  " + "-" * 60)
        if div_yield_1 is not None:
            print(f"  股息率1 (价格):  {div_yield_1}%")
        if div_yield_2 is not None:
            print(f"  股息率2 (净值):  {div_yield_2}%")

    # 历史分位
    if 'PE分位_10年' in details:
        print()
        print("  📊 历史分位")
        print("  " + "-" * 60)
        percentile_items = [
            ("PE分位_3年", "PE(3年)"),
            ("PE分位_5年", "PE(5年)"),
            ("PE分位_10年", "PE(10年)"),
            ("PB分位_3年", "PB(3年)"),
            ("PB分位_5年", "PB(5年)"),
            ("PB分位_10年", "PB(10年)"),
        ]
        for key, label in percentile_items:
            value = details.get(key)
            if value is not None and value >= 0:
                print(f"  {label}:  {value}%")

    # 历史参考
    reference_items = [
        ("PE参考_10年", "PE-TTM"),
        ("PB参考_10年", "PB"),
    ]
    if any(details.get(key) for key, _ in reference_items):
        print()
        print("  📏 10年历史参考")
        print("  " + "-" * 60)
        for key, label in reference_items:
            reference = details.get(key)
            if not reference:
                continue
            current = reference.get("当前")
            median = reference.get("中位数")
            low = reference.get("最低")
            high = reference.get("最高")
            print(f"  {label}:  当前 {current} | 中位数 {median} | 最低 {low} | 最高 {high}")

    # 估值等级
    pe_level = details.get('PE估值等级') or details.get('估值等级_PE')
    pb_level = details.get('PB估值等级') or details.get('估值等级_PB')
    valuation_level = details.get('估值等级')
    if (pe_level and pe_level != "N/A") or (pb_level and pb_level != "N/A") or (
        valuation_level and valuation_level != "N/A"
    ):
        print()
        print("  🌡️  估值温度")
        print("  " + "-" * 60)
        if pe_level and pe_level != "N/A":
            print(f"  PE口径:  {pe_level}")
        if pb_level and pb_level != "N/A":
            print(f"  PB口径:  {pb_level}")
        elif valuation_level and valuation_level != "N/A":
            print(f"  兼容字段估值等级:  {valuation_level}")

    # 口径与规则
    valuation_method = details.get('估值口径')
    valuation_rule = details.get('估值规则')
    if valuation_method or valuation_rule:
        print()
        print("  🧭 口径与规则")
        print("  " + "-" * 60)
        if valuation_method:
            for key, value in valuation_method.items():
                print(f"  {key}:  {value}")
        if valuation_rule:
            print(f"  估值判断:  {valuation_rule}")

    # 数据来源
    print()
    print(f"  📍 数据源:  {details.get('估值数据源', 'N/A')}")
    print(f"  📈 数据点数:  {details.get('数据点数', 'N/A')}")


@index_app.command("valuation")
def valuation(
    code: str = typer.Argument(..., help="6位指数代码"),
):
    """查看指数估值信息"""
    from fund_tools import get_index_valuation

    print_banner()
    print(f"💰 查询指数估值: {code}")
    print()

    result = get_index_valuation(code)
    print_index_valuation(result)
