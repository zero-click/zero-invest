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
    if index_name not in LG_INDEX_MAP:
        return {}

    try:
        symbol = LG_INDEX_MAP[index_name]

        # Get PE data
        df_pe = ak.stock_index_pe_lg(symbol=symbol)
        df_pe["日期"] = pd.to_datetime(df_pe["日期"])

        # Get PB data
        df_pb = ak.stock_index_pb_lg(symbol=symbol)
        df_pb["日期"] = pd.to_datetime(df_pb["日期"])

        # Latest values
        latest_pe = float(df_pe.iloc[-1]["滚动市盈率"])
        latest_pb = float(df_pb.iloc[-1]["市净率"])

        # Calculate percentiles (10年)
        cutoff_date = datetime.now() - timedelta(days=10 * 365)
        df_pe_hist = df_pe[df_pe["日期"] >= cutoff_date]
        df_pb_hist = df_pb[df_pb["日期"] >= cutoff_date]

        pe_10y = _calc_percentile(df_pe_hist["滚动市盈率"], latest_pe)
        pb_10y = _calc_percentile(df_pb_hist["市净率"], latest_pb)

        # Also 5y and 3y
        cutoff_5y = datetime.now() - timedelta(days=5 * 365)
        cutoff_3y = datetime.now() - timedelta(days=3 * 365)

        pe_5y = _calc_percentile(df_pe_hist[df_pe_hist["日期"] >= cutoff_5y]["滚动市盈率"], latest_pe)
        pe_3y = _calc_percentile(df_pe_hist[df_pe_hist["日期"] >= cutoff_3y]["滚动市盈率"], latest_pe)
        pb_5y = _calc_percentile(df_pb_hist[df_pb_hist["日期"] >= cutoff_5y]["市净率"], latest_pb)
        pb_3y = _calc_percentile(df_pb_hist[df_pb_hist["日期"] >= cutoff_3y]["市净率"], latest_pb)

        return {
            "PE_TTM": round(latest_pe, 2),
            "PB": round(latest_pb, 2),
            "PE分位_10年": pe_10y,
            "PE分位_5年": pe_5y,
            "PE分位_3年": pe_3y,
            "PB分位_10年": pb_10y,
            "PB分位_5年": pb_5y,
            "PB分位_3年": pb_3y,
            "估值等级": _get_valuation_level(pe_10y),
            "数据点数_10年": len(df_pe_hist),
        }

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
    result = {
        "status": "success",
        "代码": code,
    }

    try:
        # 1. 获取指数基本信息（使用已有的 get_index_info 函数）
        from . import get_all_stock_indices
        all_indices = get_all_stock_indices()
        index_info = get_index_info(all_indices, code)

        if not index_info:
            return {
                "status": "error",
                "message": f"未找到指数 {code}"
            }

        result["名称"] = index_info["name"]
        result["分类"] = index_info["category"]
        result["指数类别"] = index_info.get("index_class", "")
        result["发布日期"] = index_info.get("publish_date", "")

        # 2. 获取历史行情数据（包含收盘价和滚动PE）
        logger.info(f"正在获取指数 {code} 的历史行情...")
        end_date = datetime.now().strftime("%Y%m%d")
        df_hist = ak.stock_zh_index_hist_csindex(symbol=code, end_date=end_date)

        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据"
            }

        df_hist["日期"] = pd.to_datetime(df_hist["日期"])
        latest = df_hist.iloc[-1]

        # 3. 当前值
        result["日期"] = str(latest["日期"].date())
        result["收盘点位"] = round(float(latest["收盘"]), 2)
        result["涨跌幅"] = round(float(latest["涨跌幅"]), 2)

        # 4. 业绩表现
        logger.info(f"正在计算指数 {code} 的收益率...")
        returns = _calc_returns(df_hist, float(latest["收盘"]))
        result.update(returns)

        # 5. PE/PB数据（优先从乐咕乐股获取历史分位）
        lg_valuation = _get_lg_valuation(index_info["name"])
        if lg_valuation:
            result.update(lg_valuation)
            result["估值数据源"] = "乐咕乐股"
        else:
            # 使用中证指数的滚动PE（没有历史分位）
            pe_ttm = latest.get("滚动市盈率")
            if pd.notna(pe_ttm):
                result["PE_TTM"] = round(float(pe_ttm), 2)
            result["估值数据源"] = "中证指数"
            result["估值等级"] = "N/A"

        # 6. 股息率数据
        logger.info(f"正在获取指数 {code} 的股息率...")
        dividend_yield = _get_dividend_yield(code)
        if dividend_yield:
            result.update(dividend_yield)

        # 7. 数据完整性标记
        result["数据点数"] = len(df_hist)

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

