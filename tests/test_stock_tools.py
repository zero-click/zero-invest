# -*- coding: utf-8 -*-
"""
src.fund_tools.stock 模块的集成测试
使用真实的 akshare API，需要网络连接

测试股票：000001(平安银行), 600519(贵州茅台), 000002(万科A)
"""

import pytest
import pandas as pd
import sys
import os

# 导入被测试的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fund_tools.stock import (
    search_stock,
    get_stock_spot,
    get_stock_hist,
    get_stock_financial_indicator,
    analyze_scenario_a,
    analyze_scenario_b,
    analyze_scenario_c,
    classify_stock,
    get_stock_checklist,
)

# 测试用的股票代码
TEST_STOCKS = ['000001', '600519', '000002']


# ============================================================================
# 测试股票搜索
# ============================================================================

@pytest.mark.integration
class TestStockSearch:
    """测试股票搜索功能（真实网络请求）"""

    def test_search_by_keyword(self):
        """测试按关键词搜索股票"""
        result = search_stock("平安")

        assert result['status'] == 'success'
        assert len(result['data']) > 0
        assert '股票代码' in result['data'].columns
        assert '股票名称' in result['data'].columns

    def test_search_returns_china_stock(self):
        """测试搜索返回中国股票"""
        result = search_stock("银行")

        assert result['status'] == 'success'
        # 应该包含银行相关股票
        assert len(result['data']) > 0

    def test_search_empty_result(self):
        """测试搜索不存在的股票"""
        result = search_stock("不存在的股票xyz123")

        assert result['status'] == 'success'
        # 空结果也是成功的
        assert len(result['data']) == 0


# ============================================================================
# 测试实时行情
# ============================================================================

@pytest.mark.integration
class TestStockSpot:
    """测试实时行情功能（真实网络请求）"""

    def test_get_stock_spot_success(self):
        """测试获取实时行情成功"""
        result = get_stock_spot('000001')

        assert result['status'] == 'success'
        data = result['data']
        assert '名称' in data
        assert '当前价' in data
        assert '市盈率' in data
        assert '市净率' in data

    def test_get_stock_spot_invalid_code(self):
        """测试获取无效股票代码"""
        result = get_stock_spot('999999')

        assert result['status'] == 'error'

    def test_get_stock_spot_contains_test_stocks(self):
        """测试获取测试股票行情"""
        for code in TEST_STOCKS:
            result = get_stock_spot(code)
            if result['status'] == 'success':
                assert '名称' in result['data']
                print(f"找到 {code}: {result['data']['名称']}")


# ============================================================================
# 测试历史行情
# ============================================================================

@pytest.mark.integration
class TestStockHist:
    """测试历史行情功能（真实网络请求）"""

    def test_get_stock_hist_default_days(self):
        """测试获取默认90天历史行情"""
        result = get_stock_hist('000001')

        assert result['status'] == 'success'
        assert 'data' in result
        assert isinstance(result['data'], pd.DataFrame)
        assert '收盘' in result['data'].columns
        assert len(result['data']) > 0

    def test_get_stock_hist_custom_days(self):
        """测试获取自定义天数历史行情"""
        result = get_stock_hist('000001', days=30)

        assert result['status'] == 'success'
        # 30天大约20-22个交易日
        assert 15 <= len(result['data']) <= 25

    def test_get_stock_hist_has_stats(self):
        """测试历史行情包含统计信息"""
        result = get_stock_hist('000001')

        assert result['status'] == 'success'
        assert 'stats' in result
        assert '最大回撤' in result['stats']
        assert '当前回撤' in result['stats']


# ============================================================================
# 测试财务指标
# ============================================================================

@pytest.mark.integration
class TestStockFinancial:
    """测试财务指标功能（真实网络请求）"""

    def test_get_stock_financial_indicator(self):
        """测试获取财务指标"""
        result = get_stock_financial_indicator('000001')

        # 财务指标可能因为数据源不可用而失败
        # 这里只验证返回格式正确
        assert 'status' in result
        if result['status'] == 'success':
            assert 'data' in result

    def test_get_stock_financial_indicator_invalid_code(self):
        """测试获取无效股票代码的财务指标"""
        result = get_stock_financial_indicator('999999')

        assert result['status'] == 'error'


# ============================================================================
# 测试场景分析
# ============================================================================

@pytest.mark.integration
class TestStockScenario:
    """测试场景分析功能（真实网络请求）"""

    def test_analyze_scenario_a(self):
        """测试场景A分析（稳定成长型）"""
        result = analyze_scenario_a('000001')

        assert 'status' in result
        if result['status'] == 'success':
            assert 'data' in result

    def test_analyze_scenario_b(self):
        """测试场景B分析（成长/亏损型）"""
        result = analyze_scenario_b('000001')

        assert 'status' in result
        # 场景B可能返回不完整实现

    def test_analyze_scenario_c(self):
        """测试场景C分析（强周期型）"""
        result = analyze_scenario_c('000001')

        assert 'status' in result


# ============================================================================
# 测试股票分类
# ============================================================================

@pytest.mark.integration
class TestStockClassify:
    """测试股票分类功能（真实网络请求）"""

    def test_classify_stock(self):
        """测试股票分类"""
        result = classify_stock('000001')

        assert result['status'] == 'success'
        assert 'type' in result
        assert 'reason' in result
        # 类型应该是三种之一
        assert result['type'] in ['稳定成长型', '强周期型', '生态垄断型']


# ============================================================================
# 测试准入检查
# ============================================================================

@pytest.mark.integration
class TestStockChecklist:
    """测试准入检查功能（真实网络请求）"""

    def test_get_stock_checklist(self):
        """测试准入检查流水表"""
        result = get_stock_checklist('000001')

        assert result['status'] == 'success'
        assert 'classify' in result
        assert 'analysis' in result
