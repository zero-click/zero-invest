"""
portfolio_analysis.py 的单元测试和集成测试
"""
import os
import sys
import pytest
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_analysis import (
    _get_valuation_grade,
    _calc_percentile,
    _parse_multpl_date,
    calculate_deviation,
    read_portfolio_from_excel,
    format_deviation_report,
    format_us_valuation_report,
    format_hk_valuation_report,
    TARGET_ALLOCATIONS,
    EXCEL_PATH,
)


# ============ 单元测试 ============


class TestHelpers:
    """纯函数单元测试"""

    def test_valuation_grade_extremely_undervalued(self):
        assert _get_valuation_grade(5) == "极度低估 🥶"

    def test_valuation_grade_undervalued(self):
        assert _get_valuation_grade(15) == "低估 🟢"

    def test_valuation_grade_below_average(self):
        assert _get_valuation_grade(30) == "偏低 🟡"

    def test_valuation_grade_fair(self):
        assert _get_valuation_grade(50) == "合理 🟠"

    def test_valuation_grade_above_average(self):
        assert _get_valuation_grade(70) == "偏高 🔴"

    def test_valuation_grade_overvalued(self):
        assert _get_valuation_grade(85) == "高估 🔥"

    def test_valuation_grade_extremely_overvalued(self):
        assert _get_valuation_grade(95) == "极度高估 🚨"

    def test_valuation_grade_boundary(self):
        assert _get_valuation_grade(0) == "极度低估 🥶"
        assert _get_valuation_grade(10) == "低估 🟢"
        assert _get_valuation_grade(20) == "偏低 🟡"
        assert _get_valuation_grade(40) == "合理 🟠"
        assert _get_valuation_grade(60) == "偏高 🔴"
        assert _get_valuation_grade(80) == "高估 🔥"
        assert _get_valuation_grade(90) == "极度高估 🚨"
        assert _get_valuation_grade(100) == "极度高估 🚨"

    def test_calc_percentile_basic(self):
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert _calc_percentile(values, 5) == 50.0
        assert _calc_percentile(values, 1) == 10.0
        assert _calc_percentile(values, 10) == 100.0

    def test_calc_percentile_single_value(self):
        assert _calc_percentile([42], 42) == 100.0

    def test_parse_multpl_date(self):
        assert _parse_multpl_date("Apr 23, 2026") == "2026-04-23"
        assert _parse_multpl_date("Jan 1, 2025") == "2025-01-01"
        assert _parse_multpl_date("Dec 31, 2024") == "2024-12-31"

    def test_target_allocations_sum(self):
        total = sum(TARGET_ALLOCATIONS.values())
        assert abs(total - 1.0) < 0.001, f"目标配比之和应为1.0，实际为{total}"


class TestDeviationCalculation:
    """偏离度计算单元测试"""

    def test_normal_portfolio(self):
        portfolio = {
            "total": 1000000,
            "accounts": {
                "安全账户": {"amount": 300000, "items": []},
                "稳定现金流": {"amount": 250000, "items": []},
                "成长账户": {"amount": 350000, "items": []},
                "机会账户": {"amount": 100000, "items": []},
            },
        }
        result = calculate_deviation(portfolio)
        assert result["total"] == 1000000
        for acc_name in TARGET_ALLOCATIONS:
            acc = result["accounts"][acc_name]
            assert acc["status"] == "正常"
            assert acc["absolute_deviation"] < 0.001
        assert len(result["alerts"]) == 0

    def test_unbalanced_portfolio(self):
        portfolio = {
            "total": 1000000,
            "accounts": {
                "安全账户": {"amount": 560000, "items": []},
                "稳定现金流": {"amount": 185000, "items": []},
                "成长账户": {"amount": 255000, "items": []},
                "机会账户": {"amount": 0, "items": []},
            },
        }
        result = calculate_deviation(portfolio)
        assert result["accounts"]["安全账户"]["status"] == "紧急"
        assert result["accounts"]["安全账户"]["direction"] == "超配"
        assert result["accounts"]["机会账户"]["status"] == "紧急"
        assert result["accounts"]["机会账户"]["direction"] == "欠配"
        assert len(result["alerts"]) >= 2

    def test_zero_total(self):
        portfolio = {
            "total": 0,
            "accounts": {k: {"amount": 0, "items": []} for k in TARGET_ALLOCATIONS},
        }
        result = calculate_deviation(portfolio)
        assert result["total"] == 0
        assert "总资产为0" in result["alerts"]

    def test_relative_deviation_calculation(self):
        # 安全账户 30% target, actual 36% → relative = 6/30 = 20%
        portfolio = {
            "total": 100000,
            "accounts": {
                "安全账户": {"amount": 36000, "items": []},
                "稳定现金流": {"amount": 25000, "items": []},
                "成长账户": {"amount": 35000, "items": []},
                "机会账户": {"amount": 4000, "items": []},
            },
        }
        result = calculate_deviation(portfolio)
        safety = result["accounts"]["安全账户"]
        assert abs(safety["relative_deviation"] - 0.20) < 0.01


class TestFormatting:
    """格式化函数测试"""

    def test_format_deviation_report(self):
        deviation = {
            "total": 500000,
            "accounts": {
                "安全账户": {
                    "amount": 150000,
                    "actual": 0.30,
                    "target": 0.30,
                    "absolute_deviation": 0.0,
                    "relative_deviation": 0.0,
                    "status": "正常",
                    "direction": "欠配",
                    "items_count": 3,
                }
            },
            "alerts": [],
        }
        report = format_deviation_report(deviation)
        assert "四账户偏离度报告" in report
        assert "安全账户" in report

    def test_format_us_valuation_error(self):
        report = format_us_valuation_report({"status": "error", "error": "timeout"})
        assert "失败" in report

    def test_format_hk_valuation_report(self):
        hk_data = {
            "status": "ok",
            "中国互联网": {"PE": 22.79, "滚动PE": 10.46, "股息率": 1.13, "date": "2026-03-27"},
        }
        report = format_hk_valuation_report(hk_data)
        assert "中国互联网" in report


# ============ 集成测试 ============


@pytest.mark.integration
class TestIntegrationExcel:
    """需要 current.xlsx 文件的集成测试"""

    @pytest.fixture(autouse=True)
    def check_excel(self):
        if not os.path.exists(EXCEL_PATH):
            pytest.skip(f"投资组合文件不存在: {EXCEL_PATH}")

    def test_read_portfolio(self):
        portfolio = read_portfolio_from_excel()
        assert portfolio["total"] > 0
        assert len(portfolio["funds"]) > 0

        # 四个账户都应有数据（至少有金额）
        for acc_name in TARGET_ALLOCATIONS:
            assert acc_name in portfolio["accounts"], f"缺少账户: {acc_name}"

    def test_calculate_deviation_with_real_data(self):
        portfolio = read_portfolio_from_excel()
        deviation = calculate_deviation(portfolio)

        assert deviation["total"] > 0
        assert len(deviation["accounts"]) == 4
        assert all(acc["status"] in ("正常", "关注", "紧急") for acc in deviation["accounts"].values())

    def test_format_deviation_report_with_real_data(self):
        portfolio = read_portfolio_from_excel()
        deviation = calculate_deviation(portfolio)
        report = format_deviation_report(deviation)
        assert len(report) > 100
        assert "总资产" in report


@pytest.mark.integration
@pytest.mark.slow
class TestIntegrationNetwork:
    """需要网络访问的集成测试"""

    def test_get_us_index_valuation(self):
        from portfolio_analysis import get_us_index_valuation

        result = get_us_index_valuation()
        assert result.get("status") == "ok", f"美股估值获取失败: {result.get('error')}"
        assert "标普500" in result
        sp = result["标普500"]
        assert sp["PE"] > 0
        assert sp["PE分位_10年"] > 0
        assert "估值等级_PE" in sp

    def test_get_hk_index_valuation(self):
        from portfolio_analysis import get_hk_index_valuation

        result = get_hk_index_valuation()
        assert result.get("status") == "ok"
        assert "中国互联网" in result
        ci = result["中国互联网"]
        assert ci.get("PE") is not None or ci.get("error") is not None

    def test_get_portfolio_analysis_full(self):
        from portfolio_analysis import get_portfolio_analysis

        result = get_portfolio_analysis()
        assert "deviation" in result
        assert "us_valuation" in result
        assert "hk_valuation" in result
        assert "summary" in result
        assert len(result["summary"]) > 100
