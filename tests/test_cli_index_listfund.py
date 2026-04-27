# -*- coding: utf-8 -*-
"""
Tests for CLI index listfund command.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cli


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
        cli.print_index_candidate_funds(sample)
        output = capsys.readouterr().out
        assert "候选基金数量" in output
        assert "510300" in output

    def test_index_listfund_dispatch(self, monkeypatch, capsys):
        monkeypatch.setattr(
            cli,
            "get_index_candidate_funds",
            lambda code: {
                "status": "success",
                "index": {"code": code, "name": "沪深300"},
                "aliases": ["沪深300"],
                "count": 1,
                "funds": [
                    {
                        "基金代码": "510300",
                        "基金名称": "沪深300ETF",
                        "跟踪方式": "被动指数型",
                        "手续费": "0.12",
                    }
                ],
            },
        )
        monkeypatch.setattr(sys, "argv", ["cli.py", "index", "listfund", "000300"])
        cli.main()
        output = capsys.readouterr().out
        assert "查询指数候选基金池" in output
        assert "510300" in output
