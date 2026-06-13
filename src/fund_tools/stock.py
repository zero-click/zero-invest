# -*- coding: utf-8 -*-
"""个股数据查询模块

基于 akshare 获取 A 股个股数据，支持：
- 基础行情查询
- 历史价格走势
- 财务指标分析
- 估值分析（场景A/B/C）
- 准入检查
- 持仓状态管理
"""

import akshare as ak
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import pandas as pd


def search_stock(keyword: str) -> dict:
    """搜索股票

    Args:
        keyword: 股票代码或名称关键词

    Returns:
        {"status": "success", "data": [列表]} 或 {"status": "error", "message": "..."}
    """
    try:
        df = ak.stock_zh_a_spot_em()
        # 按代码或名称过滤
        filtered = df[(df['代码'].str.contains(keyword, case=False, na=False)) |
                      (df['名称'].str.contains(keyword, case=False, na=False))]
        return {
            "status": "success",
            "data": filtered[['代码', '名称', '最新价', '涨跌幅', '市值', '市盈率-动态', '市净率']].to_dict('records')
        }
    except Exception as e:
        return {"status": "error", "message": f"搜索失败: {str(e)}"}


def get_stock_spot(code: str) -> dict:
    """获取个股实时行情

    Args:
        code: 股票代码（如 "000001"）

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        df = ak.stock_zh_a_spot_em()
        stock = df[df['代码'] == code]
        if stock.empty:
            return {"status": "error", "message": f"未找到股票 {code}"}

        row = stock.iloc[0]
        return {
            "status": "success",
            "data": {
                "代码": row['代码'],
                "名称": row['名称'],
                "最新价": row['最新价'],
                "涨跌幅": row['涨跌幅'],
                "涨跌额": row['涨跌额'],
                "总市值": row['总市值'],
                "流通市值": row['流通市值'],
                "市盈率": row['市盈率-动态'],
                "市净率": row['市净率'],
                "换手率": row['换手率'],
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"获取行情失败: {str(e)}"}


def get_stock_hist(code: str, days: int = 90) -> dict:
    """获取个股历史K线数据

    Args:
        code: 股票代码
        days: 查询天数

    Returns:
        {"status": "success", "data": DataFrame, "stats": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')

        df = ak.stock_zh_a_hist(
            symbol=code,
            period='daily',
            start_date=start_date,
            end_date=end_date,
            adjust='qfq'
        )

        if df.empty:
            return {"status": "error", "message": f"未获取到 {code} 的历史数据"}

        # 计算统计指标
        current_price = df.iloc[-1]['收盘']
        high_30d = df.tail(30)['最高'].max()
        max_drawdown = ((df['收盘'].cummax() - df['收盘']) / df['收盘'].cummax()).max()
        current_drawdown = (current_price - high_30d) / high_30d if high_30d > 0 else 0

        returns = df['收盘'].pct_change().dropna()
        volatility = returns.std() * (252 ** 0.5)  # 年化波动率

        stats = {
            "期间涨跌幅": (current_price - df.iloc[0]['收盘']) / df.iloc[0]['收盘'] * 100,
            "30日高点": high_30d,
            "当前回撤": current_drawdown * 100,
            "最大回撤": max_drawdown * 100,
            "年化波动率": volatility * 100,
        }

        return {
            "status": "success",
            "data": df,
            "stats": stats
        }
    except Exception as e:
        return {"status": "error", "message": f"获取历史数据失败: {str(e)}"}


def get_stock_financial_indicator(code: str) -> dict:
    """获取个股财务分析指标

    Args:
        code: 股票代码（需带后缀，如 "301389.SZ"）

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        # 转换代码格式
        if code.startswith('6'):
            symbol = f"SH{code}"
        elif code.startswith('0') or code.startswith('3'):
            symbol = f"{code}.SZ"
        else:
            symbol = code

        df = ak.stock_financial_analysis_indicator_em(symbol=symbol, indicator="按报告期")

        if df.empty:
            return {"status": "error", "message": f"未获取到 {code} 的财务指标"}

        # 获取最新一期数据
        latest = df.iloc[-1]

        return {
            "status": "success",
            "data": {
                "ROE": latest.get('净资产收益率(ROE)'),
                "毛利率": latest.get('销售毛利率'),
                "净利率": latest.get('销售净利率'),
                "营收增速": latest.get('营业总收入同比增长'),
                "净利润增速": latest.get('净利润同比增长'),
                "资产负债率": latest.get('资产负债率'),
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"获取财务指标失败: {str(e)}"}


def analyze_scenario_a(code: str) -> dict:
    """场景A分析：稳定成长型（Forward PE / PEG）

    Args:
        code: 股票代码

    Returns:
        分析结果字典
    """
    # 获取基础数据
    spot = get_stock_spot(code)
    if spot['status'] != 'success':
        return spot

    data = spot['data']

    # 获取财务指标
    financial = get_stock_financial_indicator(code)

    # 获取盈利预测（简化处理，使用营收增速近似）
    growth_rate = financial.get('data', {}).get('营收增速', 0)

    # 计算 PEG
    pe = data.get('市盈率', 0)
    if pe and pe > 0 and growth_rate:
        peg = pe / growth_rate
    else:
        peg = None

    return {
        "status": "success",
        "scenario": "A",
        "type": "稳定成长型",
        "data": {
            "股票代码": code,
            "股票名称": data.get('名称'),
            "市盈率-TTM": pe,
            "营收增速": growth_rate,
            "PEG": peg,
            "判断": _evaluate_scenario_a(peg, growth_rate),
        }
    }


def _evaluate_scenario_a(peg: Optional[float], growth_rate: Optional[float]) -> str:
    """场景A估值判断"""
    if peg is None or growth_rate is None:
        return "数据不足，无法判断"

    if peg < 1:
        return "市场低估了增速（可能便宜）"
    elif peg <= 2:
        return "估值处于正常区间"
    else:
        return "市场给予高溢价（需增速持续加速支撑）"


def analyze_scenario_b(code: str) -> dict:
    """场景B分析：高速成长/亏损型（PS + FCF反算）

    Args:
        code: 股票代码

    Returns:
        分析结果字典
    """
    spot = get_stock_spot(code)
    if spot['status'] != 'success':
        return spot

    data = spot['data']

    # 获取财务数据
    financial = get_stock_financial_indicator(code)
    if financial['status'] != 'success':
        return {"status": "error", "message": "无法获取财务数据"}

    fin_data = financial['data']

    # 简化计算（实际需要完整的利润表和现金流量表）
    market_cap = data.get('总市值', 0)
    revenue_growth = fin_data.get('营收增速', 0)
    gross_margin = fin_data.get('毛利率', 0)

    # PS 估值
    # 假设年收入需要从利润表获取，这里用市值和营收增速做简化
    ps = "N/A"  # 需要营收数据

    return {
        "status": "success",
        "scenario": "B",
        "type": "高速成长/亏损型",
        "data": {
            "股票代码": code,
            "股票名称": data.get('名称'),
            "PS": ps,
            "营收增速": revenue_growth,
            "毛利率": gross_margin,
            "说明": "完整场景B分析需要利润表和现金流量表数据",
        }
    }


def analyze_scenario_c(code: str) -> dict:
    """场景C分析：强周期型（DOI、EV/EBITDA、PB）

    Args:
        code: 股票代码

    Returns:
        分析结果字典
    """
    spot = get_stock_spot(code)
    if spot['status'] != 'success':
        return spot

    data = spot['data']

    pb = data.get('市净率', 0)

    # 获取估值比较数据（包含EV/EBITDA）
    # 这里做简化处理

    return {
        "status": "success",
        "scenario": "C",
        "type": "强周期型",
        "data": {
            "股票代码": code,
            "股票名称": data.get('名称'),
            "PB": pb,
            "说明": "完整场景C分析需要库存天数和EV/EBITDA数据",
        }
    }


def classify_stock(code: str) -> dict:
    """股票类型查询

    本工具是数据脚本，不预测股票类型。
    用户应根据公司基本面自行判断后选择场景分析。

    Args:
        code: 股票代码

    Returns:
        {"status": "error", "message": "..."}
    """
    return {
        "status": "error",
        "message": "本工具是数据脚本，不预测股票类型。请根据公司基本面自行判断后选择场景分析："
                 "\n  - scenario-a: 稳定成长型（Forward PE / PEG）"
                 "\n  - scenario-b: 高速成长型（PS + FCF反算）"
                 "\n  - scenario-c: 强周期型（DOI / EV/EBITDA / PB）"
    }


def get_stock_checklist(code: str, stock_type: str = "a") -> dict:
    """个股准入完整检查（附录A流水表）

    Args:
        code: 股票代码
        stock_type: 股票类型（a=稳定成长型, b=高速成长型, c=强周期型）

    Returns:
        完整检查数据
    """
    # 获取分类
    classify_result = classify_stock(code)

    # 获取场景分析
    stock_type = classify_result.get('type', '待分类')

    # 根据用户指定的类型选择场景分析
    if stock_type == "a":
        analysis = analyze_scenario_a(code)
        type_name = "稳定成长型（Forward PE / PEG）"
    elif stock_type == "b":
        analysis = analyze_scenario_b(code)
        type_name = "高速成长型（PS + FCF反算）"
    elif stock_type == "c":
        analysis = analyze_scenario_c(code)
        type_name = "强周期型（DOI / EV/EBITDA / PB）"
    else:
        return {
            "status": "error",
            "message": f"无效的股票类型: {stock_type}，请使用 a/b/c"
        }

    return {
        "status": "success",
        "code": code,
        "stock_type": stock_type,
        "type_name": type_name,
        "analysis": analysis,
    }
