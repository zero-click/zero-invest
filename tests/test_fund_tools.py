# -*- coding: utf-8 -*-
"""
src.fund_tools 模块的集成测试
使用真实的 akshare API，需要网络连接

测试基金：000001, 000012, 000041
"""

import pytest
import pandas as pd
import sys
import os

# 导入被测试的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fund_tools import (
    cache,
    core,
    get_fund_list,
    search_funds,
    query_fund_details,
    get_fund_rankings,
    get_fund_rating,
    get_fund_manager_details,
    get_fund_holdings_analysis,
    get_fund_asset_allocation,
    get_fund_fee_details,
    get_fund_liquidity_info,
    FUND_DB_FILE,
)

# 测试用的基金代码
TEST_FUNDS = ['000001', '000012', '000041']


# ============================================================================
# 测试缓存模块
# ============================================================================

@pytest.mark.integration
class TestCache:
    """测试缓存功能（真实网络请求）"""

    def test_get_fund_list_has_required_columns(self):
        """测试基金列表包含必需的列"""
        df = get_fund_list()

        # 验证数据框不为空
        assert not df.empty
        assert len(df) > 10000

        # 验证必需的列存在
        required_columns = ['基金代码', '基金简称', '拼音缩写', '基金类型']
        for col in required_columns:
            assert col in df.columns, f"缺少列: {col}"

    def test_get_fund_list_contains_test_funds(self):
        """测试基金列表包含我们的测试基金"""
        df = get_fund_list()

        for fund_code in TEST_FUNDS:
            matching = df[df['基金代码'] == fund_code]
            assert not matching.empty, f"测试基金 {fund_code} 不在列表中"
            print(f"找到 {fund_code}: {matching.iloc[0]['基金简称']}")

    def test_cache_file_exists_after_save(self):
        """测试缓存文件被正确保存"""
        # 确保缓存已生成
        df = get_fund_list()

        assert os.path.exists(FUND_DB_FILE), "缓存文件不存在"

        # 验证缓存文件可读
        import json
        with open(FUND_DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data) > 0
        assert '基金代码' in data[0]


# ============================================================================
# 测试搜索功能
# ============================================================================

@pytest.mark.integration
class TestSearchFunds:
    """测试基金搜索（真实数据）"""

    def test_search_by_fund_code(self):
        """测试按基金代码搜索"""
        result = search_funds('000001')

        assert result['status'] == 'success'
        assert result['count'] >= 1
        assert result['data'][0]['基金代码'] == '000001'

    def test_search_by_fund_name(self):
        """测试按基金名称搜索"""
        result = search_funds('华夏')

        assert result['status'] == 'success'
        assert result['count'] >= 10
        # 验证返回的结果中包含"华夏"
        assert any('华夏' in f['基金简称'] for f in result['data'])

    def test_search_by_pinyin(self):
        """测试按拼音搜索"""
        result = search_funds('HX')

        assert result['status'] == 'success'
        assert result['count'] >= 1

    def test_search_not_found(self):
        """测试搜索不存在的基金"""
        result = search_funds('不存在的基金XYZ123')

        assert result['status'] == 'success'
        assert result['count'] == 0


# ============================================================================
# 测试详情查询
# ============================================================================

@pytest.mark.integration
class TestQueryFundDetails:
    """测试基金详情查询（真实数据）"""

    @pytest.mark.parametrize("fund_code", TEST_FUNDS)
    def test_query_fund_details_success(self, fund_code):
        """测试查询测试基金的详情"""
        result = query_fund_details(fund_code)

        assert result['status'] == 'success'
        assert result['code'] == fund_code
        assert result['name'] is not None
        assert len(result['name']) > 0
        assert result['type'] is not None

        print(f"\n{fund_code}: {result['name']} - {result['type']}")

    def test_query_fund_details_000001_details(self):
        """测试 000001 华夏成长的详细信息"""
        result = query_fund_details('000001')

        assert result['status'] == 'success'
        assert result['name'] == '华夏成长混合'
        assert result['type'] == '混合型-灵活'

        # 验证基金经理
        assert 'managers' in result
        assert len(result['managers']) >= 1

        # 验证费率
        assert 'fee_rates' in result
        assert '管理费率' in result['fee_rates']

    def test_query_fund_details_invalid_code_format(self):
        """测试无效的基金代码格式"""
        invalid_codes = ['123', 'abcdef', '', '1234567']

        for code in invalid_codes:
            result = query_fund_details(code)
            assert result['status'] == 'error'
            assert '无效的基金代码格式' in result['message']


# ============================================================================
# 测试排行榜
# ============================================================================

@pytest.mark.integration
class TestFundRankings:
    """测试基金排行榜（真实数据）"""

    def test_get_rankings_all_funds(self):
        """测试获取全部基金排行榜"""
        result = get_fund_rankings('全部')

        assert result['status'] == 'success'
        assert result['count'] >= 10
        assert len(result['data']) <= 100

        # 验证数据格式
        first_fund = result['data'][0]
        assert '基金代码' in first_fund
        assert '基金简称' in first_fund

    def test_get_rankings_by_type(self):
        """测试按类型获取排行榜"""
        types_to_test = ['股票型', '混合型', '债券型']

        for fund_type in types_to_test:
            result = get_fund_rankings(fund_type)

            assert result['status'] == 'success'
            assert result['count'] >= 10
            print(f"{fund_type}: {result['count']} 只基金")


# ============================================================================
# 测试基金评级
# ============================================================================

@pytest.mark.integration
class TestFundRating:
    """测试基金评级（真实数据）"""

    @pytest.mark.parametrize("fund_code", TEST_FUNDS)
    def test_get_fund_rating(self, fund_code):
        """测试获取测试基金的评级"""
        result = get_fund_rating(fund_code)

        # 评级可能返回数据，也可能返回"暂无评级"
        assert 'status' in result
        print(f"\n{fund_code} 评级状态: {result['status']}")


# ============================================================================
# 测试基金经理详情
# ============================================================================

@pytest.mark.integration
class TestFundManagerDetails:
    """测试基金经理详情（真实数据）"""

    @pytest.mark.parametrize("fund_code", TEST_FUNDS)
    def test_get_manager_details(self, fund_code):
        """测试获取测试基金的基金经理详情"""
        result = get_fund_manager_details(fund_code)

        assert result['status'] == 'success'
        assert 'managers' in result
        assert 'manager_count' in result

        if result['manager_count'] > 0:
            first_manager = result['managers'][0]
            assert '姓名' in first_manager
            print(f"\n{fund_code} 基金经理: {first_manager.get('姓名', 'N/A')}")

    def test_get_manager_details_invalid_code(self):
        """测试无效代码"""
        result = get_fund_manager_details('123')

        assert result['status'] == 'error'


# ============================================================================
# 测试持仓分析
# ============================================================================

@pytest.mark.integration
class TestFundHoldingsAnalysis:
    """测试持仓分析（真实数据）"""

    @pytest.mark.parametrize("fund_code", TEST_FUNDS)
    def test_get_holdings_analysis(self, fund_code):
        """测试获取测试基金的持仓分析"""
        result = get_fund_holdings_analysis(fund_code)

        assert result['status'] == 'success'
        assert 'code' in result
        assert 'concentration' in result

        # 验证持仓集中度
        concentration = result['concentration']
        if concentration:
            assert '前10大持仓占比' in concentration or len(concentration) == 0

    def test_get_holdings_analysis_invalid_code(self):
        """测试无效代码"""
        result = get_fund_holdings_analysis('abc')

        assert result['status'] == 'error'


# ============================================================================
# 测试资产配置
# ============================================================================

@pytest.mark.integration
class TestFundAssetAllocation:
    """测试资产配置（真实数据）"""

    @pytest.mark.parametrize("fund_code", TEST_FUNDS)
    def test_get_asset_allocation(self, fund_code):
        """测试获取测试基金的资产配置"""
        result = get_fund_asset_allocation(fund_code, '2024')

        assert result['status'] == 'success'
        assert 'code' in result
        assert 'investment_style' in result

        # 验证行业配置
        if result['industry_allocation']:
            first_industry = result['industry_allocation'][0]
            assert '行业类别' in first_industry

    def test_get_asset_allocation_invalid_code(self):
        """测试无效代码"""
        result = get_fund_asset_allocation('1234567', '2024')

        assert result['status'] == 'error'


# ============================================================================
# 测试费用明细
# ============================================================================

@pytest.mark.integration
class TestFundFeeDetails:
    """测试费用明细（真实数据）"""

    @pytest.mark.parametrize("fund_code", TEST_FUNDS)
    def test_get_fee_details(self, fund_code):
        """测试获取测试基金的费用明细"""
        result = get_fund_fee_details(fund_code)

        assert result['status'] == 'success'
        assert 'code' in result
        assert 'fee_details' in result

        # 验证包含管理费率和托管费率
        fee_details = result['fee_details']
        assert '管理费率' in fee_details or len(fee_details) > 0

    def test_get_fee_details_invalid_code(self):
        """测试无效代码"""
        result = get_fund_fee_details('abc')

        assert result['status'] == 'error'


# ============================================================================
# 测试流动性信息
# ============================================================================

@pytest.mark.integration
class TestFundLiquidityInfo:
    """测试流动性信息（真实数据）"""

    @pytest.mark.parametrize("fund_code", TEST_FUNDS)
    def test_get_liquidity_info(self, fund_code):
        """测试获取测试基金的流动性信息"""
        result = get_fund_liquidity_info(fund_code)

        assert result['status'] == 'success'
        assert 'code' in result
        assert 'liquidity_info' in result

        # 验证包含基本流动性信息
        liquidity = result['liquidity_info']
        assert '申赎时间' in liquidity
        assert '交易场所' in liquidity

    def test_get_liquidity_info_invalid_code(self):
        """测试无效代码"""
        result = get_fund_liquidity_info('123')

        assert result['status'] == 'error'


# ============================================================================
# 完整工作流测试
# ============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestFullWorkflow:
    """测试完整的用户工作流"""

    def test_complete_fund_analysis_workflow(self):
        """测试完整的基金分析流程：搜索 -> 详情 -> 经理 -> 持仓"""
        # 步骤1: 搜索"华夏成长"
        search_result = search_funds('华夏成长')
        assert search_result['status'] == 'success'
        assert search_result['count'] >= 1

        # 步骤2: 获取第一个基金的详情
        fund_code = search_result['data'][0]['基金代码']
        detail_result = query_fund_details(fund_code)
        assert detail_result['status'] == 'success'
        print(f"\n分析基金: {detail_result['name']}")

        # 步骤3: 获取基金经理信息
        manager_result = get_fund_manager_details(fund_code)
        assert manager_result['status'] == 'success'

        # 步骤4: 获取持仓分析
        holdings_result = get_fund_holdings_analysis(fund_code)
        assert holdings_result['status'] == 'success'

        # 步骤5: 获取费用信息
        fee_result = get_fund_fee_details(fund_code)
        assert fee_result['status'] == 'success'

    def test_compare_three_test_funds(self):
        """对比三只测试基金的基本信息"""
        results = []

        for fund_code in TEST_FUNDS:
            detail = query_fund_details(fund_code)
            assert detail['status'] == 'success'

            results.append({
                'code': fund_code,
                'name': detail['name'],
                'type': detail['type'],
                'managers': len(detail.get('managers', []))
            })

        # 打印对比结果
        print("\n基金对比:")
        for r in results:
            print(f"  {r['code']}: {r['name']} ({r['type']}) - {r['managers']} 位经理")

        # 验证所有基金都成功获取
        assert len(results) == 3


# ============================================================================
# 测试标记
# ============================================================================

pytestmark = [
    pytest.mark.integration,  # 所有测试都是集成测试
    pytest.mark.fund_tools,   # fund_tools 模块测试
]


# ============================================================================
# 运行说明
# ============================================================================
"""
运行所有集成测试（需要网络）:
    pytest tests/test_fund_tools.py -v

运行特定测试类:
    pytest tests/test_fund_tools.py::TestQueryFundDetails -v

运行特定基金测试:
    pytest tests/test_fund_tools.py::TestQueryFundDetails::test_query_fund_details_success -v

跳过慢速测试:
    pytest tests/test_fund_tools.py -m "not slow" -v

显示详细输出:
    pytest tests/test_fund_tools.py -v -s

注意事项：
1. 这些测试需要网络连接
2. 会调用真实的 akshare API
3. 使用基金 000001, 000012, 000041 作为测试对象
4. 可能受网络状况和API限制影响
5. 首次运行会下载完整基金列表（约26000只基金）
"""
