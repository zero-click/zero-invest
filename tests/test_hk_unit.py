# -*- coding: utf-8 -*-
"""
香港市场单元测试

测试内容:
  1. 参数校验（排序字段、搜索关键字、历史类型、days 范围）
  2. 错误响应格式
  3. 数据源 fallback 机制
  4. Cache 函数集成
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from fund_tools.hk_fund import (
    get_hk_fund_rankings,
    search_hk_funds,
    get_hk_fund_history,
    VALID_SORT_FIELDS,
)
from fund_tools.hk_index import (
    get_hk_index_spot,
    get_hk_index_daily,
)


# ============================================================
# get_hk_fund_rankings — 参数校验
# ============================================================

class TestHkFundRankingsParams:
    """AC-2: 排序字段参数校验"""

    def test_invalid_sort_field_returns_error(self):
        result = get_hk_fund_rankings(sort_by="无效字段")
        assert result["status"] == "error"
        assert "不支持的排序字段" in result["message"]

    @patch("fund_tools.hk_fund.get_hk_fund_list")
    def test_valid_sort_field_succeeds(self, mock_list):
        mock_list.return_value = pd.DataFrame({
            "基金代码": ["968063"],
            "基金简称": ["摩根太平洋科技"],
            "近1年": [0.15],
        })
        result = get_hk_fund_rankings(sort_by="近1年", limit=10)
        assert result["status"] == "success"
        assert result["sort_by"] == "近1年"
        assert result["count"] == 1

    @patch("fund_tools.hk_fund.get_hk_fund_list")
    def test_empty_list_returns_error(self, mock_list):
        mock_list.return_value = pd.DataFrame()
        result = get_hk_fund_rankings()
        assert result["status"] == "error"

    @patch("fund_tools.hk_fund.get_hk_fund_list")
    def test_limit_truncates_results(self, mock_list):
        mock_list.return_value = pd.DataFrame({
            "基金代码": ["A", "B", "C"],
            "基金简称": ["F1", "F2", "F3"],
            "近1年": [0.1, 0.2, 0.3],
        })
        result = get_hk_fund_rankings(limit=2)
        assert result["count"] == 2


# ============================================================
# search_hk_funds — 参数校验
# ============================================================

class TestSearchHkFunds:
    """AC-3: 搜索关键字校验"""

    def test_empty_keyword_returns_error(self):
        result = search_hk_funds("")
        assert result["status"] == "error"
        assert "不能为空" in result["message"]

    def test_whitespace_keyword_returns_error(self):
        result = search_hk_funds("   ")
        assert result["status"] == "error"

    @patch("fund_tools.hk_fund.get_hk_fund_list")
    def test_keyword_search_finds_match(self, mock_list):
        mock_list.return_value = pd.DataFrame({
            "基金代码": ["968063", "968010"],
            "基金简称": ["摩根太平洋科技", "南方东英恒生科技"],
        })
        result = search_hk_funds("摩根")
        assert result["status"] == "success"
        assert result["count"] == 1

    @patch("fund_tools.hk_fund.get_hk_fund_list")
    def test_keyword_search_code_match(self, mock_list):
        mock_list.return_value = pd.DataFrame({
            "基金代码": ["968063", "968010"],
            "基金简称": ["摩根太平洋科技", "南方东英恒生科技"],
        })
        result = search_hk_funds("968063")
        assert result["status"] == "success"
        assert result["count"] == 1


# ============================================================
# get_hk_fund_history — 参数校验
# ============================================================

class TestHkFundHistoryParams:
    """AC-4: 历史类型参数校验"""

    def test_invalid_history_type_returns_error(self):
        result = get_hk_fund_history("968063", history_type="无效类型")
        assert result["status"] == "error"
        assert "不支持的类型" in result["message"]

    @patch("fund_tools.hk_fund.get_hk_fund_list")
    def test_code_not_found_returns_error(self, mock_list):
        mock_list.return_value = pd.DataFrame({
            "基金代码": ["968063"],
            "基金简称": ["摩根太平洋科技"],
            "香港基金代码": ["OF000009"],
        })
        result = get_hk_fund_history("999999")
        assert result["status"] == "error"
        assert "未找到基金代码" in result["message"]

    @patch("fund_tools.hk_fund.get_hk_fund_list")
    def test_empty_db_returns_error(self, mock_list):
        mock_list.return_value = pd.DataFrame()
        result = get_hk_fund_history("968063")
        assert result["status"] == "error"
        assert "不可用" in result["message"]


# ============================================================
# get_hk_index_daily — 参数校验
# ============================================================

class TestHkIndexDailyParams:
    """AC-6: days 参数范围校验"""

    def test_days_zero_returns_error(self):
        result = get_hk_index_daily("CES100", days=0)
        assert result["status"] == "error"

    def test_days_negative_returns_error(self):
        result = get_hk_index_daily("CES100", days=-1)
        assert result["status"] == "error"

    def test_days_over_365_returns_error(self):
        result = get_hk_index_daily("CES100", days=400)
        assert result["status"] == "error"
        assert "365" in result["message"]

    def test_empty_symbol_returns_error(self):
        result = get_hk_index_daily("")
        assert result["status"] == "error"
        assert "不能为空" in result["message"]


# ============================================================
# Fallback 机制测试
# ============================================================

class TestHkIndexFallback:
    """数据源 fallback: Sina → EM"""

    @patch("fund_tools.hk_index.ak.stock_hk_index_spot_sina")
    def test_spot_prefers_sina(self, mock_sina):
        mock_sina.return_value = pd.DataFrame({"代码": ["CES100"], "名称": ["指数"], "最新价": [100]})
        result = get_hk_index_spot()
        assert result["status"] == "success"
        assert result["source"] == "sina"

    @patch("fund_tools.hk_index.ak.stock_hk_index_spot_em")
    @patch("fund_tools.hk_index.ak.stock_hk_index_spot_sina")
    def test_spot_falls_back_to_em(self, mock_sina, mock_em):
        mock_sina.side_effect = Exception("sina down")
        mock_em.return_value = pd.DataFrame({"代码": ["CES100"], "名称": ["指数"], "最新价": [100]})
        result = get_hk_index_spot()
        assert result["status"] == "success"
        assert result["source"] == "em"

    @patch("fund_tools.hk_index.ak.stock_hk_index_spot_em")
    @patch("fund_tools.hk_index.ak.stock_hk_index_spot_sina")
    def test_spot_both_fail_returns_error(self, mock_sina, mock_em):
        mock_sina.side_effect = Exception("sina down")
        mock_em.side_effect = Exception("em down")
        result = get_hk_index_spot()
        assert result["status"] == "error"
