# -*- coding: utf-8 -*-
"""
指数估值模块 - 基于 akshare 的指数PE/PB/历史分位查询

数据源:
  - 乐咕乐股 (stock_index_pe_lg / stock_index_pb_lg): 宽基指数PE/PB历史数据
  - 中证指数 (stock_zh_index_value_csindex): 行业/主题指数估值

功能:
  1. 查询单个指数的当前PE/PB及历史分位
  2. 批量查询多个指数估值
  3. 计算估值百分位（近10年/近5年/近3年）
  4. 估值温度计（低估/合理/高估）
"""

import os
import warnings
from datetime import datetime, timedelta
from typing import Optional

import akshare as ak
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# Remove proxy for Chinese sites
for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(k, None)

# ============================================================
# Constants
# ============================================================

# 乐咕乐股支持的宽基指数
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

# 中证指数支持的行业/主题指数 (code -> name)
CSINDEX_MAP = {
    "000300": ("沪深300", "000300"),
    "000905": ("中证500", "000905"),
    "000852": ("中证1000", "000852"),
    "000016": ("上证50", "000016"),
    "399006": ("创业板指", "399006"),
    "000688": ("科创50", "000688"),
    "399967": ("中证军工", "399967"),
    "000819": ("有色金属", "000819"),
    "399987": ("中证白酒", "399987"),
    "000991": ("全指医药", "000991"),
    "H30225": ("中证机器人", "H30225"),
    "399971": ("中证传媒", "399971"),
    "399997": ("中证白酒", "399997"),
    "H30166": ("CS创新药", "H30166"),
    "931865": ("中证半导", "931865"),
    "H30174": ("中证新能源", "H30174"),
}

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


def get_index_pe(symbol: str, years: int = 10) -> dict:
    """
    获取乐咕乐股指数PE数据及历史分位
    
    Args:
        symbol: 指数名称，如 "沪深300", "中证500"
        years: 计算分位的历史年数（默认10年）
    
    Returns:
        dict with pe, pb, percentiles, valuation_level
    """
    if symbol not in LG_INDEX_MAP:
        return {"status": "error", "message": f"不支持的指数: {symbol}。支持: {list(LG_INDEX_MAP.keys())}"}
    
    symbol = LG_INDEX_MAP[symbol]
    cutoff_date = (datetime.now() - timedelta(days=years * 365)).strftime("%Y-%m-%d")
    
    try:
        # Get PE data
        df_pe = ak.stock_index_pe_lg(symbol=symbol)
        df_pe["日期"] = pd.to_datetime(df_pe["日期"])
        
        # Get PB data
        df_pb = ak.stock_index_pb_lg(symbol=symbol)
        df_pb["日期"] = pd.to_datetime(df_pb["日期"])
        
        # Latest values
        latest_pe_row = df_pe.iloc[-1]
        latest_pb_row = df_pb.iloc[-1]
        
        pe_ttm = float(latest_pe_row["滚动市盈率"])
        pb = float(latest_pb_row["市净率"])
        date_str = latest_pe_row["日期"].strftime("%Y-%m-%d")
        index_value = float(latest_pe_row["指数"])
        
        # Calculate percentiles from cutoff
        df_pe_hist = df_pe[df_pe["日期"] >= cutoff_date]
        df_pb_hist = df_pb[df_pb["日期"] >= cutoff_date]
        
        pe_10y = _calc_percentile(df_pe_hist["滚动市盈率"], pe_ttm)
        pb_10y = _calc_percentile(df_pb_hist["市净率"], pb)
        
        # Also 5y and 3y
        cutoff_5y = (datetime.now() - timedelta(days=5 * 365)).strftime("%Y-%m-%d")
        cutoff_3y = (datetime.now() - timedelta(days=3 * 365)).strftime("%Y-%m-%d")
        
        pe_5y = _calc_percentile(df_pe_hist[df_pe_hist["日期"] >= cutoff_5y]["滚动市盈率"], pe_ttm)
        pe_3y = _calc_percentile(df_pe_hist[df_pe_hist["日期"] >= cutoff_3y]["滚动市盈率"], pe_ttm)
        pb_5y = _calc_percentile(df_pb_hist[df_pb_hist["日期"] >= cutoff_5y]["市净率"], pb)
        pb_3y = _calc_percentile(df_pb_hist[df_pb_hist["日期"] >= cutoff_3y]["市净率"], pb)
        
        return {
            "status": "success",
            "指数": symbol,
            "日期": date_str,
            "收盘点位": index_value,
            "PE_TTM": round(pe_ttm, 2),
            "PB": round(pb, 2),
            "PE分位_10年": pe_10y,
            "PE分位_5年": pe_5y,
            "PE分位_3年": pe_3y,
            "PB分位_10年": pb_10y,
            "PB分位_5年": pb_5y,
            "PB分位_3年": pb_3y,
            "估值等级": _get_valuation_level(pe_10y),
            "数据点数": len(df_pe_hist),
        }
    except Exception as e:
        return {"status": "error", "message": f"查询失败: {str(e)}"}


def get_csindex_valuation(symbol: str) -> dict:
    """
    获取中证指数估值数据（支持行业/主题指数）
    
    Args:
        symbol: 指数代码，如 "000300", "H30225"
    
    Returns:
        dict with PE, dividend yield from CSIndex
    """
    try:
        df = ak.stock_zh_index_value_csindex(symbol=symbol)
        if df is None or df.empty:
            return {"status": "error", "message": f"未找到指数 {symbol} 的估值数据"}
        
        latest = df.iloc[-1]
        name = str(latest.get("指数中文简称", symbol))
        
        return {
            "status": "success",
            "指数代码": symbol,
            "指数名称": name,
            "日期": str(latest.get("日期", "")),
            "市盈率1": latest.get("市盈率1"),  # 静态PE
            "市盈率2": latest.get("市盈率2"),  # 滚动PE
            "股息率1": latest.get("股息率1"),  # 近12月股息率
            "股息率2": latest.get("股息率2"),  # 预期股息率
        }
    except Exception as e:
        return {"status": "error", "message": f"查询中证指数估值失败: {str(e)}"}


def get_index_valuation_batch(
    lg_indices: Optional[list] = None,
    csindex_codes: Optional[list] = None,
) -> dict:
    """
    批量查询指数估值
    
    Args:
        lg_indices: 乐咕乐股指数名称列表，如 ["沪深300", "中证500"]
        csindex_codes: 中证指数代码列表，如 ["399967", "000819"]
    
    Returns:
        dict with all valuation results
    """
    results = {"乐咕宽基指数": {}, "中证行业指数": {}}
    
    # Query LG indices
    if lg_indices:
        for name in lg_indices:
            r = get_index_pe(name)
            results["乐咕宽基指数"][name] = r
    
    # Query CSIndex indices
    if csindex_codes:
        for code in csindex_codes:
            display_name = CSINDEX_MAP.get(code, (code, code))[0]
            r = get_csindex_valuation(code)
            results["中证行业指数"][display_name] = r
    
    return results


def get_portfolio_index_valuation() -> dict:
    """
    一键获取投资组合相关的所有指数估值
    包含: 宽基指数(6个) + 行业指数(11个)
    
    Returns:
        dict with structured valuation data for all relevant indices
    """
    lg_indices = ["沪深300", "中证500", "中证1000", "上证50", "创业板50", "深证红利"]
    csindex_codes = [
        "000688",   # 科创50
        "399967",   # 中证军工
        "000819",   # 有色金属
        "399987",   # 中证白酒
        "000991",   # 全指医药
        "H30225",   # 中证机器人
        "931865",   # 中证半导
        "H30174",   # 中证新能源
    ]
    
    return get_index_valuation_batch(lg_indices=lg_indices, csindex_codes=csindex_codes)


def compare_fund_with_index(fund_code: str, index_name: str = "沪深300") -> dict:
    """
    对比基金与指数的估值情况
    
    Args:
        fund_code: 基金代码 (6位)
        index_name: 对比的指数名称
    
    Returns:
        dict with fund details + index valuation comparison
    """
    from fund_tool_akshare import query_fund_details
    
    fund_result = query_fund_details(fund_code)
    index_result = get_index_pe(index_name)
    
    return {
        "基金": fund_result,
        "对比指数": index_result,
    }
