# -*- coding: utf-8 -*-
"""
基金信息查询核心模块
提供基金搜索、详情查询、排行榜、评级等功能
"""

import akshare as ak
import pandas as pd
from typing import Dict, Any, Optional, List
from functools import lru_cache
import logging
import re
import time
import os

from .cache import get_fund_list

logger = logging.getLogger(__name__)

# ETF 行情缓存（仅缓存成功结果，避免失败结果污染）
_ETF_SPOT_CACHE = {"df": None, "ts": 0.0, "source": ""}
_ETF_SPOT_CACHE_TTL_SECONDS = 120

# 全局函数：获得所有基金经理
@lru_cache(maxsize=1)
def _get_all_managers() -> pd.DataFrame:
    """获取所有基金经理数据（带缓存）"""
    try:
        return ak.fund_manager_em()
    except Exception as e:
        logger.warning(f"获取基金经理数据失败: {e}")
        return pd.DataFrame()

# 全局函数，获得所有基金的排名
# 基金类型白名单
VALID_FUND_TYPES = ["全部", "股票型", "混合型", "债券型", "指数型", "QDII", "FOF"]


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


def _clear_proxy_env() -> None:
    """移除代理环境变量，避免访问国内源时走本地代理导致失败"""
    for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(k, None)


def _fetch_table_with_retry(fetcher, source_name: str, retries: int = 2) -> pd.DataFrame:
    """带重试地获取表数据"""
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            _clear_proxy_env()
            df = fetcher()
            if df is not None and not df.empty:
                return df
        except Exception as e:
            last_error = e
            logger.warning(f"获取 ETF 行情失败 [{source_name}] 第{attempt}/{retries}次: {e}")
        time.sleep(0.2)

    if last_error is not None:
        logger.warning(f"获取 ETF 行情失败 [{source_name}]，已重试{retries}次")
    return pd.DataFrame()


def _get_etf_spot_table(force_refresh: bool = False) -> pd.DataFrame:
    """
    获取 ETF 实时行情表（成功缓存，失败不缓存）

    数据源优先级: 东方财富 -> 同花顺 -> 场内基金排行（降级）
    """
    now = time.time()
    cached_df = _ETF_SPOT_CACHE.get("df")
    cached_ts = _ETF_SPOT_CACHE.get("ts", 0.0)
    if (
        not force_refresh
        and isinstance(cached_df, pd.DataFrame)
        and not cached_df.empty
        and now - cached_ts < _ETF_SPOT_CACHE_TTL_SECONDS
    ):
        return cached_df

    sources = [
        ("em", ak.fund_etf_spot_em),
        ("ths", getattr(ak, "fund_etf_spot_ths", None)),
        ("rank", ak.fund_exchange_rank_em),
    ]

    for source_name, fetcher in sources:
        if fetcher is None:
            continue
        df = _fetch_table_with_retry(fetcher, source_name=source_name, retries=2)
        if df is not None and not df.empty:
            _ETF_SPOT_CACHE["df"] = df
            _ETF_SPOT_CACHE["ts"] = now
            _ETF_SPOT_CACHE["source"] = source_name
            return df

    return pd.DataFrame()


def _pick_first_value(row: pd.Series, candidates: List[str]) -> Any:
    """按候选字段顺序提取首个可用值"""
    for col in candidates:
        if col in row.index and pd.notna(row.get(col)):
            return row.get(col)
    return None


def get_fund_market_metrics(code: str) -> Dict[str, Any]:
    """
    获取基金场内行情指标（ETF/LOF 等）

    说明:
      - 成交额、折溢价等数据主要适用于场内交易基金
      - 对场外基金通常返回 N/A
    """
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}'"}

    try:
        df = _get_etf_spot_table()
        if df is None or df.empty:
            return {
                "status": "success",
                "code": code,
                "is_exchange_traded": False,
                "market_data_source": _ETF_SPOT_CACHE.get("source", ""),
                "market_metrics": {
                    "成交额": "N/A",
                    "折溢价率": "N/A",
                    "IOPV实时估值": "N/A",
                    "成交量": "N/A",
                    "换手率": "N/A",
                },
            }

        code_col = None
        for c in ["代码", "基金代码", "证券代码", "symbol"]:
            if c in df.columns:
                code_col = c
                break

        if not code_col:
            return {
                "status": "success",
                "code": code,
                "is_exchange_traded": False,
                "market_data_source": _ETF_SPOT_CACHE.get("source", ""),
                "market_metrics": {
                    "成交额": "N/A",
                    "折溢价率": "N/A",
                    "IOPV实时估值": "N/A",
                    "成交量": "N/A",
                    "换手率": "N/A",
                },
            }

        matched = df[df[code_col].astype(str).str.zfill(6) == code]
        if matched.empty:
            return {
                "status": "success",
                "code": code,
                "is_exchange_traded": False,
                "market_data_source": _ETF_SPOT_CACHE.get("source", ""),
                "market_metrics": {
                    "成交额": "N/A",
                    "折溢价率": "N/A",
                    "IOPV实时估值": "N/A",
                    "成交量": "N/A",
                    "换手率": "N/A",
                },
            }

        row = matched.iloc[0]
        turnover_amount = _pick_first_value(row, ["成交额", "成交金额"])
        discount_rate = _pick_first_value(row, ["基金折价率", "折价率", "溢折率", "溢价率"])
        iopv = _pick_first_value(row, ["IOPV实时估值", "IOPV", "参考净值"])
        volume = _pick_first_value(row, ["成交量", "成交手"])
        turnover_ratio = _pick_first_value(row, ["换手率"])

        return {
            "status": "success",
            "code": code,
            "is_exchange_traded": True,
            "market_data_source": _ETF_SPOT_CACHE.get("source", ""),
            "market_metrics": {
                "成交额": turnover_amount if turnover_amount is not None else "N/A",
                "折溢价率": discount_rate if discount_rate is not None else "N/A",
                "IOPV实时估值": iopv if iopv is not None else "N/A",
                "成交量": volume if volume is not None else "N/A",
                "换手率": turnover_ratio if turnover_ratio is not None else "N/A",
            },
        }
    except Exception as e:
        logger.warning(f"获取基金 {code} 场内行情指标失败: {e}")
        return {
            "status": "success",
            "code": code,
            "is_exchange_traded": False,
            "market_data_source": _ETF_SPOT_CACHE.get("source", ""),
            "market_metrics": {
                "成交额": "N/A",
                "折溢价率": "N/A",
                "IOPV实时估值": "N/A",
                "成交量": "N/A",
                "换手率": "N/A",
            },
        }


def _build_index_aliases(index_code: str, index_name: str) -> List[str]:
    """
    基于指数代码和名称动态构造别名（不依赖硬编码字典）

    目标是提升“任意指数”候选基金匹配召回率。
    """
    base_names = {
        str(index_name).strip(),
        str(index_name).replace("指数", "").strip(),
        str(index_name).replace("中证", "").strip(),
        str(index_name).replace("国证", "").strip(),
    }

    # 数字短码：000300 -> 300
    short_code = str(int(index_code)) if index_code.isdigit() else index_code

    aliases = {index_code, short_code}
    for name in base_names:
        if not name or len(name) < 2:
            continue
        aliases.add(name)
        aliases.add(f"{name}ETF")
        aliases.add(f"{name}联接")
        aliases.add(f"{name}指数")

    # 数字形态别名（适配 300ETF / 300联接 这类命名）
    if short_code and len(short_code) >= 2:
        aliases.add(f"{short_code}ETF")
        aliases.add(f"{short_code}联接")
        aliases.add(f"{short_code}指数")

    return list(dict.fromkeys([x for x in aliases if x]))


def _extract_tracking_target(overview_df: pd.DataFrame) -> str:
    """从基金概况中提取跟踪标的信息"""
    if overview_df is None or overview_df.empty:
        return ""

    row = overview_df.iloc[0]
    for col in ("跟踪标的", "跟踪标的指数", "跟踪指数", "业绩比较基准"):
        if col in overview_df.columns and pd.notna(row.get(col)):
            return str(row.get(col)).strip()
    return ""


@lru_cache(maxsize=128)
def get_index_candidate_funds(index_code: str) -> Dict[str, Any]:
    """
    获取某个指数对应的候选基金池（第一步：候选列表）

    逻辑:
      1. 基于基金名称进行初筛
      2. 用基金概况中的跟踪标的信息做二次确认

    Args:
        index_code: 6位指数代码，如 "000300"

    Returns:
        候选基金列表和基础元数据
    """
    if not isinstance(index_code, str) or len(index_code) != 6:
        return {"status": "error", "message": f"无效的指数代码: '{index_code}'"}

    try:
        from . import get_index_info_by_code

        index_info = get_index_info_by_code(index_code)
        if not index_info:
            return {"status": "error", "message": f"未找到指数 {index_code}"}

        index_name = index_info.get("name", "").strip()
        aliases = _build_index_aliases(index_code=index_code, index_name=index_name)
        if not aliases:
            return {"status": "error", "message": f"无法为指数 {index_code} 构造匹配关键词"}

        logger.info(f"正在获取指数 {index_code} 候选基金池...")

        # 先取被动指数基金全集，再按名称筛选
        all_index_funds = ak.fund_info_index_em(symbol="全部", indicator="被动指数型")
        if all_index_funds is None or all_index_funds.empty:
            return {"status": "error", "message": "指数基金列表为空"}

        if "基金名称" not in all_index_funds.columns:
            return {"status": "error", "message": "指数基金列表缺少'基金名称'字段"}

        pattern = "|".join(re.escape(a) for a in aliases if a != index_code)
        candidates = all_index_funds[
            all_index_funds["基金名称"].astype(str).str.contains(pattern, case=False, na=False)
        ].copy()

        # 二次确认：优先使用概况里的跟踪标的
        confirmed_records: List[Dict[str, Any]] = []
        for _, row in candidates.iterrows():
            fund_code = str(row.get("基金代码", "")).zfill(6)
            if not fund_code:
                continue

            tracking_target = str(row.get("跟踪标的", "")).strip()
            try:
                overview = ak.fund_overview_em(symbol=fund_code)
                overview_target = _extract_tracking_target(overview)
                if overview_target:
                    tracking_target = overview_target
            except Exception as e:
                logger.debug(f"获取基金 {fund_code} 概况失败（使用初筛结果）: {e}")

            confirm_text = f"{row.get('基金名称', '')} {tracking_target}"
            is_confirmed = (
                index_name in confirm_text
                or index_name.replace("指数", "") in confirm_text
                or index_code in confirm_text
            )

            if not is_confirmed:
                continue

            confirmed_records.append({
                "基金代码": fund_code,
                "基金名称": row.get("基金名称", ""),
                "跟踪方式": row.get("跟踪方式", ""),
                "跟踪标的": tracking_target or row.get("跟踪标的", ""),
                "单位净值": row.get("单位净值"),
                "日期": row.get("日期"),
                "近1年": row.get("近1年"),
                "手续费": row.get("手续费"),
                "起购金额": row.get("起购金额"),
            })

        confirmed_records.sort(key=lambda x: str(x.get("基金代码", "")))

        return {
            "status": "success",
            "index": {
                "code": index_code,
                "name": index_name,
                "category": index_info.get("category", ""),
            },
            "aliases": aliases,
            "count": len(confirmed_records),
            "funds": confirmed_records,
        }

    except Exception as e:
        logger.error(f"获取指数 {index_code} 候选基金池失败: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

# 全局函数：搜索基金
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

# 基金函数： 获得某个基金的业绩数据
def get_fund_performance(code: str) -> Dict[str, str]:
    """
    获取基金业绩数据

    Args:
        code: 6位基金代码

    Returns:
        业绩数据字典，key为周期（如"近1月"、"近1年"等），value为收益率
    """
    performance = {}
    try:
        logger.info(f"正在查询基金 {code} 的业绩数据...")
        achievement = ak.fund_individual_achievement_xq(symbol=code)

        if achievement.empty:
            return performance

        # 提取阶段业绩
        perf_dict = achievement.to_dict('records')
        for item in perf_dict:
            if item.get('业绩类型') == '阶段业绩':
                cycle = item.get('周期', '')
                return_pct = item.get('本产品区间收益', 0)
                if cycle and return_pct:
                    performance[cycle] = f"{return_pct:.2f}%"

    except KeyError as e:
        # 某些基金在雪球数据源中没有完整的业绩数据，这是正常现象
        logger.debug(f"基金 {code} 在雪球数据源中无业绩数据: {e}")
    except Exception as e:
        logger.warning(f"获取基金业绩失败: {e}")

    return performance

# 基金函数：获得某个基金的风险指标
def get_fund_risk_metrics(code: str) -> Optional[Dict[str, str]]:
    """
    获取基金风险指标

    Args:
        code: 6位基金代码

    Returns:
        风险指标字典，包含年化波动率、夏普比率、最大回撤
    """
    try:
        logger.info(f"正在查询基金 {code} 的风险指标...")
        analysis = ak.fund_individual_analysis_xq(symbol=code)

        if analysis.empty:
            return None

        return calculate_risk_metrics_from_data(analysis)

    except KeyError as e:
        # 某些基金在雪球数据源中没有风险分析数据
        logger.debug(f"基金 {code} 无风险分析数据: {e}")
        return None
    except Exception as e:
        logger.warning(f"获取风险指标失败: {e}")
        return None

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

# 基金函数： 获得某个基金的top10 持仓
def _parse_operating_costs(operating_costs_df: pd.DataFrame) -> Dict[str, str]:
    """
    解析运作费用DataFrame，提取管理费率、托管费率、销售服务费率

    Args:
        operating_costs_df: ak.fund_fee_em(indicator='运作费用') 返回的DataFrame

    Returns:
        费率字典，如 {"管理费率": "1.20%（每年）", "托管费率": "0.20%（每年）"}
    """
    if operating_costs_df.empty:
        return {}

    try:
        # 第一行数据，格式：0列是标签，1列是值，2列是标签，3列是值...
        row = operating_costs_df.iloc[0]
        costs = {}

        for i in range(0, len(operating_costs_df.columns), 2):
            if i + 1 < len(operating_costs_df.columns):
                label = str(row[i]).strip()
                value = str(row[i + 1]).strip()
                costs[label] = value

        return costs
    except Exception as e:
        logger.warning(f"解析运作费用失败: {e}")
        return {}

def get_fund_basic_fee_rates(code: str) -> Dict[str, str]:
    """
    获取基金基础费率（管理费率、托管费率、销售服务费率）

    Args:
        code: 6位基金代码

    Returns:
        基础费率字典
    """
    try:
        logger.info(f"正在查询基金 {code} 的基础费率...")
        operating_costs = ak.fund_fee_em(symbol=code, indicator='运作费用')
        return _parse_operating_costs(operating_costs)
    except Exception as e:
        logger.warning(f"获取基础费率失败: {e}")
        return {}

def get_fund_top_holdings(code: str, year: str) -> list:
    """
    获取基金十大重仓股信息

    Args:
        code: 6位基金代码
        year: 年份（用于获取最新持仓数据）

    Returns:
        重仓股列表，格式为 ["股票名称 (占比)", ...]
    """
    top_holdings = []
    try:
        logger.info(f"正在查询基金 {code} 的十大重仓股...")
        portfolio = ak.fund_portfolio_hold_em(symbol=code, date=year)

        if portfolio.empty:
            return top_holdings

        # 整理十大重仓股
        for _, row in portfolio.head(10).iterrows():
            stock_name = row.get('股票名称', '')
            pct = row.get('占净值比例', 0)
            if stock_name:
                top_holdings.append(f"{stock_name} ({pct:.2f}%)" if pct else stock_name)

    except Exception as e:
        logger.warning(f"获取持仓数据失败: {e}")

    return top_holdings

# 基金函数： 查询某个基金的详细信息
def query_fund_details(code: str, year: str) -> Dict[str, Any]:
    """
    查询基金详细信息

    Args:
        code: 6位基金代码
        year: 年份（用于获取持仓数据）

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

        # 调用独立函数获取业绩和重仓股
        performance = get_fund_performance(code)
        top_holdings = get_fund_top_holdings(code, year)

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

        # 费率信息（调用独立函数）
        fee_rates = get_fund_basic_fee_rates(code)

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

        # 获取风险指标
        risk_metrics = get_fund_risk_metrics(code)
        # 暂时停用场内行情指标抓取（网络链路不稳定）
        # market_metrics_result = get_fund_market_metrics(code)

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
            "top_holdings": top_holdings,
            "is_exchange_traded": False,
            "market_data_source": "",
            "market_metrics": {},
        }

    except Exception as e:
        logger.error(f"查询基金详情失败 {code}: {e}")
        return {"status": "error", "message": f"查询失败: {str(e)}"}

# 基金函数： 获得某个基金的评级信息
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

# 基金函数：获得某个基金的基金经理信息
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

        return {
            "status": "success",
            "managers": managers_list,
            "manager_count": len(managers_list)
        }

    except Exception as e:
        logger.error(f"获取基金经理信息失败 {code}: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

# 基金函数：获得某个基金的持仓分析（向后兼容函数）
def get_fund_holdings_analysis(code: str, year: str, periods: int = 4) -> Dict[str, Any]:
    """
    获取持仓动态分析（向后兼容函数）

    已被 get_fund_portfolio_analysis 取代，保留此函数以保持向后兼容。

    注意：periods 参数已废弃，现在始终返回本年和前一年的完整数据。

    Args:
        code: 基金代码
        year: 年份（用于获取最新持仓数据）
        periods: 废弃参数（保留以兼容旧代码）

    Returns:
        持仓动态分析数据
    """
    # periods 参数已废弃，不再使用
    _ = periods  # 标记为未使用
    result = get_fund_portfolio_analysis(code, year)
    if result.get('status') == 'error':
        return result
    # 只返回持仓分析相关的字段
    return {
        "status": result["status"],
        "code": result["code"],
        "concentration": result["concentration"],
        "holdings_change_by_quarter": result["holdings_change_by_quarter"],
        "latest_top_holdings": result["latest_top_holdings"]
    }


# 基金函数：获得某个基金的投资组合分析（合并函数）
def get_fund_portfolio_analysis(code: str, year: str) -> Dict[str, Any]:
    """
    获取基金投资组合完整分析

    包括：
    - 持仓集中度（前10大持仓占比）
    - 季度持仓变化（本年+前一年，累计买入金额）
    - 最新股票持仓（前10大）
    - 行业配置分布
    - 债券持仓样本

    Args:
        code: 基金代码
        year: 年份（用于获取最新持仓数据，会同时获取本年和前一年的持仓变化）

    Returns:
        投资组合分析数据字典
    """
    if not isinstance(code, str) or len(code) != 6 or not code.isdigit():
        return {"status": "error", "message": f"无效的基金代码格式: '{code}'"}

    try:
        logger.info(f"正在分析基金 {code} 的投资组合...")

        # ========== 1. 获取股票持仓（核心数据） ==========
        latest_holdings = None
        try:
            latest_holdings = ak.fund_portfolio_hold_em(symbol=code, date=year)
        except Exception as e:
            logger.warning(f"获取股票持仓失败: {e}")

        # ========== 2. 计算持仓集中度 ==========
        concentration = {}
        if latest_holdings is not None and not latest_holdings.empty:
            top10_holdings = latest_holdings.head(10)
            if '占净值比例' in top10_holdings.columns:
                total_pct = top10_holdings['占净值比例'].sum()
                concentration = {
                    "前10大持仓占比": f"{total_pct:.2f}%",
                    "持仓集中度": "高" if total_pct > 70 else "中" if total_pct > 50 else "低"
                }

        # ========== 3. 获取季度持仓变化（本年+前一年） ==========
        changes_by_quarter = {}

        # 计算前一年
        prev_year = str(int(year) - 1)
        years_to_fetch = [prev_year, year]

        for year_to_fetch in years_to_fetch:
            try:
                yearly_change = ak.fund_portfolio_change_em(symbol=code, date=year_to_fetch)
                if yearly_change is not None and not yearly_change.empty:
                    if '季度' in yearly_change.columns:
                        # 获取该年所有季度的数据
                        quarters = yearly_change['季度'].unique()
                        for q in quarters:
                            # 如果该季度已存在，跳过（避免重复）
                            if str(q) in changes_by_quarter:
                                continue
                            q_data = yearly_change[yearly_change['季度'] == q].head(10)
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
            except KeyError:
                # akshare 内部 bug：数据格式不匹配（通常是该年份无数据）
                logger.debug(f"基金 {code} 在 {year_to_fetch} 年无持仓变化数据")
            except Exception as e:
                logger.warning(f"获取 {year_to_fetch} 年持仓变化失败: {e}")

        # ========== 4. 获取行业配置 ==========
        industry_allocation = []
        try:
            industry_df = ak.fund_portfolio_industry_allocation_em(symbol=code, date=year)
            if not industry_df.empty:
                for _, row in industry_df.iterrows():
                    industry_allocation.append({
                        "行业类别": row.get('行业类别', ''),
                        "占净值比例": f"{float(row.get('占净值比例', 0)):.2f}%",
                        "市值": f"{float(row.get('市值', 0)):.2f}万" if pd.notna(row.get('市值')) else 'N/A'
                    })
        except Exception as e:
            logger.warning(f"获取行业配置失败: {e}")

        # ========== 5. 获取债券持仓 ==========
        bond_holdings = []
        try:
            bond_df = ak.fund_portfolio_bond_hold_em(symbol=code, date=year)
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

        # ========== 6. 组装返回结果 ==========
        return {
            "status": "success",
            "code": code,
            "year": year,
            # 持仓分析
            "concentration": concentration,
            "holdings_change_by_quarter": changes_by_quarter,
            "latest_top_holdings": latest_holdings.head(10).to_dict('records') if latest_holdings is not None and not latest_holdings.empty else [],
            # 资产配置
            "industry_allocation": industry_allocation,
            "bond_holdings_sample": bond_holdings[:5]
        }

    except Exception as e:
        logger.error(f"投资组合分析失败 {code}: {e}")
        return {"status": "error", "message": f"分析失败: {str(e)}"}

# 基金函数：获得某个基金的资产配置结构（向后兼容函数）
def get_fund_asset_allocation(code: str, date: str) -> Dict[str, Any]:
    """
    获取资产配置结构（向后兼容函数）

    已被 get_fund_portfolio_analysis 取代，保留此函数以保持向后兼容。

    Args:
        code: 基金代码
        date: 年份

    Returns:
        资产配置数据
    """
    result = get_fund_portfolio_analysis(code, date)
    if result.get('status') == 'error':
        return result
    # 只返回资产配置相关的字段，并添加 stock_holdings_sample 以保持兼容
    stock_holdings_sample = []
    for holding in result.get('latest_top_holdings', [])[:5]:
        stock_holdings_sample.append({
            "股票名称": holding.get('股票名称', ''),
            "占净值比例": holding.get('占净值比例', 'N/A')
        })
    return {
        "status": result["status"],
        "code": result["code"],
        "date": result["year"],
        "industry_allocation": result["industry_allocation"],
        "stock_holdings_sample": stock_holdings_sample,
        "bond_holdings_sample": result["bond_holdings_sample"]
    }

# 基金函数：获得某个基金的费用信息
def get_fund_fee_details(code: str) -> Dict[str, Any]:
    """
    获取费用明细
    包括：申购费率、赎回费率、管理费率、托管费率、销售服务费率等

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

        # 1. 获取基础费率（管理费率、托管费率、销售服务费率）- 一次调用
        basic_rates = get_fund_basic_fee_rates(code)
        fee_details.update(basic_rates)

        # 2. 获取交易费率（需要多次调用，但指标不同）
        # 注意：认购费率对已成立基金通常不适用，且akshare有bug，跳过
        fee_indicators = ["申购费率（前端）", "赎回费率"]
        for indicator in fee_indicators:
            try:
                fee_df = ak.fund_fee_em(symbol=code, indicator=indicator)
                if not fee_df.empty:
                    # 使用简化的key，去掉"（前端）"等后缀
                    key = indicator.replace("（前端）", "").replace("（后端）", "")
                    fee_details[key] = fee_df.to_dict('records')
            except Exception as e:
                logger.warning(f"获取{indicator}失败: {e}")

        return {
            "status": "success",
            "code": code,
            "fee_details": fee_details
        }

    except Exception as e:
        logger.error(f"获取费用明细失败 {code}: {e}")
        return {"status": "error", "message": f"获取失败: {str(e)}"}

# 基金函数：获得某个基金的流动性信息
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
