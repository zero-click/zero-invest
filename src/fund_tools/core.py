# -*- coding: utf-8 -*-
"""
基金信息查询核心模块
提供基金搜索、详情查询、排行榜、评级等功能
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional
from functools import lru_cache
import logging
from datetime import datetime

from .cache import get_fund_list

logger = logging.getLogger(__name__)


# ============================================================================
# 工具函数
# ============================================================================

def _get_current_year() -> str:
    """获取当前年份作为字符串"""
    return str(datetime.now().year)


# ============================================================================
# 搜索功能
# ============================================================================

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


# ============================================================================
# 详情查询
# ============================================================================

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
        except KeyError as e:
            # 某些基金在雪球数据源中没有完整的业绩数据，这是正常现象
            logger.debug(f"基金 {code} 在雪球数据源中无业绩数据: {e}")
        except Exception as e:
            logger.warning(f"获取基金业绩失败: {e}")

        # 风险分析（雪球）
        analysis = None
        try:
            analysis = ak.fund_individual_analysis_xq(symbol=code)
        except KeyError as e:
            # 某些基金在雪球数据源中没有风险分析数据，这是正常现象
            # 常见的缺失字段: 'index_data_list', 'annual_performance_list' 等
            logger.debug(f"基金 {code} 在雪球数据源中无风险分析数据: {e}")
        except Exception as e:
            logger.warning(f"获取风险分析失败: {e}")

        # 十大重仓股
        portfolio = None
        try:
            portfolio = ak.fund_portfolio_hold_em(symbol=code, date=_get_current_year())
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
            # akshare 返回的字段名是 "净资产规模"
            if '净资产规模' in overview.columns and not pd.isna(overview.iloc[0]['净资产规模']):
                scale = overview.iloc[0]['净资产规模']
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


# ============================================================================
# 排行榜和评级
# ============================================================================

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
# 基金经理
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


# ============================================================================
# 持仓分析
# ============================================================================

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
        current_year = _get_current_year()
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


# ============================================================================
# 资产配置
# ============================================================================

def get_fund_asset_allocation(code: str, date: Optional[str] = None) -> Dict[str, Any]:
    """
    获取资产配置结构
    包括：股债比例、行业配置、投资风格等

    Args:
        code: 基金代码
        date: 年份（可选，默认使用当前年份）

    Returns:
        资产配置数据
    """
    if date is None:
        date = _get_current_year()
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
        except KeyError as e:
            # 某些基金没有债券持仓数据（如股票型基金、QDII基金），这是正常现象
            logger.debug(f"基金 {code} 无债券持仓数据: {e}")
        except Exception as e:
            logger.warning(f"获取债券持仓失败: {e}")

        # 获取股票持仓
        stock_holdings = []
        try:
            stock_df = ak.fund_portfolio_hold_em(symbol=code, date=date)
            if not stock_df.empty:
                for _, row in stock_df.iterrows():
                    pct = row.get('占净值比例', 0)
                    stock_name = row.get('股票名称', '')
                    if stock_name:
                        stock_holdings.append({
                            "股票名称": stock_name,
                            "占净值比例": f"{float(pct):.2f}%" if pd.notna(pct) else 'N/A'
                        })
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


# ============================================================================
# 费用信息
# ============================================================================

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


# ============================================================================
# 流动性信息
# ============================================================================

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

        return {
            "status": "success",
            "code": code,
            "liquidity_info": liquidity_info
        }

    except Exception as e:
        logger.error(f"获取流动性信息失败 {code}: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}
