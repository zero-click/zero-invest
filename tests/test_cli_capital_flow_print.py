# -*- coding: utf-8 -*-
"""
Tests for CLI capital-flow print functions.
Uses mock data matching actual API return shapes to verify field alignment.
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, "src"))

from cli.capital_flow.summary import print_capital_flow_summary
from cli.capital_flow.history import print_capital_flow_history


# === Mock data matching actual capital_flow.py return shapes ===

MOCK_SUMMARY_SUCCESS = {
    "status": "success",
    "date": "2026-05-09",
    "channels": [
        {
            "name": "沪股通",
            "type": "北向",
            "direction": "北向",
            "trade_status": "已收盘",
            "net_buy": 0.0,
            "fund_inflow": 56.78,
            "balance": 520.12,
            "up_count": 450,
            "flat_count": 30,
            "down_count": 200,
            "index_name": "上证指数",
            "index_change_pct": 0.85,
            "data_available": False,
        },
        {
            "name": "港股通(沪)",
            "type": "南向",
            "direction": "南向",
            "trade_status": "已收盘",
            "net_buy": -5.67,
            "fund_inflow": -23.45,
            "balance": 430.50,
            "up_count": 150,
            "flat_count": 10,
            "down_count": 300,
            "index_name": "恒生指数",
            "index_change_pct": -0.32,
        },
        {
            "name": "深股通",
            "type": "北向",
            "direction": "北向",
            "trade_status": "已收盘",
            "net_buy": 0.0,
            "fund_inflow": 33.21,
            "balance": 310.00,
            "up_count": 350,
            "flat_count": 20,
            "down_count": 180,
            "index_name": "深证成指",
            "index_change_pct": 0.62,
            "data_available": False,
        },
        {
            "name": "港股通(深)",
            "type": "南向",
            "direction": "南向",
            "trade_status": "已收盘",
            "net_buy": -2.10,
            "fund_inflow": -10.50,
            "balance": 210.30,
            "up_count": 120,
            "flat_count": 8,
            "down_count": 250,
            "index_name": "恒生指数",
            "index_change_pct": -0.32,
        },
    ],
}

MOCK_SUMMARY_ERROR = {
    "status": "error",
    "message": "暂无资金流数据",
}

MOCK_HISTORY_SUCCESS = {
    "status": "success",
    "direction": "南向",
    "days": 5,
    "summary": {
        "cumulative_net_buy": 45.67,
        "daily_avg_net_buy": 9.13,
        "trend": "持续流入",
        "max_daily_inflow": {"date": "2026-05-07", "value": 15.20},
        "max_daily_outflow": {"date": "2026-05-06", "value": -3.40},
    },
    "data": [
        {"date": "2026-05-05", "net_buy": 10.50, "buy_amount": 200.30, "sell_amount": 189.80, "cumulative_net_buy": 1000.50},
        {"date": "2026-05-06", "net_buy": -3.40, "buy_amount": 150.00, "sell_amount": 153.40, "cumulative_net_buy": 997.10},
        {"date": "2026-05-07", "net_buy": 15.20, "buy_amount": 250.00, "sell_amount": 234.80, "cumulative_net_buy": 1012.30},
        {"date": "2026-05-08", "net_buy": 8.37, "buy_amount": 180.00, "sell_amount": 171.63, "cumulative_net_buy": 1020.67},
        {"date": "2026-05-09", "net_buy": 15.00, "buy_amount": 220.00, "sell_amount": 205.00, "cumulative_net_buy": 1035.67},
    ],
}

MOCK_HISTORY_ERROR = {
    "status": "error",
    "message": "获取历史资金流失败: timeout",
}

MOCK_HISTORY_EMPTY_DATA = {
    "status": "success",
    "direction": "南向",
    "days": 5,
    "summary": {
        "trend": "数据不足",
        "cumulative_net_buy": None,
        "daily_avg_net_buy": None,
        "max_daily_inflow": None,
        "max_daily_outflow": None,
    },
    "data": [],
}

MOCK_HISTORY_NORTHBOUND = {
    "status": "success",
    "direction": "北向",
    "data_available": False,
    "days": 5,
    "summary": {
        "trend": "数据不足",
        "cumulative_net_buy": None,
        "daily_avg_net_buy": None,
    },
    "data": [],
}


class TestPrintSummary:
    """Test print_capital_flow_summary with mock data matching actual return shape."""

    def test_success_output_contains_date(self, capsys):
        print_capital_flow_summary(MOCK_SUMMARY_SUCCESS)
        output = capsys.readouterr().out
        assert "2026-05-09" in output

    def test_success_output_contains_channel_names(self, capsys):
        print_capital_flow_summary(MOCK_SUMMARY_SUCCESS)
        output = capsys.readouterr().out
        assert "沪股通" in output
        assert "港股通(沪)" in output
        assert "深股通" in output
        assert "港股通(深)" in output

    def test_success_output_contains_net_buy(self, capsys):
        print_capital_flow_summary(MOCK_SUMMARY_SUCCESS)
        output = capsys.readouterr().out
        # 南向 net_buy values
        assert "5.67" in output

    def test_success_output_contains_direction_labels(self, capsys):
        print_capital_flow_summary(MOCK_SUMMARY_SUCCESS)
        output = capsys.readouterr().out
        assert "北向" in output
        assert "南向" in output

    def test_success_northbound_marked_unavailable(self, capsys):
        print_capital_flow_summary(MOCK_SUMMARY_SUCCESS)
        output = capsys.readouterr().out
        assert "不再公布" in output or "不可用" in output or "数据不可用" in output

    def test_error_output(self, capsys):
        print_capital_flow_summary(MOCK_SUMMARY_ERROR)
        output = capsys.readouterr().out
        assert "❌" in output
        assert "暂无资金流数据" in output


class TestPrintHistory:
    """Test print_capital_flow_history with mock data matching actual return shape."""

    def test_success_output_contains_direction(self, capsys):
        print_capital_flow_history(MOCK_HISTORY_SUCCESS)
        output = capsys.readouterr().out
        assert "南向" in output

    def test_success_output_contains_dates(self, capsys):
        print_capital_flow_history(MOCK_HISTORY_SUCCESS)
        output = capsys.readouterr().out
        assert "2026-05-09" in output
        assert "2026-05-05" in output

    def test_success_output_contains_trend(self, capsys):
        print_capital_flow_history(MOCK_HISTORY_SUCCESS)
        output = capsys.readouterr().out
        assert "持续流入" in output
        assert "45.67" in output  # cumulative_net_buy

    def test_success_output_contains_max_inflow(self, capsys):
        print_capital_flow_history(MOCK_HISTORY_SUCCESS)
        output = capsys.readouterr().out
        assert "15.2" in output  # max daily inflow value

    def test_error_output(self, capsys):
        print_capital_flow_history(MOCK_HISTORY_ERROR)
        output = capsys.readouterr().out
        assert "❌" in output

    def test_empty_data_no_crash(self, capsys):
        print_capital_flow_history(MOCK_HISTORY_EMPTY_DATA)
        output = capsys.readouterr().out
        assert "暂无历史数据" in output

    def test_northbound_unavailable_note(self, capsys):
        """北向查询应打印数据不可用说明"""
        print_capital_flow_history(MOCK_HISTORY_NORTHBOUND)
        output = capsys.readouterr().out
        assert "不再公布" in output or "不可用" in output
