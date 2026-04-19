# -*- coding: utf-8 -*-
"""
Tests for index_valuation module and fund_tool integration.
Run: python -m pytest tests/ -v
"""

import json
import sys
import os

import pytest

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from index_valuation import (
    get_index_pe,
    get_csindex_valuation,
    get_index_valuation_batch,
    get_portfolio_index_valuation,
    _get_valuation_level,
    LG_INDEX_MAP,
    CSINDEX_MAP,
)


class TestValuationLevel:
    """Test valuation level helper function."""

    def test_extremely_undervalued(self):
        assert "极度低估" in _get_valuation_level(5)

    def test_undervalued(self):
        assert "低估" in _get_valuation_level(15)

    def test_reasonable(self):
        assert "合理" in _get_valuation_level(50)

    def test_overvalued(self):
        assert "高估" in _get_valuation_level(85)

    def test_extremely_overvalued(self):
        assert "极度高估" in _get_valuation_level(95)


class TestGetIndexPE:
    """Test single index PE/PB query via Legulegu."""

    def test_hs300(self):
        """沪深300 - must have valid PE/PB data."""
        result = get_index_pe("沪深300")
        assert result["status"] == "success"
        assert result["PE_TTM"] > 0
        assert result["PB"] > 0
        assert 0 <= result["PE分位_10年"] <= 100
        assert 0 <= result["PB分位_10年"] <= 100
        assert result["日期"] is not None
        assert result["估值等级"] is not None
        print(f"  沪深300: PE={result['PE_TTM']} PB={result['PB']} 分位={result['PE分位_10年']}%")

    def test_csi500(self):
        """中证500 - must have valid data."""
        result = get_index_pe("中证500")
        assert result["status"] == "success"
        assert result["PE_TTM"] > 0

    def test_csi1000(self):
        """中证1000."""
        result = get_index_pe("中证1000")
        assert result["status"] == "success"

    def test_invalid_index(self):
        """Invalid index name should return error."""
        result = get_index_pe("不存在的指数")
        assert result["status"] == "error"


class TestGetCSIndexValuation:
    """Test CSIndex valuation query."""

    def test_military(self):
        """中证军工."""
        result = get_csindex_valuation("399967")
        assert result["status"] == "success"
        assert result["市盈率1"] is not None
        print(f"  中证军工: PE={result['市盈率1']}")

    def test_nonferrous(self):
        """有色金属."""
        result = get_csindex_valuation("000819")
        assert result["status"] == "success"

    def test_invalid_code(self):
        """Invalid code should return error."""
        result = get_csindex_valuation("999999")
        assert result["status"] == "error"


class TestBatchQuery:
    """Test batch valuation query."""

    def test_batch_lg(self):
        """Batch query multiple LG indices."""
        result = get_index_valuation_batch(lg_indices=["沪深300", "中证500"])
        assert "乐咕宽基指数" in result
        assert "沪深300" in result["乐咕宽基指数"]
        assert "中证500" in result["乐咕宽基指数"]
        assert result["乐咕宽基指数"]["沪深300"]["status"] == "success"

    def test_batch_csindex(self):
        """Batch query CSIndex indices."""
        result = get_index_valuation_batch(csindex_codes=["399967", "000819"])
        assert "中证行业指数" in result
        assert result["中证行业指数"]["中证军工"]["status"] == "success"

    def test_batch_mixed(self):
        """Batch query both LG and CSIndex."""
        result = get_index_valuation_batch(
            lg_indices=["沪深300"],
            csindex_codes=["399967"],
        )
        assert len(result["乐咕宽基指数"]) == 1
        assert len(result["中证行业指数"]) == 1


class TestPortfolioValuation:
    """Test full portfolio valuation query."""

    def test_portfolio(self):
        """Full portfolio valuation - the main use case."""
        result = get_portfolio_index_valuation()
        assert "乐咕宽基指数" in result
        assert "中证行业指数" in result
        
        # Should have 6 LG indices
        assert len(result["乐咕宽基指数"]) == 6
        
        # Should have 8 CSIndex indices
        assert len(result["中证行业指数"]) == 8
        
        # Print summary
        print("\n  === 宽基指数 ===")
        for name, data in result["乐咕宽基指数"].items():
            if data.get("status") == "success":
                print(f"    {name}: PE={data['PE_TTM']} 分位={data['PE分位_10年']}% {data['估值等级']}")
        
        print("\n  === 行业指数 ===")
        for name, data in result["中证行业指数"].items():
            if data.get("status") == "success":
                print(f"    {name}: PE={data.get('市盈率1', '?')}")


class TestFundToolIntegration:
    """Test fund_tool.py CLI still works with new index commands."""

    def test_import_fund_tool(self):
        """fund_tool_akshare should import cleanly."""
        from fund_tool_akshare import query_fund_details, search_funds
        assert callable(query_fund_details)
        assert callable(search_funds)

    def test_query_fund_format(self):
        """Query a real fund and check format."""
        from fund_tool_akshare import query_fund_details
        # 588000 = 科创50ETF - should work with eastmoney API
        result = query_fund_details("588000")
        assert result.get("status") in ("success", "error")
        assert "code" in result or "message" in result
