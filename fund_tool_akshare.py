# -*- coding: utf-8 -*-
"""
基于 akshare 的基金信息查询工具
提供基金搜索、详情查询、风险分析等功能
"""

import akshare as ak
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# === 缓存配置 ===
@lru_cache(maxsize=1)
def get_fund_list() -> pd.DataFrame:
    """
    获取基金列表（带缓存）
    使用 lru_cache 避免频繁请求
    """
    try:
        logger.info("正在从东方财富获取基金列表...")
        df = ak.fund_name_em()
        logger.info(f"成功获取 {len(df)} 只基金信息")
        return df
    except Exception as e:
        logger.error(f"获取基金列表失败: {e}")
        return pd.DataFrame()

@lru_cache(maxsize=1000)
def search_funds(keyword: str) -> Dict[str, Any]:
    """
    搜索基金（支持代码、名称、拼音）

    Args:
        keyword: 搜索关键词

    Returns:
        包含搜索结果的字典
    """
    df = get_fund_list()
    if df.empty:
        return {"status": "error", "message": "基金数据不可用，请稍后重试"}

    try:
        # 多字段模糊搜索
        mask = (
            df['基金代码'].str.contains(keyword, case=False, na=False) |
            df['基金简称'].str.contains(keyword, na=False) |
            df['拼音缩写'].str.contains(keyword, case=False, na=False)
        )
        results = df[mask].head(50)

        return {
            "status": "success",
            "count": len(results),
            "data": results.to_dict('records')
        }
    except Exception as e:
        logger.error(f"搜索基金失败: {e}")
        return {"status": "error", "message": f"搜索失败: {str(e)}"}

def calculate_risk_metrics_from_data(analysis_df: pd.DataFrame) -> Optional[Dict[str, str]]:
    """
    从分析数据中提取风险指标

    Args:
        analysis_df: 风险分析DataFrame

    Returns:
        风险指标字典
    """
    if analysis_df.empty:
        return None

    try:
        # 取最近一期数据（近1年）
        latest = analysis_df.iloc[0] if len(analysis_df) > 0 else None
        if latest is not None:
            return {
                "年化波动率": f"{float(latest.get('年化波动率', 0)):.2f}%",
                "夏普比率": f"{float(latest.get('年化夏普比率', 0)):.2f}",
                "最大回撤": f"{float(latest.get('最大回撤', 0)):.2f}%"
            }
    except Exception as e:
        logger.warning(f"解析风险指标失败: {e}")

    return None

def query_fund_details(code: str) -> Dict[str, Any]:
    """
    查询基金详细信息

    Args:
        code: 6位基金代码

    Returns:
        包含基金详细信息的字典
    """
    # 验证代码格式
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}' (应为6位数字)"}

    try:
        logger.info(f"正在查询基金 {code} 的详细信息...")

        # 并发获取多个数据源
        overview = ak.fund_overview_em(symbol=code)

        # 基金业绩（雪球）
        achievement = None
        try:
            achievement = ak.fund_individual_achievement_xq(symbol=code)
        except Exception as e:
            logger.warning(f"获取基金业绩失败: {e}")

        # 风险分析（雪球）
        analysis = None
        try:
            analysis = ak.fund_individual_analysis_xq(symbol=code)
        except Exception as e:
            logger.warning(f"获取风险分析失败: {e}")

        # 十大重仓股
        portfolio = None
        try:
            portfolio = ak.fund_portfolio_hold_em(symbol=code, date="2024")
        except Exception as e:
            logger.warning(f"获取持仓数据失败: {e}")

        # 基金经理信息
        managers = []
        try:
            if '基金经理人' in overview.columns and not pd.isna(overview.iloc[0]['基金经理人']):
                manager_str = overview.iloc[0]['基金经理人']
                managers = [{"姓名": m.strip()} for m in str(manager_str).split(',')]
        except Exception as e:
            logger.warning(f"解析基金经理失败: {e}")

        # 基金规模
        scale = None
        try:
            if '资产规模' in overview.columns and not pd.isna(overview.iloc[0]['资产规模']):
                scale = overview.iloc[0]['资产规模']
        except Exception as e:
            logger.warning(f"获取基金规模失败: {e}")

        # 费率信息
        fee_rates = {}
        try:
            if '管理费率' in overview.columns and not pd.isna(overview.iloc[0]['管理费率']):
                fee_rates['管理费率'] = overview.iloc[0]['管理费率']
            if '托管费率' in overview.columns and not pd.isna(overview.iloc[0]['托管费率']):
                fee_rates['托管费率'] = overview.iloc[0]['托管费率']
        except Exception as e:
            logger.warning(f"获取费率信息失败: {e}")

        # 业绩比较基准
        benchmark = None
        try:
            if '业绩比较基准' in overview.columns and not pd.isna(overview.iloc[0]['业绩比较基准']):
                benchmark = overview.iloc[0]['业绩比较基准']
        except Exception as e:
            logger.warning(f"获取业绩基准失败: {e}")

        # 成立日期
        inception_date = None
        try:
            if '成立日期/规模' in overview.columns and not pd.isna(overview.iloc[0]['成立日期/规模']):
                inception_date = str(overview.iloc[0]['成立日期/规模']).split(' /')[0].strip()
        except Exception as e:
            logger.warning(f"获取成立日期失败: {e}")

        # 整理十大重仓股
        top_holdings = []
        if portfolio is not None and not portfolio.empty:
            for _, row in portfolio.head(10).iterrows():
                stock_name = row.get('股票名称', '')
                pct = row.get('占净值比例', 0)
                if stock_name:
                    top_holdings.append(f"{stock_name} ({pct:.2f}%)" if pct else stock_name)

        # 整理风险指标
        risk_metrics = calculate_risk_metrics_from_data(analysis) if analysis is not None else None

        # 整理业绩数据
        performance = {}
        if achievement is not None and not achievement.empty:
            perf_dict = achievement.to_dict('records')
            # 提取年度业绩
            for item in perf_dict:
                if item.get('业绩类型') == '阶段业绩':
                    cycle = item.get('周期', '')
                    return_pct = item.get('本产品区间收益', 0)
                    if cycle and return_pct:
                        performance[cycle] = f"{return_pct:.2f}%"

        logger.info(f"成功获取基金 {code} 的详细信息")

        return {
            "status": "success",
            "code": code,
            "name": overview.iloc[0]['基金简称'] if not overview.empty else "",
            "type": overview.iloc[0]['基金类型'] if not overview.empty else "",
            "inception_date": inception_date,
            "scale": scale,
            "managers": managers,
            "fee_rates": fee_rates,
            "benchmark": benchmark,
            "performance": performance,
            "risk_metrics": risk_metrics,
            "top_holdings": top_holdings
        }

    except Exception as e:
        logger.error(f"查询基金详情失败 {code}: {e}")
        return {"status": "error", "message": f"查询失败: {str(e)}"}

def get_fund_rankings(fund_type: str = "全部") -> Dict[str, Any]:
    """
    获取基金排行榜

    Args:
        fund_type: 基金类型（全部/股票型/混合型/债券型/指数型/QDII/FOF）

    Returns:
        排行榜数据
    """
    try:
        logger.info(f"正在获取{fund_type}基金排行榜...")
        df = ak.fund_open_fund_rank_em(symbol=fund_type)

        return {
            "status": "success",
            "count": len(df),
            "data": df.head(100).to_dict('records')  # 限制返回前100名
        }
    except Exception as e:
        logger.error(f"获取基金排行榜失败: {e}")
        return {"status": "error", "message": f"获取排行榜失败: {str(e)}"}

def get_fund_rating(code: str) -> Dict[str, Any]:
    """
    获取基金评级信息

    Args:
        code: 基金代码

    Returns:
        评级信息
    """
    try:
        # 从汇总数据中查找
        df = ak.fund_rating_all()
        if df.empty:
            return {"status": "error", "message": "暂无评级数据"}

        fund_rating = df[df['代码'] == code]
        if fund_rating.empty:
            return {"status": "success", "ratings": None, "message": "该基金暂无评级"}

        return {
            "status": "success",
            "ratings": fund_rating.iloc[0].to_dict()
        }
    except Exception as e:
        logger.error(f"获取基金评级失败: {e}")
        return {"status": "error", "message": f"获取评级失败: {str(e)}"}

# ============================================================================
# 命令行接口
# ============================================================================

def print_banner():
    """打印横幅"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                    📊 中国基金信息查询工具 v2.0                          ║
║                    基于 akshare + MCP Python SDK                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════════╝
""")


def print_fund_search_results(results: List[Dict], show_all: bool = False):
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


def print_fund_details(details: Dict):
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


def print_rankings(results: List[Dict], top_n: int = 10):
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


def print_rating(ratings: Optional[Dict]):
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


def main():
    """命令行主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='中国基金信息查询命令行工具',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用示例:
  1. 搜索基金:
     python fund_tool_akshare.py search "华夏"

  2. 查询基金详情:
     python fund_tool_akshare.py query 000001

  3. 查看排行榜:
     python fund_tool_akshare.py ranking --type 股票型 --top 10

   4. 查询基金评级:
     python fund_tool_akshare.py rating 000001

  5. 更新本地数据库:
     python fund_tool_akshare.py update

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

    args = parser.parse_args()

    # 配置日志
    logging.basicConfig(
        level=logging.WARNING,  # 只显示警告和错误
        format='%(message)s'
    )

    # 执行对应的命令
    if args.command == 'update':
        print("正在更新基金数据库...")
        result = get_fund_list()
        # 清除缓存以强制重新加载
        get_fund_list.cache_clear()

        if not result.empty:
            print(f"✅ 基金数据库更新成功！共 {len(result)} 只基金")
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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
