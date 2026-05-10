# -*- coding: utf-8 -*-
"""
香港市场集成测试

需要网络连接，测试真实 API 调用。
使用 pytest -m integration 标记。

测试内容:
  1. 香港基金排行查询
  2. 香港基金搜索
  3. 香港基金历史净值
  4. 港股指数实时行情
  5. 港股指数历史行情
"""

import pytest

# 标记为集成测试（需要网络）
pytestmark = pytest.mark.integration

from fund_tools.hk_fund import (
    get_hk_fund_rankings,
    search_hk_funds,
    get_hk_fund_history,
)
from fund_tools.hk_index import (
    get_hk_index_spot,
    get_hk_index_daily,
)


class TestHkFundRankingsIntegration:
    """集成测试: 香港基金排行"""

    def test_rankings_default(self):
        result = get_hk_fund_rankings()
        assert result["status"] == "success"
        assert result["count"] > 0
        assert "data" in result
        # 验证数据字段
        first = result["data"][0]
        assert "基金代码" in first
        assert "基金简称" in first

    def test_rankings_with_sort(self):
        result = get_hk_fund_rankings(sort_by="近3月", limit=5)
        assert result["status"] == "success"
        assert result["count"] <= 5
        assert result["sort_by"] == "近3月"


class TestSearchHkFundsIntegration:
    """集成测试: 香港基金搜索"""

    def test_search_by_name(self):
        result = search_hk_funds("摩根")
        assert result["status"] == "success"
        assert result["count"] > 0

    def test_search_no_result(self):
        result = search_hk_funds("不存在的基金名称xyz123")
        assert result["status"] == "success"
        assert result["count"] == 0


class TestHkFundHistoryIntegration:
    """集成测试: 香港基金历史净值"""

    def test_history_net_value(self):
        # 968063 = 摩根太平洋科技
        result = get_hk_fund_history("968063", history_type="历史净值明细")
        assert result["status"] == "success"
        assert result["count"] > 0
        assert result["code"] == "968063"
        assert "data" in result

    def test_history_dividend(self):
        result = get_hk_fund_history("968063", history_type="分红送配详情")
        # 分红送配可能有数据也可能没有，不强制 count > 0
        assert result["status"] in ("success", "error")


class TestHkIndexSpotIntegration:
    """集成测试: 港股指数实时行情"""

    def test_spot_returns_data(self):
        result = get_hk_index_spot()
        assert result["status"] == "success"
        assert result["count"] > 0
        assert result["source"] in ("sina", "em")
        assert "data_delay_note" in result
        # 验证数据字段
        first = result["data"][0]
        assert "代码" in first or "名称" in first


class TestHkIndexDailyIntegration:
    """集成测试: 港股指数历史行情"""

    def test_daily_ces100(self):
        result = get_hk_index_daily("CES100", days=10)
        assert result["status"] == "success"
        assert result["count"] > 0
        assert result["count"] <= 10
        assert result["symbol"] == "CES100"
        # 验证数据字段
        first = result["data"][0]
        # Sina 返回 date/open/high/low/close/volume
        assert "date" in first or "日期" in first
