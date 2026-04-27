# -*- coding: utf-8 -*-
"""
行业估值热力图集成测试
使用真实 akshare 接口，需要网络连接
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cli
from src.fund_tools import format_heatmap_table, get_valuation_heatmap


@pytest.mark.integration
class TestIndustryHeatmap:
    def test_get_valuation_heatmap_returns_data(self):
        result = get_valuation_heatmap(sort_by="pe")

        assert isinstance(result, dict)
        assert result["sort_by"] == "pe"
        assert result["total"] > 0
        assert len(result["data"]) > 0

        first = result["data"][0]
        for field in ["代码", "名称", "分类", "PE", "PB", "股息率", "估值温度", "数据源"]:
            assert field in first

    def test_format_heatmap_table_contains_header(self):
        result = get_valuation_heatmap(sort_by="pb")
        table = format_heatmap_table(result, limit=5)

        assert "指数估值热力图" in table
        assert "排序: pb" in table

    def test_cli_index_heatmap(self, monkeypatch, capsys):
        monkeypatch.setattr(
            sys,
            "argv",
            ["cli.py", "index", "heatmap", "--sort-by", "pe", "--limit", "5"],
        )

        cli.main()
        output = capsys.readouterr().out
        assert "查询指数估值热力图" in output
        assert "指数估值热力图" in output
