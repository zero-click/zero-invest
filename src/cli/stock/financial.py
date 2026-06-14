# -*- coding: utf-8 -*-
"""财务数据查询命令"""

import typer
from src.fund_tools.stock import (
    get_stock_profit_sheet,
    get_stock_cash_flow,
    get_stock_balance_sheet,
)
from src.cli.helpers import print_banner

financial_app = typer.Typer(help="财务数据查询")


@financial_app.command("profit")
def profit(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询利润表数据（营业收入、净利润等）"""
    print_banner("利润表数据")

    result = get_stock_profit_sheet(code)
    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']
    typer.echo(f"  股票代码: {code}")
    typer.echo(f"  报告期: {data.get('报告期', 'N/A')}")
    typer.echo(f"  营业收入: {data.get('营业收入', 'N/A')} 亿元")
    typer.echo(f"  营业成本: {data.get('营业成本', 'N/A')} 亿元")
    typer.echo(f"  净利润: {data.get('净利润', 'N/A')} 亿元")
    if data.get('EBITDA'):
        typer.echo(f"  EBITDA: {data.get('EBITDA')} 亿元")


@financial_app.command("cashflow")
def cashflow(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询现金流量表数据（自由现金流）"""
    print_banner("现金流量表数据")

    result = get_stock_cash_flow(code)
    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']
    typer.echo(f"  股票代码: {code}")
    typer.echo(f"  报告期: {data.get('报告期', 'N/A')}")
    typer.echo(f"  经营活动现金流: {data.get('经营活动现金流', 'N/A')} 亿元")
    typer.echo(f"  资本支出: {data.get('资本支出', 'N/A')} 亿元")
    typer.echo(f"  自由现金流: {data.get('自由现金流', 'N/A')} 亿元")


@financial_app.command("balance")
def balance(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询资产负债表数据（存货、负债、现金）"""
    print_banner("资产负债表数据")

    result = get_stock_balance_sheet(code)
    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']
    typer.echo(f"  股票代码: {code}")
    typer.echo(f"  报告期: {data.get('报告期', 'N/A')}")
    typer.echo(f"  存货: {data.get('存货', 'N/A')} 亿元")
    typer.echo(f"  总负债: {data.get('总负债', 'N/A')} 亿元")
    typer.echo(f"  货币资金: {data.get('货币资金', 'N/A')} 亿元")
    typer.echo(f"  总资产: {data.get('总资产', 'N/A')} 亿元")


@financial_app.command("all")
def all_financial(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询财务三表完整数据"""
    print_banner("财务三表完整数据")

    # 利润表
    profit_result = get_stock_profit_sheet(code)
    # 现金流量表
    cash_result = get_stock_cash_flow(code)
    # 资产负债表
    balance_result = get_stock_balance_sheet(code)

    if profit_result['status'] == 'error':
        typer.echo(f"  ❌ 利润表: {profit_result['message']}")

    if cash_result['status'] == 'error':
        typer.echo(f"  ❌ 现金流量表: {cash_result['message']}")

    if balance_result['status'] == 'error':
        typer.echo(f"  ❌ 资产负债表: {balance_result['message']}")

    if profit_result['status'] == 'error' or cash_result['status'] == 'error' or balance_result['status'] == 'error':
        raise typer.Exit(1)

    # 利润表
    typer.echo("【利润表】")
    p_data = profit_result['data']
    typer.echo(f"  报告期: {p_data.get('报告期', 'N/A')}")
    typer.echo(f"  营业收入: {p_data.get('营业收入', 'N/A')} 亿元")
    typer.echo(f"  营业成本: {p_data.get('营业成本', 'N/A')} 亿元")
    typer.echo(f"  净利润: {p_data.get('净利润', 'N/A')} 亿元")
    if p_data.get('EBITDA'):
        typer.echo(f"  EBITDA: {p_data.get('EBITDA')} 亿元")

    typer.echo("")

    # 现金流量表
    typer.echo("【现金流量表】")
    c_data = cash_result['data']
    typer.echo(f"  报告期: {c_data.get('报告期', 'N/A')}")
    typer.echo(f"  经营活动现金流: {c_data.get('经营活动现金流', 'N/A')} 亿元")
    typer.echo(f"  资本支出: {c_data.get('资本支出', 'N/A')} 亿元")
    typer.echo(f"  自由现金流: {c_data.get('自由现金流', 'N/A')} 亿元")

    typer.echo("")

    # 资产负债表
    typer.echo("【资产负债表】")
    b_data = balance_result['data']
    typer.echo(f"  报告期: {b_data.get('报告期', 'N/A')}")
    typer.echo(f"  存货: {b_data.get('存货', 'N/A')} 亿元")
    typer.echo(f"  总负债: {b_data.get('总负债', 'N/A')} 亿元")
    typer.echo(f"  货币资金: {b_data.get('货币资金', 'N/A')} 亿元")
    typer.echo(f"  总资产: {b_data.get('总资产', 'N/A')} 亿元")
