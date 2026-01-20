# -*- coding: utf-8 -*-
"""
基金信息查询工具 - 单元测试
使用 pytest 进行测试
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import fund_tool_akshare as fund_tool


class TestFundList:
    """测试基金列表获取功能"""

    @patch('fund_tool_akshare.ak.fund_name_em')
    def test_get_fund_list_success(self, mock_fund_name_em):
        """测试成功获取基金列表"""
        # Mock 数据
        mock_data = pd.DataFrame({
            '基金代码': ['000001', '000002', '000003'],
            '拼音缩写': ['HXCZHH', 'HXCZHH', 'ZHKZZZQA'],
            '基金简称': ['华夏成长混合', '华夏成长混合', '中海可转债债券A'],
            '基金类型': ['混合型-灵活', '混合型-灵活', '债券型-混合一级'],
            '拼音全称': ['HUAXIACHENGZHANGHUNHE', 'HUAXIACHENGZHANGHUNHE', 'ZHONGHAIKEZHUANZHAIZHAIQUANA']
        })
        mock_fund_name_em.return_value = mock_data

        # 清除缓存
        fund_tool.get_fund_list.cache_clear()

        # 执行测试
        result = fund_tool.get_fund_list()

        # 验证
        assert not result.empty
        assert len(result) == 3
        assert result.iloc[0]['基金代码'] == '000001'
        assert result.iloc[0]['基金简称'] == '华夏成长混合'
        mock_fund_name_em.assert_called_once()

    @patch('fund_tool_akshare.ak.fund_name_em')
    def test_get_fund_list_cached(self, mock_fund_name_em):
        """测试缓存功能"""
        mock_data = pd.DataFrame({
            '基金代码': ['000001'],
            '拼音缩写': ['HXCZHH'],
            '基金简称': ['华夏成长混合'],
            '基金类型': ['混合型-灵活'],
            '拼音全称': ['HUAXIACHENGZHANGHUNHE']
        })
        mock_fund_name_em.return_value = mock_data

        # 清除缓存并首次调用
        fund_tool.get_fund_list.cache_clear()
        result1 = fund_tool.get_fund_list()

        # 第二次调用（应该使用缓存）
        result2 = fund_tool.get_fund_list()

        # 验证只调用了一次
        assert mock_fund_name_em.call_count == 1
        assert len(result1) == len(result2)

    @patch('fund_tool_akshare.ak.fund_name_em')
    def test_get_fund_list_error(self, mock_fund_name_em):
        """测试获取失败的情况"""
        mock_fund_name_em.side_effect = Exception("网络错误")

        # 清除缓存
        fund_tool.get_fund_list.cache_clear()

        # 执行测试
        result = fund_tool.get_fund_list()

        # 验证
        assert result.empty


class TestSearchFunds:
    """测试基金搜索功能"""

    @patch('fund_tool_akshare.get_fund_list')
    def test_search_funds_by_code(self, mock_get_list):
        """测试按基金代码搜索"""
        # Mock 数据
        mock_data = pd.DataFrame({
            '基金代码': ['000001', '000002', '110022'],
            '拼音缩写': ['HXCZHH', 'HXCZHH', 'CGF'],
            '基金简称': ['华夏成长混合', '华夏成长混合', '混合国债ETF'],
            '基金类型': ['混合型-灵活', '混合型-灵活', '债券型'],
            '拼音全称': ['HUAXIACHENGZHANGHUNHE', 'HUAXIACHENGZHANGHUNHE', 'HANGHEGUOZHAI']
        })
        mock_get_list.return_value = mock_data

        # 搜索 "000001"
        result = fund_tool.search_funds('000001')

        # 验证
        assert result['status'] == 'success'
        assert result['count'] == 1
        assert result['data'][0]['基金代码'] == '000001'

    @patch('fund_tool_akshare.get_fund_list')
    def test_search_funds_by_name(self, mock_get_list):
        """测试按基金名称搜索"""
        mock_data = pd.DataFrame({
            '基金代码': ['000001', '000011', '000014'],
            '拼音缩写': ['HXCZHH', 'HXDPJXA', 'HXJLZA'],
            '基金简称': ['华夏成长混合', '华夏大盘精选混合A', '华夏聚利债券A'],
            '基金类型': ['混合型-灵活', '混合型-灵活', '债券型-混合一级'],
            '拼音全称': ['HUAXIACHENGZHANGHUNHE', 'HUAXIADAPANJINGXUANHUNHE', 'HUAJULIZHAIQUAN']
        })
        mock_get_list.return_value = mock_data

        # 搜索 "华夏"
        result = fund_tool.search_funds('华夏')

        # 验证
        assert result['status'] == 'success'
        assert result['count'] == 3
        assert all('华夏' in f['基金简称'] for f in result['data'])

    @patch('fund_tool_akshare.get_fund_list')
    def test_search_funds_by_pinyin(self, mock_get_list):
        """测试按拼音缩写搜索"""
        mock_data = pd.DataFrame({
            '基金代码': ['000001', '000011'],
            '拼音缩写': ['HXCZHH', 'HXDPJXA'],
            '基金简称': ['华夏成长混合', '华夏大盘精选混合A'],
            '基金类型': ['混合型-灵活', '混合型-灵活'],
            '拼音全称': ['HUAXIACHENGZHANGHUNHE', 'HUAXIADAPANJINGXUANHUNHE']
        })
        mock_get_list.return_value = mock_data

        # 搜索 "HX"
        result = fund_tool.search_funds('HX')

        # 验证
        assert result['status'] == 'success'
        assert result['count'] == 2

    @patch('fund_tool_akshare.get_fund_list')
    def test_search_funds_not_found(self, mock_get_list):
        """测试搜索不到结果"""
        mock_data = pd.DataFrame({
            '基金代码': ['000001', '000002'],
            '拼音缩写': ['HXCZHH', 'HXCZHH'],
            '基金简称': ['华夏成长混合', '华夏成长混合'],
            '基金类型': ['混合型-灵活', '混合型-灵活'],
            '拼音全称': ['HUAXIACHENGZHANGHUNHE', 'HUAXIACHENGZHANGHUNHE']
        })
        mock_get_list.return_value = mock_data

        # 搜索不存在的关键词
        result = fund_tool.search_funds('不存在的关键词XYZ')

        # 验证
        assert result['status'] == 'success'
        assert result['count'] == 0
        assert result['data'] == []

    @patch('fund_tool_akshare.get_fund_list')
    def test_search_funds_empty_database(self, mock_get_list):
        """测试数据库为空的情况"""
        # 清除缓存
        fund_tool.search_funds.cache_clear()

        mock_get_list.return_value = pd.DataFrame()

        # 搜索
        result = fund_tool.search_funds('华夏')

        # 验证 - 实际代码在DataFrame为空时返回error
        assert result['status'] == 'error'
        assert '数据不可用' in result['message']


class TestGetFundDetails:
    """测试基金详情查询功能"""

    def test_query_fund_details_invalid_code_format(self):
        """测试无效的基金代码格式"""
        # 测试非6位数字
        result1 = fund_tool.query_fund_details('123')
        assert result1['status'] == 'error'
        assert '无效的基金代码格式' in result1['message']

        # 测试包含字母
        result2 = fund_tool.query_fund_details('ABCDEF')
        assert result2['status'] == 'error'

        # 测试空字符串
        result3 = fund_tool.query_fund_details('')
        assert result3['status'] == 'error'

    @patch('fund_tool_akshare.ak.fund_overview_em')
    @patch('fund_tool_akshare.ak.fund_individual_achievement_xq')
    @patch('fund_tool_akshare.ak.fund_individual_analysis_xq')
    @patch('fund_tool_akshare.ak.fund_portfolio_hold_em')
    def test_query_fund_details_success(self, mock_portfolio, mock_analysis, mock_achievement, mock_overview):
        """测试成功查询基金详情"""
        # Mock overview 数据
        mock_overview_data = pd.DataFrame({
            '基金简称': ['华夏成长混合'],
            '基金类型': ['混合型-灵活'],
            '成立日期/规模': ['2001年12月18日 / 27.30亿元'],
            '基金经理人': ['郑晓辉,刘睿聪'],
            '资产规模': ['27.30亿元'],
            '管理费率': ['1.20%（每年）'],
            '托管费率': ['0.20%（每年）'],
            '业绩比较基准': ['本基金暂不设业绩比较基准']
        })
        mock_overview.return_value = mock_overview_data

        # Mock 其他数据
        mock_achievement.side_effect = Exception("SSL error")
        mock_analysis.side_effect = Exception("SSL error")
        mock_portfolio.return_value = pd.DataFrame({
            '股票名称': ['航天电器', '中航高科', '中国移动'],
            '占净值比例': [3.46, 3.24, 2.86]
        })

        # 执行查询
        result = fund_tool.query_fund_details('000001')

        # 验证基本信息
        assert result['status'] == 'success'
        assert result['code'] == '000001'
        assert result['name'] == '华夏成长混合'
        assert result['type'] == '混合型-灵活'
        assert result['inception_date'] == '2001年12月18日'

        # 验证基金经理
        assert len(result['managers']) == 2
        assert result['managers'][0]['姓名'] == '郑晓辉'
        assert result['managers'][1]['姓名'] == '刘睿聪'

        # 验证费率
        assert '管理费率' in result['fee_rates']
        assert '托管费率' in result['fee_rates']

        # 验证重仓股
        assert len(result['top_holdings']) == 3
        assert '航天电器' in result['top_holdings'][0]


class TestGetFundRankings:
    """测试基金排行榜功能"""

    @patch('fund_tool_akshare.ak.fund_open_fund_rank_em')
    def test_get_fund_rankings_success(self, mock_rank):
        """测试成功获取排行榜"""
        # Mock 数据
        mock_data = pd.DataFrame({
            '序号': [1, 2, 3],
            '基金代码': ['008382', '021875', '010391'],
            '基金简称': ['融通产业趋势股票', '路博迈资源精选股票发起A', '易方达战略新兴产业股票A'],
            '近1年': ['123.65', '116.1', '115.96'],
            '近3月': ['20.5', '18.3', '19.2'],
            '今年来': ['45.6', '42.1', '43.8']
        })
        mock_rank.return_value = mock_data

        # 执行查询
        result = fund_tool.get_fund_rankings('股票型')

        # 验证
        assert result['status'] == 'success'
        assert result['count'] == 3
        assert result['data'][0]['基金代码'] == '008382'
        assert result['data'][0]['近1年'] == '123.65'

    @patch('fund_tool_akshare.ak.fund_open_fund_rank_em')
    def test_get_fund_rankings_error(self, mock_rank):
        """测试获取失败"""
        mock_rank.side_effect = Exception("网络错误")

        # 执行查询
        result = fund_tool.get_fund_rankings('股票型')

        # 验证
        assert result['status'] == 'error'
        assert '获取排行榜失败' in result['message']


class TestGetFundRating:
    """测试基金评级功能"""

    @patch('fund_tool_akshare.ak.fund_rating_all')
    def test_get_fund_rating_success(self, mock_rating):
        """测试成功获取评级"""
        # Mock 数据
        mock_data = pd.DataFrame({
            '代码': ['000001', '000002'],
            '简称': ['华夏成长混合', '华夏成长混合'],
            '上海证券': [2.0, 3.0],
            '招商证券': [2.0, 2.0],
            '济安金信': [1.0, 2.0],
            '晨星评级': [3.0, 4.0]
        })
        mock_rating.return_value = mock_data

        # 执行查询
        result = fund_tool.get_fund_rating('000001')

        # 验证
        assert result['status'] == 'success'
        assert result['ratings']['代码'] == '000001'
        assert result['ratings']['上海证券'] == 2.0
        assert result['ratings']['晨星评级'] == 3.0

    @patch('fund_tool_akshare.ak.fund_rating_all')
    def test_get_fund_rating_not_found(self, mock_rating):
        """测试基金未找到"""
        # Mock 空数据
        mock_rating.return_value = pd.DataFrame()

        # 执行查询
        result = fund_tool.get_fund_rating('999999')

        # 验证 - 实际代码在DataFrame为空时返回error
        assert result['status'] == 'error'
        assert '暂无评级数据' in result['message']

    @patch('fund_tool_akshare.ak.fund_rating_all')
    def test_get_fund_rating_error(self, mock_rating):
        """测试获取失败"""
        mock_rating.side_effect = Exception("网络错误")

        # 执行查询
        result = fund_tool.get_fund_rating('000001')

        # 验证
        assert result['status'] == 'error'
        assert '获取评级失败' in result['message']


class TestCalculateRiskMetrics:
    """测试风险指标计算"""

    def test_calculate_risk_metrics_from_data_valid(self):
        """测试从有效数据计算风险指标"""
        # 创建模拟数据
        mock_data = pd.DataFrame({
            '周期': ['近1年', '近3年', '近5年'],
            '年化波动率': [12.72, 18.66, 19.04],
            '年化夏普比率': [-1.89, -0.93, -0.11],
            '最大回撤': [26.58, 48.55, 48.55]
        })

        # 执行计算
        result = fund_tool.calculate_risk_metrics_from_data(mock_data)

        # 验证
        assert result is not None
        assert '年化波动率' in result
        assert '夏普比率' in result
        assert '最大回撤' in result
        assert result['年化波动率'] == '12.72%'
        assert result['夏普比率'] == '-1.89'
        assert result['最大回撤'] == '26.58%'

    def test_calculate_risk_metrics_from_data_empty(self):
        """测试空数据"""
        result = fund_tool.calculate_risk_metrics_from_data(pd.DataFrame())
        assert result is None


class TestIntegration:
    """集成测试"""

    @pytest.mark.integration
    @patch('fund_tool_akshare.ak.fund_name_em')
    def test_full_workflow_search_and_details(self, mock_fund_name_em):
        """测试完整工作流：搜索 -> 详情"""
        # Mock 基金列表
        mock_list_data = pd.DataFrame({
            '基金代码': ['000001', '000002'],
            '拼音缩写': ['HXCZHH', 'HXCZHH'],
            '基金简称': ['华夏成长混合', '华夏成长混合'],
            '基金类型': ['混合型-灵活', '混合型-灵活'],
            '拼音全称': ['HUAXIACHENGZHANGHUNHE', 'HUAXIACHENGZHANGHUNHE']
        })
        mock_fund_name_em.return_value = mock_list_data

        # 清除缓存
        fund_tool.get_fund_list.cache_clear()
        fund_tool.search_funds.cache_clear()

        # 步骤1: 搜索
        search_result = fund_tool.search_funds('华夏')
        assert search_result['status'] == 'success'
        assert search_result['count'] == 2

        # 步骤2: 获取详情（需要mock更多数据）
        with patch('fund_tool_akshare.ak.fund_overview_em') as mock_overview, \
             patch('fund_tool_akshare.ak.fund_individual_achievement_xq'), \
             patch('fund_tool_akshare.ak.fund_individual_analysis_xq'), \
             patch('fund_tool_akshare.ak.fund_portfolio_hold_em') as mock_portfolio:

            mock_overview_data = pd.DataFrame({
                '基金简称': ['华夏成长混合'],
                '基金类型': ['混合型-灵活'],
                '成立日期/规模': ['2001年12月18日 / 27.30亿元'],
                '基金经理人': ['郑晓辉,刘睿聪'],
                '资产规模': ['27.30亿元'],
                '管理费率': ['1.20%（每年）'],
                '托管费率': ['0.20%（每年）'],
                '业绩比较基准': ['本基金暂不设业绩比较基准']
            })
            mock_overview.return_value = mock_overview_data
            mock_portfolio.return_value = pd.DataFrame()

            details_result = fund_tool.query_fund_details('000001')
            assert details_result['status'] == 'success'
            assert details_result['name'] == '华夏成长混合'


# === Pytest 配置和夹具 ===

@pytest.fixture(scope="module")
def fund_data_sample():
    """提供示例基金数据"""
    return pd.DataFrame({
        '基金代码': ['000001', '000002', '000011'],
        '拼音缩写': ['HXCZHH', 'HXCZHH', 'HXDPJXA'],
        '基金简称': ['华夏成长混合', '华夏成长混合', '华夏大盘精选混合A'],
        '基金类型': ['混合型-灵活', '混合型-灵活', '混合型-灵活'],
        '拼音全称': ['HUAXIACHENGZHANGHUNHE', 'HUAXIACHENGZHANGHUNHE', 'HUAXIADAPANJINGXUANHUNHE']
    })


@pytest.fixture(scope="module")
def fund_details_sample():
    """提供示例基金详情数据"""
    return pd.DataFrame({
        '基金简称': ['华夏成长混合'],
        '基金类型': ['混合型-灵活'],
        '成立日期/规模': ['2001年12月18日 / 27.30亿元'],
        '基金经理人': ['郑晓辉,刘睿聪'],
        '资产规模': ['27.30亿元'],
        '管理费率': ['1.20%（每年）'],
        '托管费率': ['0.20%（每年）'],
        '业绩比较基准': ['本基金暂不设业绩比较基准']
    })


# === 测试标记 ===

pytestmark = [
    pytest.mark.unit,  # 单元测试
    pytest.mark.fund,  # 基金相关测试
]


# === 运行测试的说明 ===
"""
运行所有测试:
    pytest test_fund_tool.py -v

运行特定测试类:
    pytest test_fund_tool.py::TestSearchFunds -v

运行特定测试方法:
    pytest test_fund_tool.py::TestSearchFunds::test_search_funds_by_name -v

运行集成测试:
    pytest test_fund_tool.py -m integration -v

显示覆盖率:
    pytest test_fund_tool.py --cov=fund_tool_akshare --cov-report=html

并行运行:
    pytest test_fund_tool.py -n auto

生成详细报告:
    pytest test_fund_tool.py -v --tb=short
"""
