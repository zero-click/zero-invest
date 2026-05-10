# -*- coding: utf-8 -*-
"""
沪深港通资金流分析 — 集成测试

遵循项目约定: 真实 API 集成测试, 不 mock。

注意：2024-08-19 后北向净买额不再公布，相关功能已移除。
仅保留南向资金流查询。
"""

import pytest
from fund_tools.capital_flow import (
    get_capital_flow_summary,
    get_capital_flow_history,
    _safe_float,
    _safe_int,
    _parse_trade_status,
    DIRECTION_MAP,
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

    def test_northbound_channels_marked_unavailable(self):
        """北向通道应标注数据不可用"""
        result = get_capital_flow_summary()
        northbound = [c for c in result["channels"] if c["direction"] == "北向"]
        for ch in northbound:
            assert ch.get("data_available") is False, f"Channel {ch['name']} should be marked unavailable"


# ==========================================
# get_capital_flow_history 集成测试
# ==========================================

@pytest.mark.integration
class TestCapitalFlowHistory:
    def test_southbound_default(self):
        """默认方向应为南向"""
        result = get_capital_flow_history()
        assert result["status"] == "success"
        assert result["direction"] == "南向"
        assert len(result["data"]) <= 20

    def test_custom_days(self):
        result = get_capital_flow_history(days=5)
        assert result["status"] == "success"
        assert len(result["data"]) <= 5

    def test_southbound_explicit(self):
        result = get_capital_flow_history(direction="南向")
        assert result["status"] == "success"
        assert result["direction"] == "南向"

    def test_all_directions(self):
        """所有 direction 参数都应能返回成功"""
        for d in DIRECTION_MAP:
            result = get_capital_flow_history(direction=d)
            assert result["status"] == "success", f"Failed for direction: {d}"

    def test_northbound_has_availability_note(self):
        """北向方向应附带数据可用性说明"""
        result = get_capital_flow_history(direction="北向")
        assert result["status"] == "success"
        assert "data_available" in result
        assert result["data_available"] is False

    def test_summary_fields(self):
        result = get_capital_flow_history(direction="南向")
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

    def test_data_item_fields(self):
        result = get_capital_flow_history(direction="南向")
        if result["data"]:
            item = result["data"][-1]
            required = ["date", "net_buy", "buy_amount", "sell_amount", "cumulative_net_buy"]
            for field in required:
                assert field in item, f"Missing field: {field}"
