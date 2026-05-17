# -*- coding: utf-8 -*-
"""
fetch_index_history_data 集成测试

测试目标:
  验证 fetch_index_history_data 能够成功获取真实指数的历史数据

测试指数:
  - 宽基: 000300（沪深300）、000016（上证50）
  - 行业: 399986（银行）、399811（电子）、932136（保险）

测试内容:
  - 能够成功获取历史数据
  - 返回正确的数据结构
  - 数据字段完整且类型正确
  - 时间窗口过滤正确
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta

from src.fund_tools import index


class TestFetchIndexHistoryIntegration:
    """
    fetch_index_history_data 集成测试

    注意: 这些测试会调用真实的 akshare API，请确保网络连接正常
    """

    def test_fetch_broad_index_000300_history(self):
        """
        测试获取沪深300（000300）历史数据

        验证:
          - 成功返回 DataFrame
          - 包含必要的列（日期、收盘、涨跌幅）
          - 数据不为空
          - 数据按日期升序排列
        """
        df = index.fetch_index_history_data("000300")

        assert df is not None, "应成功返回数据"
        assert isinstance(df, pd.DataFrame), "返回值应为 DataFrame"
        assert len(df) > 0, "数据不应为空"

        # 验证必要的列存在
        required_columns = ["日期", "收盘", "涨跌幅"]
        for col in required_columns:
            assert col in df.columns, f"缺少必要列: {col}"

        # 验证数据类型
        assert pd.api.types.is_datetime64_any_dtype(df["日期"]), "日期列应为 datetime 类型"
        assert pd.api.types.is_numeric_dtype(df["收盘"]), "收盘价应为数值类型"
        assert pd.api.types.is_numeric_dtype(df["涨跌幅"]), "涨跌幅应为数值类型"

        # 验证数据按日期升序排列
        assert df["日期"].is_monotonic_increasing, "数据应按日期升序排列"

        # 验证最新数据不是太旧（应该在最近7天内）
        latest_date = df.iloc[-1]["日期"]
        days_ago = (datetime.now() - latest_date).days
        assert days_ago <= 7, f"最新数据应该是最近的，当前差 {days_ago} 天"

    def test_fetch_broad_index_000016_history(self):
        """
        测试获取上证50（000016）历史数据

        验证:
          - 成功返回 DataFrame
          - 数据字段完整
          - 数据点数合理（至少500条，覆盖约2年）
        """
        df = index.fetch_index_history_data("000016")

        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) >= 500, f"数据点数应足够多，当前 {len(df)} 条"

        # 验证数据完整性
        assert df["收盘"].notna().all(), "收盘价不应有缺失值"
        assert df["日期"].notna().all(), "日期不应有缺失值"

        # 验证价格合理性（上证50在 700-5000 点之间，考虑历史波动）
        closes = df["收盘"].astype(float)
        assert closes.min() > 500, f"最低价应在合理范围内，实际 {closes.min():.2f}"
        assert closes.max() < 10000, f"最高价应在合理范围内，实际 {closes.max():.2f}"

    def test_fetch_industry_index_399986_bank_history(self):
        """
        测试获取银行指数（399986）历史数据

        验证:
          - 成功返回 DataFrame
          - 银行指数数据点合理
          - 数据质量符合要求
        """
        df = index.fetch_index_history_data("399986")

        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        # 验证基本列结构
        assert "日期" in df.columns
        assert "收盘" in df.columns

        # 验证数据质量
        # 银行指数通常比较稳定，波动不会太大
        if len(df) > 1:
            returns = df["收盘"].pct_change().dropna()
            # 日涨跌幅超过 10% 的天数应该很少（银行指数相对稳定）
            extreme_moves = (returns.abs() > 0.10).sum()
            assert extreme_moves <= len(df) * 0.05, "极端波动天数应该很少"

    def test_fetch_industry_index_399811_electronics_history(self):
        """
        测试获取电子指数（399811）历史数据

        验证:
          - 成功返回 DataFrame
          - 科技行业指数数据正常
          - 数据字段完整
        """
        df = index.fetch_index_history_data("399811")

        assert df is not None
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        # 验证必要列
        required_columns = ["日期", "收盘"]
        for col in required_columns:
            assert col in df.columns

        # 验证数据有效性
        assert df["收盘"].min() > 0, "指数点位应大于0"
        assert df["收盘"].max() < 20000, "指数点位应在合理范围内"

    def test_fetch_industry_index_932136_insurance_history(self):
        """
        测试获取保险指数（932136）历史数据

        验证:
          - 成功返回 DataFrame
          - 保险行业指数数据正常
          - 数据字段完整
          - 数据点数合理
        """
        df = index.fetch_index_history_data("932136")

        assert df is not None, "应成功返回保险指数数据"
        assert isinstance(df, pd.DataFrame), "返回值应为 DataFrame"
        assert len(df) > 0, "数据不应为空"

        # 验证必要列
        required_columns = ["日期", "收盘"]
        for col in required_columns:
            assert col in df.columns, f"缺少必要列: {col}"

        # 验证数据有效性（保险指数通常在 800-2500 点之间）
        closes = df["收盘"].astype(float)
        assert closes.min() > 500, f"最低价应在合理范围内，实际 {closes.min():.2f}"
        assert closes.max() < 5000, f"最高价应在合理范围内，实际 {closes.max():.2f}"

        # 验证数据点数（保险指数较新，至少有 200 条数据）
        assert len(df) >= 200, f"数据点数应足够，当前 {len(df)} 条"

        # 验证数据质量
        assert df["收盘"].notna().all(), "收盘价不应有缺失值"
        assert df["日期"].notna().all(), "日期不应有缺失值"

    def test_fetch_with_time_window(self):
        """
        测试带时间窗口的历史数据获取

        验证:
          - start_date 和 end_date 参数正确传递
          - 返回数据在指定时间范围内
        """
        # 获取最近1年的数据
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

        df = index.fetch_index_history_data("000300", start_date=start_date, end_date=end_date)

        assert df is not None
        assert len(df) > 0

        # 验证时间范围
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")

        assert df.iloc[0]["日期"] >= start_dt, "数据起始日期应在 start_date 之后"
        assert df.iloc[-1]["日期"] <= end_dt, "数据结束日期应在 end_date 之前"

        # 验证数据点数合理（1年大约 250 个交易日）
        assert 200 <= len(df) <= 300, f"1年数据点数应在 200-300 之间，当前 {len(df)}"

    def test_fetch_multiple_sources_fallback(self):
        """
        测试多数据源容错机制

        验证:
          - 即使某个数据源失败，仍能获取数据
          - 至少有一个数据源可用
        """
        # 测试一个可能不在主流数据源的指数
        test_codes = ["000300", "000016", "399986", "399811", "932136"]

        for code in test_codes:
            df = index.fetch_index_history_data(code)
            assert df is not None, f"应能获取指数 {code} 的数据"
            assert len(df) > 0, f"指数 {code} 的数据不应为空"

    def test_data_normalization(self):
        """
        测试数据标准化

        验证:
          - 不同数据源返回的数据格式统一
          - 列名符合规范（中文列名）
          - 数据类型正确
        """
        df = index.fetch_index_history_data("000300")

        # 验证列名是中文
        expected_columns = ["日期", "收盘", "开盘", "最高", "最低", "成交量", "涨跌幅"]
        for col in expected_columns:
            if col in df.columns:
                assert isinstance(col, str), "列名应为字符串"

        # 验证数值列的类型
        numeric_columns = ["收盘", "开盘", "最高", "最低", "成交量", "涨跌幅"]
        for col in numeric_columns:
            if col in df.columns:
                assert pd.api.types.is_numeric_dtype(df[col]), f"{col} 应为数值类型"

    def test_index_returns_calculation(self):
        """
        测试基于历史数据的收益率计算

        验证:
          - get_index_returns 能正确计算收益率
          - 收益率计算结果合理
        """
        df = index.fetch_index_history_data("000300")
        current_price = float(df.iloc[-1]["收盘"])

        returns = index.get_index_returns(df, current_price=current_price)

        assert isinstance(returns, dict), "收益率应返回字典"
        assert "1月_收益率" in returns, "应包含 1月_收益率"
        assert "1年_收益率" in returns, "应包含 1年_收益率"

        # 验证收益率值合理（-50% 到 100% 之间）
        for key, value in returns.items():
            if value is not None:
                assert -50 <= value <= 100, f"{key} 收益率应在合理范围内: {value}"

    @pytest.mark.parametrize("code,expected_name", [
        ("000300", "沪深300"),
        ("000016", "上证50"),
        ("399986", "银行"),
        ("399811", "电子"),
        ("932136", "保险"),
    ])
    def test_index_codes_match_database(self, code, expected_name):
        """
        测试指数代码与数据库匹配

        验证:
          - 指数代码能在数据库中找到
          - 指数名称匹配
        """
        all_indices = index.get_all_stock_indices()
        index_info = index.get_index_info(all_indices, code)

        assert index_info is not None, f"应在数据库中找到指数 {code}"
        assert expected_name in index_info["name"] or index_info["name"] in expected_name, \
            f"指数名称应匹配: 期望 {expected_name}, 实际 {index_info['name']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
