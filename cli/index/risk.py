# -*- coding: utf-8 -*-
"""指数风险分析命令"""

import typer

from cli.index import index_app
from cli.helpers import print_banner


def print_index_risk(risk: dict):
    """打印指数风险分析"""
    if risk.get('status') == 'error':
        print(f"  ❌ {risk.get('message')}")
        return

    print()
    print("  ⚠️  指数风险分析")
    print("  " + "-" * 60)

    # 基本信息
    print(f"  指数代码:  {risk.get('代码', '')}")
    name = risk.get('名称')
    if name:
        print(f"  指数名称:  {name}")

    # 收益率
    print()
    print("  📈 收益率")
    print("  " + "-" * 60)
    for period in ["近1月收益率", "近3月收益率", "近6月收益率", "近1年收益率"]:
        value = risk.get(period)
        if value is not None:
            print(f"  {period}:  {value}%")
        else:
            print(f"  {period}:  N/A")

    # 波动率
    print()
    print("  📊 波动率（年化）")
    print("  " + "-" * 60)
    for vol_key in ["近1年波动率", "近3年波动率", "历史波动率"]:
        value = risk.get(vol_key)
        if value is not None:
            print(f"  {vol_key}:  {value}%")

    # 最大回撤
    print()
    print("  📉 最大回撤")
    print("  " + "-" * 60)
    max_dd = risk.get('最大回撤')
    if max_dd is not None:
        print(f"  最大回撤幅度:  {max_dd}%")
        print(f"  回撤开始日期:  {risk.get('回撤开始日期', 'N/A')}")
        print(f"  回撤最低日期:  {risk.get('回撤最低日期', 'N/A')}")
        print(f"  回撤持续天数:  {risk.get('回撤持续天数', 'N/A')}")
        recovery_date = risk.get('回撤修复日期')
        if recovery_date:
            print(f"  回撤修复日期:  {recovery_date}")
            print(f"  回撤修复天数:  {risk.get('回撤修复天数', 'N/A')}")
        else:
            unrecovered_days = risk.get('未恢复天数')
            if unrecovered_days:
                print(f"  尚未恢复（已过 {unrecovered_days} 天）")

    # 回撤修复分析
    recovery_analysis = risk.get('回撤修复分析')
    if recovery_analysis:
        print()
        print("  🔁 历史回撤修复周期")
        print("  " + "-" * 60)
        print(f"  显著回撤次数:  {recovery_analysis.get('显著回撤次数', 'N/A')}")
        print(f"  平均修复天数:  {recovery_analysis.get('平均回撤修复天数', 'N/A')}")
        print(f"  最长修复天数:  {recovery_analysis.get('最长回撤修复天数', 'N/A')}")
        print(f"  最短修复天数:  {recovery_analysis.get('最短回撤修复天数', 'N/A')}")
        print(f"  未恢复回撤数:  {recovery_analysis.get('未恢复回撤数', 'N/A')}")

    # 夏普比率
    sharpe = risk.get('夏普比率')
    if sharpe is not None:
        print()
        print("  📊 夏普比率（风险调整后收益）")
        print("  " + "-" * 60)
        print(f"  夏普比率:  {sharpe}")
        print(f"  说明:  数值越高，单位风险下的超额收益越高")
        print(f"        >1 为优秀，0.5-1 为良好，<0.5 为一般")

    # 数据范围
    print()
    print("  📈 数据范围")
    print("  " + "-" * 60)
    print(f"  数据起始日期:  {risk.get('数据起始日期', 'N/A')}")
    print(f"  数据截止日期:  {risk.get('数据截止日期', 'N/A')}")
    print(f"  数据点数:  {risk.get('数据点数', 'N/A')}")


@index_app.command("risk")
def risk(
    code: str = typer.Argument(..., help="6位指数代码"),
):
    """查看指数风险分析"""
    from fund_tools import get_index_risk

    print_banner()
    print(f"⚠️  查询指数风险分析: {code}")
    print()

    result = get_index_risk(code)
    print_index_risk(result)
