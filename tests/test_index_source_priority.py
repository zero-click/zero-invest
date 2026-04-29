# -*- coding: utf-8 -*-
"""
数据源优先级映射测试

测试目标:
  验证 get_history_source_priority 和 get_valuation_source_priority
  能够根据指数代码前缀返回正确的数据源优先级列表

测试指数:
  - 中证行业: 932136（保险）
  - 深交所宽基: 000300（沪深300）、399330（深证100）
  - 上交所宽基: 000016（上证50）

测试内容:
  - 93xxxx 开头指数只返回 csindex
  - 000xxx/399xxx 开头指数返回完整数据源列表
  - 估值数据源优先级正确
"""

import pytest
from src.fund_tools.index import get_history_source_priority, get_valuation_source_priority


class TestDataSourcePriority:
    """数据源优先级映射测试"""

    def test_csrc_industry_index_93xxxx_csindex_only(self):
        """
        测试中证行业指数（93xxxx）数据源优先级

        验证:
          - 历史数据源只包含 csindex
          - 估值数据源只包含 csindex
          - 不包含 sina、tx、eastmoney 等不支持的数据源
        """
        # 保险行业 932136
        hist_priority = get_history_source_priority("932136")
        val_priority = get_valuation_source_priority("932136")

        assert hist_priority == ["csindex"], \
            f"中证行业指数历史数据源应为 [csindex], 实际 {hist_priority}"

        assert val_priority == ["csindex"], \
            f"中证行业指数估值数据源应为 [csindex], 实际 {val_priority}"

        # 验证不包含不支持的数据源
        assert "sina_daily" not in hist_priority
        assert "tx_daily" not in hist_priority
        assert "eastmoney_daily" not in hist_priority
        assert "legulegu" not in val_priority

    def test_szse_broad_index_000xxx_full_sources(self):
        """
        测试深交所宽基指数（000xxx）数据源优先级

        验证:
          - 历史数据源包含 sina_daily, tx_daily, eastmoney_daily, csindex, eastmoney_hist
          - 估值数据源包含 legulegu, csindex
          - 优先级顺序正确
        """
        # 沪深300 000300
        hist_priority = get_history_source_priority("000300")
        val_priority = get_valuation_source_priority("000300")

        # 验证历史数据源包含所有预期数据源
        assert "sina_daily" in hist_priority, "应包含 sina_daily"
        assert "tx_daily" in hist_priority, "应包含 tx_daily"
        assert "eastmoney_daily" in hist_priority, "应包含 eastmoney_daily"
        assert "csindex" in hist_priority, "应包含 csindex"
        assert "eastmoney_hist" in hist_priority, "应包含 eastmoney_hist"

        # 验证优先级顺序（sina 应该在 csindex 之前）
        sina_index = hist_priority.index("sina_daily")
        csindex_index = hist_priority.index("csindex")
        assert sina_index < csindex_index, "sina_daily 优先级应高于 csindex"

        # 验证估值数据源
        assert val_priority == ["legulegu", "csindex"], \
            f"深交所指数估值数据源应为 [legulegu, csindex], 实际 {val_priority}"

    def test_szse_broad_index_399xxx_full_sources(self):
        """
        测试深交所宽基指数（399xxx）数据源优先级

        验证:
          - 历史数据源包含所有数据源
          - 估值数据源包含 legulegu, csindex
          - 与 000xxx 开头指数优先级一致
        """
        # 深证100 399330
        hist_priority = get_history_source_priority("399330")
        val_priority = get_valuation_source_priority("399330")

        # 验证历史数据源
        assert "sina_daily" in hist_priority
        assert "tx_daily" in hist_priority
        assert "csindex" in hist_priority

        # 验证估值数据源
        assert val_priority == ["legulegu", "csindex"]

    def test_other_index_default_sources(self):
        """
        测试其他指数（非93、非000、非399开头）数据源优先级

        验证:
          - 历史数据源包含完整列表
          - 估值数据源包含 legulegu, csindex
        """
        # 上证50 000016
        hist_priority = get_history_source_priority("000016")
        val_priority = get_valuation_source_priority("000016")

        # 验证历史数据源
        assert len(hist_priority) == 5, "应包含 5 个数据源"
        assert "sina_daily" in hist_priority
        assert "csindex" in hist_priority

        # 验证估值数据源
        assert val_priority == ["legulegu", "csindex"]

    @pytest.mark.parametrize("code,expected_hist_sources,expected_val_sources", [
        ("932136", ["csindex"], ["csindex"]),
        ("000300", ["sina_daily", "tx_daily", "eastmoney_daily", "csindex", "eastmoney_hist"], ["legulegu", "csindex"]),
        ("399330", ["sina_daily", "tx_daily", "eastmoney_daily", "csindex", "eastmoney_hist"], ["legulegu", "csindex"]),
        ("000016", ["sina_daily", "tx_daily", "eastmoney_daily", "csindex", "eastmoney_hist"], ["legulegu", "csindex"]),
    ])
    def test_source_priority_mapping(
        self, code, expected_hist_sources, expected_val_sources
    ):
        """
        参数化测试数据源优先级映射

        验证:
          - 不同指数代码返回正确的优先级列表
          - 历史数据源优先级正确
          - 估值数据源优先级正确
        """
        hist_priority = get_history_source_priority(code)
        val_priority = get_valuation_source_priority(code)

        assert hist_priority == expected_hist_sources, \
            f"指数 {code} 历史数据源应为 {expected_hist_sources}, 实际 {hist_priority}"

        assert val_priority == expected_val_sources, \
            f"指数 {code} 估值数据源应为 {expected_val_sources}, 实际 {val_priority}"

    def test_source_priority_efficiency(self):
        """
        测试数据源优先级映射的效率优化

        验证:
          - 中证行业指数（93xxxx）只尝试 1 个数据源
          - 避免浪费时间在不支持的数据源上
        """
        # 中证行业指数应该只返回 1 个数据源
        hist_priority = get_history_source_priority("932136")
        val_priority = get_valuation_source_priority("932136")

        assert len(hist_priority) == 1, "中证行业指数历史数据源应只有 1 个"
        assert len(val_priority) == 1, "中证行业指数估值数据源应只有 1 个"

        # 深交所/上交所指数应该有更多数据源
        hist_priority_000 = get_history_source_priority("000300")
        assert len(hist_priority_000) > 1, "深交所指数历史数据源应多于 1 个"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
