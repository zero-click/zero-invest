# -*- coding: utf-8 -*-
"""
Tests for capital_flow_analysis module.
Run: python3.13 -m pytest tests/test_capital_flow.py -v
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from capital_flow_analysis import (
    get_northbound_holdings,
    get_southbound_holdings,
    get_historical_flow,
    get_fund_flow_summary,
    get_industry_aggregation,
    get_top_holdings,
    get_capital_flow_report,
    format_industry_report,
    format_flow_history,
    get_market_fund_flow,
    format_market_fund_flow,
    _analyze_fund_flow_trend,
    _safe_float,
    _safe_str,
    _normalize_holdings_df,
    INDUSTRY_ALIAS,
)

import pandas as pd


# ============================================================
# Helper tests (no network)
# ============================================================

class TestHelperFunctions:
    """Test internal utility functions."""

    def test_safe_float_normal(self):
        assert _safe_float(123.45) == 123.45

    def test_safe_float_nan(self):
        assert _safe_float(float("nan")) is None

    def test_safe_float_none(self):
        assert _safe_float(None) is None

    def test_safe_float_string(self):
        assert _safe_float("abc") is None

    def test_safe_str_normal(self):
        assert _safe_str("hello") == "hello"

    def test_safe_str_none(self):
        assert _safe_str(None) == ""

    def test_safe_str_datetime(self):
        from datetime import datetime
        dt = datetime(2026, 4, 21)
        assert _safe_str(dt) == "2026-04-21"

    def test_industry_alias_coverage(self):
        """Ensure key industries have aliases."""
        for key in ["电子", "银行", "医药生物", "计算机"]:
            assert key in INDUSTRY_ALIAS


class TestNormalizeDF:
    """Test DataFrame normalization."""

    def test_basic_columns(self):
        """Test with real akshare column names."""
        df = pd.DataFrame({
            "代码": ["600519"],
            "名称": ["贵州茅台"],
            "今日持股-股数": [1000],
            "今日持股-市值": [200000],
            "所属板块": ["酿酒行业"],
        })
        result = _normalize_holdings_df(df, direction="北向")
        assert "代码" in result.columns
        assert "名称" in result.columns
        assert "行业" in result.columns
        assert "持股数量" in result.columns
        assert "持股市值" in result.columns
        assert result.iloc[0]["行业"] == "消费"
        assert result.iloc[0]["持股数量"] == 1000
        assert result.iloc[0]["持股市值"] == 200000

    def test_missing_industry(self):
        df = pd.DataFrame({
            "代码": ["600519"],
            "名称": ["贵州茅台"],
            "今日持股-股数": [1000],
            "今日持股-市值": [200000],
        })
        result = _normalize_holdings_df(df, direction="北向")
        assert "行业" in result.columns
        assert result.iloc[0]["行业"] == "未知"


# ============================================================
# Integration tests (require network / akshare)
# ============================================================

class TestNorthboundHoldings:
    """Test northbound holdings retrieval."""

    def test_get_northbound_data(self):
        """Should return non-empty list with valid structure."""
        data = get_northbound_holdings()
        assert isinstance(data, list)
        if data:  # May be empty if API is down
            item = data[0]
            assert "代码" in item
            assert "名称" in item
            assert "行业" in item
            print(f"  北向持股: {len(data)} 只个股, 首只: {item['名称']} ({item['行业']})")

    def test_northbound_has_numeric_fields(self):
        """Numeric fields should be float."""
        data = get_northbound_holdings()
        if data:
            item = data[0]
            assert isinstance(item["持股市值"], (int, float))
            assert isinstance(item["持股数量"], (int, float))


class TestSouthboundHoldings:
    """Test southbound holdings retrieval."""

    @pytest.mark.slow
    def test_get_southbound_data(self):
        data = get_southbound_holdings()
        assert isinstance(data, list)
        if data:
            item = data[0]
            assert "代码" in item
            assert "名称" in item
            print(f"  南向持股: {len(data)} 只个股, 首只: {item['名称']}")


class TestHistoricalFlow:
    """Test historical fund flow data."""

    def test_shanghai_connect(self):
        data = get_historical_flow("沪股通", days=10)
        assert isinstance(data, list)
        if data:
            item = data[-1]
            assert "日期" in item
            assert "当日净买入" in item
            print(f"  沪股通最近: {item['日期']} 净买入={item['当日净买入']}")

    def test_shenzhen_connect(self):
        data = get_historical_flow("深股通", days=10)
        assert isinstance(data, list)

    def test_invalid_symbol(self):
        data = get_historical_flow("不存在的通道", days=10)
        assert data == []


class TestFundFlowSummary:
    """Test daily fund flow summary."""

    def test_summary(self):
        result = get_fund_flow_summary()
        assert isinstance(result, dict)
        assert "success" in result
        if result["success"]:
            assert "data" in result
            print(f"  汇总数据: {len(result['data'])} 条记录")


class TestIndustryAggregation:
    """Test industry-level aggregation."""

    def test_northbound_industry(self):
        result = get_industry_aggregation("北向")
        assert isinstance(result, dict)
        assert "direction" in result

        if result.get("success"):
            assert "industries" in result
            assert len(result["industries"]) > 0
            # First industry should have required fields
            first = result["industries"][0]
            assert "行业" in first
            assert "持股市值" in first
            assert "个股数" in first
            assert "市值占比(%)" in first
            print(f"  北向行业数: {result['total_industries']}")
            print(f"  Top行业: {first['行业']} ({first['市值占比(%)']:.2f}%)")

    @pytest.mark.slow
    def test_southbound_industry(self):
        result = get_industry_aggregation("南向")
        assert isinstance(result, dict)


class TestTopHoldings:
    """Test top holdings ranking."""

    def test_top_northbound(self):
        result = get_top_holdings("北向", metric="持股市值", top_n=5)
        assert isinstance(result, dict)

        if result.get("success"):
            assert len(result["data"]) <= 5
            if result["data"]:
                first = result["data"][0]
                assert "代码" in first
                assert "名称" in first
                print(f"  北向Top1: {first['名称']} 市值={first['持股市值']}")


class TestFormatOutput:
    """Test CLI formatting functions."""

    def test_format_industry_report(self):
        # Use a mock aggregation result
        mock_agg = {
            "success": True,
            "direction": "北向",
            "timestamp": "2026-04-21T00:00:00",
            "total_industries": 2,
            "total_stocks": 100,
            "industries": [
                {"行业": "电子", "个股数": 30, "持股市值": 5e11, "市值占比(%)": 50.0},
                {"行业": "银行", "个股数": 20, "持股市值": 3e11, "市值占比(%)": 30.0},
            ],
        }
        output = format_industry_report(mock_agg)
        assert "北向" in output
        assert "电子" in output
        assert "银行" in output

    def test_format_industry_report_failure(self):
        mock_agg = {"success": False, "direction": "北向", "message": "error"}
        output = format_industry_report(mock_agg)
        assert "❌" in output

    def test_format_flow_history_empty(self):
        output = format_flow_history([], "沪股通")
        assert "不可用" in output

    def test_format_flow_history_with_data(self):
        data = [
            {"日期": "2026-04-21", "当日净买入": 1e9, "历史净买入": 1e12},
            {"日期": "2026-04-20", "当日净买入": -5e8, "历史净买入": 9.99e11},
        ]
        output = format_flow_history(data, "沪股通")
        assert "沪股通" in output
        assert "2026-04-21" in output


class TestCapitalFlowReport:
    """Test comprehensive report generation."""

    @pytest.mark.slow
    def test_report_structure(self):
        report = get_capital_flow_report()
        assert isinstance(report, dict)
        assert "timestamp" in report
        assert "northbound" in report
        assert "southbound" in report
        assert "flow_history" in report
        assert "summary" in report
        print(f"  报告时间: {report['timestamp']}")


# ============================================================
# 大盘主力资金流 tests
# ============================================================

class TestMarketFundFlowTrend:
    """Test internal trend analysis (no network)."""

    def test_consecutive_inflow(self):
        """3+ days of net inflow → 偏多."""
        records = [
            {"主力净流入": 1e10, "超大单净流入": 5e9, "小单净流入": -1e10},
            {"主力净流入": 2e10, "超大单净流入": 1e10, "小单净流入": -2e10},
            {"主力净流入": 3e10, "超大单净流入": 2e10, "小单净流入": -1e10},
            {"主力净流入": 1e10, "超大单净流入": 5e9, "小单净流入": -5e9},
        ]
        result = _analyze_fund_flow_trend(records)
        assert result["signal"] == "偏多"
        assert "4日净流入" in result["main_force_trend"]
        assert "主力吸筹" in result["divergence"]

    def test_consecutive_outflow(self):
        """3+ days of net outflow → 偏空."""
        records = [
            {"主力净流入": -1e10, "超大单净流入": -5e9, "小单净流入": 1e10},
            {"主力净流入": -2e10, "超大单净流入": -1e10, "小单净流入": 2e10},
            {"主力净流入": -3e10, "超大单净流入": -2e10, "小单净流入": 1e10},
        ]
        result = _analyze_fund_flow_trend(records)
        assert result["signal"] == "偏空"
        assert "净流出" in result["main_force_trend"]
        assert "主力出货" in result["divergence"]

    def test_oscillating_positive(self):
        """Mixed direction but total positive → 中性偏多."""
        records = [
            {"主力净流入": 1e10, "超大单净流入": 5e9, "小单净流入": -5e9},
            {"主力净流入": -3e9, "超大单净流入": -1e9, "小单净流入": 2e9},
            {"主力净流入": 5e9, "超大单净流入": 2e9, "小单净流入": -3e9},
        ]
        result = _analyze_fund_flow_trend(records)
        assert "偏多" in result["signal"]

    def test_resonance_inflow(self):
        """Main + small both positive → 资金共振流入."""
        records = [
            {"主力净流入": 1e10, "超大单净流入": 5e9, "小单净流入": 5e9},
        ]
        result = _analyze_fund_flow_trend(records)
        assert "共振流入" in result["divergence"]

    def test_empty_records(self):
        result = _analyze_fund_flow_trend([])
        assert result["signal"] == "中性"

    def test_none_values_handled(self):
        """None values should be treated as 0."""
        records = [
            {"主力净流入": None, "超大单净流入": None, "小单净流入": None},
            {"主力净流入": 1e10, "超大单净流入": 5e9, "小单净流入": -1e9},
        ]
        result = _analyze_fund_flow_trend(records)
        assert isinstance(result["主力净流入合计(亿)"], float)


class TestMarketFundFlowIntegration:
    """Integration tests for market fund flow (requires network)."""

    def test_get_market_fund_flow(self):
        """Should return valid fund flow data."""
        result = get_market_fund_flow(days=10)
        assert isinstance(result, dict)
        assert result["success"] is True
        assert "data" in result
        assert "summary" in result
        assert len(result["data"]) <= 10

        # Check data structure
        item = result["data"][-1]
        assert "日期" in item
        assert "主力净流入" in item
        assert "超大单净流入" in item
        assert "大单净流入" in item
        assert "小单净流入" in item
        assert isinstance(item["主力净流入"], (int, float))

        print(f"  大盘资金流: {result['days']}天")
        summary = result["summary"]
        print(f"  趋势: {summary['main_force_trend']} | 信号: {summary['signal']}")

    def test_get_market_fund_flow_30days(self):
        """Default 30 days should work."""
        result = get_market_fund_flow()
        assert result["success"] is True
        assert result["days"] > 0


class TestFormatMarketFundFlow:
    """Test CLI formatting for market fund flow."""

    def test_format_success(self):
        mock_result = {
            "success": True,
            "timestamp": "2026-04-21T00:00:00",
            "days": 3,
            "data": [
                {"日期": "2026-04-18", "上证涨跌幅": 0.5, "主力净流入": 1e10,
                 "超大单净流入": 5e9, "大单净流入": 5e9, "中单净流入": -2e9,
                 "小单净流入": -8e9},
                {"日期": "2026-04-20", "上证涨跌幅": -0.3, "主力净流入": -5e9,
                 "超大单净流入": -2e9, "大单净流入": -3e9, "中单净流入": 1e9,
                 "小单净流入": 4e9},
                {"日期": "2026-04-21", "上证涨跌幅": 1.0, "主力净流入": 2e10,
                 "超大单净流入": 1e10, "大单净流入": 1e10, "中单净流入": -3e9,
                 "小单净流入": -1.7e10},
            ],
            "summary": {
                "recent_days": 3,
                "主力净流入合计(亿)": 250.0,
                "超大单净流入合计(亿)": 130.0,
                "小单净流入合计(亿)": -210.0,
                "main_force_trend": "连续1日净流入",
                "divergence": "主力吸筹、散户出逃",
                "signal": "中性偏多",
            },
        }
        output = format_market_fund_flow(mock_result)
        assert "大盘主力资金流" in output
        assert "2026-04-21" in output
        assert "主力吸筹" in output

    def test_format_failure(self):
        mock_result = {"success": False, "message": "API error"}
        output = format_market_fund_flow(mock_result)
        assert "❌" in output
