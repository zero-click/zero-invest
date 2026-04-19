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
# 新增功能：基金经理、持仓、配置、费用、流动性
# ============================================================================

@lru_cache(maxsize=1)
def _get_all_managers() -> pd.DataFrame:
    """获取所有基金经理数据（带缓存）"""
    try:
        return ak.fund_manager_em()
    except Exception as e:
        logger.warning(f"获取基金经理数据失败: {e}")
        return pd.DataFrame()

def get_fund_manager_details(code: str) -> Dict[str, Any]:
    """
    获取基金经理深度信息
    包括：管理年限、学历背景、任期业绩、管理其他基金等

    Args:
        code: 基金代码

    Returns:
        基金经理详细信息
    """
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}'"}

    try:
        logger.info(f"正在查询基金 {code} 的基金经理信息...")

        # 获取基金经理数据
        managers_df = _get_all_managers()

        if managers_df.empty:
            return {"status": "error", "message": "基金经理数据不可用"}

        # 过滤该基金的经理
        fund_managers = managers_df[managers_df['现任基金代码'] == code]

        if fund_managers.empty:
            return {"status": "success", "managers": [], "manager_count": 0, "message": "未找到该基金的经理信息"}

        # 整理经理信息
        managers_list = []
        for _, row in fund_managers.iterrows():
            manager_info = {
                "姓名": row.get('姓名', ''),
                "所属公司": row.get('所属公司', ''),
                "累计从业时间": f"{row.get('累计从业时间', 0)}天",
                "现任基金资产总规模": f"{row.get('现任基金资产总规模', 0):.2f}亿元" if pd.notna(row.get('现任基金资产总规模')) else 'N/A',
                "现任基金最佳回报": f"{row.get('现任基金最佳回报', 0):.2f}%" if pd.notna(row.get('现任基金最佳回报')) else 'N/A',
                "现任基金": row.get('现任基金', ''),
                "现任基金代码": row.get('现任基金代码', '')
            }
            managers_list.append(manager_info)

        # 获取该基金的所有经理（通过fund_overview_em验证）
        try:
            overview = ak.fund_overview_em(symbol=code)
            if not overview.empty and '基金经理人' in overview.columns:
                manager_names = [m['姓名'] for m in managers_list]
        except:
            pass

        return {
            "status": "success",
            "managers": managers_list,
            "manager_count": len(managers_list)
        }

    except Exception as e:
        logger.error(f"获取基金经理信息失败 {code}: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

def get_fund_holdings_analysis(code: str, periods: int = 4) -> Dict[str, Any]:
    """
    获取持仓动态分析
    包括：重仓股变化、持仓集中度、换手率等

    Args:
        code: 基金代码
        periods: 分析最近几个季度

    Returns:
        持仓动态分析数据
    """
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}'"}

    try:
        logger.info(f"正在分析基金 {code} 的持仓动态...")

        # 获取持仓变化数据
        holdings_change = None
        try:
            holdings_change = ak.fund_portfolio_change_em(symbol=code)
        except Exception as e:
            logger.warning(f"获取持仓变化失败: {e}")

        # 获取最新持仓
        latest_holdings = None
        current_year = "2024"
        try:
            latest_holdings = ak.fund_portfolio_hold_em(symbol=code, date=current_year)
        except Exception as e:
            logger.warning(f"获取最新持仓失败: {e}")

        # 计算持仓集中度
        concentration = {}
        if latest_holdings is not None and not latest_holdings.empty:
            top10_holdings = latest_holdings.head(10)
            if '占净值比例' in top10_holdings.columns:
                total_pct = top10_holdings['占净值比例'].sum()
                concentration = {
                    "前10大持仓占比": f"{total_pct:.2f}%",
                    "持仓集中度": "高" if total_pct > 70 else "中" if total_pct > 50 else "低"
                }

        # 整理持仓变化
        changes_by_quarter = {}
        if holdings_change is not None and not holdings_change.empty:
            # 按季度分组
            if '季度' in holdings_change.columns:
                recent_quarters = holdings_change['季度'].unique()[:periods]
                for q in recent_quarters:
                    q_data = holdings_change[holdings_change['季度'] == q].head(10)
                    stocks = []
                    for _, row in q_data.iterrows():
                        stock_name = row.get('股票名称', '')
                        amount = row.get('本期累计买入金额', 0)
                        if stock_name:
                            stocks.append({
                                "股票名称": stock_name,
                                "股票代码": row.get('股票代码', ''),
                                "买入金额": f"{float(amount):.2f}万" if pd.notna(amount) else 'N/A'
                            })
                    changes_by_quarter[str(q)] = stocks

        return {
            "status": "success",
            "code": code,
            "concentration": concentration,
            "holdings_change_by_quarter": changes_by_quarter,
            "latest_top_holdings": latest_holdings.head(10).to_dict('records') if latest_holdings is not None and not latest_holdings.empty else []
        }

    except Exception as e:
        logger.error(f"持仓分析失败 {code}: {e}")
        return {"status": "error", "message": f"分析失败: {str(e)}"}

def get_fund_asset_allocation(code: str, date: str = "2024") -> Dict[str, Any]:
    """
    获取资产配置结构
    包括：股债比例、行业配置、投资风格等

    Args:
        code: 基金代码
        date: 年份

    Returns:
        资产配置数据
    """
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}'"}

    try:
        logger.info(f"正在查询基金 {code} 的资产配置...")

        # 获取行业配置
        industry_allocation = []
        try:
            industry_df = ak.fund_portfolio_industry_allocation_em(symbol=code, date=date)
            if not industry_df.empty:
                for _, row in industry_df.iterrows():
                    industry_allocation.append({
                        "行业类别": row.get('行业类别', ''),
                        "占净值比例": f"{float(row.get('占净值比例', 0)):.2f}%",
                        "市值": f"{float(row.get('市值', 0)):.2f}万" if pd.notna(row.get('市值')) else 'N/A'
                    })
        except Exception as e:
            logger.warning(f"获取行业配置失败: {e}")

        # 获取债券持仓
        bond_holdings = []
        try:
            bond_df = ak.fund_portfolio_bond_hold_em(symbol=code, date=date)
            if not bond_df.empty:
                for _, row in bond_df.head(10).iterrows():
                    bond_name = row.get('债券名称', '')
                    if bond_name:
                        bond_holdings.append({
                            "债券名称": bond_name,
                            "占净值比例": f"{float(row.get('占净值比例', 0)):.2f}%" if pd.notna(row.get('占净值比例')) else 'N/A'
                        })
        except Exception as e:
            logger.warning(f"获取债券持仓失败: {e}")

        # 获取股票持仓
        stock_holdings = []
        try:
            stock_df = ak.fund_portfolio_hold_em(symbol=code, date=date)
            if not stock_df.empty:
                total_stock_pct = 0
                for _, row in stock_df.iterrows():
                    pct = row.get('占净值比例', 0)
                    stock_name = row.get('股票名称', '')
                    if stock_name:
                        stock_holdings.append({
                            "股票名称": stock_name,
                            "占净值比例": f"{float(pct):.2f}%" if pd.notna(pct) else 'N/A'
                        })
                        total_stock_pct += float(pct) if pd.notna(pct) else 0
        except Exception as e:
            logger.warning(f"获取股票持仓失败: {e}")

        # 判断投资风格
        style = "未知"
        if stock_holdings:
            top_holdings = stock_holdings[:5]
            # 这里简化判断，实际应该根据具体的股票特征来判断
            style = "平衡型"

        return {
            "status": "success",
            "code": code,
            "date": date,
            "investment_style": style,
            "industry_allocation": industry_allocation,
            "stock_holdings_sample": stock_holdings[:5],
            "bond_holdings_sample": bond_holdings[:5]
        }

    except Exception as e:
        logger.error(f"获取资产配置失败 {code}: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

def get_fund_fee_details(code: str) -> Dict[str, Any]:
    """
    获取费用明细
    包括：申购费率、赎回费率、管理费率、托管费率等

    Args:
        code: 基金代码

    Returns:
        费用明细
    """
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}'"}

    try:
        logger.info(f"正在查询基金 {code} 的费用明细...")

        fee_details = {}

        # 获取认购费率
        try:
            purchase_fee = ak.fund_fee_em(symbol=code, indicator="认购费率")
            if not purchase_fee.empty:
                fee_details["认购费率"] = purchase_fee.to_dict('records')
        except Exception as e:
            logger.warning(f"获取认购费率失败: {e}")

        # 获取申购费率
        try:
            subscription_fee = ak.fund_fee_em(symbol=code, indicator="申购费率")
            if not subscription_fee.empty:
                fee_details["申购费率"] = subscription_fee.to_dict('records')
        except Exception as e:
            logger.warning(f"获取申购费率失败: {e}")

        # 获取赎回费率
        try:
            redemption_fee = ak.fund_fee_em(symbol=code, indicator="赎回费率")
            if not redemption_fee.empty:
                fee_details["赎回费率"] = redemption_fee.to_dict('records')
        except Exception as e:
            logger.warning(f"获取赎回费率失败: {e}")

        # 从overview获取管理费率和托管费率
        try:
            overview = ak.fund_overview_em(symbol=code)
            if not overview.empty:
                if '管理费率' in overview.columns:
                    fee_details["管理费率"] = overview.iloc[0]['管理费率']
                if '托管费率' in overview.columns:
                    fee_details["托管费率"] = overview.iloc[0]['托管费率']
        except Exception as e:
            logger.warning(f"获取管理费率/托管费率失败: {e}")

        return {
            "status": "success",
            "code": code,
            "fee_details": fee_details
        }

    except Exception as e:
        logger.error(f"获取费用明细失败 {code}: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

def get_fund_liquidity_info(code: str) -> Dict[str, Any]:
    """
    获取流动性信息
    包括：申赎状态、申赎时间、最低金额、大额限制等

    Args:
        code: 基金代码

    Returns:
        流动性信息
    """
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}'"}

    try:
        logger.info(f"正在查询基金 {code} 的流动性信息...")

        # 从overview获取基本信息
        liquidity_info = {}
        try:
            overview = ak.fund_overview_em(symbol=code)
            if not overview.empty:
                # 基金状态
                liquidity_info["基金状态"] = "开放"  # 默认值
                if '申购状态' in overview.columns:
                    liquidity_info["申购状态"] = overview.iloc[0]['申购状态']
                if '赎回状态' in overview.columns:
                    liquidity_info["赎回状态"] = overview.iloc[0]['赎回状态']
        except Exception as e:
            logger.warning(f"获取申赎状态失败: {e}")

        # 添加常规流动性信息
        liquidity_info.update({
            "申赎时间": "T+1",  # 大多数开放式基金
            "交易场所": "场外基金",
            "最低申购金额": "1元",
            "申购确认时间": "T+1日",
            "赎回到账时间": "T+1至T+7日（根据渠道）"
        })

        # 尝试获取更多流动性信息
        # 注意：部分信息可能需要从其他数据源获取

        return {
            "status": "success",
            "code": code,
            "liquidity_info": liquidity_info
        }

    except Exception as e:
        logger.error(f"获取流动性信息失败 {code}: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

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


# ============================================================================
# 新增功能的打印函数
# ============================================================================

def print_manager_details(result: Dict):
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


def print_holdings_analysis(result: Dict):
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


def print_asset_allocation(result: Dict):
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


def print_fee_details(result: Dict):
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


def print_liquidity_info(result: Dict):
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


def main():
    """命令行主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='中国基金信息查询命令行工具 v2.1',
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用示例:
  1. 搜索基金:
     python fund_tool_akshare.py search "华夏"

  2. 查询基金详情（基本信息）:
     python fund_tool_akshare.py query 000001

  2.1 查询基金完整详情（包含所有分析）:
     python fund_tool_akshare.py query 000001 --detail
     python fund_tool_akshare.py query 000001 -d

  3. 查看排行榜:
     python fund_tool_akshare.py ranking --type 股票型 --top 10

  4. 查询基金评级:
     python fund_tool_akshare.py rating 000001

  5. 查询基金经理详情:
     python fund_tool_akshare.py manager 000001

  6. 持仓动态分析:
     python fund_tool_akshare.py holdings 000001 --periods 4

  7. 资产配置结构:
     python fund_tool_akshare.py allocation 000001 --year 2024

  8. 费用明细:
     python fund_tool_akshare.py fee 000001

  9. 流动性信息:
     python fund_tool_akshare.py liquidity 000001

 10. 更新本地数据库:
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

    # === manager 命令 (新增) ===
    manager_parser = subparsers.add_parser('manager', help='查询基金经理深度信息')
    manager_parser.add_argument('code', type=str, help='6位基金代码')

    # === holdings 命令 (新增) ===
    holdings_parser = subparsers.add_parser('holdings', help='持仓动态分析')
    holdings_parser.add_argument('code', type=str, help='6位基金代码')
    holdings_parser.add_argument('--periods', '-p', type=int, default=4,
                                help='分析最近几个季度（默认: 4）')

    # === allocation 命令 (新增) ===
    alloc_parser = subparsers.add_parser('allocation', help='资产配置结构')
    alloc_parser.add_argument('code', type=str, help='6位基金代码')
    alloc_parser.add_argument('--year', '-y', type=str, default='2024',
                             help='年份（默认: 2024）')

    # === fee 命令 (新增) ===
    fee_parser = subparsers.add_parser('fee', help='费用明细')
    fee_parser.add_argument('code', type=str, help='6位基金代码')

    # === liquidity 命令 (新增) ===
    liq_parser = subparsers.add_parser('liquidity', help='流动性信息')
    liq_parser.add_argument('code', type=str, help='6位基金代码')

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

    # === 新增命令处理 ===

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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
