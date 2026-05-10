# -*- coding: utf-8 -*-
"""基金查询命令（标准/完整模式）"""

import typer

from . import bond_app
from ..helpers import print_banner, get_current_year


def print_fund_details(details: dict):
    """美式打印基金详情"""
    if details.get('status') == 'error':
        print(f"  ❌ {details.get('message')}")
        return

    print()
    print("  📋 基本信息")
    print("  " + "-" * 60)
    print(f"  基金代码:  {details.get('code', '')}")
    print(f"  基金名称:  {details.get('name', '')}")
    print(f"  基金类型:  {details.get('type', '')}")
    print(f"  成立日期:  {details.get('inception_date', 'N/A')}")
    print(f"  基金规模:  {details.get('scale', 'N/A')}")

    # 基金经理
    managers = details.get('managers', [])
    if managers:
        print(f"  基金经理:  {', '.join([m['姓名'] for m in managers])}")
    else:
        print("  基金经理:  N/A")

    # 费率
    fee_rates = details.get('fee_rates', {})
    if fee_rates:
        print("  💰 费率信息")
        print("  " + "-" * 60)
        for key, value in fee_rates.items():
            print(f"    {key}: {value}")

    # 业绩表现
    performance = details.get('performance', {})
    if performance:
        print()
        print("  📈 业绩表现")
        print("  " + "-" * 60)
        for period, return_rate in list(performance.items())[:6]:
            print(f"    {period}: {return_rate}")

    # 风险指标
    risk_metrics = details.get('risk_metrics')
    if risk_metrics:
        print()
        print("  ⚠️  风险指标")
        print("  " + "-" * 60)
        for key, value in risk_metrics.items():
            print(f"    {key}: {value}")

    # 十大重仓股
    holdings = details.get('top_holdings', [])
    if holdings:
        print()
        print("  💼 十大重仓股")
        print("  " + "-" * 60)
        for i, holding in enumerate(holdings[:10], 1):
            # holding 可能是字典或字符串
            if isinstance(holding, dict):
                name = holding.get('股票名称', 'N/A')
                code = holding.get('股票代码', '')
                pct = holding.get('占净值比例', 0)
                if isinstance(pct, (int, float)):
                    print(f"    {i:2d}. {name:<12s} {code:<10s} {pct:.2f}%")
                else:
                    print(f"    {i:2d}. {name:<12s} {code:<10s} {pct}")
            elif isinstance(holding, str):
                # 字符串格式: "股票名称 (占比)"
                print(f"    {i:2d}. {holding}")

    # 基金经理详情
    manager_details = details.get('manager_details')
    if manager_details:
        print()
        print("  👤 基金经理详情")
        print("  " + "-" * 60)
        print(f"  姓名: {manager_details.get('姓名', 'N/A')}")
        print(f"  从业年限: {manager_details.get('从业年限', 'N/A')}")
        print(f"  管理规模: {manager_details.get('管理规模', 'N/A')}")
        print(f"  最佳回报: {manager_details.get('最佳回报', 'N/A')}")
        print(f"  现任基金: {manager_details.get('现任基金', 'N/A')}")

    # 费用详情
    fee_details = details.get('fee_details')
    if fee_details:
        print()
        print("  💸 费用详情")
        print("  " + "-" * 60)
        subitem = fee_details.get('申购费', {})
        if subitem:
            print(f"  申购费率: ")
            for amount, rate in subitem.items():
                print(f"    {amount}: {rate}")
        subitem = fee_details.get('赎回费', {})
        if subitem:
            print(f"  赎回费率: ")
            for period, rate in subitem.items():
                print(f"    持有{period}: {rate}")
        print(f"  管理费率: {fee_details.get('管理费', 'N/A')}")
        print(f"  托管费率: {fee_details.get('托管费', 'N/A')}")

    # 流动性信息
    liquidity = details.get('liquidity')
    if liquidity:
        print()
        print("  💧 流动性信息")
        print("  " + "-" * 60)
        for key, value in liquidity.items():
            print(f"  {key}: {value}")


@bond_app.command("query")
def query(
    code: str = typer.Argument(..., help="6位基金代码"),
    detail: bool = typer.Option(False, "--detail", "-d",
                                help="显示完整详情（包括基金经理、持仓、配置、费用、流动性等）"),
):
    """查询基金详细信息"""
    from fund_tools import (
        query_fund_details,
        get_fund_manager_details,
        get_fund_portfolio_analysis,
        get_fund_fee_details,
        get_fund_liquidity_info,
        get_fund_rating,
    )

    print_banner()
    print(f"📊 查询基金: {code}")
    print()

    if detail:
        # 完整详情模式：调用所有查询函数
        print("=" * 70)
        print("  📋 基金完整分析报告")
        print("=" * 70)
        print()

        # 1. 基本信息
        details = query_fund_details(code, year=get_current_year())
        print_fund_details(details)

        # 2. 基金经理详情
        print("=" * 70)
        print("  👤 基金经理详情")
        print("=" * 70)
        print()
        manager_result = get_fund_manager_details(code)
        print_manager_details(manager_result)

        # 3. 投资组合完整分析
        print("=" * 70)
        print("  📊 投资组合完整分析")
        print("=" * 70)
        print()
        portfolio_result = get_fund_portfolio_analysis(code, year=get_current_year())
        from .portfolio import print_portfolio_analysis
        print_portfolio_analysis(portfolio_result)

        # 4. 费用明细
        print("=" * 70)
        print("  💰 费用明细")
        print("=" * 70)
        print()
        fee_result = get_fund_fee_details(code)
        from .fee import print_fee_details
        print_fee_details(fee_result)

        # 5. 流动性信息
        print("=" * 70)
        print("  💧 流动性信息")
        print("=" * 70)
        print()
        liquidity_result = get_fund_liquidity_info(code)
        from .liquidity import print_liquidity_info
        print_liquidity_info(liquidity_result)

        # 6. 基金评级
        print("=" * 70)
        print("  ⭐ 基金评级")
        print("=" * 70)
        print()
        rating_result = get_fund_rating(code)
        if rating_result.get('status') == 'success':
            ratings = rating_result.get('ratings')
            if ratings:
                for key, value in ratings.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {rating_result.get('message', '暂无评级数据')}")
        else:
            print(f"  {rating_result.get('message', '查询失败')}")
        print()

        print("=" * 70)
        print("  ✅ 分析报告完成")
        print("=" * 70)
    else:
        # 标准模式：只显示基本信息
        details = query_fund_details(code, year=get_current_year())
        print_fund_details(details)


def print_manager_details(result: dict):
    """打印基金经理详情"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    managers = result.get('managers', [])
    if not managers:
        print("  ℹ️  未找到该基金的经理信息")
        return

    print(f"  基金经理数量: {result.get('manager_count', len(managers))}")
    print()

    for i, mgr in enumerate(managers, 1):
        print(f"  👤 经理 {i}: {mgr.get('姓名', 'N/A')}")
        print("  " + "-" * 60)
        print(f"    所属公司: {mgr.get('所属公司', 'N/A')}")
        print(f"    累计从业时间: {mgr.get('累计从业时间', 'N/A')}")
        print(f"    管理规模: {mgr.get('现任基金资产总规模', 'N/A')}")
        print(f"    最佳回报: {mgr.get('现任基金最佳回报', 'N/A')}")
        print(f"    现任基金: {mgr.get('现任基金', 'N/A')} ({mgr.get('现任基金代码', 'N/A')})")
        print()
