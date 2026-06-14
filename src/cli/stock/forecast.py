# -*- coding: utf-8 -*-
"""预测数据查询命令"""

import typer
from src.fund_tools.stock import (
    get_stock_profit_forecast,
    get_stock_share_change,
    get_stock_report_date,
)
from src.cli.helpers import print_banner

forecast_app = typer.Typer(help="预测数据查询")


@forecast_app.command("profit-forecast")
def profit_forecast(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询分析师盈利预测"""
    print_banner("分析师盈利预测")

    result = get_stock_profit_forecast(code)
    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']
    typer.echo(f"  股票代码: {code}")
    typer.echo(f"  机构覆盖数: {data.get('机构覆盖数', 'N/A')} 家")
    buy = data.get('评级_买入', 0)
    add = data.get('评级_增持', 0)
    if buy or add:
        typer.echo(f"  评级分布: 买入{int(buy) if buy else 0} / 增持{int(add) if add else 0}")
    def _eps(val):
        return f"{val:.2f}" if val is not None else "N/A"
    eps = [data.get(y) for y in ('2025E_EPS', '2026E_EPS', '2027E_EPS', '2028E_EPS')]
    typer.echo(f"  EPS预测: 2025E {_eps(eps[0])} / 2026E {_eps(eps[1])} / 2027E {_eps(eps[2])} / 2028E {_eps(eps[3])}")


@forecast_app.command("share-change")
def share_change(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询股本变动情况（稀释率）"""
    print_banner("股本变动情况")

    result = get_stock_share_change(code)
    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    data = result['data']
    typer.echo(f"  股票代码: {code}")
    typer.echo(f"  公告日期: {data.get('公告日期', 'N/A')}")
    typer.echo(f"  变动前总股本: {data.get('变动前总股本', 'N/A')} 万股")
    typer.echo(f"  变动后总股本: {data.get('变动后总股本', 'N/A')} 万股")
    typer.echo(f"  变动数量: {data.get('变动数量', 'N/A')} 万股")
    if data.get('稀释率') is not None:
        typer.echo(f"  稀释率: {data.get('稀释率', 'N/A'):.2f}%")
    typer.echo(f"  变动原因: {data.get('变动原因', 'N/A')}")


@forecast_app.command("report-date")
def report_date(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询财报披露日期"""
    print_banner("财报披露日期")

    result = get_stock_report_date(code)
    if result['status'] == 'error':
        typer.echo(f"  ❌ {result['message']}")
        raise typer.Exit(1)

    disclosures = result.get('data', {}).get('最近披露', [])
    typer.echo(f"  股票代码: {code}")
    typer.echo("")

    for i, disc in enumerate(disclosures[:5], 1):
        typer.echo(f"  [{i}] {disc.get('报告期', 'N/A')}")
        typer.echo(f"      实际披露日期: {disc.get('实际披露日期', 'N/A')}")
        typer.echo(f"      类型: {disc.get('报告类型', 'N/A')}")
        typer.echo("")


@forecast_app.command("all")
def all_forecast(
    code: str = typer.Argument(..., help="股票代码"),
):
    """查询所有预测相关数据"""
    print_banner("预测数据汇总")

    # 盈利预测
    profit_result = get_stock_profit_forecast(code)
    # 股本变动
    share_result = get_stock_share_change(code)
    # 财报披露日期
    date_result = get_stock_report_date(code)

    # 盈利预测
    if profit_result['status'] == 'success':
        typer.echo("【分析师预测】")
        data = profit_result['data']
        typer.echo(f"  机构覆盖数: {data.get('机构覆盖数', 'N/A')} 家")
        buy = data.get('评级_买入', 0)
        add = data.get('评级_增持', 0)
        if buy or add:
            typer.echo(f"  评级分布: 买入{int(buy) if buy else 0} / 增持{int(add) if add else 0}")
        def _eps(val):
            return f"{val:.2f}" if val is not None else "N/A"
        eps26 = data.get('2026E_EPS')
        eps27 = data.get('2027E_EPS')
        typer.echo(f"  EPS预测: 2026E {_eps(eps26)} / 2027E {_eps(eps27)}")
    else:
        typer.echo(f"  ❌ 分析师预测: {profit_result['message']}")

    typer.echo("")

    # 股本变动
    if share_result['status'] == 'success':
        typer.echo("【股本变动】")
        data = share_result['data']
        typer.echo(f"  公告日期: {data.get('公告日期', 'N/A')}")
        typer.echo(f"  变动前总股本: {data.get('变动前总股本', 'N/A')} 万股")
        typer.echo(f"  变动后总股本: {data.get('变动后总股本', 'N/A')} 万股")
        if data.get('稀释率') is not None:
            typer.echo(f"  稀释率: {data.get('稀释率', 'N/A'):.2f}%")
        typer.echo(f"  变动原因: {data.get('变动原因', 'N/A')}")
    else:
        typer.echo(f"  ❌ 股本变动: {share_result['message']}")

    typer.echo("")

    # 财报披露日期
    if date_result['status'] == 'success':
        typer.echo("【财报披露日期】")
        disclosures = date_result.get('data', {}).get('最近披露', [])
        for i, disc in enumerate(disclosures[:3], 1):
            typer.echo(f"  [{i}] {disc.get('报告期', 'N/A')} - {disc.get('实际披露日期', 'N/A')}")
    else:
        typer.echo(f"  ❌ 财报披露日期: {date_result['message']}")
