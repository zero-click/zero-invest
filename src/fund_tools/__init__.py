# -*- coding: utf-8 -*-
"""
基金工具包
基于 akshare 的基金信息查询工具
"""

from .cache import get_fund_list, FUND_DB_FILE
from .core import (
    search_funds,
    query_fund_details,
    get_fund_rankings,
    get_fund_rating,
    get_fund_risk_metrics,
    get_fund_performance,
    get_fund_top_holdings,
    get_fund_basic_fee_rates,
    get_fund_manager_details,
    get_fund_holdings_analysis,
    get_fund_asset_allocation,
    get_fund_portfolio_analysis,
    get_fund_fee_details,
    get_fund_liquidity_info,
)

__all__ = [
    # Cache
    "get_fund_list",
    "FUND_DB_FILE",
    # Core
    "search_funds",
    "query_fund_details",
    "get_fund_rankings",
    "get_fund_rating",
    "get_fund_risk_metrics",
    "get_fund_performance",
    "get_fund_top_holdings",
    "get_fund_basic_fee_rates",
    "get_fund_manager_details",
    "get_fund_holdings_analysis",
    "get_fund_asset_allocation",
    "get_fund_portfolio_analysis",
    "get_fund_fee_details",
    "get_fund_liquidity_info",
]

__version__ = "2.0.0"
