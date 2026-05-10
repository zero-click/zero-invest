# -*- coding: utf-8 -*-
"""
Tests for CLI index listfund command.
"""

import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_root, "src"))

from cli.index.listfund import print_index_candidate_funds


class TestCliIndexListFund:
    def test_print_index_candidate_funds(self, capsys):
        sample = {
            "status": "success",
            "index": {"code": "000300", "name": "沪深300"},
            "aliases": ["沪深300", "300ETF"],
            "count": 1,
            "funds": [
                {
                    "基金代码": "510300",
                    "基金名称": "沪深300ETF",
                    "跟踪方式": "被动指数型",
                    "手续费": "0.12",
                }
            ],
        }
        print_index_candidate_funds(sample)
        output = capsys.readouterr().out
        assert "候选基金数量" in output
        assert "510300" in output
