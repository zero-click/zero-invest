# -*- coding: utf-8 -*-
"""
指数数据获取模块

功能:
  1. 从中证指数官网获取所有A股指数列表
  2. 指数分类（宽基/行业/主题/策略/风格）
  3. 提供搜索和查询功能
  4. 获取指数详情（当前值、业绩、PE/PB、分位）

数据源:
  - 中证指数官网: 指数列表 + 历史行情 + 滚动PE
  - 乐咕乐股: PE/PB历史分位（宽基指数）
"""

import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Remove proxy for Chinese sites
for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(k, None)

# 估值温度等级
VALUATION_LEVELS = {
    (0, 10): "极度低估 🥶",
    (10, 20): "低估 🟢",
    (20, 40): "偏低 🟡",
    (40, 60): "合理 🟠",
    (60, 80): "偏高 🔴",
    (80, 90): "高估 🔥",
    (90, 101): "极度高估 🚨",
}

# 乐咕乐股支持的宽基指数（用于获取PE/PB历史分位）
LG_INDEX_MAP = {
    "上证50": "上证50",
    "沪深300": "沪深300",
    "中证500": "中证500",
    "中证800": "中证800",
    "中证100": "中证100",
    "中证1000": "中证1000",
    "上证180": "上证180",
    "上证380": "上证380",
    "创业板50": "创业板50",
    "深证红利": "深证红利",
    "深证100": "深证100",
    "上证红利": "上证红利",
}

def _classify_index(index_class: str, asset_class: str) -> str:
    """
    根据指数类别和资产类别分类

    Args:
        index_class: 指数类别（规模/行业/主题/策略/风格）
        asset_class: 资产类别（股票/固定收益/多资产）

    Returns:
        "broad" | "industry" | "sector" | "strategy" | "style"
    """
    # 只处理股票指数
    if asset_class != "股票":
        return None

    category_map = {
        "规模": "broad",
        "行业": "industry",
        "主题": "sector",
        "策略": "strategy",
        "风格": "style",
    }

    return category_map.get(index_class, None)


def fetch_indices_from_csindex() -> Dict[str, List[Dict]]:
    """
    从中证指数官网获取所有指数列表

    Returns:
        {
            "broad": [...],      # 宽基指数（规模）
            "industry": [...],   # 行业指数
            "sector": [...],     # 主题指数
            "strategy": [...],   # 策略指数
            "style": [...],      # 风格指数
        }
    """
    logger.info("正在从中证指数官网获取指数列表...")

    all_indices = {
        "broad": [],
        "industry": [],
        "sector": [],
        "strategy": [],
        "style": [],
    }

    try:
        df = ak.index_csindex_all()
        logger.info(f"成功获取 {len(df)} 个中证指数")

        for _, row in df.iterrows():
            code = str(row.get("指数代码", ""))
            name = str(row.get("指数简称", ""))
            index_class = str(row.get("指数类别", ""))
            asset_class = str(row.get("资产类别", ""))
            base_date = str(row.get("基日", ""))
            publish_date = str(row.get("发布时间", ""))

            # 分类
            category = _classify_index(index_class, asset_class)
            if not category:
                continue

            all_indices[category].append({
                "code": code,
                "name": name,
                "category": category,
                "index_class": index_class,
                "asset_class": asset_class,
                "base_date": base_date,
                "publish_date": publish_date,
            })

    except Exception as e:
        logger.error(f"从中证指数官网获取数据失败: {e}")
        raise

    # 统计
    total = sum(len(indices) for indices in all_indices.values())
    logger.info(f"指数获取完成: "
               f"{len(all_indices['broad'])} 宽基 + "
               f"{len(all_indices['industry'])} 行业 + "
               f"{len(all_indices['sector'])} 主题 + "
               f"{len(all_indices['strategy'])} 策略 + "
               f"{len(all_indices['style'])} 风格 = "
               f"{total} 总计")

    return all_indices


def search_indices(indices: List[Dict], keyword: str) -> List[Dict]:
    """
    在指数列表中搜索

    Args:
        indices: 指数列表
        keyword: 搜索关键词（代码或名称）

    Returns:
        匹配的指数列表
    """
    results = []
    for idx in indices:
        if (keyword in idx["name"]) or (keyword in idx["code"]):
            results.append(idx)
    return results


def get_index_info(indices: List[Dict], code: str) -> Dict:
    """
    根据代码获取指数详情

    Args:
        indices: 指数列表
        code: 指数代码

    Returns:
        指数信息字典，未找到返回 None
    """
    for idx in indices:
        if idx["code"] == code:
            return idx
    return None


# ============================================================
# 指数详情查询
# ============================================================

def _get_valuation_level(percentile: float) -> str:
    """根据百分位返回估值等级描述"""
    for (low, high), desc in VALUATION_LEVELS.items():
        if low <= percentile < high:
            return desc
    return "N/A"


def _calc_percentile(series: pd.Series, value: float) -> float:
    """计算value在series中的百分位（0-100）"""
    if len(series) == 0:
        return -1.0
    return round(float((series < value).sum() / len(series) * 100), 1)


def _calc_valuation_reference(series: pd.Series, value: float) -> Dict[str, Optional[float]]:
    """计算估值指标在历史区间内的参考值"""
    clean_series = pd.to_numeric(series, errors="coerce").dropna()
    if clean_series.empty:
        return {
            "当前": round(value, 2),
            "中位数": None,
            "最低": None,
            "最高": None,
        }

    return {
        "当前": round(value, 2),
        "中位数": round(float(clean_series.median()), 2),
        "最低": round(float(clean_series.min()), 2),
        "最高": round(float(clean_series.max()), 2),
    }


def _calc_returns(df: pd.DataFrame, current_price: float) -> Dict[str, Optional[float]]:
    """
    计算各个时间段的收益率

    Args:
        df: 历史行情数据
        current_price: 当前价格

    Returns:
        各时间段收益率字典
    """
    if df is None or df.empty:
        return {}

    returns = {}
    periods = {
        "1周": 5,
        "1月": 21,
        "3月": 63,
        "6月": 126,
        "1年": 252,
        "3年": 756,
    }

    for period_name, days in periods.items():
        if len(df) > days:
            past_price = df.iloc[-days]["收盘"]
            ret = (current_price - past_price) / past_price * 100
            returns[f"{period_name}_收益率"] = round(ret, 2)
        else:
            returns[f"{period_name}_收益率"] = None

    # 年初至今收益率
    try:
        year_start = datetime.now().replace(month=1, day=1)
        df_year = df[df["日期"] >= year_start]
        if len(df_year) > 0:
            year_start_price = df_year.iloc[0]["收盘"]
            ytd_ret = (current_price - year_start_price) / year_start_price * 100
            returns["今年收益率"] = round(ytd_ret, 2)
    except:
        returns["今年收益率"] = None

    return returns


def _get_lg_valuation(index_name: str) -> Dict:
    """
    从乐咕乐股获取PE/PB历史分位

    Args:
        index_name: 指数名称

    Returns:
        PE/PB分位数据
    """
    valuation = _build_lg_valuation(index_name=index_name, years=10)
    if not valuation:
        return {}
    return {
        "PE_TTM": valuation.get("PE_TTM"),
        "PB": valuation.get("PB"),
        "PE分位_10年": valuation.get("PE分位_10年"),
        "PE分位_5年": valuation.get("PE分位_5年"),
        "PE分位_3年": valuation.get("PE分位_3年"),
        "PB分位_10年": valuation.get("PB分位_10年"),
        "PB分位_5年": valuation.get("PB分位_5年"),
        "PB分位_3年": valuation.get("PB分位_3年"),
        "PE参考_10年": valuation.get("PE参考_10年"),
        "PB参考_10年": valuation.get("PB参考_10年"),
        "估值等级": valuation.get("估值等级"),
        "估值规则": valuation.get("估值规则"),
        "估值口径": valuation.get("估值口径"),
        "数据点数_10年": valuation.get("数据点数"),
    }


def _build_lg_valuation(index_name: str, years: int = 10) -> Dict:
    """
    构造乐咕乐股估值结果（内部使用）
    """
    if index_name not in LG_INDEX_MAP or years <= 0:
        return {}

    try:
        symbol = LG_INDEX_MAP[index_name]
        df_pe = ak.stock_index_pe_lg(symbol=symbol)
        df_pb = ak.stock_index_pb_lg(symbol=symbol)
        df_pe["日期"] = pd.to_datetime(df_pe["日期"])
        df_pb["日期"] = pd.to_datetime(df_pb["日期"])

        latest_pe = float(df_pe.iloc[-1]["滚动市盈率"])
        latest_pb = float(df_pb.iloc[-1]["市净率"])

        cutoff_main = datetime.now() - timedelta(days=years * 365)
        cutoff_5y = datetime.now() - timedelta(days=5 * 365)
        cutoff_3y = datetime.now() - timedelta(days=3 * 365)
        df_pe_hist = df_pe[df_pe["日期"] >= cutoff_main]
        df_pb_hist = df_pb[df_pb["日期"] >= cutoff_main]

        pe_main = _calc_percentile(df_pe_hist["滚动市盈率"], latest_pe)
        pb_main = _calc_percentile(df_pb_hist["市净率"], latest_pb)
        pe_5y = _calc_percentile(df_pe[df_pe["日期"] >= cutoff_5y]["滚动市盈率"], latest_pe)
        pe_3y = _calc_percentile(df_pe[df_pe["日期"] >= cutoff_3y]["滚动市盈率"], latest_pe)
        pb_5y = _calc_percentile(df_pb[df_pb["日期"] >= cutoff_5y]["市净率"], latest_pb)
        pb_3y = _calc_percentile(df_pb[df_pb["日期"] >= cutoff_3y]["市净率"], latest_pb)

        result = {
            "PE_TTM": round(latest_pe, 2),
            "PB": round(latest_pb, 2),
            "PE分位_5年": pe_5y,
            "PE分位_3年": pe_3y,
            "PB分位_5年": pb_5y,
            "PB分位_3年": pb_3y,
            "估值等级": _get_valuation_level(pe_main),
            "估值规则": f"按 PE-TTM {years}年历史分位划分：<10% 极度低估，10%-20% 低估，20%-40% 偏低，40%-60% 合理，60%-80% 偏高，80%-90% 高估，>=90% 极度高估。",
            "估值口径": {
                "PE_TTM": "乐咕乐股 stock_index_pe_lg 的滚动市盈率",
                "PB": "乐咕乐股 stock_index_pb_lg 的市净率",
                "历史分位": f"当前值在近{years}年、近5年、近3年历史样本中的分位，数值越高表示估值越贵",
                "历史参考": f"近{years}年样本的当前值、中位数、最低值、最高值",
            },
            "数据点数": len(df_pe_hist),
        }

        result[f"PE分位_{years}年"] = pe_main
        result[f"PB分位_{years}年"] = pb_main
        result[f"PE参考_{years}年"] = _calc_valuation_reference(df_pe_hist["滚动市盈率"], latest_pe)
        result[f"PB参考_{years}年"] = _calc_valuation_reference(df_pb_hist["市净率"], latest_pb)
        if years == 10:
            result["PE分位_10年"] = pe_main
            result["PB分位_10年"] = pb_main
            result["PE参考_10年"] = result[f"PE参考_{years}年"]
            result["PB参考_10年"] = result[f"PB参考_{years}年"]
        return result
    except Exception as e:
        logger.warning(f"从乐咕乐股获取估值数据失败 ({index_name}): {e}")
        return {}


def _get_dividend_yield(code: str) -> Optional[Dict]:
    """
    从中证指数获取股息率数据

    Args:
        code: 指数代码（6位），如 "000300"

    Returns:
        股息率数据字典，包含：
        - 股息率1: 基于价格计算的股息率
        - 股息率2: 基于净值计算的股息率
    """
    try:
        # 直接使用原始代码（不需要去掉前导零）
        df = ak.stock_zh_index_value_csindex(symbol=code)
        if df.empty:
            return None

        latest = df.iloc[-1]
        return {
            "股息率1": round(float(latest["股息率1"]), 2),
            "股息率2": round(float(latest["股息率2"]), 2),
        }

    except Exception as e:
        logger.warning(f"获取指数 {code} 股息率失败: {e}")
        return None


def _fetch_index_history_data(code: str) -> Optional[pd.DataFrame]:
    """
    获取指数历史行情数据（内部辅助函数）

    Args:
        code: 指数代码（6位）

    Returns:
        历史行情 DataFrame，包含日期、收盘价等字段
        失败返回 None
    """
    try:
        end_date = datetime.now().strftime("%Y%m%d")
        df_hist = ak.stock_zh_index_hist_csindex(symbol=code, end_date=end_date)

        if df_hist is None or df_hist.empty:
            return None

        df_hist["日期"] = pd.to_datetime(df_hist["日期"])
        return df_hist

    except Exception as e:
        logger.warning(f"获取指数 {code} 历史行情失败: {e}")
        return None


def _get_index_context(code: str) -> Dict:
    """
    获取指数上下文信息

    Args:
        code: 指数代码（6位）

    Returns:
        指数信息字典，未找到返回 None
    """
    from . import get_all_stock_indices

    all_indices = get_all_stock_indices()
    return get_index_info(all_indices, code)


def get_index_query(
    code: str,
    df_hist: Optional[pd.DataFrame] = None,
    index_info: Optional[Dict] = None,
) -> Dict:
    """
    获取指数查询基础数据（基本信息 + 当前值 + 业绩表现）

    Args:
        code: 指数代码（6位），如 "000300", "000905"
        df_hist: 可选历史行情（用于复用）
        index_info: 可选指数基础信息（用于复用）

    Returns:
        基础查询结果
    """
    result = {
        "status": "success",
        "代码": code,
    }

    try:
        if index_info is None:
            index_info = _get_index_context(code)

        if not index_info:
            return {
                "status": "error",
                "message": f"未找到指数 {code}",
            }

        result["名称"] = index_info["name"]
        result["分类"] = index_info["category"]
        result["指数类别"] = index_info.get("index_class", "")
        result["发布日期"] = index_info.get("publish_date", "")

        if df_hist is None or df_hist.empty:
            logger.info(f"正在获取指数 {code} 的历史行情...")
            df_hist = _fetch_index_history_data(code)

        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据",
            }

        latest = df_hist.iloc[-1]
        current_price = float(latest["收盘"])

        result["日期"] = str(latest["日期"].date())
        result["收盘点位"] = round(current_price, 2)
        result["涨跌幅"] = round(float(latest["涨跌幅"]), 2)

        logger.info(f"正在计算指数 {code} 的收益率...")
        returns = _calc_returns(df_hist, current_price)
        result.update(returns)

        result["数据点数"] = len(df_hist)

    except Exception as e:
        logger.error(f"获取指数 {code} 基础查询失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}",
        }

    return result


def get_index_valuation(
    code: str,
    df_hist: Optional[pd.DataFrame] = None,
    index_info: Optional[Dict] = None,
) -> Dict:
    """
    获取指数估值数据（估值 + 股息率 + 分位 + 口径规则）

    Args:
        code: 指数代码（6位）
        df_hist: 可选历史行情（用于复用）
        index_info: 可选指数基础信息（用于复用）

    Returns:
        估值结果
    """
    result = {
        "status": "success",
        "代码": code,
    }

    try:
        if index_info is None:
            index_info = _get_index_context(code)

        if not index_info:
            return {
                "status": "error",
                "message": f"未找到指数 {code}",
            }

        result["名称"] = index_info["name"]

        if df_hist is None or df_hist.empty:
            logger.info(f"正在获取指数 {code} 的历史行情...")
            df_hist = _fetch_index_history_data(code)

        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据",
            }

        latest = df_hist.iloc[-1]

        lg_valuation = _get_lg_valuation(index_info["name"])
        if lg_valuation:
            result.update(lg_valuation)
            result["估值数据源"] = "乐咕乐股"
        else:
            pe_ttm = latest.get("滚动市盈率")
            if pd.notna(pe_ttm):
                result["PE_TTM"] = round(float(pe_ttm), 2)
            result["估值数据源"] = "中证指数"
            result["估值等级"] = "N/A"
            result["估值口径"] = {
                "PE_TTM": "中证指数历史行情接口返回的滚动市盈率",
                "历史分位": "当前数据源未提供足够历史估值样本，暂不计算",
            }

        logger.info(f"正在获取指数 {code} 的股息率...")
        dividend_yield = _get_dividend_yield(code)
        if dividend_yield:
            result.update(dividend_yield)
            result.setdefault("估值口径", {})
            result["估值口径"].update({
                "股息率1": "中证指数 stock_zh_index_value_csindex 的 D/P1（总股本口径）",
                "股息率2": "中证指数 stock_zh_index_value_csindex 的 D/P2（计算用股本口径）",
            })

        result["数据点数"] = len(df_hist)

    except Exception as e:
        logger.error(f"获取指数 {code} 估值数据失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}",
        }

    return result


def get_index_details(code: str) -> Dict:
    """
    获取指数完整详情

    Args:
        code: 指数代码（6位），如 "000300", "000905"

    Returns:
        指数详情字典，包含：
        - 基本信息: 代码、名称、分类、发布日期
        - 当前值: 收盘点位、日期、涨跌幅
        - 业绩表现: 各时间段收益率
        - 估值数据: PE、PB及分位
        - 估值等级: 低估/合理/高估
    """
    try:
        index_info = _get_index_context(code)
        if not index_info:
            return {
                "status": "error",
                "message": f"未找到指数 {code}",
            }

        df_hist = _fetch_index_history_data(code)
        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据",
            }

        query_result = get_index_query(code, df_hist=df_hist, index_info=index_info)
        if query_result.get("status") == "error":
            return query_result

        valuation_result = get_index_valuation(code, df_hist=df_hist, index_info=index_info)
        if valuation_result.get("status") == "error":
            return valuation_result

        result = dict(query_result)
        for key, value in valuation_result.items():
            if key != "status":
                result[key] = value

    except Exception as e:
        logger.error(f"获取指数 {code} 详情失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}"
        }

    return result


def get_index_details_batch(codes: List[str]) -> Dict[str, Dict]:
    """
    批量获取指数详情

    Args:
        codes: 指数代码列表

    Returns:
        批量查询结果 {code: details}
    """
    results = {}

    for code in codes:
        results[code] = get_index_details(code)

    return results


# ============================================================
# 指数风险分析
# ============================================================

def _calc_volatility(df: pd.DataFrame, period_days: int = 252) -> Optional[float]:
    """
    计算年化波动率

    Args:
        df: 历史行情数据
        period_days: 年化交易日数（默认252）

    Returns:
        年化波动率（百分比）
    """
    if df is None or len(df) < 2:
        return None

    try:
        # 计算日收益率
        closes = df["收盘"].astype(float)
        returns = closes.pct_change().dropna()

        # 年化波动率 = 日收益率标准差 * sqrt(252)
        volatility = returns.std() * np.sqrt(period_days) * 100
        return round(float(volatility), 2)

    except Exception as e:
        logger.warning(f"计算波动率失败: {e}")
        return None


def _calc_max_drawdown(df: pd.DataFrame) -> Dict[str, any]:
    """
    计算最大回撤

    Args:
        df: 历史行情数据

    Returns:
        {
            "最大回撤": -25.5,  # 百分比
            "回撤开始日期": "2021-02-18",
            "回撤结束日期": "2022-04-26",
            "回撤持续天数": 432
        }
    """
    if df is None or len(df) < 2:
        return {}

    try:
        closes = df["收盘"].astype(float)
        dates = df["日期"]

        # 计算累计最高点
        cummax = closes.cummax()

        # 计算回撤
        drawdown = (closes - cummax) / cummax * 100

        # 找到最大回撤
        max_dd_idx = drawdown.idxmin()
        max_dd_value = drawdown.loc[max_dd_idx]

        # 找到回撤开始点（最高点）
        peak_idx = closes[:max_dd_idx].idxmax()

        # 找到回撤结束点（如果已经恢复）
        recovery_idx = None
        recovery_date = None
        recovery_days = None

        if max_dd_idx < len(df) - 1:
            # 检查是否恢复到回撤前的高点
            for i in range(max_dd_idx + 1, len(df)):
                if closes.loc[i] >= closes.loc[peak_idx]:
                    recovery_idx = i
                    break

        peak_date = dates.loc[peak_idx].strftime("%Y-%m-%d")
        bottom_date = dates.loc[max_dd_idx].strftime("%Y-%m-%d")

        result = {
            "最大回撤": round(float(max_dd_value), 2),
            "回撤开始日期": peak_date,
            "回撤最低日期": bottom_date,
            "回撤持续天数": int((dates.loc[max_dd_idx] - dates.loc[peak_idx]).days),
        }

        if recovery_idx is not None:
            recovery_date = dates.loc[recovery_idx].strftime("%Y-%m-%d")
            recovery_days = int((dates.loc[recovery_idx] - dates.loc[peak_idx]).days)
            result["回撤修复日期"] = recovery_date
            result["回撤修复天数"] = recovery_days
        else:
            # 未恢复，计算截至现在的天数
            result["回撤修复日期"] = None
            result["回撤修复天数"] = None
            result["未恢复天数"] = int((dates.iloc[-1] - dates.loc[peak_idx]).days)

        return result

    except Exception as e:
        logger.warning(f"计算最大回撤失败: {e}")
        return {}


def _calc_drawdown_recovery_periods(df: pd.DataFrame) -> Dict[str, any]:
    """
    分析历史回撤修复周期

    Args:
        df: 历史行情数据

    Returns:
        {
            "平均回撤修复天数": 150,
            "最长回撤修复天数": 400,
            "最短回撤修复天数": 30,
            "未恢复回撤数": 1
        }
    """
    if df is None or len(df) < 2:
        return {}

    try:
        closes = df["收盘"].astype(float)
        dates = df["日期"]

        # 找到所有显著回撤（超过5%）
        cummax = closes.cummax()
        drawdown = (closes - cummax) / cummax * 100

        # 找回撤开始点
        drawdown_starts = []
        in_drawdown = False
        threshold = -5  # 5%以上才算显著回撤

        for i in range(len(drawdown)):
            if not in_drawdown and drawdown.iloc[i] <= threshold:
                drawdown_starts.append(i)
                in_drawdown = True
            elif in_drawdown and drawdown.iloc[i] > threshold:
                in_drawdown = False

        recovery_periods = []
        unrecovered_count = 0

        for start_idx in drawdown_starts:
            peak_price = closes.loc[start_idx]

            # 向前找最高点
            actual_peak_idx = closes[:start_idx].idxmax()

            # 向后找恢复点
            recovered = False
            for i in range(start_idx, len(df)):
                if closes.loc[i] >= peak_price:
                    recovery_days = int((dates.loc[i] - dates.loc[actual_peak_idx]).days)
                    recovery_periods.append(recovery_days)
                    recovered = True
                    break

            if not recovered:
                unrecovered_count += 1

        if recovery_periods:
            return {
                "显著回撤次数": len(drawdown_starts),
                "平均回撤修复天数": round(sum(recovery_periods) / len(recovery_periods)),
                "最长回撤修复天数": max(recovery_periods),
                "最短回撤修复天数": min(recovery_periods),
                "未恢复回撤数": unrecovered_count,
            }
        else:
            return {}

    except Exception as e:
        logger.warning(f"计算回撤修复周期失败: {e}")
        return {}


def _calc_sharpe_ratio(df: pd.DataFrame, risk_free_rate: float = 0.03) -> Optional[float]:
    """
    计算夏普比率（年化）

    Args:
        df: 历史行情数据
        risk_free_rate: 无风险利率（年化，默认3%）

    Returns:
        夏普比率
    """
    if df is None or len(df) < 2:
        return None

    try:
        closes = df["收盘"].astype(float)

        # 计算日收益率
        returns = closes.pct_change().dropna()

        # 年化收益率 = 日收益率均值 * 252
        annual_return = returns.mean() * 252

        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252)

        if annual_volatility == 0:
            return None

        # 夏普比率 = (年化收益 - 无风险利率) / 年化波动率
        excess_return = annual_return - risk_free_rate
        sharpe = excess_return / annual_volatility

        return round(float(sharpe), 2)

    except Exception as e:
        logger.warning(f"计算夏普比率失败: {e}")
        return None


def get_index_risk(code: str, df_hist: Optional[pd.DataFrame] = None) -> Dict:
    """
    获取指数风险分析

    Args:
        code: 指数代码（6位）
        df_hist: 可选的历史行情数据（复用已有数据，避免重复网络调用）

    Returns:
        风险分析字典，包含：
        - 收益率: 近1月/3月/6月/1年收益率
        - 波动率: 年化波动率
        - 最大回撤: 回撤幅度、时间、修复情况
        - 回撤分析: 历史回撤修复周期统计
        - 夏普比率: 风险调整后收益
    """
    result = {
        "status": "success",
        "代码": code,
    }

    try:
        # 1. 获取历史行情数据（复用已有数据或重新获取）
        if df_hist is None or df_hist.empty:
            logger.info(f"正在获取指数 {code} 的历史行情...")
            df_hist = _fetch_index_history_data(code)

        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据"
            }

        # 2. 获取指数基本信息
        from . import get_all_stock_indices
        all_indices = get_all_stock_indices()
        index_info = get_index_info(all_indices, code)

        if index_info:
            result["名称"] = index_info["name"]

        latest = df_hist.iloc[-1]
        current_price = float(latest["收盘"])

        # 3. 计算各时间段收益率
        logger.info(f"正在计算指数 {code} 的收益率...")
        returns = _calc_returns(df_hist, current_price)
        result.update({
            "近1月收益率": returns.get("1月_收益率"),
            "近3月收益率": returns.get("3月_收益率"),
            "近6月收益率": returns.get("6月_收益率"),
            "近1年收益率": returns.get("1年_收益率"),
        })

        # 4. 计算年化波动率（按时间段）
        logger.info(f"正在计算指数 {code} 的波动率...")
        for period_name, days in [("1年", 252), ("3年", 756)]:
            if len(df_hist) > days:
                df_period = df_hist.tail(days)
                vol = _calc_volatility(df_period)
                result[f"近{period_name}波动率"] = vol

        # 全历史波动率
        result["历史波动率"] = _calc_volatility(df_hist)

        # 5. 计算最大回撤
        logger.info(f"正在计算指数 {code} 的最大回撤...")
        max_dd = _calc_max_drawdown(df_hist)
        result.update(max_dd)

        # 6. 分析回撤修复周期
        logger.info(f"正在分析指数 {code} 的回撤修复周期...")
        recovery_analysis = _calc_drawdown_recovery_periods(df_hist)
        if recovery_analysis:
            result["回撤修复分析"] = recovery_analysis

        # 7. 计算夏普比率
        logger.info(f"正在计算指数 {code} 的夏普比率...")
        sharpe = _calc_sharpe_ratio(df_hist)
        if sharpe is not None:
            result["夏普比率"] = sharpe

        # 8. 数据完整性
        result["数据点数"] = len(df_hist)
        result["数据起始日期"] = str(df_hist.iloc[0]["日期"].date())
        result["数据截止日期"] = str(df_hist.iloc[-1]["日期"].date())

    except Exception as e:
        logger.error(f"获取指数 {code} 风险分析失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}"
        }

    return result


# ============================================================
# 指数便捷函数
# ============================================================

def get_broad_indices() -> List[Dict]:
    """获取宽基指数列表（规模类）"""
    from . import get_index_list
    data = get_index_list()
    return data.get("broad", [])


def get_industry_indices() -> List[Dict]:
    """获取行业指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("industry", [])


def get_sector_indices() -> List[Dict]:
    """获取主题指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("sector", [])


def get_strategy_indices() -> List[Dict]:
    """获取策略指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("strategy", [])


def get_style_indices() -> List[Dict]:
    """获取风格指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("style", [])


def get_all_stock_indices() -> List[Dict]:
    """获取所有股票指数"""
    from . import get_index_list
    data = get_index_list()
    all_indices = []
    for cat in ["broad", "industry", "sector", "strategy", "style"]:
        all_indices.extend(data.get(cat, []))
    return all_indices


def search_indices_all(keyword: str) -> List[Dict]:
    """
    搜索指数（按名称或代码）

    Args:
        keyword: 搜索关键词

    Returns:
        匹配的指数列表
    """
    all_indices = get_all_stock_indices()
    return search_indices(all_indices, keyword)


def get_index_info_by_code(code: str) -> Dict:
    """
    根据代码获取指数详情

    Args:
        code: 指数代码

    Returns:
        指数信息字典，未找到返回 None
    """
    all_indices = get_all_stock_indices()
    return get_index_info(all_indices, code)
