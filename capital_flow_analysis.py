# -*- coding: utf-8 -*-
"""
北向/南向资金流 + 大盘主力资金流分析模块

数据源 (akshare -> 东方财富):
  - stock_hsgt_hold_stock_em(market='北向')  北向持股明细（含行业字段）
  - stock_hsgt_hold_stock_em(market='南向')  南向持股明细
  - stock_hsgt_hist_em(symbol='沪股通/深股通')  日度历史资金流入
  - stock_hsgt_fund_flow_summary_em()  当日南北向汇总
  - stock_market_fund_flow()  大盘主力/散户资金流（每日更新，120天历史）

功能:
  1. 行业维度聚合：北向/南向资金按行业分布
  2. 个股排行：增持/减持 Top N
  3. 历史资金流：沪股通/深股通近期趋势
  4. 当日汇总：南北向资金净流入概览
  5. 大盘主力资金流：主力/超大单/大单/中单/小单净流入趋势
  6. 综合分析报告
"""

import os
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import akshare as ak
import pandas as pd

warnings.filterwarnings("ignore")

# 移除代理环境变量（akshare 需要直连）
for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(k, None)


# ============================================================
# 行业映射 & 配置
# ============================================================

# 东方财富"所属板块" -> 大类行业映射（更细粒度）
INDUSTRY_ALIAS = {
    # 科技 / 电子
    "半导体": "科技",
    "消费电子": "科技",
    "电子元件": "科技",
    "电子化学品": "科技",
    "光学光电子": "科技",
    "计算机设备": "科技",
    "软件开发": "科技",
    "互联网服务": "科技",
    "通信设备": "科技",
    "通信服务": "科技",
    # 新能源 / 电力
    "光伏设备": "新能源",
    "电池": "新能源",
    "电源设备": "新能源",
    "电网设备": "新能源",
    "风电设备": "新能源",
    "电力行业": "公用事业",
    "公用事业": "公用事业",
    "燃气": "公用事业",
    # 有色 / 资源
    "有色金属": "有色",
    "小金属": "有色",
    "能源金属": "有色",
    "贵金属": "有色",
    "煤炭行业": "煤炭",
    "石油行业": "石油",
    "采掘行业": "资源",
    "钢铁行业": "钢铁",
    "化纤行业": "化工",
    "化学制品": "化工",
    "化学原料": "化工",
    "化肥行业": "化工",
    "非金属材料": "化工",
    # 制造 / 机械
    "专用设备": "机械",
    "通用设备": "机械",
    "工程机械": "机械",
    "电机": "机械",
    "交运设备": "机械",
    "仪器仪表": "机械",
    "工程建设": "建筑",
    "工程咨询服务": "建筑",
    "水泥建材": "建材",
    "装修建材": "建材",
    "玻璃玻纤": "建材",
    # 消费 / 食品
    "食品饮料": "消费",
    "酿酒行业": "消费",
    "家电行业": "家电",
    "家用轻工": "家电",
    "美容护理": "消费",
    "纺织服装": "消费",
    "珠宝首饰": "消费",
    "包装材料": "消费",
    "塑料制品": "消费",
    "橡胶制品": "消费",
    "造纸印刷": "消费",
    # 医药
    "化学制药": "医药",
    "生物制品": "医药",
    "医疗器械": "医药",
    "医疗服务": "医药",
    "医药商业": "医药",
    "中药": "医药",
    # 金融
    "银行": "银行",
    "证券": "证券",
    "保险": "保险",
    "多元金融": "金融",
    # 汽车
    "汽车整车": "汽车",
    "汽车零部件": "汽车",
    "汽车服务": "汽车",
    # 军工 / 航天
    "航天航空": "军工",
    "船舶制造": "军工",
    # 地产
    "房地产开发": "地产",
    "房地产服务": "地产",
    # 物流 / 交运
    "物流行业": "物流",
    "航空机场": "物流",
    "航运港口": "物流",
    "铁路公路": "物流",
    # 传媒 / 文娱
    "文化传媒": "传媒",
    "游戏": "传媒",
    "教育": "教育",
    "旅游酒店": "消费",
    # 商业 / 贸易
    "商业百货": "商贸",
    "贸易行业": "商贸",
    "专业服务": "服务",
    # 环保 / 农业
    "环保行业": "环保",
    "农牧饲渔": "农业",
    "农药兽药": "农业",
    # 综合
    "综合行业": "综合",
    # 兼容旧格式（申万一级行业名）
    "电子": "科技",
    "电力设备": "新能源",
    "食品饮料": "消费",
    "医药生物": "医药",
    "计算机": "科技",
    "非银金融": "金融",
    "有色金属": "有色",
    "基础化工": "化工",
    "机械设备": "机械",
    "汽车": "汽车",
    "家用电器": "家电",
    "房地产": "地产",
    "国防军工": "军工",
    "传媒": "传媒",
    "交通运输": "物流",
    "建筑装饰": "建筑",
    "社会服务": "服务",
    "农林牧渔": "农业",
    "商贸零售": "商贸",
    "轻工制造": "消费",
    "建筑材料": "建材",
}

# 沪股通 / 深股通 symbol 映射
HSGT_SYMBOLS = {
    "沪股通": "沪股通",
    "深股通": "深股通",
}


# ============================================================
# 核心数据获取函数
# ============================================================

def get_northbound_holdings() -> List[Dict]:
    """
    获取北向持股明细（含行业字段），返回标准化的 dict 列表

    Returns:
        List[Dict]: 每个元素包含 code, name, industry, hold_amount, ratio 等
    """
    try:
        df = ak.stock_hsgt_hold_stock_em(market="北向")
        if df is None or df.empty:
            print("北向持股数据为空")
            return []

        # 标准化列名
        df = _normalize_holdings_df(df, direction="北向")

        print(f"北向持股获取成功: {len(df)} 只个股")
        return df.to_dict("records")

    except Exception as e:
        print(f"获取北向持股失败: {e}")
        return []


def get_southbound_holdings() -> List[Dict]:
    """
    获取南向持股明细，返回标准化的 dict 列表
    """
    try:
        df = ak.stock_hsgt_hold_stock_em(market="南向")
        if df is None or df.empty:
            print("南向持股数据为空")
            return []

        df = _normalize_holdings_df(df, direction="南向")

        print(f"南向持股获取成功: {len(df)} 只个股")
        return df.to_dict("records")

    except Exception as e:
        print(f"获取南向持股失败: {e}")
        return []


def get_historical_flow(symbol: str = "沪股通", days: int = 30) -> List[Dict]:
    """
    获取沪股通/深股通日度历史资金流入

    Args:
        symbol: "沪股通" 或 "深股通"
        days: 返回最近 N 天的数据

    Returns:
        List[Dict]: 每日资金流入数据
    """
    if symbol not in HSGT_SYMBOLS:
        return []

    try:
        df = ak.stock_hsgt_hist_em(symbol=symbol)
        if df is None or df.empty:
            return []

        # 只取最近 days 天
        df = df.tail(days)

        # 标准化
        result = []
        for _, row in df.iterrows():
            # 优先用 当日成交净买额，其次 当日资金流入
            net_buy = row.get("当日成交净买额")
            if net_buy is None or pd.isna(net_buy):
                net_buy = row.get("当日资金流入")

            hist_buy = row.get("历史累计净买额")
            balance = row.get("当日余额")

            result.append({
                "日期": _safe_str(row.get("日期")),
                "当日净买入": _safe_float(net_buy),
                "当日余额": _safe_float(balance),
                "历史净买入": _safe_float(hist_buy),
                "数据源": symbol,
            })

        return result

    except Exception as e:
        print(f"获取{symbol}历史资金流失败: {e}")
        return []


def get_fund_flow_summary() -> Dict:
    """
    获取当日南北向资金净流入汇总

    Returns:
        Dict with 北向/南向 各通道的当日净流入
    """
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df is None or df.empty:
            return {"success": False, "message": "汇总数据为空"}

        records = df.to_dict("records")
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": records,
        }

    except Exception as e:
        return {"success": False, "message": f"获取资金流汇总失败: {e}"}


# ============================================================
# 分析函数
# ============================================================

def get_industry_aggregation(direction: str = "北向") -> Dict:
    """
    按行业聚合持股数据

    Args:
        direction: "北向" 或 "南向"

    Returns:
        Dict with industry distribution data
    """
    if direction == "北向":
        holdings = get_northbound_holdings()
    else:
        holdings = get_southbound_holdings()

    if not holdings:
        return {
            "success": False,
            "direction": direction,
            "message": f"{direction}持股数据获取失败",
        }

    df = pd.DataFrame(holdings)

    # 按行业聚合
    if "行业" not in df.columns:
        return {
            "success": False,
            "direction": direction,
            "message": "数据中缺少行业字段",
        }

    agg = (
        df.groupby("行业")
        .agg(
            持股数量=("持股数量", "sum"),
            持股市值=("持股市值", "sum"),
            个股数=("代码", "count"),
        )
        .reset_index()
    )

    # 排序按持股市值降序
    agg = agg.sort_values("持股市值", ascending=False)

    # 计算占比
    total_value = agg["持股市值"].sum()
    if total_value > 0:
        agg["市值占比(%)"] = (agg["持股市值"] / total_value * 100).round(2)
    else:
        agg["市值占比(%)"] = 0.0

    # 转换为记录
    industries = agg.to_dict("records")

    return {
        "success": True,
        "direction": direction,
        "timestamp": datetime.now().isoformat(),
        "total_industries": len(industries),
        "total_stocks": len(df),
        "total_market_value": round(total_value, 2),
        "industries": industries,
    }


def get_top_holdings(
    direction: str = "北向",
    metric: str = "持股市值",
    top_n: int = 20,
) -> Dict:
    """
    获取增持/减持 Top N 个股

    Args:
        direction: "北向" 或 "南向"
        metric: 排序字段，默认 "持股市值"
        top_n: 返回前 N 个

    Returns:
        Dict with top holdings
    """
    if direction == "北向":
        holdings = get_northbound_holdings()
    else:
        holdings = get_southbound_holdings()

    if not holdings:
        return {"success": False, "message": f"{direction}持股数据获取失败"}

    df = pd.DataFrame(holdings)

    if metric not in df.columns:
        # 尝试替代排序
        metric = "持股市值"

    df = df.sort_values(metric, ascending=False)

    return {
        "success": True,
        "direction": direction,
        "metric": metric,
        "top_n": top_n,
        "timestamp": datetime.now().isoformat(),
        "data": df.head(top_n).to_dict("records"),
    }


def get_capital_flow_report() -> Dict:
    """
    综合资金流分析报告

    Returns:
        Dict with complete analysis
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "northbound": {},
        "southbound": {},
        "flow_history": {},
        "summary": {},
    }

    # 1. 北向行业分布
    print(">>> 获取北向行业分布...")
    report["northbound"] = get_industry_aggregation("北向")

    # 2. 南向行业分布
    print(">>> 获取南向行业分布...")
    report["southbound"] = get_industry_aggregation("南向")

    # 3. 沪股通历史资金流（近30天）
    print(">>> 获取沪股通历史资金流...")
    report["flow_history"]["沪股通"] = get_historical_flow("沪股通", days=30)

    # 4. 深股通历史资金流（近30天）
    print(">>> 获取深股通历史资金流...")
    report["flow_history"]["深股通"] = get_historical_flow("深股通", days=30)

    # 5. 当日汇总
    print(">>> 获取当日资金流汇总...")
    report["summary"] = get_fund_flow_summary()

    return report


def format_industry_report(agg: Dict) -> str:
    """
    格式化行业分布报告（CLI 输出）
    """
    if not agg.get("success"):
        return f"❌ {agg.get('direction', '')}行业数据不可用: {agg.get('message', '')}"

    direction = agg["direction"]
    industries = agg["industries"]

    lines = []
    lines.append("=" * 90)
    lines.append(f"{direction}资金行业分布 | {agg.get('timestamp', '')[:10]}")
    lines.append("=" * 90)
    lines.append(
        f"{'行业':<12} {'个股数':>6} {'持股市值(亿)':>14} {'占比':>8}"
    )
    lines.append("-" * 90)

    for item in industries[:20]:
        name = item["行业"]
        count = item["个股数"]
        value = item["持股市值"]
        pct = item["市值占比(%)"]

        # 市值转换为亿
        value_yi = value / 1e8 if value > 1e8 else value / 1e4

        lines.append(
            f"{name:<12} {count:>6} {value_yi:>14.2f} {pct:>7.2f}%"
        )

    lines.append("=" * 90)
    lines.append(
        f"共 {agg['total_industries']} 个行业 | {agg['total_stocks']} 只个股"
    )

    return "\n".join(lines)


def format_flow_history(flow_data: List[Dict], symbol: str = "") -> str:
    """
    格式化历史资金流（CLI 输出）
    """
    if not flow_data:
        return f"❌ {symbol}历史资金流数据不可用"

    lines = []
    lines.append(f"\n{'=' * 70}")
    lines.append(f"{symbol} 近 {len(flow_data)} 日资金流")
    lines.append("=" * 70)
    lines.append(f"{'日期':<14} {'当日净买入(亿)':>16} {'累计(亿)':>16}")
    lines.append("-" * 70)

    for item in flow_data[-10:]:  # 显示最近10天
        date = str(item.get("日期", ""))[:10]
        net_raw = item.get("当日净买入")
        hist_raw = item.get("历史净买入")
        net = (net_raw / 1e8) if net_raw is not None else 0.0
        hist = (hist_raw / 1e8) if hist_raw is not None else 0.0
        lines.append(f"{date:<14} {net:>16.2f} {hist:>16.2f}")

    lines.append("=" * 70)

    return "\n".join(lines)


# ============================================================
# 内部工具函数
# ============================================================

def _normalize_holdings_df(df: pd.DataFrame, direction: str) -> pd.DataFrame:
    """
    标准化持股明细 DataFrame 列名和数据类型

    东方财富返回的典型列名 (2024+):
      序号, 代码, 名称, 今日收盘价, 今日涨跌幅,
      今日持股-股数, 今日持股-市值, 今日持股-占流通股比, 今日持股-占总股本比,
      5日增持估计-股数, 5日增持估计-市值, 5日增持估计-市值增幅,
      5日增持估计-占流通股比, 5日增持估计-占总股本比,
      所属板块, 日期
    """
    # 列名映射 -> 标准名
    col_map = {}
    for col in df.columns:
        cl = col.strip()
        if cl == "股票代码" or cl == "代码":
            col_map[col] = "代码"
        elif cl == "股票简称" or cl == "名称":
            col_map[col] = "名称"
        elif cl == "今日收盘价" or "收盘价" in cl:
            col_map[col] = "收盘价"
        elif cl == "今日涨跌幅" or cl == "涨跌幅":
            col_map[col] = "涨跌幅"
        elif cl in ("今日持股-股数", "持股数量"):
            col_map[col] = "持股数量"
        elif cl in ("今日持股-市值", "持股市值"):
            col_map[col] = "持股市值"
        elif cl in ("今日持股-占流通股比",):
            col_map[col] = "占流通股比"
        elif cl in ("今日持股-占总股本比",):
            col_map[col] = "占总股本比"
        elif cl in ("5日增持估计-股数", "持股数量变化"):
            col_map[col] = "5日增持股数"
        elif cl in ("5日增持估计-市值", "持股市值变化"):
            col_map[col] = "5日增持市值"
        elif cl in ("5日增持估计-市值增幅",):
            col_map[col] = "5日增幅"
        elif cl in ("所属板块", "行业"):
            col_map[col] = "行业"

    df = df.rename(columns=col_map)

    # 确保行业字段存在
    if "行业" not in df.columns:
        df["行业"] = "未知"

    # 行业名称标准化
    df["行业"] = df["行业"].apply(
        lambda x: INDUSTRY_ALIAS.get(str(x).strip(), str(x).strip())
    )

    # 数值字段转 float
    for field in [
        "持股数量", "持股市值", "涨跌幅", "收盘价",
        "占流通股比", "占总股本比",
        "5日增持股数", "5日增持市值", "5日增幅",
    ]:
        if field in df.columns:
            df[field] = pd.to_numeric(df[field], errors="coerce").fillna(0)

    # 添加方向标记
    df["方向"] = direction

    return df


def _safe_float(val) -> Optional[float]:
    """安全转 float"""
    try:
        if pd.isna(val):
            return None
        return float(val)
    except (TypeError, ValueError):
        return None


def _safe_str(val) -> str:
    """安全转 str"""
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        if hasattr(val, "strftime"):
            return val.strftime("%Y-%m-%d")
        return str(val)
    except Exception:
        return ""


# ============================================================
# 大盘主力资金流（stock_market_fund_flow）
# ============================================================

def get_market_fund_flow(days: int = 30) -> Dict:
    """
    获取大盘主力资金流数据（含主力/超大单/大单/中单/小单净流入）

    数据源: akshare stock_market_fund_flow() -> 东方财富
    默认返回约120天数据，此函数取最近 N 天。

    Args:
        days: 返回最近 N 天的数据（默认30天）

    Returns:
        Dict with:
          - success: bool
          - data: List[Dict] 每日资金流明细
          - summary: 最近5日汇总 + 趋势判断
    """
    try:
        df = ak.stock_market_fund_flow()
        if df is None or df.empty:
            return {"success": False, "message": "大盘资金流数据为空"}

        df = df.tail(days)

        records = []
        for _, row in df.iterrows():
            records.append({
                "日期": _safe_str(row.get("日期")),
                "上证收盘": _safe_float(row.get("上证-收盘价")),
                "上证涨跌幅": _safe_float(row.get("上证-涨跌幅")),
                "深证收盘": _safe_float(row.get("深证-收盘价")),
                "深证涨跌幅": _safe_float(row.get("深证-涨跌幅")),
                "主力净流入": _safe_float(row.get("主力净流入-净额")),
                "主力净占比": _safe_float(row.get("主力净流入-净占比")),
                "超大单净流入": _safe_float(row.get("超大单净流入-净额")),
                "超大单净占比": _safe_float(row.get("超大单净流入-净占比")),
                "大单净流入": _safe_float(row.get("大单净流入-净额")),
                "大单净占比": _safe_float(row.get("大单净流入-净占比")),
                "中单净流入": _safe_float(row.get("中单净流入-净额")),
                "中单净占比": _safe_float(row.get("中单净流入-净占比")),
                "小单净流入": _safe_float(row.get("小单净流入-净额")),
                "小单净占比": _safe_float(row.get("小单净流入-净占比")),
            })

        # 最近5日趋势判断
        summary = _analyze_fund_flow_trend(records[-5:] if len(records) >= 5 else records)

        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "days": len(records),
            "data": records,
            "summary": summary,
        }

    except Exception as e:
        print(f"获取大盘资金流失败: {e}")
        return {"success": False, "message": f"获取大盘资金流失败: {e}"}


def _analyze_fund_flow_trend(records: List[Dict]) -> Dict:
    """
    分析最近N日资金流趋势

    Returns:
        Dict with trend analysis:
          - recent_days: 最近几日汇总
          - main_force_trend: 主力趋势判断（连续流入/流出/震荡）
          - signal: 操作信号（偏多/偏空/中性）
    """
    if not records:
        return {"main_force_trend": "无数据", "signal": "中性"}

    # 统计主力净流入连续方向
    main_flows = [r.get("主力净流入", 0) or 0 for r in records]
    super_large_flows = [r.get("超大单净流入", 0) or 0 for r in records]

    # 连续流入/流出天数
    consecutive_in = 0
    consecutive_out = 0
    for f in reversed(main_flows):
        if f > 0:
            consecutive_in += 1
        else:
            break
    for f in reversed(main_flows):
        if f < 0:
            consecutive_out += 1
        else:
            break

    # 主力净流入合计
    main_total = sum(main_flows)
    super_total = sum(super_large_flows)

    # 趋势判断
    if consecutive_in >= 3:
        trend = f"连续{consecutive_in}日净流入"
        signal = "偏多"
    elif consecutive_out >= 3:
        trend = f"连续{consecutive_out}日净流出"
        signal = "偏空"
    elif main_total > 0:
        trend = "震荡偏多"
        signal = "中性偏多"
    else:
        trend = "震荡偏空"
        signal = "中性偏空"

    # 主力 vs 散户方向
    small_flows = [r.get("小单净流入", 0) or 0 for r in records]
    small_total = sum(small_flows)

    divergence = ""
    if main_total > 0 and small_total < 0:
        divergence = "主力吸筹、散户出逃"
    elif main_total < 0 and small_total > 0:
        divergence = "主力出货、散户接盘"
    elif main_total > 0 and small_total > 0:
        divergence = "资金共振流入"
    else:
        divergence = "资金共振流出"

    return {
        "recent_days": len(records),
        "主力净流入合计(亿)": round(main_total / 1e8, 2),
        "超大单净流入合计(亿)": round(super_total / 1e8, 2),
        "小单净流入合计(亿)": round(small_total / 1e8, 2),
        "main_force_trend": trend,
        "divergence": divergence,
        "signal": signal,
    }


def format_market_fund_flow(result: Dict, show_days: int = 10) -> str:
    """
    格式化大盘主力资金流报告（CLI 输出）

    Args:
        result: get_market_fund_flow() 的返回值
        show_days: 显示最近几天明细（默认10天）
    """
    if not result.get("success"):
        return f"❌ 大盘资金流数据不可用: {result.get('message', '')}"

    data = result["data"]
    summary = result.get("summary", {})

    lines = []
    lines.append("=" * 100)
    lines.append(f"大盘主力资金流 | {result.get('timestamp', '')[:10]} | 共{len(data)}日")
    lines.append("=" * 100)

    # 趋势摘要
    if summary:
        lines.append(f"")
        lines.append(f"  📊 近{summary.get('recent_days', 0)}日趋势:")
        lines.append(f"     主力净流入合计: {summary.get('主力净流入合计(亿)', 0):>10.2f} 亿")
        lines.append(f"     超大单净流入:   {summary.get('超大单净流入合计(亿)', 0):>10.2f} 亿")
        lines.append(f"     小单净流入合计: {summary.get('小单净流入合计(亿)', 0):>10.2f} 亿")
        lines.append(f"     趋势: {summary.get('main_force_trend', '-')}")
        lines.append(f"     博弈: {summary.get('divergence', '-')}")
        signal = summary.get("signal", "中性")
        icon = "🟢" if "多" in signal else "🔴" if "空" in signal else "🟡"
        lines.append(f"     信号: {icon} {signal}")

    # 明细表格
    lines.append("")
    lines.append(
        f"  {'日期':<12} {'上证%':>6} {'主力净流入(亿)':>14} {'超大单(亿)':>12} "
        f"{'大单(亿)':>12} {'中单(亿)':>12} {'小单(亿)':>12}"
    )
    lines.append("  " + "-" * 96)

    for item in data[-show_days:]:
        date = str(item.get("日期", ""))[:10]
        sh_pct = item.get("上证涨跌幅", 0) or 0
        main_net = (item.get("主力净流入", 0) or 0) / 1e8
        super_net = (item.get("超大单净流入", 0) or 0) / 1e8
        big_net = (item.get("大单净流入", 0) or 0) / 1e8
        mid_net = (item.get("中单净流入", 0) or 0) / 1e8
        small_net = (item.get("小单净流入", 0) or 0) / 1e8

        lines.append(
            f"  {date:<12} {sh_pct:>+6.2f} {main_net:>+14.2f} {super_net:>+12.2f} "
            f"{big_net:>+12.2f} {mid_net:>+12.2f} {small_net:>+12.2f}"
        )

    lines.append("=" * 100)

    return "\n".join(lines)


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    print("🚀 资金流分析报告\n")

    # 北向行业分布
    nb = get_industry_aggregation("北向")
    print(format_industry_report(nb))

    # 南向行业分布
    sb = get_industry_aggregation("南向")
    print(format_industry_report(sb))

    # 沪股通历史
    flow = get_historical_flow("沪股通", days=30)
    print(format_flow_history(flow, "沪股通"))

    # 深股通历史
    flow2 = get_historical_flow("深股通", days=30)
    print(format_flow_history(flow2, "深股通"))

    # 当日汇总
    summary = get_fund_flow_summary()
    if summary.get("success"):
        print("\n📊 当日资金流汇总:")
        for item in summary.get("data", []):
            print(f"  {item}")

    # 大盘主力资金流
    print("\n")
    mff = get_market_fund_flow(days=30)
    print(format_market_fund_flow(mff, show_days=10))
