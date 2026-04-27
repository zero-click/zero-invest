# -*- coding: utf-8 -*-
"""
Tests for multi-source index cache aggregation.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import src.fund_tools as fund_tools
from src.fund_tools import cache, index


class TestIndexCacheMultiSource:
    def test_fetch_index_spot_sources_adds_common_missing_indices(self, monkeypatch):
        monkeypatch.setattr(
            cache.ak,
            "stock_zh_index_spot_em",
            lambda: pd.DataFrame(
                [
                    {
                        "代码": "000016",
                        "名称": "上证50",
                        "最新价": 2939.05,
                        "涨跌幅": -0.2,
                        "成交额": 159040616221.0,
                    }
                ]
            ),
        )
        monkeypatch.setattr(
            cache.ak,
            "stock_zh_index_spot_sina",
            lambda: pd.DataFrame(
                [
                    {
                        "代码": "sz399673",
                        "名称": "创业板50",
                        "最新价": 3885.42,
                        "涨跌幅": -0.81,
                        "成交额": 219522974526.0,
                    }
                ]
            ),
        )
        monkeypatch.setattr(
            cache.ak,
            "index_stock_info",
            lambda: pd.DataFrame(
                [
                    {"index_code": "000016", "display_name": "上证50", "publish_date": "2004-01-02"},
                    {"index_code": "399673", "display_name": "创业板50", "publish_date": "2014-06-18"},
                ]
            ),
        )

        records = cache._fetch_index_spot_sources()
        by_code = {item["code"]: item for item in records}

        assert by_code["000016"]["name"] == "上证50"
        assert by_code["000016"]["category"] == "broad"
        assert by_code["000016"]["publish_date"] == "2004-01-02"
        assert "eastmoney_spot_em" in by_code["000016"]["sources"]
        assert "index_stock_info" in by_code["000016"]["sources"]

        assert by_code["399673"]["name"] == "创业板50"
        assert by_code["399673"]["category"] == "broad"
        assert by_code["399673"]["publish_date"] == "2014-06-18"
        assert "sina_spot" in by_code["399673"]["sources"]

    def test_finalize_index_catalog_dedupes_and_preserves_primary_category(self):
        records = [
            {
                "code": "000300",
                "name": "沪深300",
                "category": "broad",
                "index_class": "规模",
                "asset_class": "股票",
                "source": "csindex",
            },
            {
                "code": "sh000300",
                "name": "沪深300",
                "category": "other",
                "latest_price": 4769.37,
                "source": "sina_spot",
            },
            {
                "code": "399673",
                "name": "创业板50",
                "category": "broad",
                "index_class": "规模",
                "source": "index_stock_info",
            },
        ]

        catalog = cache._finalize_index_catalog(records)
        broad_codes = {item["code"] for item in catalog["broad"]}

        assert "000300" in broad_codes
        assert "399673" in broad_codes
        assert sum(1 for item in catalog["broad"] if item["code"] == "000300") == 1

        hs300 = next(item for item in catalog["broad"] if item["code"] == "000300")
        assert hs300["category"] == "broad"
        assert hs300["latest_price"] == 4769.37
        assert hs300["sources"] == ["csindex", "sina_spot"]

    def test_get_all_stock_indices_includes_other_bucket(self, monkeypatch):
        monkeypatch.setattr(
            fund_tools,
            "get_index_list",
            lambda: {
                "broad": [{"code": "000300", "name": "沪深300"}],
                "industry": [],
                "sector": [],
                "strategy": [],
                "style": [],
                "other": [{"code": "399001", "name": "深证成指"}],
            },
        )

        codes = {item["code"] for item in index.get_all_stock_indices()}
        assert codes == {"000300", "399001"}

    def test_fetch_index_history_data_falls_back_to_eastmoney(self, monkeypatch):
        def _raise_csindex(*args, **kwargs):
            raise ValueError("csindex unavailable")

        monkeypatch.setattr(index.ak, "stock_zh_index_hist_csindex", _raise_csindex)
        monkeypatch.setattr(
            index.ak,
            "index_zh_a_hist",
            lambda **kwargs: pd.DataFrame(
                [
                    {
                        "日期": "2026-04-24",
                        "收盘": 3880.10,
                        "涨跌幅": 1.2,
                    },
                    {
                        "日期": "2026-04-27",
                        "收盘": 3885.42,
                        "涨跌幅": -0.81,
                    },
                ]
            ),
        )

        df = index._fetch_index_history_data("399673")

        assert len(df) == 2
        assert str(df.iloc[-1]["日期"].date()) == "2026-04-27"
        assert df.iloc[-1]["收盘"] == 3885.42
