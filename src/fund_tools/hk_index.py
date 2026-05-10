# -*- coding: utf-8 -*-
"""
港股指数数据模块

功能:
  1. 港股指数实时行情查询（多源 fallback）
  2. 港股指数历史行情查询（多源 fallback）

数据源:
  - 新浪财经: stock_hk_index_spot_sina() / stock_hk_index_daily_sina() (主)
  - 东方财富: stock_hk_index_spot_em() / stock_hk_index_daily_em() (备)
"""

import os
import logging
from typing import Any, Dict

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)

DATA_DELAY_NOTE = "数据可能有15分钟延迟，仅供参考"


def _clear_proxy_env() -> None:
    """移除代理环境变量，避免访问国内数据源时被本地代理干扰"""
    for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(key, None)


def _fetch_with_fallback(primary_fn, fallback_fn, source_name: str) -> tuple:
    """
    双源 fallback 获取数据

    Args:
        primary_fn: 主数据源函数
        fallback_fn: 备用数据源函数
        source_name: 数据名称（用于日志）

    Returns:
        (DataFrame, source_name) 或 (None, None)
    """
    # 尝试主数据源
    try:
        _clear_proxy_env()
        df = primary_fn()
        if df is not None and not df.empty:
            return df, "sina"
    except Exception as e:
        logger.warning(f"获取{source_name}（新浪）失败: {e}")

    # 尝试备用数据源
    try:
        _clear_proxy_env()
        df = fallback_fn()
        if df is not None and not df.empty:
            return df, "em"
    except Exception as e:
        logger.warning(f"获取{source_name}（东方财富）失败: {e}")

    return None, None


def get_hk_index_spot() -> Dict[str, Any]:
    """
    获取港股指数实时行情

    数据源优先级：新浪 → 东方财富（fallback）

    Returns:
        成功: {status, source, count, data_delay_note, data: [...]}
        失败: {status: "error", message: "港股指数行情暂时不可用，请稍后重试"}
    """
    df, source = _fetch_with_fallback(
        primary_fn=ak.stock_hk_index_spot_sina,
        fallback_fn=ak.stock_hk_index_spot_em,
        source_name="港股指数实时行情",
    )

    if df is None:
        return {
            "status": "error",
            "message": "港股指数行情暂时不可用，请稍后重试",
        }

    return {
        "status": "success",
        "source": source,
        "count": len(df),
        "data_delay_note": DATA_DELAY_NOTE,
        "data": df.to_dict("records"),
    }


def get_hk_index_daily(symbol: str, days: int = 30) -> Dict[str, Any]:
    """
    获取港股指数历史行情

    数据源优先级：新浪 → 东方财富（fallback）

    Args:
        symbol: 指数代码（如 CES100）
        days: 返回最近多少天的数据（范围 1-365，默认 30）

    Returns:
        成功: {status, symbol, count, data: [...]}
        参数错误: {status: "error", message: "..."}
        接口失败: {status: "error", message: "..."}
    """
    # 参数校验
    if days <= 0:
        return {"status": "error", "message": "days 必须 > 0"}
    if days > 365:
        return {"status": "error", "message": "days 不能超过 365"}
    if not symbol or not symbol.strip():
        return {"status": "error", "message": "指数代码不能为空"}

    symbol = symbol.strip()

    def _fetch_sina():
        return ak.stock_hk_index_daily_sina(symbol=symbol)

    def _fetch_em():
        return ak.stock_hk_index_daily_em(symbol=symbol)

    df, source = _fetch_with_fallback(
        primary_fn=_fetch_sina,
        fallback_fn=_fetch_em,
        source_name=f"港股指数历史行情({symbol})",
    )

    if df is None:
        return {
            "status": "error",
            "message": f"获取港股指数历史行情失败: {symbol}",
        }

    # 取最近 N 天
    if len(df) > days:
        df = df.tail(days)

    return {
        "status": "success",
        "symbol": symbol,
        "source": source,
        "count": len(df),
        "data": df.to_dict("records"),
    }
