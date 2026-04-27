# -*- coding: utf-8 -*-
"""
Tests for fund market metrics fallback and caching behavior.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.fund_tools import core


class TestFundMarketMetrics:
    def setup_method(self):
        core._ETF_SPOT_CACHE["df"] = None
        core._ETF_SPOT_CACHE["ts"] = 0.0
        core._ETF_SPOT_CACHE["source"] = ""

    def test_fallback_to_ths_when_em_fails(self, monkeypatch):
        def _raise_em():
            raise ConnectionError("RemoteDisconnected")

        df_ths = pd.DataFrame(
            [
                {
                    "代码": "510300",
                    "成交额": 123456789,
                    "基金折价率": -0.12,
                    "IOPV实时估值": 4.123,
                    "成交量": 998877,
                    "换手率": 2.3,
                }
            ]
        )

        monkeypatch.setattr(core.ak, "fund_etf_spot_em", _raise_em)
        monkeypatch.setattr(core.ak, "fund_etf_spot_ths", lambda: df_ths)
        monkeypatch.setattr(core.ak, "fund_exchange_rank_em", lambda: pd.DataFrame())

        result = core.get_fund_market_metrics("510300")
        assert result["status"] == "success"
        assert result["is_exchange_traded"] is True
        assert result["market_data_source"] == "ths"
        assert result["market_metrics"]["成交额"] == 123456789

    def test_failed_result_not_cached(self, monkeypatch):
        monkeypatch.setattr(core.ak, "fund_etf_spot_em", lambda: pd.DataFrame())
        monkeypatch.setattr(core.ak, "fund_etf_spot_ths", lambda: pd.DataFrame())
        monkeypatch.setattr(core.ak, "fund_exchange_rank_em", lambda: pd.DataFrame())

        first = core.get_fund_market_metrics("510300")
        assert first["status"] == "success"
        assert first["is_exchange_traded"] is False
        assert first["market_metrics"]["成交额"] == "N/A"

        df_em = pd.DataFrame(
            [
                {
                    "代码": "510300",
                    "成交额": 8888,
                    "基金折价率": 0.01,
                    "IOPV实时估值": 4.001,
                    "成交量": 1000,
                    "换手率": 0.2,
                }
            ]
        )
        monkeypatch.setattr(core.ak, "fund_etf_spot_em", lambda: df_em)

        second = core.get_fund_market_metrics("510300")
        assert second["status"] == "success"
        assert second["is_exchange_traded"] is True
        assert second["market_data_source"] == "em"
        assert second["market_metrics"]["成交额"] == 8888
