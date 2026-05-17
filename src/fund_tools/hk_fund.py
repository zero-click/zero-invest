# -*- coding: utf-8 -*-
"""
香港基金数据模块

功能:
  1. 香港基金排行查询
  2. 香港基金搜索
  3. 香港基金历史净值/分红送配查询

数据源:
  - 东方财富: fund_hk_rank_em() 排行, fund_hk_fund_hist_em() 历史净值
"""

import logging
from typing import Any, Dict

import akshare as ak
import pandas as pd

from .cache import get_hk_fund_list

logger = logging.getLogger(__name__)

# 允许的排序字段
VALID_SORT_FIELDS = [
    "近1周", "近1月", "近3月", "近6月", "近1年", "近2年", "近3年", "今年来", "成立来",
]

# 允许的历史类型
VALID_HISTORY_TYPES = ["历史净值明细", "分红送配详情"]


def get_hk_fund_rankings(
    sort_by: str = "近1年",
    limit: int = 50,
) -> Dict[str, Any]:
    """
    获取香港基金排行榜

    Args:
        sort_by: 排序字段，可选值：近1周/近1月/近3月/近6月/近1年/近2年/近3年/今年来/成立来
        limit: 返回数量上限

    Returns:
        成功: {status, count, sort_by, data: [...]}
        失败: {status: "error", message: "..."}
    """
    # 参数校验
    if sort_by not in VALID_SORT_FIELDS:
        return {
            "status": "error",
            "message": f"不支持的排序字段: {sort_by}，可选值: {', '.join(VALID_SORT_FIELDS)}",
        }

    try:
        df = get_hk_fund_list()
        if df.empty:
            return {"status": "error", "message": "获取香港基金排行失败，请稍后重试"}

        # 按指定字段排序（降序）
        if sort_by in df.columns:
            df_sorted = df.sort_values(by=sort_by, ascending=False, na_position="last")
        else:
            logger.warning(f"排序字段 {sort_by} 不在数据列中，使用原始顺序")
            df_sorted = df

        # 限制数量
        df_result = df_sorted.head(limit)

        return {
            "status": "success",
            "count": len(df_result),
            "sort_by": sort_by,
            "data": df_result.to_dict("records"),
        }
    except Exception as e:
        logger.error(f"获取香港基金排行失败: {e}")
        return {"status": "error", "message": f"获取香港基金排行失败: {str(e)}"}


def search_hk_funds(keyword: str) -> Dict[str, Any]:
    """
    搜索香港基金（按基金代码或基金简称）

    Args:
        keyword: 搜索关键字

    Returns:
        成功: {status, count, data: [...]}
        失败: {status: "error", message: "..."}
    """
    if not keyword or not keyword.strip():
        return {"status": "error", "message": "搜索关键字不能为空"}

    try:
        df = get_hk_fund_list()
        if df.empty:
            return {"status": "error", "message": "香港基金数据不可用，请稍后重试"}

        keyword_lower = keyword.strip().lower()

        # 按基金代码或基金简称搜索
        mask = pd.Series([False] * len(df), index=df.index)
        for col in ["基金代码", "基金简称"]:
            if col in df.columns:
                mask = mask | df[col].astype(str).str.lower().str.contains(
                    keyword_lower, na=False
                )

        results = df[mask]

        return {
            "status": "success",
            "count": len(results),
            "data": results.to_dict("records"),
        }
    except Exception as e:
        logger.error(f"搜索香港基金失败: {e}")
        return {"status": "error", "message": f"搜索香港基金失败: {str(e)}"}


def get_hk_fund_history(
    code: str,
    history_type: str = "历史净值明细",
) -> Dict[str, Any]:
    """
    获取香港基金历史净值/分红送配

    Args:
        code: 基金代码（6位），函数内部自动查找对应的香港基金代码
        history_type: "历史净值明细" 或 "分红送配详情"

    Returns:
        成功: {status, code, name, type, count, data: [...]}
        失败: {status: "error", message: "..."}
    """
    # 参数校验
    if history_type not in VALID_HISTORY_TYPES:
        return {
            "status": "error",
            "message": f"不支持的类型: {history_type}，可选值: {', '.join(VALID_HISTORY_TYPES)}",
        }

    # 查找香港基金代码
    df = get_hk_fund_list()
    if df.empty:
        return {"status": "error", "message": "香港基金数据不可用，请稍后重试"}

    # 查找基金记录
    matches = df[df["基金代码"].astype(str) == str(code)]
    if matches.empty:
        return {
            "status": "error",
            "message": f"未找到基金代码 {code}，请通过 search_hk_funds 搜索确认",
        }

    row = matches.iloc[0]
    hk_code = str(row.get("香港基金代码", ""))
    fund_name = str(row.get("基金简称", ""))

    if not hk_code or hk_code == "nan":
        return {
            "status": "error",
            "message": f"基金 {code} 缺少香港基金代码映射",
        }

    try:
        logger.info(f"正在获取香港基金 {code} ({fund_name}) 的{history_type}...")
        result_df = ak.fund_hk_fund_hist_em(code=hk_code, symbol=history_type)

        if result_df is None or result_df.empty:
            return {
                "status": "error",
                "message": f"基金 {code} 暂无{history_type}数据",
            }

        return {
            "status": "success",
            "code": code,
            "name": fund_name,
            "hk_code": hk_code,
            "type": history_type,
            "count": len(result_df),
            "data": result_df.to_dict("records"),
        }
    except Exception as e:
        logger.error(f"获取香港基金历史数据失败: {e}")
        return {"status": "error", "message": f"获取基金 {code} 历史数据失败: {str(e)}"}
