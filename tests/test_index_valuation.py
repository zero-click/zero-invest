# -*- coding: utf-8 -*-
"""
Tests for index valuation/query APIs.
Run: python -m pytest tests/test_index_valuation.py -v
"""

import sys
import os

import pytest
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fund_tools.index import (
    _build_csindex_pe_valuation,
    _get_index_query_window,
    _get_valuation_level,
    LG_INDEX_MAP,
    get_index_returns,
    get_index_query,
    get_index_valuation,
)


class TestValuationLevel:
    def test_extremely_undervalued(self):
        assert "极度低估" in _get_valuation_level(5)

    def test_undervalued(self):
        assert "低估" in _get_valuation_level(15)

    def test_reasonable(self):
        assert "合理" in _get_valuation_level(50)

    def test_reasonable_upper(self):
        assert "合理偏上" in _get_valuation_level(65)

    def test_slightly_expensive(self):
        assert "偏高" in _get_valuation_level(75)

    def test_overvalued(self):
        assert "高估" in _get_valuation_level(90)

    def test_extremely_overvalued(self):
        assert "极度高估" in _get_valuation_level(95)

    def test_csindex_pe_fallback_builds_level(self):
        dates = pd.date_range("2020-01-01", periods=6, freq="365D")
        df = pd.DataFrame(
            {
                "日期": dates,
                "滚动市盈率": [8, 10, 12, 14, 16, 18],
            }
        )

        result = _build_csindex_pe_valuation(df, latest_pe=18, years=10)
        assert result["PE_TTM"] == 18.0
        assert result["PE估值等级"] != "N/A"
        assert "PE分位_10年" in result

    def test_get_index_returns(self):
        dates = pd.date_range("2026-01-01", periods=300, freq="D")
        closes = list(range(100, 400))
        df = pd.DataFrame({"日期": dates, "收盘": closes})

        result = get_index_returns(df)

        assert result["1周_收益率"] is not None
        assert result["1月_收益率"] is not None
        assert result["1年_收益率"] is not None
        assert "今年收益率" in result

    def test_query_window_is_bounded(self):
        start_date, end_date = _get_index_query_window("20260429")
        assert start_date == "20220430"
        assert end_date == "20260429"


class TestIndexQueryAndValuation:
    def test_query_hs300(self):
        result = get_index_query("000300")
        assert result["status"] in ("success", "error")
        if result["status"] == "success":
            assert result["代码"] == "000300"
            assert result.get("名称")
            assert result.get("收盘点位") is not None
            assert "1年_收益率" in result
        else:
            assert "message" in result

    def test_valuation_hs300(self):
        result = get_index_valuation("000300")
        assert result["status"] in ("success", "error")
        if result["status"] == "success":
            assert result["代码"] == "000300"
            assert result.get("PE_TTM") is not None
            assert result.get("PB") is not None
            assert result.get("估值数据源") in ("乐咕乐股", "中证指数")
            assert "PE估值等级" in result
            assert "PB估值等级" in result
        else:
            assert "message" in result

    def test_valuation_invalid_code(self):
        result = get_index_valuation("999999")
        assert result["status"] == "error"


class TestFundToolsExport:
    def test_import_from_package(self):
        from src.fund_tools import get_index_query as pkg_query
        from src.fund_tools import get_index_valuation as pkg_val

        assert callable(pkg_query)
        assert callable(pkg_val)

    def test_lg_index_map_not_empty(self):
        assert len(LG_INDEX_MAP) > 0
