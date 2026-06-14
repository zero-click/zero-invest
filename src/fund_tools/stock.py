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
import numpy as np


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


def get_stock_hist(code: str, days: int = 250) -> dict:
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

        # 新增技术指标（需要足够数据）
        if len(df) >= 14:
            rsi_14 = _calculate_rsi(df['收盘'], 14)
            stats["RSI(14)"] = rsi_14

        if len(df) >= 200:
            # 200日均线
            ma200 = df.tail(200)['收盘'].mean()
            ma200_deviation = (current_price - ma200) / ma200 * 100 if ma200 > 0 else 0
            stats["200日均线"] = ma200
            stats["200日均线乖离率"] = ma200_deviation

        if len(df) >= 252:
            # 52周（约252个交易日）数据
            yearly_data = df.tail(252)
            high_52w = yearly_data['最高'].max()
            low_52w = yearly_data['最低'].min()

            stats["52周最高"] = high_52w
            stats["52周最低"] = low_52w

            # 52周涨幅
            return_52w = (current_price - yearly_data.iloc[0]['收盘']) / yearly_data.iloc[0]['收盘'] * 100
            stats["52周涨幅"] = return_52w

            # 距52周高点距离
            dist_to_high = (current_price - high_52w) / high_52w * 100 if high_52w > 0 else 0
            stats["距52周高点距离"] = dist_to_high

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

        # 获取最新一期数据（akshare返回降序，第一行是最新的）
        latest = df.iloc[0]

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


def _calculate_rsi(prices: pd.Series, period: int = 14) -> Optional[float]:
    """计算RSI指标

    Args:
        prices: 价格序列
        period: RSI周期（默认14）

    Returns:
        RSI值（0-100），计算失败返回None
    """
    try:
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not rsi.empty and pd.notna(rsi.iloc[-1]) else None
    except Exception:
        return None


def get_stock_profit_sheet(code: str) -> dict:
    """获取个股利润表数据（营业收入）

    Args:
        code: 股票代码（如 "000001"）

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        # 转换代码格式
        if code.startswith('6'):
            symbol = f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            symbol = f"{code}.SZ"
        else:
            symbol = code

        df = ak.stock_profit_sheet_by_report_em(symbol=symbol)

        if df.empty:
            return {"status": "error", "message": f"未获取到 {code} 的利润表数据"}

        # 获取最新一期数据（akshare返回降序，第一行是最新的）
        latest = df.iloc[0]

        # 数值单位转换：元 → 亿元
        revenue = latest.get('TOTAL_OPERATE_INCOME')
        cost = latest.get('TOTAL_OPERATE_COST')
        net_profit = latest.get('PARENT_NETPROFIT')
        ebitda = latest.get('OPERATE_PROFIT')

        return {
            "status": "success",
            "data": {
                "报告期": latest.get('REPORT_DATE'),
                "营业收入": revenue / 1e8 if revenue is not None and pd.notna(revenue) else None,
                "营业成本": cost / 1e8 if cost is not None and pd.notna(cost) else None,
                "净利润": net_profit / 1e8 if net_profit is not None and pd.notna(net_profit) else None,
                "EBITDA": ebitda / 1e8 if ebitda is not None and pd.notna(ebitda) else None,  # 注：用营业利润近似EBITDA，未加回折旧摊销，会系统性低估
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"获取利润表失败: {str(e)}"}


def get_stock_cash_flow(code: str) -> dict:
    """获取个股现金流量表数据（自由现金流）

    Args:
        code: 股票代码

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        # 转换代码格式
        if code.startswith('6'):
            symbol = f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            symbol = f"{code}.SZ"
        else:
            symbol = code

        df = ak.stock_cash_flow_sheet_by_report_em(symbol=symbol)

        if df.empty:
            return {"status": "error", "message": f"未获取到 {code} 的现金流量表数据"}

        # 获取最新一期数据（akshare返回降序，第一行是最新的）
        latest = df.iloc[0]

        # 计算自由现金流：经营现金流 - 资本支出
        operating_cf = latest.get('NETCASH_OPERATE', 0)
        capex = latest.get('CONSTRUCT_LONG_ASSET', 0)
        fcf = operating_cf - capex if operating_cf and capex else None

        # 数值单位转换：元 → 亿元
        return {
            "status": "success",
            "data": {
                "报告期": latest.get('REPORT_DATE'),
                "经营活动现金流": operating_cf / 1e8 if pd.notna(operating_cf) else None,
                "资本支出": capex / 1e8 if pd.notna(capex) else None,
                "自由现金流": fcf / 1e8 if pd.notna(fcf) else None,
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"获取现金流量表失败: {str(e)}"}


def get_stock_balance_sheet(code: str) -> dict:
    """获取个股资产负债表数据

    Args:
        code: 股票代码

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        # 转换代码格式
        if code.startswith('6'):
            symbol = f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            symbol = f"{code}.SZ"
        else:
            symbol = code

        df = ak.stock_balance_sheet_by_report_em(symbol=symbol)

        if df.empty:
            return {"status": "error", "message": f"未获取到 {code} 的资产负债表数据"}

        # 获取最新一期数据（akshare返回降序，第一行是最新的）
        latest = df.iloc[0]

        # 数值单位转换：元 → 亿元
        inventory = latest.get('INVENTORY')
        total_debt = latest.get('TOTAL_LIABILITIES')
        cash = latest.get('MONETARYFUNDS')
        total_assets = latest.get('TOTAL_ASSETS')

        return {
            "status": "success",
            "data": {
                "报告期": latest.get('REPORT_DATE'),
                "存货": inventory / 1e8 if inventory is not None and pd.notna(inventory) else None,
                "总负债": total_debt / 1e8 if total_debt is not None and pd.notna(total_debt) else None,
                "货币资金": cash / 1e8 if cash is not None and pd.notna(cash) else None,
                "总资产": total_assets / 1e8 if total_assets is not None and pd.notna(total_assets) else None,
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"获取资产负债表失败: {str(e)}"}


def get_stock_profit_forecast(code: str) -> dict:
    """获取个股盈利预测（分析师一致预期）

    注：该数据源可能不稳定，部分股票无分析师覆盖

    Args:
        code: 股票代码

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        # API用法：不传symbol参数，拉全量数据后按代码过滤
        # symbol参数是行业板块名（如"白酒"），不是股票代码
        df = ak.stock_profit_forecast_em()

        if df is None or df.empty:
            return {"status": "error", "message": "未获取到盈利预测数据（API返回空）"}

        # 按股票代码过滤
        row = df[df['代码'] == code]

        if row.empty:
            return {"status": "error", "message": f"未找到 {code} 的盈利预测数据（该股票可能无分析师覆盖）"}

        # 取第一行（同一代码可能有多年预测）
        latest = row.iloc[0]

        return {
            "status": "success",
            "data": {
                "预测年度": latest.get('预测年度'),
                "预测EPS": latest.get('预测每股收益'),
                "预测净利润": latest.get('预测净利润'),
                "机构数": latest.get('机构数'),
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"获取盈利预测失败: {str(e)}"}


def get_stock_share_change(code: str) -> dict:
    """获取个股股本变动情况（用于计算稀释率）

    Args:
        code: 股票代码

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    try:
        # API需要日期范围参数
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = '20200101'

        df = ak.stock_share_change_cninfo(symbol=code, start_date=start_date, end_date=end_date)

        if df.empty:
            return {"status": "error", "message": f"未获取到 {code} 的股本变动数据"}

        # 获取最新一期股本变动
        latest = df.iloc[-1]

        # 计算稀释率：股本YoY变动百分比（数值）
        current_shares = latest.get('总股本', 0)
        change_reason = latest.get('变动原因', '')
        notice_date = latest.get('公告日期')

        # 尝试计算实际稀释率（需要上期数据）
        dilution_rate = None
        if len(df) >= 2:
            previous_shares = df.iloc[-2].get('总股本', 0)
            if previous_shares and previous_shares > 0:
                dilution_rate = (current_shares - previous_shares) / previous_shares * 100

        return {
            "status": "success",
            "data": {
                "公告日期": str(notice_date) if notice_date else 'N/A',
                "总股本": current_shares,
                "稀释率": dilution_rate,  # 数值百分比，如 -0.2 表示回购缩股0.2%
                "变动原因": change_reason,
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"获取股本变动失败: {str(e)}"}


def get_stock_report_date(code: str) -> dict:
    """获取个股财报披露日期

    注：当前akshare API仅支持按市场批量查询，不支持按单个股票代码查询

    Args:
        code: 股票代码

    Returns:
        {"status": "success", "data": {...}} 或 {"status": "error", "message": "..."}
    """
    # 当前API不支持按股票代码查询，返回提示信息
    return {
        "status": "error",
        "message": "财报披露日期查询暂不支持（akshare API仅支持按市场批量查询）"
    }


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

    # 获取盈利预测
    forecast = get_stock_profit_forecast(code)

    # 获取财务指标（作为fallback）
    financial = get_stock_financial_indicator(code)

    # 计算Forward PE和增速
    current_price = data.get('最新价', 0)
    forecast_eps = None
    growth_rate = None

    if forecast['status'] == 'success':
        forecast_data = forecast.get('data', {})
        forecast_eps = forecast_data.get('预测EPS')
        # 预测净利润增速需要从预测数据计算或使用历史增速
        growth_rate = financial.get('data', {}).get('净利润增速')

    # 如果没有预测EPS，使用TTM PE
    if forecast_eps and forecast_eps > 0:
        forward_pe = current_price / forecast_eps
    else:
        forward_pe = data.get('市盈率', 0)

    # PEG计算
    if forward_pe and growth_rate and growth_rate != 0:
        peg = forward_pe / abs(growth_rate)
    else:
        peg = None

    return {
        "status": "success",
        "scenario": "A",
        "type": "稳定成长型",
        "data": {
            "股票代码": code,
            "股票名称": data.get('名称'),
            "最新价": current_price,
            "Forward PE": forward_pe,
            "预测EPS": forecast_eps,
            "预期增速": growth_rate,
            "PEG": peg,
            "判断": _evaluate_scenario_a(peg, growth_rate),
        }
    }


def _evaluate_scenario_a(peg: Optional[float], growth_rate: Optional[float]) -> str:
    """场景A估值判断（基于PEG）

    PEG = PE / 营收增速
    - PEG < 1: 增速相对估值被低估（可能便宜）
    - PEG 1~2: 估值与增速基本匹配（正常区间）
    - PEG > 2: 估值相对增速较高（市场给予高溢价，需增速持续加速支撑）

    Args:
        peg: PEG 比率
        growth_rate: 营收增速（%）

    Returns:
        估值判断文本
    """
    if peg is None or growth_rate is None:
        return "数据不足，无法判断"

    if peg < 1:
        return "PEG < 1，市场低估了增速（可能便宜）"
    elif peg <= 2:
        return "PEG 1-2，估值与增速基本匹配（正常区间）"
    else:
        return "PEG > 2，估值相对增速较高（高溢价，需增速持续加速支撑）"


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

    # 获取利润表（营收）
    profit_sheet = get_stock_profit_sheet(code)
    revenue = None
    if profit_sheet['status'] == 'success':
        revenue = profit_sheet.get('data', {}).get('营业收入')

    # 获取现金流量表（FCF）
    cash_flow = get_stock_cash_flow(code)
    fcf = None
    if cash_flow['status'] == 'success':
        fcf = cash_flow.get('data', {}).get('自由现金流')

    # 获取股本变动（稀释率）
    share_change = get_stock_share_change(code)
    dilution_rate = None
    if share_change['status'] == 'success':
        dilution_rate = share_change.get('data', {}).get('稀释率')

    # 获取财务指标（毛利率、净利率、营收增速）
    financial = get_stock_financial_indicator(code)
    gross_margin = None
    net_margin = None
    revenue_growth = None
    if financial['status'] == 'success':
        fin_data = financial.get('data', {})
        gross_margin = fin_data.get('毛利率')
        net_margin = fin_data.get('净利率')
        revenue_growth = fin_data.get('营收增速')

    # 计算PS
    market_cap = data.get('总市值', 0)
    ps = None
    if revenue and revenue > 0:
        ps = market_cap / revenue

    # 计算FCF Margin
    fcf_margin = None
    if fcf and revenue and revenue > 0:
        fcf_margin = (fcf / revenue) * 100

    return {
        "status": "success",
        "scenario": "B",
        "type": "高速成长/亏损型",
        "data": {
            "股票代码": code,
            "股票名称": data.get('名称'),
            "最新价": data.get('最新价'),
            "总市值": market_cap,
            "PS": ps,
            "营收": revenue,
            "营收增速": revenue_growth,
            "毛利率": gross_margin,
            "净利率": net_margin,
            "自由现金流": fcf,
            "FCF Margin": fcf_margin,
            "稀释率": dilution_rate,
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

    # 获取资产负债表
    balance_sheet = get_stock_balance_sheet(code)
    inventory = None
    total_debt = None
    cash = None
    if balance_sheet['status'] == 'success':
        bs_data = balance_sheet.get('data', {})
        inventory = bs_data.get('存货')
        total_debt = bs_data.get('总负债')
        cash = bs_data.get('货币资金')

    # 获取利润表（营业成本、EBITDA）
    profit_sheet = get_stock_profit_sheet(code)
    cogs = None
    ebitda = None
    if profit_sheet['status'] == 'success':
        ps_data = profit_sheet.get('data', {})
        cogs = ps_data.get('营业成本')
        ebitda = ps_data.get('EBITDA')

    # 计算DOI（库存周转天数）
    doi = None
    if cogs and cogs > 0 and inventory is not None:
        doi = (inventory / cogs) * 365

    # 计算EV（企业价值）
    market_cap = data.get('总市值', 0)
    ev = None
    if total_debt is not None and cash is not None:
        ev = market_cap + total_debt - cash

    # 计算EV/EBITDA
    ev_ebitda = None
    if ev and ebitda and ebitda > 0:
        ev_ebitda = ev / ebitda

    pb = data.get('市净率', 0)

    return {
        "status": "success",
        "scenario": "C",
        "type": "强周期型",
        "data": {
            "股票代码": code,
            "股票名称": data.get('名称'),
            "最新价": data.get('最新价'),
            "PB": pb,
            "存货": inventory,
            "营业成本": cogs,
            "DOI": doi,
            "总负债": total_debt,
            "货币资金": cash,
            "企业价值EV": ev,
            "EBITDA": ebitda,
            "EV/EBITDA": ev_ebitda,
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
