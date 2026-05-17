# -*- coding: utf-8 -*-
"""
沪深港通资金流分析模块

数据源: akshare - 东方财富沪深港通数据
  - stock_hsgt_fund_flow_summary_em(): 今日资金流总览
  - stock_hsgt_hist_em(symbol): 历史资金流

注意: 2024-08-19 起北向资金净买额不再公布（沪深港交易所政策变更）。
北向通道返回 data_available=False，南向数据正常。

约束:
  - 所有函数返回 {status: "success/error", ...} 字典
  - 2024-08-19 后北向字段为 NaN/0，需防御性处理
"""

import logging

import akshare as ak
import pandas as pd

logger = logging.getLogger(__name__)

# === 常量映射 ===

DIRECTION_MAP = {
    "北向": "北向资金",
    "沪股通": "沪股通",
    "深股通": "深股通",
    "南向": "南向资金",
    "港股通沪": "港股通沪",
    "港股通深": "港股通深",
}

# 北向方向（净买额不再公布）
NORTHBOUND_DIRECTIONS = {"北向", "沪股通", "深股通"}

TRADE_STATUS_MAP = {1: "盘前", 2: "交易中", 3: "已收盘"}

MAX_HISTORY_DAYS = 365


# === 辅助函数 ===


def _safe_float(val):
    """NaN/无效值 → None, 有效数值 → round(float, 2)"""
    if val is None:
        return None
    try:
        v = pd.to_numeric(val, errors="coerce")
    except (TypeError, ValueError):
        return None
    if pd.isna(v):
        return None
    return round(float(v), 2)


def _safe_int(val):
    """NaN/无效值 → None, 有效数值 → int"""
    if val is None:
        return None
    try:
        v = pd.to_numeric(val, errors="coerce")
    except (TypeError, ValueError):
        return None
    if pd.isna(v):
        return None
    return int(v)


def _parse_trade_status(val):
    """交易状态数字转文字: 1=盘前, 2=交易中, 3=已收盘"""
    try:
        num = int(float(val))
        return TRADE_STATUS_MAP.get(num, str(val))
    except (TypeError, ValueError):
        return str(val) if val is not None else ""


# === 核心函数 ===


def get_capital_flow_summary() -> dict:
    """
    获取沪深港通今日资金流总览。

    数据源: ak.stock_hsgt_fund_flow_summary_em()
    实际返回 4 行: 沪股通(北向), 港股通(沪)(南向), 深股通(北向), 港股通(深)(南向)

    注意: 2024-08-19 后北向通道 net_buy 字段为 0，标记 data_available=False。

    Returns:
        {status, date, channels: [{name, type, direction, data_available, ...}]}
    """
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is None or df.empty:
            return {"status": "error", "message": "暂无资金流数据"}

        date = str(df["交易日"].iloc[0])
        channels = []
        for _, row in df.iterrows():
            direction = row["资金方向"]
            channel = {
                "name": row["板块"],
                "type": row["类型"],
                "direction": direction,
                "trade_status": _parse_trade_status(row["交易状态"]),
                "net_buy": _safe_float(row["成交净买额"]),
                "fund_inflow": _safe_float(row["资金净流入"]),
                "balance": _safe_float(row["当日资金余额"]),
                "up_count": _safe_int(row["上涨数"]),
                "flat_count": _safe_int(row["持平数"]),
                "down_count": _safe_int(row["下跌数"]),
                "index_name": row["相关指数"],
                "index_change_pct": _safe_float(row["指数涨跌幅"]),
            }
            # 标记北向数据不可用
            if direction in NORTHBOUND_DIRECTIONS or direction == "北向":
                channel["data_available"] = False
            channels.append(channel)

        return {"status": "success", "date": date, "channels": channels}

    except Exception as e:
        logger.error(f"获取资金流总览失败: {e}")
        return {"status": "error", "message": f"获取资金流总览失败: {e}"}


def get_capital_flow_history(direction: str = "南向", days: int = 20) -> dict:
    """
    查询沪深港通历史资金流数据。

    数据源: ak.stock_hsgt_hist_em(symbol)
    注: 返回全部历史数据（~2664行），客户端按 days 截取尾部。

    Args:
        direction: 方向，默认"南向"。可选见 DIRECTION_MAP
        days: 返回天数，默认20，最大365

    Returns:
        {status, direction, days, data_available, summary: {trend, ...}, data: [{date, net_buy, ...}]}
    """
    if direction not in DIRECTION_MAP:
        return {
            "status": "error",
            "message": f"无效方向 '{direction}'，支持: {list(DIRECTION_MAP.keys())}",
        }

    days = max(1, min(days, MAX_HISTORY_DAYS))

    # 北向方向标记数据不可用
    is_northbound = direction in NORTHBOUND_DIRECTIONS

    try:
        symbol = DIRECTION_MAP[direction]
        df = ak.stock_hsgt_hist_em(symbol=symbol)

        if df is None or df.empty:
            return {"status": "error", "message": "暂无历史资金流数据"}

        # 截取尾部 N 天
        df = df.tail(days).reset_index(drop=True)

        # === 趋势计算（仅基于非 NaN 的净买额） ===
        net_buys = pd.to_numeric(df["当日成交净买额"], errors="coerce").dropna()
        if len(net_buys) > 0:
            positive_ratio = (net_buys > 0).sum() / len(net_buys)
            if positive_ratio >= 0.7:
                trend = "持续流入"
            elif positive_ratio <= 0.3:
                trend = "持续流出"
            else:
                trend = "震荡"

            cumulative_net_buy = round(float(net_buys.sum()), 2)
            daily_avg_net_buy = round(float(net_buys.mean()), 2)

            # 最大单日流入/流出
            max_inflow_idx = net_buys.idxmax()
            max_outflow_idx = net_buys.idxmin()

            max_daily_inflow = {
                "date": str(df.loc[max_inflow_idx, "日期"]),
                "value": _safe_float(net_buys.loc[max_inflow_idx]),
            } if len(net_buys) > 0 and net_buys.loc[max_inflow_idx] > 0 else None

            max_daily_outflow = {
                "date": str(df.loc[max_outflow_idx, "日期"]),
                "value": _safe_float(net_buys.loc[max_outflow_idx]),
            } if len(net_buys) > 0 and net_buys.loc[max_outflow_idx] < 0 else None
        else:
            trend = "数据不足"
            cumulative_net_buy = None
            daily_avg_net_buy = None
            max_daily_inflow = None
            max_daily_outflow = None

        summary = {
            "cumulative_net_buy": cumulative_net_buy,
            "daily_avg_net_buy": daily_avg_net_buy,
            "trend": trend,
            "max_daily_inflow": max_daily_inflow,
            "max_daily_outflow": max_daily_outflow,
        }

        # === 逐行转换 ===
        data = []
        for _, row in df.iterrows():
            data.append({
                "date": str(row["日期"]),
                "net_buy": _safe_float(row["当日成交净买额"]),
                "buy_amount": _safe_float(row["买入成交额"]),
                "sell_amount": _safe_float(row["卖出成交额"]),
                "cumulative_net_buy": _safe_float(row["历史累计净买额"]),
            })

        result = {
            "status": "success",
            "direction": direction,
            "days": days,
            "summary": summary,
            "data": data,
        }

        # 北向标记数据不可用
        if is_northbound:
            result["data_available"] = False

        return result

    except Exception as e:
        logger.error(f"获取历史资金流失败: {e}")
        return {"status": "error", "message": f"获取历史资金流失败: {e}"}
