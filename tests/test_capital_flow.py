# -*- coding: utf-8 -*-
"""
沪深港通资金流分析 — 集成测试

遵循项目约定: 真实 API 集成测试, 不 mock。
"""

import pytest
from fund_tools.capital_flow import (
    get_capital_flow_summary,
    get_capital_flow_history,
    get_northbound_sector_rank,
    _safe_float,
    _safe_int,
    _parse_trade_status,
    DIRECTION_MAP,
    BOARD_TYPE_MAP,
    VALID_INDICATORS,
)


# ==========================================
# 辅助函数测试
# ==========================================

class TestSafeFloat:
    def test_normal_number(self):
        assert _safe_float(52.346) == 52.35

    def test_int_input(self):
        assert _safe_float(100) == 100.0

    def test_nan_returns_none(self):
        import math
        assert _safe_float(float("nan")) is None

    def test_string_number(self):
        assert _safe_float("52.34") == 52.34

    def test_invalid_string_returns_none(self):
        assert _safe_float("abc") is None

    def test_none_returns_none(self):
        assert _safe_float(None) is None


class TestSafeInt:
    def test_normal_int(self):
        assert _safe_int(860) == 860

    def test_float_input(self):
        assert _safe_int(860.7) == 860

    def test_nan_returns_none(self):
        import math
        assert _safe_int(float("nan")) is None

    def test_none_returns_none(self):
        assert _safe_int(None) is None


class TestParseTradeStatus:
    def test_status_1(self):
        assert _parse_trade_status(1) == "盘前"

    def test_status_2(self):
        assert _parse_trade_status(2) == "交易中"

    def test_status_3(self):
        assert _parse_trade_status(3) == "已收盘"

    def test_string_number(self):
        assert _parse_trade_status("3") == "已收盘"

    def test_unknown_value(self):
        result = _parse_trade_status(99)
        assert isinstance(result, str)


# ==========================================
# get_capital_flow_summary 集成测试
# ==========================================

@pytest.mark.integration
class TestCapitalFlowSummary:
    def test_returns_success_status(self):
        result = get_capital_flow_summary()
        assert result["status"] == "success"

    def test_contains_date(self):
        result = get_capital_flow_summary()
        assert "date" in result
        assert len(result["date"]) >= 10  # YYYY-MM-DD

    def test_contains_4_channels(self):
        """实际返回 4 行: 沪股通, 港股通(沪), 深股通, 港股通(深)"""
        result = get_capital_flow_summary()
        assert "channels" in result
        assert len(result["channels"]) == 4

    def test_channel_has_required_fields(self):
        result = get_capital_flow_summary()
        channel = result["channels"][0]
        required = [
            "name", "type", "direction", "trade_status",
            "net_buy", "fund_inflow", "balance",
            "up_count", "flat_count", "down_count",
            "index_name", "index_change_pct",
        ]
        for field in required:
            assert field in channel, f"Missing field: {field}"

    def test_channel_direction_values(self):
        """应包含北向和南向"""
        result = get_capital_flow_summary()
        directions = {c["direction"] for c in result["channels"]}
        assert "北向" in directions
        assert "南向" in directions


# ==========================================
# get_capital_flow_history 集成测试
# ==========================================

@pytest.mark.integration
class TestCapitalFlowHistory:
    def test_northbound_default(self):
        result = get_capital_flow_history()
        assert result["status"] == "success"
        assert result["direction"] == "北向"
        assert len(result["data"]) <= 20

    def test_custom_days(self):
        result = get_capital_flow_history(days=5)
        assert result["status"] == "success"
        assert len(result["data"]) <= 5

    def test_southbound(self):
        result = get_capital_flow_history(direction="南向")
        assert result["status"] == "success"
        assert result["direction"] == "南向"

    def test_all_directions(self):
        """所有 direction 参数都应能返回成功"""
        for d in DIRECTION_MAP:
            result = get_capital_flow_history(direction=d)
            assert result["status"] == "success", f"Failed for direction: {d}"

    def test_summary_fields(self):
        result = get_capital_flow_history()
        assert "summary" in result
        summary = result["summary"]
        assert "cumulative_net_buy" in summary
        assert "daily_avg_net_buy" in summary
        assert "trend" in summary
        assert summary["trend"] in ("持续流入", "持续流出", "震荡", "数据不足")

    def test_invalid_direction(self):
        result = get_capital_flow_history(direction="无效")
        assert result["status"] == "error"

    def test_days_capped_at_365(self):
        result = get_capital_flow_history(days=9999)
        assert result["status"] == "success"
        assert result["days"] == 365

    def test_data_has_null_for_recent(self):
        """2024-08-19 后净买额可能为 null"""
        result = get_capital_flow_history()
        recent = [d for d in result["data"] if d["date"] >= "2024-08-19"]
        if recent:
            assert "net_buy" in recent[0]
            # net_buy 可以是 None 或 float

    def test_data_item_fields(self):
        result = get_capital_flow_history()
        if result["data"]:
            item = result["data"][-1]
            required = ["date", "net_buy", "buy_amount", "sell_amount", "cumulative_net_buy"]
            for field in required:
                assert field in item, f"Missing field: {field}"


# ==========================================
# get_northbound_sector_rank 集成测试
# ==========================================

@pytest.mark.integration
class TestNorthboundSectorRank:
    def test_industry_default(self):
        result = get_northbound_sector_rank()
        assert result["status"] in ("success", "error")  # 非交易日可能失败
        if result["status"] == "success":
            assert len(result["data"]) <= 10

    def test_concept_board(self):
        result = get_northbound_sector_rank(board_type="概念板块")
        assert result["status"] in ("success", "error")

    def test_custom_indicator(self):
        result = get_northbound_sector_rank(indicator="1月")
        assert result["status"] in ("success", "error")

    def test_top_n(self):
        result = get_northbound_sector_rank(top_n=5)
        if result["status"] == "success":
            assert len(result["data"]) <= 5

    def test_sector_has_required_fields(self):
        result = get_northbound_sector_rank()
        if result["status"] == "success" and result["data"]:
            item = result["data"][0]
            required = [
                "rank", "name", "change_pct",
                "holding_count", "holding_market_cap", "holding_ratio",
                "increase_count", "increase_market_cap", "increase_market_cap_change",
            ]
            for field in required:
                assert field in item, f"Missing field: {field}"

    def test_invalid_board_type(self):
        result = get_northbound_sector_rank(board_type="无效")
        assert result["status"] == "error"

    def test_nontrading_day_graceful_error(self):
        """非交易日应返回明确错误而非崩溃"""
        result = get_northbound_sector_rank()
        assert result["status"] in ("success", "error")
        if result["status"] == "error":
            assert "message" in result

    def test_board_type_and_indicator_in_result(self):
        result = get_northbound_sector_rank()
        if result["status"] == "success":
            assert result["board_type"] == "行业板块"
            assert result["indicator"] == "5日"
