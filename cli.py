# -*- coding: utf-8 -*-
"""
基金信息查询命令行工具
"""

import argparse
import logging
import os
import sys
import pandas as pd

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from fund_tools import (
    search_funds,
    query_fund_details,
    get_fund_rankings,
    get_fund_rating,
    get_fund_manager_details,
    get_fund_holdings_analysis,
    get_fund_asset_allocation,
    get_fund_fee_details,
    get_fund_liquidity_info,
    get_fund_list,
    FUND_DB_FILE,
)

# 配置日志
logging.basicConfig(
    level=logging.WARNING,  # 只显示警告和错误
    format='%(message)s'
)

logger = logging.getLogger(__name__)


# ============================================================================
# 打印横幅
# ============================================================================

def print_banner():
    """打印横幅"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                    📊 中国基金信息查询工具 v2.0                          ║
║                    基于 akshare + MCP Python SDK                        ║
║                                                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")


# ============================================================================
# 打印函数
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
            print(f"    {i}. {holding}")
    else:
        print()
        print("  💼 十大重仓股:  暂无数据")


def print_rankings(results: dict, top_n: int = 10):
    """美式打印排行榜"""
    if results.get('status') == 'error':
        print(f"  ❌ {results.get('message')}")
        return

    data = results.get('data', [])
    count = len(data)
    display_count = min(top_n, count)

    print(f"  共 {count} 只基金 (TOP {display_count}):")
    print()
    print(f"  {'排名':<6}{'基金代码':<12}{'基金名称':<30}{'近1年收益率':<15}")
    print("  " + "-" * 65)

    for i, fund in enumerate(data[:display_count], 1):
        code = fund.get('基金代码', '')
        name = fund.get('基金简称', '')
        return_1y = fund.get('近1年', 'N/A')

        # 截断过长的名称
        if len(name) > 28:
            name = name[:25] + '...'

        print(f"  {i:<6}{code:<12}{name:<30}{return_1y:<15}")


def print_rating(ratings):
    """美式打印基金评级"""
    if not ratings:
        print("  ℹ️  该基金暂无评级数据")
        return

    print()
    print("  ⭐ 评级详情")
    print("  " + "-" * 60)
    print(f"  基金代码:  {ratings.get('代码', '')}")
    print(f"  基金名称:  {ratings.get('简称', '')}")
    print(f"  基金公司:  {ratings.get('基金公司', '')}")
    print()

    if '上海证券' in ratings and ratings['上海证券'] and not pd.isna(ratings['上海证券']):
        print(f"    上海证券: {ratings['上海证券']} ⭐")
    if '招商证券' in ratings and ratings['招商证券'] and not pd.isna(ratings['招商证券']):
        print(f"    招商证券: {ratings['招商证券']} ⭐")
    if '济安金信' in ratings and ratings['济安金信'] and not pd.isna(ratings['济安金信']):
        print(f"    济安金信: {ratings['济安金信']} ⭐")
    if '晨星评级' in ratings and ratings['晨星评级'] and not pd.isna(ratings['晨星评级']):
        print(f"    晨星评级: {ratings['晨星评级']} ⭐")


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


def print_holdings_analysis(result: dict):
    """打印持仓动态分析"""
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
            pct = h.get('占净值比例', 0)
            print(f"    {i:2d}. {name:<12s} {pct:.2f}%" if isinstance(pct, (int, float)) else f"    {i:2d}. {name}")
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


def print_asset_allocation(result: dict):
    """打印资产配置结构"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message')}")
        return

    # 投资风格
    style = result.get('investment_style', '')
    if style:
        print(f"  🎯 投资风格: {style}")
        print()

    # 行业配置
    industries = result.get('industry_allocation', [])
    if industries:
        print("  🏭 行业配置 (前5大)")
        print("  " + "-" * 60)
        for i, ind in enumerate(industries[:5], 1):
            print(f"    {i}. {ind['行业类别']:<30s} {ind['占净值比例']}")
        print()

    # 股票持仓
    stocks = result.get('stock_holdings_sample', [])
    if stocks:
        print("  📈 股票持仓样本")
        print("  " + "-" * 60)
        for s in stocks[:5]:
            print(f"    - {s['股票名称']}: {s['占净值比例']}")
        print()

    # 债券持仓
    bonds = result.get('bond_holdings_sample', [])
    if bonds:
        print("  🏛️  债券持仓样本")
        print("  " + "-" * 60)
        for b in bonds[:3]:
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
        description='中国基金信息查询命令行工具 v2.1',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用示例:
  1. 搜索基金:
     python cli.py search "华夏"

  2. 查询基金详情（基本信息）:
     python cli.py query 000001

  2.1 查询基金完整详情（包含所有分析）:
     python cli.py query 000001 --detail
     python cli.py query 000001 -d

  3. 查看排行榜:
     python cli.py ranking --type 股票型 --top 10

  4. 查询基金评级:
     python cli.py rating 000001

  5. 查询基金经理详情:
     python cli.py manager 000001

  6. 持仓动态分析:
     python cli.py holdings 000001 --periods 4

  7. 资产配置结构:
     python cli.py allocation 000001
     python cli.py allocation 000001 --year 2025  # 指定年份

  8. 费用明细:
     python cli.py fee 000001

  9. 流动性信息:
     python cli.py liquidity 000001

  10. 更新本地数据库:
     python cli.py update

项目主页: https://github.com/example/ttjj-fund
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用的命令')

    # === update 命令 ===
    subparsers.add_parser('update', help='更新基金数据库')

    # === search 命令 ===
    search_parser = subparsers.add_parser('search', help='搜索基金')
    search_parser.add_argument('keyword', type=str, help='搜索关键词（基金代码/名称/拼音）')
    search_parser.add_argument('--all', '-a', action='store_true', help='显示所有结果')

    # === query 命令 ===
    query_parser = subparsers.add_parser('query', help='查询基金详细信息')
    query_parser.add_argument('code', type=str, help='6位基金代码')
    query_parser.add_argument('--detail', '-d', action='store_true',
                             help='显示完整详情（包括基金经理、持仓、配置、费用、流动性等）')

    # === ranking 命令 ===
    ranking_parser = subparsers.add_parser('ranking', help='查看基金排行榜')
    ranking_parser.add_argument('--type', '-t', dest='fund_type',
                              default='全部',
                              choices=['全部', '股票型', '混合型', '债券型', '指数型', 'QDII', 'FOF'],
                              help='基金类型（默认: 全部）')
    ranking_parser.add_argument('--top', '-n', type=int, default=10,
                             help='显示前N名（默认: 10）')

    # === rating 命令 ===
    rating_parser = subparsers.add_parser('rating', help='查询基金评级')
    rating_parser.add_argument('code', type=str, help='6位基金代码')

    # === manager 命令 ===
    manager_parser = subparsers.add_parser('manager', help='查询基金经理深度信息')
    manager_parser.add_argument('code', type=str, help='6位基金代码')

    # === holdings 命令 ===
    holdings_parser = subparsers.add_parser('holdings', help='持仓动态分析')
    holdings_parser.add_argument('code', type=str, help='6位基金代码')
    holdings_parser.add_argument('--periods', '-p', type=int, default=4,
                                help='分析最近几个季度（默认: 4）')

    # === allocation 命令 ===
    alloc_parser = subparsers.add_parser('allocation', help='资产配置结构')
    alloc_parser.add_argument('code', type=str, help='6位基金代码')
    alloc_parser.add_argument('--year', '-y', type=str, default=None,
                             help='年份（默认: 当前年份）')

    # === fee 命令 ===
    fee_parser = subparsers.add_parser('fee', help='费用明细')
    fee_parser.add_argument('code', type=str, help='6位基金代码')

    # === liquidity 命令 ===
    liq_parser = subparsers.add_parser('liquidity', help='流动性信息')
    liq_parser.add_argument('code', type=str, help='6位基金代码')

    # === heatmap 命令 ===
    heatmap_parser = subparsers.add_parser('heatmap', help='行业估值热力图')
    heatmap_parser.add_argument('--category', '-c', type=str,
                               choices=['全部', '宽基', '科技', '成长', '消费', '医药', '资源', '金融', '军工', '红利'],
                               default='全部',
                               help='行业分类筛选（默认: 全部）')
    heatmap_parser.add_argument('--sort', '-s', type=str,
                               choices=['pe', 'pb', 'dividend', 'valuation'],
                               default='pe',
                               help='排序方式：pe(市盈率), pb(市净率), dividend(股息率), valuation(估值)')
    heatmap_parser.add_argument('--limit', '-l', type=int, default=20,
                               help='显示数量限制（默认: 20）')
    heatmap_parser.add_argument('--suggestions', '-g', action='store_true',
                               help='显示投资建议')
    heatmap_parser.add_argument('--json', '-j', action='store_true',
                               help='输出JSON格式数据')

    args = parser.parse_args()

    # 执行对应的命令
    if args.command == 'update':
        print("正在更新基金数据库...")
        # 清除内存缓存，强制重新从网络加载并写盘
        get_fund_list.cache_clear()
        if os.path.exists(FUND_DB_FILE):
            os.remove(FUND_DB_FILE)
        result = get_fund_list()
        if not result.empty:
            print(f"✅ 基金数据库更新成功！共 {len(result)} 只基金，已保存到 {FUND_DB_FILE}")
        else:
            print("❌ 基金数据库更新失败")

    elif args.command == 'search':
        print_banner()
        print(f"🔍 搜索关键词: {args.keyword}")
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
            details = query_fund_details(args.code)
            print_fund_details(details)

            # 2. 基金经理详情
            print("=" * 70)
            print("  👤 基金经理详情")
            print("=" * 70)
            print()
            manager_result = get_fund_manager_details(args.code)
            print_manager_details(manager_result)

            # 3. 持仓动态分析
            print("=" * 70)
            print("  📊 持仓动态分析")
            print("=" * 70)
            print()
            holdings_result = get_fund_holdings_analysis(args.code, periods=2)
            print_holdings_analysis(holdings_result)

            # 4. 资产配置结构
            print("=" * 70)
            print("  🎯 资产配置结构")
            print("=" * 70)
            print()
            allocation_result = get_fund_asset_allocation(args.code)
            print_asset_allocation(allocation_result)

            # 5. 费用明细
            print("=" * 70)
            print("  💰 费用明细")
            print("=" * 70)
            print()
            fee_result = get_fund_fee_details(args.code)
            print_fee_details(fee_result)

            # 6. 流动性信息
            print("=" * 70)
            print("  💧 流动性信息")
            print("=" * 70)
            print()
            liquidity_result = get_fund_liquidity_info(args.code)
            print_liquidity_info(liquidity_result)

            # 7. 基金评级（如果有）
            print("=" * 70)
            print("  ⭐ 基金评级")
            print("=" * 70)
            print()
            rating_result = get_fund_rating(args.code)
            if rating_result.get('status') == 'success':
                print_rating(rating_result.get('ratings'))
            else:
                print(f"  ℹ️  {rating_result.get('message', '暂无评级数据')}")

            print()
            print("=" * 70)
            print("  ✅ 分析报告完成")
            print("=" * 70)
        else:
            # 标准模式：只显示基本信息
            details = query_fund_details(args.code)
            print_fund_details(details)

    elif args.command == 'ranking':
        print_banner()
        print(f"🏆 {args.fund_type}基金排行榜")
        print()

        result = get_fund_rankings(args.fund_type)
        print_rankings(result, top_n=args.top)

    elif args.command == 'rating':
        print_banner()
        print(f"⭐ 查询基金评级: {args.code}")
        print()

        result = get_fund_rating(args.code)
        if result.get('status') == 'success':
            print_rating(result.get('ratings'))
        else:
            print(f"  ❌ {result['message']}")

    elif args.command == 'manager':
        print_banner()
        print(f"👤 基金经理详情: {args.code}")
        print()

        result = get_fund_manager_details(args.code)
        print_manager_details(result)

    elif args.command == 'holdings':
        print_banner()
        print(f"📊 持仓动态分析: {args.code}")
        print()

        result = get_fund_holdings_analysis(args.code, args.periods)
        print_holdings_analysis(result)

    elif args.command == 'allocation':
        print_banner()
        print(f"🎯 资产配置结构: {args.code}")
        print()

        result = get_fund_asset_allocation(args.code, args.year)
        print_asset_allocation(result)

    elif args.command == 'fee':
        print_banner()
        print(f"💰 费用明细: {args.code}")
        print()

        result = get_fund_fee_details(args.code)
        print_fee_details(result)

    elif args.command == 'liquidity':
        print_banner()
        print(f"💧 流动性信息: {args.code}")
        print()

        result = get_fund_liquidity_info(args.code)
        print_liquidity_info(result)

    elif args.command == 'heatmap':
        print_banner()
        print(f"📈 行业估值热力图 | 分类: {args.category} | 排序: {args.sort}")
        print()

        try:
            # 导入行业估值模块
            from industry_valuation import (
                get_valuation_heatmap,
                format_heatmap_table,
                get_investment_suggestions
            )

            # 获取热力图数据
            heatmap_data = get_valuation_heatmap()

            if args.json:
                # JSON输出模式
                import json
                print(json.dumps(heatmap_data, ensure_ascii=False, indent=2))
            else:
                # 表格输出模式
                table = format_heatmap_table(heatmap_data)
                print(table)

                if args.suggestions:
                    print("\n" + "=" * 80)
                    print("📋 投资建议摘要")
                    print("=" * 80)
                    suggestions = get_investment_suggestions(heatmap_data)
                    print(suggestions)

        except ImportError as e:
            print(f"❌ 导入行业估值模块失败: {e}")
            print("请确保已安装 industry_valuation.py 模块")
        except Exception as e:
            print(f"❌ 生成热力图失败: {e}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
