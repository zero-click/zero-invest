# -*- coding: utf-8 -*-
"""
Tests for index candidate funds selection.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.fund_tools as fund_tools
from src.fund_tools import core


class TestIndexCandidateFunds:
    def setup_method(self):
        core.get_index_candidate_funds.cache_clear()

    def test_invalid_index_code(self):
        result = core.get_index_candidate_funds("300")
        assert result["status"] == "error"

    def test_candidate_funds_success(self, monkeypatch):
        monkeypatch.setattr(
            fund_tools,
            "get_index_info_by_code",
            lambda code: {"code": code, "name": "沪深300", "category": "broad"},
        )

        source_df = pd.DataFrame(
            [
                {
                    "基金代码": "510300",
                    "基金名称": "沪深300ETF",
                    "跟踪方式": "被动指数型",
                    "跟踪标的": "沪深指数",
                    "单位净值": 4.12,
                    "日期": "2026-04-24",
                    "近1年": 25.3,
                    "手续费": 0.12,
                },
                {
                    "基金代码": "159919",
                    "基金名称": "300ETF联接A",
                    "跟踪方式": "被动指数型",
                    "跟踪标的": "沪深指数",
                    "单位净值": 2.03,
                    "日期": "2026-04-24",
                    "近1年": 24.8,
                    "手续费": 0.10,
                },
                {
                    "基金代码": "000001",
                    "基金名称": "华夏成长混合",
                    "跟踪方式": "主动",
                    "跟踪标的": "",
                    "单位净值": 1.23,
                    "日期": "2026-04-24",
                    "近1年": 10.0,
                    "手续费": 0.50,
                },
            ]
        )
        monkeypatch.setattr(core.ak, "fund_info_index_em", lambda symbol, indicator: source_df)

        def _mock_overview(symbol):
            if symbol in ("510300", "159919"):
                return pd.DataFrame([{"跟踪标的": "沪深300指数"}])
            return pd.DataFrame([{"跟踪标的": "中证500指数"}])

        monkeypatch.setattr(core.ak, "fund_overview_em", _mock_overview)

        result = core.get_index_candidate_funds("000300")
        assert result["status"] == "success"
        assert result["index"]["name"] == "沪深300"
        assert result["count"] == 2
        codes = {item["基金代码"] for item in result["funds"]}
        assert "510300" in codes
        assert "159919" in codes
        assert "000001" not in codes
