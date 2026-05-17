# -*- coding: utf-8 -*-
"""
基金工具包
基于 akshare 的基金信息查询工具
"""

from .cache import (
    get_fund_list,
    get_index_list,
    update_index_cache,
    FUND_DB_FILE,
    INDEX_DB_FILE,
)
from .core import (
    VALID_FUND_TYPES,
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
    get_fund_market_metrics,
    get_index_candidate_funds,
    get_fund_recent_performance,
)
from . import index
from .industry_valuation import (
    get_industry_valuation_matrix,
    get_csrc_valuation_matrix,
    get_valuation_heatmap,
    get_csrc_valuation_heatmap,
    format_heatmap_table,
)
from .capital_flow import (
    get_capital_flow_summary,
    get_capital_flow_history,
)

# 香港市场
from .hk_fund import (
    get_hk_fund_rankings,
    search_hk_funds,
    get_hk_fund_history,
)
from .hk_index import (
    get_hk_index_spot,
    get_hk_index_daily,
)

# 从 index 模块导入所有指数相关函数
from .index import (
    # 核心功能
    fetch_indices_from_csindex,
    search_indices_all,
    get_index_info as _get_index_info,
    LG_INDEX_MAP,
    get_index_query,
    get_index_query_window,
    get_index_returns,
    get_index_valuation,
    get_index_details,
    get_index_details_batch,
    get_index_risk,
    get_index_recent_performance,
    get_csrc_industry_pe_snapshot,
    # 便捷函数
    get_broad_indices,
    get_industry_indices,
    get_sector_indices,
    get_strategy_indices,
    get_style_indices,
    get_all_stock_indices,
)


def search_indices_all(keyword: str):
    """搜索所有指数（包级导出）"""
    return index.search_indices_all(keyword)


def get_index_info(code: str):
    """获取指数信息（向后兼容接口）"""
    indices = get_all_stock_indices()
    return _get_index_info(indices, code)


def get_index_info_by_code(code: str):
    """根据代码获取指数信息（向后兼容接口）"""
    return get_index_info(code)


__all__ = [
    # Cache
    "get_fund_list",
    "get_index_list",
    "update_index_cache",
    "FUND_DB_FILE",
    "INDEX_DB_FILE",
    # Core
    "VALID_FUND_TYPES",
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
    "get_fund_market_metrics",
    "get_index_candidate_funds",
    "get_fund_recent_performance",
    # Valuation
    "LG_INDEX_MAP",
    # Index module
    "index",
    "fetch_indices_from_csindex",
    "get_broad_indices",
    "get_industry_indices",
    "get_sector_indices",
    "get_strategy_indices",
    "get_style_indices",
    "get_all_stock_indices",
    "search_indices_all",
    "get_index_info",
    "get_index_info_by_code",
    "get_index_query",
    "get_index_query_window",
    "get_index_returns",
    "get_index_valuation",
    "get_index_details",
    "get_index_details_batch",
    "get_index_risk",
    "get_index_recent_performance",
    "get_csrc_industry_pe_snapshot",
    "get_industry_valuation_matrix",
    "get_csrc_valuation_matrix",
    "get_valuation_heatmap",
    "get_csrc_valuation_heatmap",
    "format_heatmap_table",
    # Capital Flow
    "get_capital_flow_summary",
    "get_capital_flow_history",
    # Hong Kong Market
    "get_hk_fund_rankings",
    "search_hk_funds",
    "get_hk_fund_history",
    "get_hk_index_spot",
    "get_hk_index_daily",
]

__version__ = "2.0.0"
