# -*- coding: utf-8 -*-
"""测试基金和指数最近收益查询功能"""

import pytest
from fund_tools import get_fund_recent_performance, get_index_recent_performance


class TestFundRecentPerformance:
    """测试基金最近收益查询"""

    def test_invalid_code_format(self):
        """测试无效的基金代码格式"""
        result = get_fund_recent_performance("abc", 30)
        assert result["status"] == "error"
        assert "无效的基金代码格式" in result["message"]

    def test_invalid_days_too_small(self):
        """测试天数太小"""
        result = get_fund_recent_performance("000001", 0)
        assert result["status"] == "error"
        assert "天数必须在 1-365 之间" in result["message"]

    def test_invalid_days_too_large(self):
        """测试天数太大"""
        result = get_fund_recent_performance("000001", 400)
        assert result["status"] == "error"
        assert "天数必须在 1-365 之间" in result["message"]

    def test_valid_fund_recent_performance(self):
        """测试有效的基金最近收益查询"""
        result = get_fund_recent_performance("000001", 30)
        assert result["status"] == "success"
        assert result["code"] == "000001"
        assert result["days"] == 30
        assert "total_return" in result
        assert "data_count" in result
        assert "data" in result
        assert isinstance(result["data"], list)


class TestIndexRecentPerformance:
    """测试指数最近收益查询"""

    def test_invalid_code_format(self):
        """测试无效的指数代码格式"""
        result = get_index_recent_performance("abc", 30)
        assert result["status"] == "error"
        assert "无效的指数代码格式" in result["message"]

    def test_invalid_days_too_small(self):
        """测试天数太小"""
        result = get_index_recent_performance("000300", 0)
        assert result["status"] == "error"
        assert "天数必须在 1-365 之间" in result["message"]

    def test_invalid_days_too_large(self):
        """测试天数太大"""
        result = get_index_recent_performance("000300", 400)
        assert result["status"] == "error"
        assert "天数必须在 1-365 之间" in result["message"]

    def test_valid_index_recent_performance(self):
        """测试有效的指数最近收益查询"""
        result = get_index_recent_performance("000300", 30)
        assert result["status"] == "success"
        assert result["code"] == "000300"
        assert result["days"] == 30
        assert "total_return" in result
        assert "data_count" in result
        assert "data" in result
        assert isinstance(result["data"], list)
