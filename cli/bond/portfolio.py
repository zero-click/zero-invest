# -*- coding: utf-8 -*-
"""投资组合完整分析命令"""

import typer

from cli.bond import bond_app
from cli.helpers import print_banner, get_current_year


def print_portfolio_analysis(result: dict):
    """打印投资组合完整分析"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    # 持仓集中度
    conc = result.get('concentration', {})
    if conc:
        print("  📊 持仓集中度")
        print("  " + "-" * 60)
        print(f"    前10大持仓占比: {conc.get('前10大持仓占比', 'N/A')}")
        print(f"    集中度评估: {conc.get('持仓集中度', 'N/A')}")
        print()

    # 最新持仓
    holdings = result.get('latest_top_holdings', [])
    if holdings:
        print("  💼 最新前10大持仓")
        print("  " + "-" * 60)
        for i, h in enumerate(holdings, 1):
            name = h.get('股票名称', 'N/A')
            code = h.get('股票代码', '')
            pct = h.get('占净值比例', 0)
            if isinstance(pct, (int, float)):
                print(f"    {i:2d}. {name:<12s} {code:<10s} {pct:.2f}%")
            else:
                print(f"    {i:2d}. {name:<12s} {code:<10s} {pct}")
        print()

    # 持仓变化
    changes = result.get('holdings_change_by_quarter', {})
    if changes:
        print("  📈 持仓变化趋势")
        print("  " + "-" * 60)
        for quarter, stocks in list(changes.items())[:2]:
            print(f"    {quarter}:")
            for s in stocks[:5]:
                print(f"      - {s['股票名称']}: 买入 {s['买入金额']}")
        print()

    # 行业配置
    industries = result.get('industry_allocation', [])
    if industries:
        print("  🏭 行业配置 (前5大)")
        print("  " + "-" * 60)
        for i, ind in enumerate(industries[:5], 1):
            print(f"    {i}. {ind['行业类别']:<30s} {ind['占净值比例']}")
        print()

    # 债券持仓
    bonds = result.get('bond_holdings_sample', [])
    if bonds:
        print("  🏛️  债券持仓样本")
        print("  " + "-" * 60)
        for b in bonds[:5]:
            print(f"    - {b['债券名称']}: {b['占净值比例']}")
        print()


@bond_app.command("portfolio")
def portfolio(
    code: str = typer.Argument(..., help="6位基金代码"),
):
    """投资组合完整分析"""
    from fund_tools import get_fund_portfolio_analysis

    print_banner()
    print(f"📊 投资组合分析: {code}")
    print()

    result = get_fund_portfolio_analysis(code, year=get_current_year())
    print_portfolio_analysis(result)
