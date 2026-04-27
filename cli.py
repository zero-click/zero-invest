# -*- coding: utf-8 -*-
"""
基金和指数信息查询命令行工具 v2.2
使用子命令命名空间：bond (基金) 和 index (指数)
"""

import argparse
import logging
import os
import sys
import pandas as pd
from datetime import datetime

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fund_tools import (
    # 基金相关
    search_funds,
    query_fund_details,
    get_fund_rankings,
    get_fund_rating,
    get_fund_risk_metrics,
    get_fund_performance,
    get_fund_top_holdings,
    get_fund_manager_details,
    get_fund_holdings_analysis,
    get_fund_asset_allocation,
    get_fund_portfolio_analysis,
    get_fund_fee_details,
    get_fund_liquidity_info,
    get_fund_list,
    FUND_DB_FILE,
    # 指数相关
    get_index_list,
    update_index_cache,
    search_indices_all,
    get_index_query,
    get_index_valuation,
    get_index_candidate_funds,
    get_index_details_batch,
    get_index_risk,
    get_valuation_heatmap,
    format_heatmap_table,
    INDEX_DB_FILE,
)

logger = logging.getLogger(__name__)


# ============================================================================
# 工具函数
# ============================================================================

def get_current_year() -> str:
    """获取当前年份作为字符串"""
    return str(datetime.now().year)


# ============================================================================
# 打印横幅
# ============================================================================

def print_banner():
    """打印横幅"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                📊 中国基金和指数信息查询工具 v2.2                         ║
║                基于 akshare + MCP Python SDK                           ║
║                                                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")


# ============================================================================
# 基金相关打印函数
# ============================================================================

def print_fund_search_results(results: list, show_all: bool = False):
    """美式打印基金搜索结果"""
    if not results:
        print("  ℹ️  未找到匹配的基金")
        return

    count = len(results)
    display_count = count if show_all else min(10, count)

    print(f"  查找到 {count} 只基金 (显示前 {display_count} 只):")
    print()
    print(f"  {'序号':<6}{'基金代码':<12}{'基金名称':<25}{'基金类型':<20}")
    print("  " + "-" * 65)

    for i, fund in enumerate(results[:display_count], 1):
        code = fund.get('基金代码', '')
        name = fund.get('基金简称', '')
        fund_type = fund.get('基金类型', '')

        # 截断过长的名称
        if len(name) > 23:
            name = name[:20] + '...'

        print(f"  {i:<6}{code:<12}{name:<25}{fund_type:<20}")

    if count > display_count:
        print(f"  ... 还有 {count - display_count} 只基金")


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


# ============================================================================
# 指数相关打印函数
# ============================================================================

def print_index_search_results(results: list, show_all: bool = False):
    """打印指数搜索结果"""
    if not results:
        print("  ℹ️  未找到匹配的指数")
        return

    count = len(results)
    display_count = count if show_all else min(15, count)

    print(f"  查找到 {count} 个指数 (显示前 {display_count} 个):")
    print()
    print(f"  {'序号':<6}{'代码':<10}{'名称':<20}{'分类':<12}{'指数类别':<10}")
    print("  " + "-" * 70)

    for i, idx in enumerate(results[:display_count], 1):
        code = idx.get('code', '')
        name = idx.get('name', '')
        category = idx.get('category', '')
        index_class = idx.get('index_class', '')

        # 截断过长的名称
        if len(name) > 18:
            name = name[:15] + '...'

        print(f"  {i:<6}{code:<10}{name:<20}{category:<12}{index_class:<10}")

    if count > display_count:
        print(f"  ... 还有 {count - display_count} 个指数")


def print_index_info(info: dict):
    """打印指数基本信息"""
    if not info:
        print("  ❌ 未找到该指数")
        return

    print()
    print("  📊 基本信息")
    print("  " + "-" * 60)
    print(f"  指数代码:  {info.get('code', '')}")
    print(f"  指数名称:  {info.get('name', '')}")
    print(f"  指数分类:  {info.get('category', '')}")
    print(f"  指数类别:  {info.get('index_class', '')}")
    print(f"  资产类别:  {info.get('asset_class', '')}")
    print(f"  基日:  {info.get('base_date', 'N/A')}")
    print(f"  发布日期:  {info.get('publish_date', 'N/A')}")


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
    valuation_level = details.get('估值等级')
    if valuation_level and valuation_level != "N/A":
        print()
        print(f"  🌡️  估值温度:  {valuation_level}")

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


def print_index_details(details: dict):
    """打印指数完整详情（兼容旧命令）"""
    print_index_query(details)
    if details.get('status') == 'error':
        return
    print_index_valuation(details)


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


def print_index_candidate_funds(result: dict, show_all: bool = False):
    """打印指数候选基金池"""
    if result.get("status") == "error":
        print(f"  ❌ {result.get('message')}")
        return

    index_info = result.get("index", {})
    funds = result.get("funds", [])
    count = result.get("count", len(funds))
    display_count = count if show_all else min(20, count)

    print(f"  指数: {index_info.get('name', '')} ({index_info.get('code', '')})")
    print(f"  候选基金数量: {count} (显示 {display_count})")
    aliases = result.get("aliases", [])
    if aliases:
        print(f"  匹配关键词: {', '.join(aliases[:8])}")
    print()

    if not funds:
        print("  ℹ️  未找到候选基金")
        return

    print(f"  {'序号':<6}{'基金代码':<10}{'基金名称':<24}{'跟踪方式':<10}{'手续费':<8}")
    print("  " + "-" * 80)
    for i, item in enumerate(funds[:display_count], 1):
        code = str(item.get("基金代码", ""))
        name = str(item.get("基金名称", ""))
        track = str(item.get("跟踪方式", ""))
        fee = str(item.get("手续费", ""))
        if len(name) > 22:
            name = name[:19] + "..."
        print(f"  {i:<6}{code:<10}{name:<24}{track:<10}{fee:<8}")

    if count > display_count:
        print(f"  ... 还有 {count - display_count} 只基金")


def print_index_heatmap(result: dict, limit: int = 30):
    """打印指数估值热力图"""
    if not result or result.get("total", 0) == 0:
        print("  ℹ️  未获取到热力图数据")
        return
    print(format_heatmap_table(result, limit=limit))


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


def print_fee_details(result: dict):
    """打印费用明细"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    fees = result.get('fee_details', {})
    if not fees:
        print("  ℹ️  暂无费用数据")
        return

    # 运作费用
    print("  💰 运作费用")
    print("  " + "-" * 60)
    if '管理费率' in fees:
        print(f"    管理费率: {fees['管理费率']}")
    if '托管费率' in fees:
        print(f"    托管费率: {fees['托管费率']}")
    print()

    # 认购/申购费率
    if '申购费率' in fees and fees['申购费率']:
        print("  📥 申购费率")
        print("  " + "-" * 60)
        for fee in fees['申购费率']:
            amount = fee.get('适用金额', '---')
            rate = fee.get('申购费率', 'N/A')
            print(f"    {amount:<15s} {rate}")
        print()

    # 赎回费率
    if '赎回费率' in fees and fees['赎回费率']:
        print("  📤 赎回费率")
        print("  " + "-" * 60)
        for fee in fees['赎回费率']:
            period = fee.get('适用期限', 'N/A')
            rate = fee.get('赎回费率', 'N/A')
            print(f"    {period:<20s} {rate}")
        print()


def print_liquidity_info(result: dict):
    """打印流动性信息"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    info = result.get('liquidity_info', {})
    if not info:
        print("  ℹ️  暂无流动性数据")
        return

    # 申赎状态
    print("  🔄 申赎状态")
    print("  " + "-" * 60)
    print(f"    基金状态: {info.get('基金状态', 'N/A')}")
    if '申购状态' in info:
        print(f"    申购状态: {info['申购状态']}")
    if '赎回状态' in info:
        print(f"    赎回状态: {info['赎回状态']}")
    print()

    # 交易规则
    print("  📋 交易规则")
    print("  " + "-" * 60)
    print(f"    交易场所: {info.get('交易场所', 'N/A')}")
    print(f"    申赎时间: {info.get('申赎时间', 'N/A')}")
    print(f"    最低申购: {info.get('最低申购金额', 'N/A')}")
    print(f"    申购确认: {info.get('申购确认时间', 'N/A')}")
    print(f"    赎回到账: {info.get('赎回到账时间', 'N/A')}")
    print()


# ============================================================================
# 主函数
# ============================================================================

def main():
    """命令行主函数"""
    parser = argparse.ArgumentParser(
        description='中国基金和指数信息查询命令行工具 v2.2',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用示例:
  === 基金查询 (bond) ===
  1. 搜索基金:
     python cli.py bond search "华夏"

  2. 查询基金详情:
     python cli.py bond query 000001
     python cli.py bond query 000001 --detail

  3. 查看排行榜:
     python cli.py bond ranking --type 股票型 --top 10

  4. 查询基金评级:
     python cli.py bond rating 000001

  5. 查询基金经理:
     python cli.py bond manager 000001

  6. 持仓分析:
     python cli.py bond holdings 000001
     python cli.py bond portfolio 000001

  7. 更新数据库:
     python cli.py bond update

  === 指数查询 (index) ===
  1. 搜索指数:
     python cli.py index search "红利"
     python cli.py index search "300"

  2. 查看指数详情:
     python cli.py index query 000300
     python cli.py index query 000300 -d

  3. 查看指数估值:
     python cli.py index valuation 000300

  4. 查看指数风险:
     python cli.py index risk 000300

  5. 查看指数候选基金池:
     python cli.py index listfund 000300

  6. 批量查询:
     python cli.py index batch 000300 000905 000852

项目主页: https://github.com/example/ttjj-fund
        """
    )

    # 全局参数
    parser.add_argument('--debug', '-D', action='store_true',
                        help='启用调试模式，显示详细日志')

    subparsers = parser.add_subparsers(dest='category', help='查询类别: bond(基金) 或 index(指数)')

    # ============================================================
    # bond 子命令（基金相关）
    # ============================================================
    bond_parser = subparsers.add_parser('bond', help='基金相关查询')
    bond_subparsers = bond_parser.add_subparsers(dest='command', help='基金命令')

    # bond search
    search_parser = bond_subparsers.add_parser('search', help='搜索基金')
    search_parser.add_argument('keyword', type=str, help='搜索关键词（基金代码/名称/拼音）')
    search_parser.add_argument('--all', '-a', action='store_true', help='显示所有结果')

    # bond query
    query_parser = bond_subparsers.add_parser('query', help='查询基金详细信息')
    query_parser.add_argument('code', type=str, help='6位基金代码')
    query_parser.add_argument('--detail', '-d', action='store_true',
                             help='显示完整详情（包括基金经理、持仓、配置、费用、流动性等）')

    # bond ranking
    ranking_parser = bond_subparsers.add_parser('ranking', help='查看基金排行榜')
    ranking_parser.add_argument('--type', '-t', dest='fund_type',
                              default='全部',
                              choices=['全部', '股票型', '混合型', '债券型', '指数型', 'QDII', 'FOF'],
                              help='基金类型（默认: 全部）')
    ranking_parser.add_argument('--top', '-n', type=int, default=10,
                             help='显示前N名（默认: 10）')

    # bond rating
    rating_parser = bond_subparsers.add_parser('rating', help='查询基金评级')
    rating_parser.add_argument('code', type=str, help='6位基金代码')

    # bond manager
    manager_parser = bond_subparsers.add_parser('manager', help='查询基金经理深度信息')
    manager_parser.add_argument('code', type=str, help='6位基金代码')

    # bond holdings
    holdings_parser = bond_subparsers.add_parser('holdings', help='持仓动态分析')
    holdings_parser.add_argument('code', type=str, help='6位基金代码')

    # bond allocation
    alloc_parser = bond_subparsers.add_parser('allocation', help='资产配置结构')
    alloc_parser.add_argument('code', type=str, help='6位基金代码')
    alloc_parser.add_argument('--year', '-y', type=str, default=None,
                             help='年份（默认: 当前年份）')

    # bond fee
    fee_parser = bond_subparsers.add_parser('fee', help='费用明细')
    fee_parser.add_argument('code', type=str, help='6位基金代码')

    # bond liquidity
    liq_parser = bond_subparsers.add_parser('liquidity', help='流动性信息')
    liq_parser.add_argument('code', type=str, help='6位基金代码')

    # bond performance
    perf_parser = bond_subparsers.add_parser('performance', help='基金业绩')
    perf_parser.add_argument('code', type=str, help='6位基金代码')

    # bond risk
    risk_parser = bond_subparsers.add_parser('risk', help='风险指标')
    risk_parser.add_argument('code', type=str, help='6位基金代码')

    # bond top-holdings
    top_holdings_parser = bond_subparsers.add_parser('top-holdings', help='十大重仓股')
    top_holdings_parser.add_argument('code', type=str, help='6位基金代码')

    # bond portfolio
    portfolio_parser = bond_subparsers.add_parser('portfolio', help='投资组合完整分析')
    portfolio_parser.add_argument('code', type=str, help='6位基金代码')

    # bond update
    bond_subparsers.add_parser('update', help='更新基金数据库')

    # ============================================================
    # index 子命令（指数相关）
    # ============================================================
    index_parser = subparsers.add_parser('index', help='指数相关查询')
    index_subparsers = index_parser.add_subparsers(dest='command', help='指数命令')

    # index search
    index_search_parser = index_subparsers.add_parser('search', help='搜索指数')
    index_search_parser.add_argument('keyword', type=str, help='搜索关键词（指数代码/名称）')
    index_search_parser.add_argument('--all', '-a', action='store_true', help='显示所有结果')

    # index query
    index_query_parser = index_subparsers.add_parser('query', help='查看指数查询信息（基本信息、当前值、业绩）')
    index_query_parser.add_argument('code', type=str, help='6位指数代码')
    index_query_parser.add_argument('--detail', '-d', action='store_true',
                                   help='显示完整信息（额外包含估值和风险分析）')

    # index valuation
    index_valuation_parser = index_subparsers.add_parser('valuation', help='查看指数估值信息')
    index_valuation_parser.add_argument('code', type=str, help='6位指数代码')

    # index batch
    index_batch_parser = index_subparsers.add_parser('batch', help='批量查询指数详情')
    index_batch_parser.add_argument('codes', type=str, nargs='+', help='指数代码列表（多个代码用空格分隔）')

    # index risk
    index_risk_parser = index_subparsers.add_parser('risk', help='查看指数风险分析')
    index_risk_parser.add_argument('code', type=str, help='6位指数代码')

    # index listfund
    index_listfund_parser = index_subparsers.add_parser('listfund', help='查看指数候选基金池')
    index_listfund_parser.add_argument('code', type=str, help='6位指数代码')
    index_listfund_parser.add_argument('--all', '-a', action='store_true', help='显示所有候选基金')

    # index heatmap
    index_heatmap_parser = index_subparsers.add_parser('heatmap', help='查看指数估值热力图')
    index_heatmap_parser.add_argument('--category', dest='heatmap_category', type=str, default='全部',
                                      help='分类筛选（默认: 全部）')
    index_heatmap_parser.add_argument('--sort-by', type=str, default='pe',
                                      choices=['pe', 'pb', 'dividend', 'valuation', 'category'],
                                      help='排序字段（默认: pe）')
    index_heatmap_parser.add_argument('--limit', type=int, default=30, help='显示条数（默认: 30）')

    # index update
    index_subparsers.add_parser('update', help='更新指数数据库')

    args = parser.parse_args()

    # 配置日志
    log_level = logging.DEBUG if args.debug else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(levelname)s: %(message)s' if args.debug else '%(message)s'
    )

    # 检查是否提供了 category
    if not args.category:
        parser.print_help()
        return

    # ============================================================
    # 处理 bond 命令（基金）
    # ============================================================
    if args.category == 'bond':
        if not args.command:
            bond_parser.print_help()
            return

        if args.command == 'search':
            print_banner()
            print(f"🔍 搜索基金: {args.keyword}")
            print()

            result = search_funds(args.keyword)

            if result.get('status') == 'error':
                print(f"  ❌ {result['message']}")
            elif result.get('count') == 0:
                print(f"  ℹ️  未找到与 '{args.keyword}' 相关的基金")
            else:
                print_fund_search_results(result['data'], show_all=args.all)

        elif args.command == 'query':
            print_banner()
            print(f"📊 查询基金: {args.code}")
            print()

            if args.detail:
                # 完整详情模式：调用所有查询函数
                print("=" * 70)
                print("  📋 基金完整分析报告")
                print("=" * 70)
                print()

                # 1. 基本信息
                details = query_fund_details(args.code, year=get_current_year())
                print_fund_details(details)

                # 2. 基金经理详情
                print("=" * 70)
                print("  👤 基金经理详情")
                print("=" * 70)
                print()
                manager_result = get_fund_manager_details(args.code)
                print_manager_details(manager_result)

                # 3. 投资组合完整分析（合并了持仓分析和资产配置）
                print("=" * 70)
                print("  📊 投资组合完整分析")
                print("=" * 70)
                print()
                portfolio_result = get_fund_portfolio_analysis(args.code, year=get_current_year())
                print_portfolio_analysis(portfolio_result)

                # 4. 费用明细
                print("=" * 70)
                print("  💰 费用明细")
                print("=" * 70)
                print()
                fee_result = get_fund_fee_details(args.code)
                print_fee_details(fee_result)

                # 5. 流动性信息
                print("=" * 70)
                print("  💧 流动性信息")
                print("=" * 70)
                print()
                liquidity_result = get_fund_liquidity_info(args.code)
                print_liquidity_info(liquidity_result)

                # 6. 基金评级（如果有）
                print("=" * 70)
                print("  ⭐ 基金评级")
                print("=" * 70)
                print()
                rating_result = get_fund_rating(args.code)
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
                details = query_fund_details(args.code, year=get_current_year())
                print_fund_details(details)

        elif args.command == 'ranking':
            print_banner()
            print(f"🏆 基金排行榜 - {args.fund_type}")
            print()

            rankings = get_fund_rankings(args.fund_type, top=args.top)
            print(f"  {'排名':<6}{'基金代码':<12}{'基金名称':<25}{'近1年收益率':<12}")
            print("  " + "-" * 60)
            for i, fund in enumerate(rankings, 1):
                print(f"  {i:<6}{fund['基金代码']:<12}{fund['基金简称']:<25}{fund['近1年']:<12}")

        elif args.command == 'rating':
            print_banner()
            print(f"⭐ 查询基金评级: {args.code}")
            print()

            rating = get_fund_rating(args.code)
            if rating.get('status') == 'success':
                ratings = rating.get('ratings')
                if ratings:
                    for key, value in ratings.items():
                        print(f"  {key}: {value}")
                else:
                    print(f"  {rating.get('message', '暂无评级数据')}")
            else:
                print(f"  ❌ {rating.get('message', '查询失败')}")

        elif args.command == 'manager':
            print_banner()
            print(f"👤 查询基金经理: {args.code}")
            print()

            manager = get_fund_manager_details(args.code)
            if manager.get('status') == 'success':
                print_fund_details({'manager_details': manager})
            else:
                print(f"  ❌ {manager.get('message', '查询失败')}")

        elif args.command == 'holdings':
            print_banner()
            print(f"💼 持仓动态分析: {args.code}")
            print()

            holdings = get_fund_top_holdings(args.code)
            if holdings.get('status') == 'success':
                print_fund_details({'top_holdings': holdings['data']})
            else:
                print(f"  ❌ {holdings.get('message', '查询失败')}")

        elif args.command == 'portfolio':
            print_banner()
            print(f"📊 投资组合分析: {args.code}")
            print()

            portfolio = get_fund_portfolio_analysis(args.code, year=get_current_year())
            print_portfolio_analysis(portfolio)

        elif args.command == 'fee':
            print_banner()
            print(f"💰 费用明细: {args.code}")
            print()

            fee = get_fund_fee_details(args.code)
            print_fee_details(fee)

        elif args.command == 'liquidity':
            print_banner()
            print(f"💧 流动性信息: {args.code}")
            print()

            liquidity = get_fund_liquidity_info(args.code)
            print_liquidity_info(liquidity)

        elif args.command == 'performance':
            print_banner()
            print(f"📈 基金业绩: {args.code}")
            print()

            perf = get_fund_performance(args.code)
            if perf:
                for period, return_rate in perf.items():
                    print(f"  {period}: {return_rate}")
            else:
                print("  ℹ️  暂无业绩数据")

        elif args.command == 'risk':
            print_banner()
            print(f"⚠️  风险指标: {args.code}")
            print()

            risk = get_fund_risk_metrics(args.code)
            if risk:
                for key, value in risk.items():
                    print(f"  {key}: {value}")
            else:
                print("  ℹ️  暂无风险数据")

        elif args.command == 'top-holdings':
            print_banner()
            print(f"💼 十大重仓股: {args.code}")
            print()

            holdings = get_fund_top_holdings(args.code, year=get_current_year())
            if holdings:
                for i, holding in enumerate(holdings[:10], 1):
                    print(f"  {i}. {holding}")
            else:
                print("  ℹ️  暂无持仓数据")

        elif args.command == 'update':
            print("正在更新基金数据库...")
            get_fund_list.cache_clear()
            if os.path.exists(FUND_DB_FILE):
                os.remove(FUND_DB_FILE)
            result = get_fund_list()
            if not result.empty:
                print(f"✅ 基金数据库更新成功！共 {len(result)} 只基金，已保存到 {FUND_DB_FILE}")
            else:
                print("❌ 基金数据库更新失败")

        else:
            bond_subparsers.choices[args.command].print_help()

    # ============================================================
    # 处理 index 命令（指数）
    # ============================================================
    elif args.category == 'index':
        if not args.command:
            index_parser.print_help()
            return

        if args.command == 'search':
            print_banner()
            print(f"🔍 搜索指数: {args.keyword}")
            print()

            results = search_indices_all(args.keyword)

            if not results:
                print(f"  ℹ️  未找到与 '{args.keyword}' 相关的指数")
            else:
                print_index_search_results(results, show_all=args.all)

        elif args.command == 'query':
            print_banner()
            print(f"📊 查询指数: {args.code}")
            print()

            query = get_index_query(args.code)
            print_index_query(query)

            if args.detail and query.get("status") == "success":
                print_index_valuation(get_index_valuation(args.code))
                print_index_risk(get_index_risk(args.code))

        elif args.command == 'valuation':
            print_banner()
            print(f"💰 查询指数估值: {args.code}")
            print()

            valuation = get_index_valuation(args.code)
            print_index_valuation(valuation)

        elif args.command == 'batch':
            print_banner()
            print(f"📊 批量查询指数详情: {' '.join(args.codes)}")
            print()

            results = get_index_details_batch(args.codes)

            for code, details in results.items():
                print(f"  === {code} ===")
                print_index_details(details)
                print()

        elif args.command == 'update':
            print("正在更新指数数据库...")
            result = update_index_cache()
            if result and isinstance(result, dict):
                total = result.get('total', 0)
                print(f"✅ 指数数据库更新成功！共 {total} 个指数，已保存到 {INDEX_DB_FILE}")
            else:
                print("❌ 指数数据库更新失败")

        elif args.command == 'risk':
            print_banner()
            print(f"⚠️  查询指数风险分析: {args.code}")
            print()

            risk = get_index_risk(args.code)
            print_index_risk(risk)

        elif args.command == 'listfund':
            print_banner()
            print(f"📋 查询指数候选基金池: {args.code}")
            print()

            result = get_index_candidate_funds(args.code)
            print_index_candidate_funds(result, show_all=args.all)

        elif args.command == 'heatmap':
            print_banner()
            print(f"📈 查询指数估值热力图: 分类={args.heatmap_category} 排序={args.sort_by}")
            print()

            result = get_valuation_heatmap(category=args.heatmap_category, sort_by=args.sort_by)
            print_index_heatmap(result, limit=args.limit)

        else:
            index_subparsers.choices[args.command].print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
