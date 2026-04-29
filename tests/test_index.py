# -*- coding: utf-8 -*-
"""
指数发现模块的集成测试
使用真实的 akshare API，需要网络连接

测试指数:
  - 宽基: 000300（沪深300）, 000905（中证500）
  - 行业: 000819（有色金属）, 399967（中证军工）
  - 主题: H30174（中证新能源）
"""

import pytest
import sys
import os
import json
from datetime import datetime

# 导入被测试的模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fund_tools import (
    cache,
    index,
    get_index_list,
    update_index_cache,
    get_broad_indices,
    get_industry_indices,
    get_sector_indices,
    get_strategy_indices,
    get_style_indices,
    get_all_stock_indices,
    search_indices_all,
    get_index_info,
    INDEX_DB_FILE,
)

# 测试用的指数代码
TEST_INDICES = {
    'broad': ['000300', '000905', '000852'],      # 沪深300, 中证500, 中证1000
    'industry': ['000819', '399967', '399987'],   # 有色金属, 中证军工, 中证白酒
    'sector': ['H30174', 'H30184'],               # 中证新能源, 中证光伏产业
}


# ============================================================================
# 测试缓存模块
# ============================================================================

@pytest.mark.integration
class TestIndexCache:
    """测试指数缓存功能（真实网络请求）"""

    def setup_method(self):
        get_index_list.cache_clear()

    def test_get_index_list_returns_data(self):
        """测试获取指数列表返回数据"""
        data = get_index_list()

        # 验证返回结构
        assert isinstance(data, dict)
        assert 'broad' in data
        assert 'industry' in data
        assert 'sector' in data
        assert 'updated_at' in data
        assert 'total' in data

    def test_get_index_list_has_sufficient_data(self):
        """测试指数列表包含足够的数据"""
        data = get_index_list()

        # 验证数据量（中证指数官网应该有1000+股票指数）
        assert data['total'] > 1000, f"指数总数太少: {data['total']}"

        # 验证各类别数量
        assert len(data['broad']) > 30, f"宽基指数太少: {len(data['broad'])}"
        assert len(data['industry']) > 300, f"行业指数太少: {len(data['industry'])}"
        assert len(data['sector']) > 500, f"主题指数太少: {len(data['sector'])}"

        print(f"✅ 总计 {data['total']} 个指数:")
        print(f"   - 宽基: {len(data['broad'])}")
        print(f"   - 行业: {len(data['industry'])}")
        print(f"   - 主题: {len(data['sector'])}")
        print(f"   - 策略: {len(data.get('strategy', []))}")
        print(f"   - 风格: {len(data.get('style', []))}")

    def test_cache_file_exists_after_save(self):
        """测试缓存文件被正确保存"""
        # 确保缓存已生成
        data = get_index_list()

        assert os.path.exists(INDEX_DB_FILE), "缓存文件不存在"

        # 验证缓存文件可读
        with open(INDEX_DB_FILE, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

        assert isinstance(cached_data, dict)
        assert 'broad' in cached_data
        assert cached_data.get('total', 0) > 0

        print(f"✅ 缓存文件存在: {INDEX_DB_FILE}")

    def test_update_index_cache_works(self):
        """测试强制更新缓存功能"""
        # 获取旧数据
        old_data = get_index_list()
        old_updated_at = old_data.get('updated_at')

        # 强制更新
        new_data = update_index_cache()

        # 验证更新成功
        assert new_data['total'] > 0
        assert 'updated_at' in new_data

        # 验证缓存文件存在
        assert os.path.exists(INDEX_DB_FILE)

        print(f"✅ 缓存更新成功: {new_data['total']} 个指数")

    def test_merged_cache_contains_missing_common_indices(self):
        """测试聚合缓存补进常见宽基指数"""
        data = get_index_list()
        all_indices = []
        for key, value in data.items():
            if isinstance(value, list):
                all_indices.extend(value)

        codes = {item.get("code") for item in all_indices}
        assert "000016" in codes, "缓存中应包含上证50"
        assert "399673" in codes, "缓存中应包含创业板50"


# ============================================================================
# 测试联网获取功能
# ============================================================================

@pytest.mark.integration
class TestIndexFetch:
    """测试联网获取指数功能（真实网络请求）"""

    def test_fetch_indices_from_csindex(self):
        """测试从中证指数官网获取数据"""
        data = index.fetch_indices_from_csindex()

        # 验证返回结构
        assert isinstance(data, dict)
        assert 'broad' in data
        assert 'industry' in data
        assert 'sector' in data

        # 验证各类别都是列表
        for category in ['broad', 'industry', 'sector', 'strategy', 'style']:
            assert category in data
            assert isinstance(data[category], list)

        print(f"✅ 成功从中证指数官网获取 {sum(len(v) for v in data.values())} 个指数")

    def test_classify_index(self):
        """测试指数分类逻辑"""
        # 测试股票指数
        assert index._classify_index("规模", "股票") == "broad"
        assert index._classify_index("行业", "股票") == "industry"
        assert index._classify_index("主题", "股票") == "sector"
        assert index._classify_index("策略", "股票") == "strategy"
        assert index._classify_index("风格", "股票") == "style"

        # 测试非股票指数
        assert index._classify_index("规模", "固定收益") is None

        print("✅ 指数分类逻辑正确")

    def test_index_data_structure(self):
        """测试指数数据结构"""
        data = index.fetch_indices_from_csindex()

        # 检查第一个指数的数据结构
        for category in ['broad', 'industry', 'sector']:
            if len(data[category]) > 0:
                first_index = data[category][0]

                # 验证必需字段
                required_fields = ['code', 'name', 'category', 'index_class', 'asset_class']
                for field in required_fields:
                    assert field in first_index, f"缺少字段: {field}"

                print(f"✅ {category} 类别数据结构正确")
                break


# ============================================================================
# 测试便捷函数
# ============================================================================

@pytest.mark.integration
class TestIndexConvenience:
    """测试便捷函数（真实数据）"""

    def test_get_broad_indices(self):
        """测试获取宽基指数"""
        indices = get_broad_indices()

        assert isinstance(indices, list)
        assert len(indices) > 30

        # 验证数据结构
        if len(indices) > 0:
            assert 'code' in indices[0]
            assert 'name' in indices[0]
            assert indices[0]['category'] == 'broad'

        print(f"✅ 宽基指数: {len(indices)} 个")

    def test_get_industry_indices(self):
        """测试获取行业指数"""
        indices = get_industry_indices()

        assert isinstance(indices, list)
        assert len(indices) > 300

        # 验证数据结构
        if len(indices) > 0:
            assert indices[0]['category'] == 'industry'

        print(f"✅ 行业指数: {len(indices)} 个")

    def test_get_sector_indices(self):
        """测试获取主题指数"""
        indices = get_sector_indices()

        assert isinstance(indices, list)
        assert len(indices) > 500

        # 验证数据结构
        if len(indices) > 0:
            assert indices[0]['category'] == 'sector'

        print(f"✅ 主题指数: {len(indices)} 个")

    def test_get_strategy_indices(self):
        """测试获取策略指数"""
        indices = get_strategy_indices()

        assert isinstance(indices, list)

        # 验证数据结构
        if len(indices) > 0:
            assert indices[0]['category'] == 'strategy'

        print(f"✅ 策略指数: {len(indices)} 个")

    def test_get_style_indices(self):
        """测试获取风格指数"""
        indices = get_style_indices()

        assert isinstance(indices, list)

        # 验证数据结构
        if len(indices) > 0:
            assert indices[0]['category'] == 'style'

        print(f"✅ 风格指数: {len(indices)} 个")

    def test_get_all_stock_indices(self):
        """测试获取所有股票指数"""
        indices = get_all_stock_indices()

        assert isinstance(indices, list)
        assert len(indices) > 1000

        # 验证去重
        codes = [idx['code'] for idx in indices]
        assert len(codes) == len(set(codes)), "存在重复的指数代码"

        print(f"✅ 所有股票指数: {len(indices)} 个（无重复）")


# ============================================================================
# 测试搜索和查询功能
# ============================================================================

@pytest.mark.integration
class TestIndexSearch:
    """测试指数搜索和查询（真实数据）"""

    def test_search_indices_all_by_name(self):
        """测试按名称搜索指数"""
        results = search_indices_all("红利")

        assert isinstance(results, list)
        assert len(results) > 10  # 应该有多个红利相关指数

        # 验证结果都包含关键词
        for idx in results:
            assert "红利" in idx['name'] or "红利" in idx['code']

        print(f"✅ 搜索'红利'找到 {len(results)} 个指数")

    def test_search_indices_all_by_code(self):
        """测试按代码搜索指数"""
        results = search_indices_all("0003")

        assert isinstance(results, list)
        assert len(results) > 0

        # 验证结果都包含关键词
        for idx in results:
            assert "0003" in idx['code']

        print(f"✅ 搜索'0003'找到 {len(results)} 个指数")

    def test_get_index_info_exists(self):
        """测试查询存在的指数"""
        info = get_index_info("000300")

        assert info is not None
        assert info['code'] == '000300'
        assert info['name'] == '沪深300'
        assert info['category'] == 'broad'
        assert 'index_class' in info
        assert 'asset_class' in info

        print(f"✅ 查询沪深300: {info['name']} ({info['category']})")

    def test_get_index_info_not_exists(self):
        """测试查询不存在的指数"""
        info = get_index_info("999999")

        assert info is None

        print("✅ 查询不存在的指数返回 None")

    def test_get_index_info_for_all_categories(self):
        """测试查询各类别的指数"""
        test_cases = [
            ('000300', 'broad'),      # 沪深300
            ('000819', 'industry'),   # 有色金属
            ('H30184', 'sector'),     # 中证光伏产业
        ]

        for code, expected_category in test_cases:
            info = get_index_info(code)

            assert info is not None, f"未找到指数 {code}"
            assert info['code'] == code
            assert info['category'] == expected_category

            print(f"✅ {code}: {info['name']} ({info['category']})")


# ============================================================================
# 测试数据完整性
# ============================================================================

@pytest.mark.integration
class TestIndexDataIntegrity:
    """测试指数数据完整性"""

    def test_all_test_indices_exist(self):
        """测试所有测试用的指数都存在"""
        all_indices = get_all_stock_indices()
        all_codes = {idx['code'] for idx in all_indices}

        for category, codes in TEST_INDICES.items():
            for code in codes:
                assert code in all_codes, f"测试指数 {code} 不在列表中"
                print(f"✅ 找到测试指数: {code}")

    def test_index_has_required_fields(self):
        """测试指数包含必需字段"""
        all_indices = get_all_stock_indices()

        if len(all_indices) > 0:
            # 抽查前10个
            for idx in all_indices[:10]:
                required_fields = ['code', 'name', 'category', 'index_class', 'asset_class']
                for field in required_fields:
                    assert field in idx, f"指数 {idx.get('code')} 缺少字段: {field}"

            print("✅ 指数数据字段完整")

    def test_no_empty_codes_or_names(self):
        """测试没有空的代码或名称"""
        all_indices = get_all_stock_indices()

        for idx in all_indices:
            assert idx['code'], "存在空的指数代码"
            assert idx['name'], "存在空的指数名称"

        print(f"✅ 所有 {len(all_indices)} 个指数代码和名称都不为空")

    def test_category_consistency(self):
        """测试类别一致性"""
        data = get_index_list()

        for category in ['broad', 'industry', 'sector', 'strategy', 'style']:
            if category in data:
                for idx in data[category]:
                    assert idx['category'] == category, \
                        f"指数 {idx['code']} 的类别不匹配: {idx['category']} != {category}"

        print("✅ 所有指数类别一致")


# ============================================================================
# 运行标记
# ============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
