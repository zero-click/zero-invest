# -*- coding: utf-8 -*-
"""
指数数据获取模块

功能:
  1. 从中证指数官网获取所有A股指数列表
  2. 指数分类（宽基/行业/主题/策略/风格）
  3. 提供搜索和查询功能
  4. 获取指数详情（当前值、业绩、PE/PB、分位）

数据源:
  - 中证指数官网: 指数列表 + 历史行情 + 滚动PE
  - 乐咕乐股: PE/PB历史分位（宽基指数）
"""

import os
import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# 估值温度等级
VALUATION_LEVELS = {
    (0, 10): "极度低估 🥶",
    (10, 20): "低估 🟢",
    (20, 40): "偏低 🟡",
    (40, 60): "合理 🟠",
    (60, 70): "合理偏上 🟠",
    (70, 85): "偏高 🔴",
    (85, 95): "高估 🔥",
    (95, 101): "极度高估 🚨",
}

# 乐咕乐股支持的宽基指数（用于获取PE/PB历史分位）
LG_INDEX_MAP = {
    "上证50": "上证50",
    "沪深300": "沪深300",
    "中证500": "中证500",
    "中证800": "中证800",
    "中证100": "中证100",
    "中证1000": "中证1000",
    "上证180": "上证180",
    "上证380": "上证380",
    "创业板50": "创业板50",
    "深证红利": "深证红利",
    "深证100": "深证100",
    "上证红利": "上证红利",
}

LG_INDEX_CODE_MAP = {
    "000016": "上证50",
    "000300": "沪深300",
    "000905": "中证500",
    "000906": "中证800",
    "000903": "中证100",
    "000852": "中证1000",
    "000010": "上证180",
    "000009": "上证380",
    "399673": "创业板50",
    "399330": "深证100",
    "000015": "上证红利",
    "000922": "中证红利",
}


def _clear_proxy_env() -> None:
    """移除代理环境变量，避免访问国内数据源时被本地代理干扰。"""
    for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
        os.environ.pop(key, None)

# 全局函数： 搜索指数
def search_indices_all(keyword: str) -> List[Dict]:
    """
    搜索指数（按名称或代码）

    Args:
        keyword: 搜索关键词

    Returns:
        匹配的指数列表
    """
    all_indices = get_all_stock_indices()

    results = []
    for idx in all_indices:
        if (keyword in idx["name"]) or (keyword in idx["code"]):
            results.append(idx)
    return results


def _is_non_retryable_history_error(exc: Exception) -> bool:
    """判断指数历史行情错误是否属于不值得重试的确定性失败。"""
    message = str(exc)
    markers = [
        "Length mismatch",
        "Expected axis has 0 elements",
        "Columns must be same length as key",
        "DataFrame is empty",
        "empty data",
        "'date'",  # sina 数据源不支持的指数会抛出 KeyError('date')
    ]
    return any(marker in message for marker in markers)


def _fetch_history_with_retry(fetcher, source_name: str, retries: int = 2) -> Optional[pd.DataFrame]:
    """带重试地获取指数历史行情。"""
    last_error = None
    attempts_made = 0
    for attempt in range(1, retries + 1):
        attempts_made = attempt
        try:
            _clear_proxy_env()
            df = fetcher()
            if df is not None and not df.empty:
                return df
        except Exception as e:
            last_error = e
            logger.debug(f"获取指数历史行情失败 [{source_name}] 第{attempt}/{retries}次: {e}")
            if _is_non_retryable_history_error(e):
                logger.debug(f"获取指数历史行情失败 [{source_name}]，判定为不可重试，直接切换数据源")
                break
        time.sleep(0.2)

    return None


def _get_history_symbol_candidates(code: str) -> List[str]:
    """为不同历史行情源构造候选 symbol。"""
    code = str(code).strip()
    if not code:
        return []

    if code.startswith("399"):
        prefixes = ["sz", "sh", "csi"]
    elif code.startswith(("930", "931", "932")):
        prefixes = ["csi", "sh", "sz"]
    else:
        prefixes = ["sh", "sz", "csi"]

    return [f"{prefix}{code}" for prefix in prefixes]


def _normalize_history_frame(df: pd.DataFrame, source_name: str) -> Optional[pd.DataFrame]:
    """将不同来源的历史行情统一为当前项目使用的列结构。"""
    if df is None or df.empty:
        return None

    normalized = df.copy()

    if "date" in normalized.columns:
        rename_map = {
            "date": "日期",
            "open": "开盘",
            "close": "收盘",
            "high": "最高",
            "low": "最低",
            "volume": "成交量",
            "amount": "成交额",
        }
        normalized = normalized.rename(columns=rename_map)

    required_columns = {"日期", "收盘"}
    if not required_columns.issubset(normalized.columns):
        logger.warning(f"历史行情标准化失败 [{source_name}]：缺少必要列 {required_columns - set(normalized.columns)}")
        return None

    normalized["日期"] = pd.to_datetime(normalized["日期"], errors="coerce")

    for col in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "涨跌幅", "涨跌", "换手率", "滚动市盈率"]:
        if col in normalized.columns:
            normalized[col] = pd.to_numeric(normalized[col], errors="coerce")

    if "涨跌幅" not in normalized.columns:
        if "开盘" in normalized.columns:
            normalized["涨跌幅"] = ((normalized["收盘"] - normalized["开盘"]) / normalized["开盘"]) * 100
        else:
            normalized["涨跌幅"] = normalized["收盘"].pct_change() * 100

    normalized = normalized.dropna(subset=["日期", "收盘"]).sort_values("日期").reset_index(drop=True)
    if normalized.empty:
        return None
    return normalized


def get_index_returns(
    df_hist: pd.DataFrame,
    current_price: Optional[float] = None,
) -> Dict[str, Optional[float]]:
    """
    根据历史行情计算常用区间收益率。

    Args:
        df_hist: 标准化后的指数历史行情
        current_price: 可选当前价格；未传时使用最后一个收盘价

    Returns:
        各时间段收益率字典
    """
    if df_hist is None or df_hist.empty:
        return {}

    if current_price is None:
        current_price = float(df_hist.iloc[-1]["收盘"])

    returns = {}
    periods = {
        "1周": 5,
        "1月": 21,
        "3月": 63,
        "6月": 126,
        "1年": 252,
        "3年": 756,
    }

    for period_name, days in periods.items():
        if len(df_hist) > days:
            past_price = float(df_hist.iloc[-days]["收盘"])
            ret = (current_price - past_price) / past_price * 100
            returns[f"{period_name}_收益率"] = round(ret, 2)
        else:
            returns[f"{period_name}_收益率"] = None

    try:
        year_start = datetime.now().replace(month=1, day=1)
        df_year = df_hist[df_hist["日期"] >= year_start]
        if len(df_year) > 0:
            year_start_price = float(df_year.iloc[0]["收盘"])
            ytd_ret = (current_price - year_start_price) / year_start_price * 100
            returns["今年收益率"] = round(ytd_ret, 2)
        else:
            returns["今年收益率"] = None
    except Exception:
        returns["今年收益率"] = None

    return returns


def _filter_history_window(
    df_hist: Optional[pd.DataFrame],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """按时间窗口裁剪历史行情。"""
    if df_hist is None or df_hist.empty or "日期" not in df_hist.columns:
        return df_hist

    filtered = df_hist.copy()
    filtered["日期"] = pd.to_datetime(filtered["日期"], errors="coerce")

    if start_date:
        start_ts = pd.to_datetime(start_date, format="%Y%m%d", errors="coerce")
        filtered = filtered[filtered["日期"] >= start_ts]
    if end_date:
        end_ts = pd.to_datetime(end_date, format="%Y%m%d", errors="coerce")
        filtered = filtered[filtered["日期"] <= end_ts]

    return filtered.sort_values("日期").reset_index(drop=True)


def get_index_query_window(end_date: Optional[str] = None) -> tuple[str, str]:
    """
    获取指数 query 场景的历史窗口。

    query 目前只展示到 3 年收益率，因此抓取 4 个自然年作为缓冲，
    既能覆盖 3 年收益率，也能覆盖年初至今收益率。

    Args:
        end_date: 结束日期，格式 YYYYMMDD，默认为当前日期

    Returns:
        (start_date, end_date) 元组，格式为 YYYYMMDD
    """
    end_dt = pd.to_datetime(end_date, format="%Y%m%d") if end_date else datetime.now()
    start_dt = end_dt - timedelta(days=365 * 4)
    return start_dt.strftime("%Y%m%d"), end_dt.strftime("%Y%m%d")


def _get_index_query_window(end_date: Optional[str] = None) -> tuple[str, str]:
    """内部兼容函数"""
    return get_index_query_window(end_date)


def get_csrc_industry_pe_snapshot(lookback_days: int = 30) -> List[Dict[str, Any]]:
    """
    获取最近可用的证监会行业 PE 快照

    Args:
        lookback_days: 向前回溯天数，默认 30 天

    Returns:
        行业估值快照列表
    """
    for days_back in range(max(1, lookback_days)):
        target_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%d")
        try:
            df = ak.stock_industry_pe_ratio_cninfo(
                symbol="证监会行业分类",
                date=target_date,
            )
        except Exception as e:
            logger.debug(f"获取证监会行业 PE 失败 ({target_date}): {e}")
            continue

        if df is None or df.empty:
            continue

        results: List[Dict[str, Any]] = []
        snapshot_date = str(df.iloc[0].get("变动日期", target_date))
        for _, row in df.iterrows():
            industry_name = str(row.get("行业名称", "")).strip()
            if not industry_name or industry_name == "中国上市公司协会上市公司行业分类标准":
                continue

            pe_weighted = pd.to_numeric(row.get("静态市盈率-加权平均"), errors="coerce")
            pe_median = pd.to_numeric(row.get("静态市盈率-中位数"), errors="coerce")
            pe_value = pe_weighted if pd.notna(pe_weighted) else pe_median
            if pd.isna(pe_value):
                continue

            results.append(
                {
                    "行业名称": industry_name,
                    "日期": snapshot_date,
                    "静态PE": round(float(pe_value), 2),
                    "静态PE_中位数": round(float(pe_median), 2) if pd.notna(pe_median) else None,
                    "静态PE_加权平均": round(float(pe_weighted), 2) if pd.notna(pe_weighted) else None,
                    "数据源": "证监会行业",
                }
            )

        if results:
            return results

    return []

def _classify_index(index_class: str, asset_class: str) -> str:
    """
    根据指数类别和资产类别分类

    Args:
        index_class: 指数类别（规模/行业/主题/策略/风格）
        asset_class: 资产类别（股票/固定收益/多资产）

    Returns:
        "broad" | "industry" | "sector" | "strategy" | "style"
    """
    # 只处理股票指数
    if asset_class != "股票":
        return None

    category_map = {
        "规模": "broad",
        "行业": "industry",
        "主题": "sector",
        "策略": "strategy",
        "风格": "style",
    }

    return category_map.get(index_class, None)


def fetch_indices_from_csindex() -> Dict[str, List[Dict]]:
    """
    从中证指数官网获取所有指数列表

    Returns:
        {
            "broad": [...],      # 宽基指数（规模）
            "industry": [...],   # 行业指数
            "sector": [...],     # 主题指数
            "strategy": [...],   # 策略指数
            "style": [...],      # 风格指数
        }
    """
    logger.info("正在从中证指数官网获取指数列表...")

    all_indices = {
        "broad": [],
        "industry": [],
        "sector": [],
        "strategy": [],
        "style": [],
    }

    try:
        df = ak.index_csindex_all()
        logger.info(f"成功获取 {len(df)} 个中证指数")

        for _, row in df.iterrows():
            code = str(row.get("指数代码", ""))
            name = str(row.get("指数简称", ""))
            index_class = str(row.get("指数类别", ""))
            asset_class = str(row.get("资产类别", ""))
            base_date = str(row.get("基日", ""))
            publish_date = str(row.get("发布时间", ""))

            # 分类
            category = _classify_index(index_class, asset_class)
            if not category:
                continue

            all_indices[category].append({
                "code": code,
                "name": name,
                "category": category,
                "index_class": index_class,
                "asset_class": asset_class,
                "base_date": base_date,
                "publish_date": publish_date,
            })

    except Exception as e:
        logger.error(f"从中证指数官网获取数据失败: {e}")
        raise

    # 统计
    total = sum(len(indices) for indices in all_indices.values())
    logger.info(f"指数获取完成: "
               f"{len(all_indices['broad'])} 宽基 + "
               f"{len(all_indices['industry'])} 行业 + "
               f"{len(all_indices['sector'])} 主题 + "
               f"{len(all_indices['strategy'])} 策略 + "
               f"{len(all_indices['style'])} 风格 = "
               f"{total} 总计")

    return all_indices


def get_index_info(indices: List[Dict], code: str) -> Dict:
    """
    根据代码获取指数详情

    Args:
        indices: 指数列表
        code: 指数代码

    Returns:
        指数信息字典，未找到返回 None
    """
    for idx in indices:
        if idx["code"] == code:
            return idx
    return None

def _get_valuation_level(percentile: float) -> str:
    """根据百分位返回估值等级描述"""
    for (low, high), desc in VALUATION_LEVELS.items():
        if low <= percentile < high:
            return desc
    return "N/A"


def _calc_percentile(series: pd.Series, value: float) -> float:
    """计算value在series中的百分位（0-100）"""
    if len(series) == 0:
        return -1.0
    return round(float((series < value).sum() / len(series) * 100), 1)


def _calc_valuation_reference(series: pd.Series, value: float) -> Dict[str, Optional[float]]:
    """计算估值指标在历史区间内的参考值"""
    clean_series = pd.to_numeric(series, errors="coerce").dropna()
    if clean_series.empty:
        return {
            "当前": round(value, 2),
            "中位数": None,
            "最低": None,
            "最高": None,
        }

    return {
        "当前": round(value, 2),
        "中位数": round(float(clean_series.median()), 2),
        "最低": round(float(clean_series.min()), 2),
        "最高": round(float(clean_series.max()), 2),
    }


# 辅助函数： 基于历史数据计算PE分位值
def _build_csindex_pe_valuation(
    df_hist: pd.DataFrame,
    latest_pe: float,
    years: int = 10,
    publish_date: Optional[str] = None,
) -> Dict:
    """
    基于中证历史行情里的滚动市盈率计算 PE 历史分位。

    Args:
        df_hist: 历史行情数据
        latest_pe: 最新的 PE 值
        years: 时间窗口（年）
        publish_date: 指数发布日期，格式 YYYY-MM-DD。如果提供，只使用发布后的数据
    """
    if df_hist is None or df_hist.empty or "滚动市盈率" not in df_hist.columns or "日期" not in df_hist.columns:
        return {}

    pe_series = pd.to_numeric(df_hist["滚动市盈率"], errors="coerce")
    hist = pd.DataFrame({
        "日期": pd.to_datetime(df_hist["日期"], errors="coerce"),
        "滚动市盈率": pe_series,
    }).dropna()

    if hist.empty:
        return {}

    # 如果提供了发布日期，只使用发布后的数据
    if publish_date:
        try:
            pub_date = pd.to_datetime(publish_date, format="%Y-%m-%d", errors="coerce")
            if pd.notna(pub_date):
                hist = hist[hist["日期"] >= pub_date]
                logger.info(f"计算 PE 分位时使用指数发布日期后的数据: {publish_date} 起，共 {len(hist)} 条")
        except Exception as e:
            logger.warning(f"解析发布日期失败: {publish_date}, 错误: {e}")

    cutoff_main = datetime.now() - timedelta(days=years * 365)
    cutoff_5y = datetime.now() - timedelta(days=5 * 365)
    cutoff_3y = datetime.now() - timedelta(days=3 * 365)

    hist_main = hist[hist["日期"] >= cutoff_main]
    hist_5y = hist[hist["日期"] >= cutoff_5y]
    hist_3y = hist[hist["日期"] >= cutoff_3y]

    if hist_main.empty:
        return {}

    pe_main = _calc_percentile(hist_main["滚动市盈率"], latest_pe)
    pe_5y = _calc_percentile(hist_5y["滚动市盈率"], latest_pe) if not hist_5y.empty else -1.0
    pe_3y = _calc_percentile(hist_3y["滚动市盈率"], latest_pe) if not hist_3y.empty else -1.0
    pe_level = _get_valuation_level(pe_main)

    result = {
        "PE_TTM": round(float(latest_pe), 2),
        "PE分位_10年": pe_main,
        "PE分位_5年": pe_5y,
        "PE分位_3年": pe_3y,
        "PE参考_10年": _calc_valuation_reference(hist_main["滚动市盈率"], latest_pe),
        "PE估值等级": pe_level,
        "估值等级_PE": pe_level,
        "估值等级": pe_level,
        "估值规则": (
            f"PE 按近{years}年历史分位划分："
            "<10% 极度低估，10%-20% 低估，20%-40% 偏低，40%-60% 合理，"
            "60%-70% 合理偏上，70%-85% 偏高，85%-95% 高估，>=95% 极度高估。"
        ),
        "估值口径": {
            "PE_TTM": "中证指数历史行情接口返回的滚动市盈率",
            "历史分位": f"当前 PE 在近{years}年、近5年、近3年历史样本中的分位，数值越高表示估值越贵",
            "PE估值等级": "根据 PE 分位单独判断；当前数据源未提供 PB 历史样本",
            "历史参考": f"近{years}年 PE 样本的当前值、中位数、最低值、最高值",
        },
        "数据点数_10年": len(hist_main),
    }
    return result

def _calc_returns(df: pd.DataFrame, current_price: float) -> Dict[str, Optional[float]]:
    """向后兼容包装器，内部复用公共收益率计算函数。"""
    return get_index_returns(df, current_price=current_price)

# 辅助函数：从乐咕获取pe/pb 分位值
def _get_lg_valuation(index_name: str, code: Optional[str] = None) -> Dict:
    """
    从乐咕乐股获取PE/PB历史分位（仅支持宽基指数）

    Args:
        index_name: 指数名称
        code: 指数代码（6位）

    Returns:
        PE/PB分位数据
    """
    valuation = _build_lg_valuation(index_name=index_name, code=code, years=10)
    if not valuation:
        return {}
    return {
        "PE_TTM": valuation.get("PE_TTM"),
        "PB": valuation.get("PB"),
        "PE分位_10年": valuation.get("PE分位_10年"),
        "PE分位_5年": valuation.get("PE分位_5年"),
        "PE分位_3年": valuation.get("PE分位_3年"),
        "PB分位_10年": valuation.get("PB分位_10年"),
        "PB分位_5年": valuation.get("PB分位_5年"),
        "PB分位_3年": valuation.get("PB分位_3年"),
        "PE参考_10年": valuation.get("PE参考_10年"),
        "PB参考_10年": valuation.get("PB参考_10年"),
        "PE估值等级": valuation.get("PE估值等级"),
        "PB估值等级": valuation.get("PB估值等级"),
        "估值等级_PE": valuation.get("估值等级_PE"),
        "估值等级_PB": valuation.get("估值等级_PB"),
        "估值等级": valuation.get("估值等级"),
        "估值规则": valuation.get("估值规则"),
        "估值口径": valuation.get("估值口径"),
        "数据点数_10年": valuation.get("数据点数"),
    }


def fetch_index_valuation_with_fallback(
    code: str,
    index_name: str,
    publish_date: Optional[str] = None,
) -> Dict:
    """
    获取指数估值数据（多数据源 fallback 机制）

    根据指数代码前缀使用不同的数据源优先级：
      - 93xxxx: 中证行业指数 -> csindex
      - 000xxx/399xxx: 深交所指数 -> legulegu -> csindex
      - 其他指数 -> legulegu -> csindex

    Args:
        code: 指数代码（6位）
        index_name: 指数名称
        publish_date: 指数发布日期（用于过滤历史数据）

    Returns:
        估值数据字典
    """
    result = {
        "status": "success",
        "代码": code,
        "名称": index_name,
    }

    # 获取估值数据源优先级
    valuation_priority = get_valuation_source_priority(code)

    # 按优先级尝试数据源
    for source in valuation_priority:
        if source == "legulegu":
            # 乐咕乐股（仅宽基指数，提供完整PE/PB分位）
            lg_valuation = _get_lg_valuation(index_name, code=code)
            if lg_valuation:
                result.update(lg_valuation)
                result["估值数据源"] = "乐咕乐股"
                logger.debug(f"指数 {code} 估值数据来源: 乐咕乐股")
                return result
            else:
                logger.debug(f"指数 {code} 乐咕乐股不支持或失败")

        elif source == "csindex":
            # 中证指数历史行情（提供滚动市盈率，可计算分位）
            try:
                df_hist = fetch_index_history_data(code)
                if df_hist is not None and not df_hist.empty and "滚动市盈率" in df_hist.columns:
                    latest = df_hist.iloc[-1]
                    pe_ttm = latest.get("滚动市盈率")

                    if pd.notna(pe_ttm):
                        csindex_pe_valuation = _build_csindex_pe_valuation(
                            df_hist, float(pe_ttm), publish_date=publish_date
                        )
                        if csindex_pe_valuation:
                            result.update(csindex_pe_valuation)
                            result["估值数据源"] = "中证指数"
                            result["PB"] = None  # 中证指数历史行情不提供 PB
                            result["PB估值等级"] = "N/A"
                            result["估值等级_PB"] = "N/A"
                            logger.debug(f"指数 {code} 估值数据来源: 中证指数")
                            return result
                        else:
                            result["PE_TTM"] = round(float(pe_ttm), 2)
                            result["估值数据源"] = "中证指数"
                            result["PB"] = None
                            result["PB估值等级"] = "N/A"
                            result["估值等级_PB"] = "N/A"
                else:
                    logger.debug(f"指数 {code} 中证指数历史行情不包含'滚动市盈率'字段")

            except Exception as e:
                logger.warning(f"从中证指数获取 {code} 估值数据失败: {e}")

    # 所有数据源都失败
    result["估值数据源"] = "无"  # 标识数据源
    result["PE_TTM"] = None
    result["PB"] = None
    result["PE估值等级"] = "N/A"
    result["PB估值等级"] = "N/A"
    result["估值等级_PE"] = "N/A"
    result["估值等级_PB"] = "N/A"
    result["估值等级"] = "N/A"
    result["估值口径"] = {
        "说明": "所有数据源均无法获取该指数的估值数据",
    }

    return result

# 辅助函数：从乐咕获得估值结果？？ why？
def _build_lg_valuation(index_name: str, code: Optional[str] = None, years: int = 10, max_retries: int = 2) -> Dict:
    """
    构造乐咕乐股估值结果（内部使用）

    Args:
        index_name: 指数名称
        code: 指数代码（6位）
        years: 历史数据年数
        max_retries: 最大重试次数（默认3次，仅对网络错误重试）
    """
    if years <= 0:
        return {}

    import time
    import requests

    symbol = LG_INDEX_CODE_MAP.get(str(code)) or LG_INDEX_MAP.get(index_name)
    if not symbol:
        return {}

    # 重试机制：仅对网络错误和解析错误重试
    df_pe = None
    df_pb = None

    for attempt in range(max_retries):
        try:
            df_pe = ak.stock_index_pe_lg(symbol=symbol)
            df_pb = ak.stock_index_pb_lg(symbol=symbol)
            break  # 成功则退出重试循环
        except (requests.exceptions.RequestException, requests.exceptions.ConnectionError,
                requests.exceptions.Timeout, requests.exceptions.HTTPError,
                ConnectionError, TimeoutError) as e:
            # 网络相关错误，重试
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2  # 递增延迟：2秒、4秒、6秒
                logger.debug(f"乐咕乐股网络错误 ({index_name})，{wait_time}秒后重试 {attempt + 1}/{max_retries}: {e}")
                time.sleep(wait_time)
            else:
                logger.warning(f"从乐咕乐股获取估值数据失败 ({index_name})，网络错误已重试 {max_retries} 次: {e}")
                return {}
        except (AttributeError, KeyError, TypeError) as e:
            # 解析错误（可能是网站返回了错误页面或空页面），重试
            error_msg = str(e)
            if "'NoneType' object has no attribute" in error_msg or "attrs" in error_msg:
                # BeautifulSoup 解析错误，通常是临时网络问题
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.debug(f"乐咕乐股解析错误 ({index_name})，{wait_time}秒后重试 {attempt + 1}/{max_retries}: {e}")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"从乐咕乐股获取估值数据失败 ({index_name})，解析错误已重试 {max_retries} 次: {e}")
                    return {}
            else:
                # 其他解析错误，不重试
                logger.warning(f"从乐咕乐股获取估值数据失败 ({index_name}): {e}")
                return {}
        except Exception as e:
            # 其他未知错误，不重试
            logger.warning(f"从乐咕乐股获取估值数据失败 ({index_name}): {e}")
            return {}

    # 数据处理阶段
    try:
        df_pe["日期"] = pd.to_datetime(df_pe["日期"])
        df_pb["日期"] = pd.to_datetime(df_pb["日期"])

        latest_pe = float(df_pe.iloc[-1]["滚动市盈率"])
        latest_pb = float(df_pb.iloc[-1]["市净率"])

        cutoff_main = datetime.now() - timedelta(days=years * 365)
        cutoff_5y = datetime.now() - timedelta(days=5 * 365)
        cutoff_3y = datetime.now() - timedelta(days=3 * 365)
        df_pe_hist = df_pe[df_pe["日期"] >= cutoff_main]
        df_pb_hist = df_pb[df_pb["日期"] >= cutoff_main]

        pe_main = _calc_percentile(df_pe_hist["滚动市盈率"], latest_pe)
        pb_main = _calc_percentile(df_pb_hist["市净率"], latest_pb)
        pe_5y = _calc_percentile(df_pe[df_pe["日期"] >= cutoff_5y]["滚动市盈率"], latest_pe)
        pe_3y = _calc_percentile(df_pe[df_pe["日期"] >= cutoff_3y]["滚动市盈率"], latest_pe)
        pb_5y = _calc_percentile(df_pb[df_pb["日期"] >= cutoff_5y]["市净率"], latest_pb)
        pb_3y = _calc_percentile(df_pb[df_pb["日期"] >= cutoff_3y]["市净率"], latest_pb)

        pe_level = _get_valuation_level(pe_main)
        pb_level = _get_valuation_level(pb_main)

        result = {
            "PE_TTM": round(latest_pe, 2),
            "PB": round(latest_pb, 2),
            "PE分位_5年": pe_5y,
            "PE分位_3年": pe_3y,
            "PB分位_5年": pb_5y,
            "PB分位_3年": pb_3y,
            "PE估值等级": pe_level,
            "PB估值等级": pb_level,
            "估值等级_PE": pe_level,
            "估值等级_PB": pb_level,
            # 向后兼容：保留单字段，但明确以 PE 口径为主，避免继续使用 PE/PB 平均值。
            "估值等级": pe_level,
            "估值规则": (
                f"PE 与 PB 分别按各自 {years}年历史分位划分："
                "<10% 极度低估，10%-20% 低估，20%-40% 偏低，40%-60% 合理，"
                "60%-70% 合理偏上，70%-85% 偏高，85%-95% 高估，>=95% 极度高估。"
            ),
            "估值口径": {
                "PE_TTM": "乐咕乐股 stock_index_pe_lg 的滚动市盈率",
                "PB": "乐咕乐股 stock_index_pb_lg 的市净率",
                "历史分位": f"当前值在近{years}年、近5年、近3年历史样本中的分位，数值越高表示估值越贵",
                "PE估值等级": "根据 PE 分位单独判断，不与 PB 混合",
                "PB估值等级": "根据 PB 分位单独判断，不与 PE 混合",
                "兼容字段估值等级": "为兼容旧调用方暂保留，当前等同于 PE估值等级",
                "历史参考": f"近{years}年样本的当前值、中位数、最低值、最高值",
            },
            "数据点数": len(df_pe_hist),
        }

        result[f"PE分位_{years}年"] = pe_main
        result[f"PB分位_{years}年"] = pb_main
        result[f"PE参考_{years}年"] = _calc_valuation_reference(df_pe_hist["滚动市盈率"], latest_pe)
        result[f"PB参考_{years}年"] = _calc_valuation_reference(df_pb_hist["市净率"], latest_pb)
        if years == 10:
            result["PE分位_10年"] = pe_main
            result["PB分位_10年"] = pb_main
            result["PE参考_10年"] = result[f"PE参考_{years}年"]
            result["PB参考_10年"] = result[f"PB参考_{years}年"]
        return result
    except Exception as e:
        logger.warning(f"处理乐咕乐股数据失败 ({index_name}): {e}")
        return {}

# 辅助函数：获得指数股息率
def _get_dividend_yield(code: str) -> Optional[Dict]:
    """
    从中证指数获取股息率数据

    Args:
        code: 指数代码（6位），如 "000300"

    Returns:
        股息率数据字典，包含：
        - 股息率1: 基于价格计算的股息率
        - 股息率2: 基于净值计算的股息率
    """
    try:
        # 直接使用原始代码（不需要去掉前导零）
        df = ak.stock_zh_index_value_csindex(symbol=code)
        if df.empty:
            return None

        latest = df.iloc[-1]
        return {
            "股息率1": round(float(latest["股息率1"]), 2),
            "股息率2": round(float(latest["股息率2"]), 2),
        }

    except Exception as e:
        logger.warning(f"获取指数 {code} 股息率失败: {e}")
        return None

# 辅助函数：从中证指数和东方财富获取指数历史行情数据（带重试和备用数据源）
def get_history_source_priority(index_code: str) -> List[str]:
    """
    根据指数代码返回历史数据源优先级列表

    Args:
        index_code: 指数代码（6位）

    Returns:
        数据源名称列表，按优先级排序
    """
    # 93xxxx: 中证行业指数（如 932136 保险），直接走中证指数
    if index_code.startswith("93"):
        return ["csindex"]

    # 000xxx 或 399xxx: 深交所指数
    # Sina -> 腾讯 -> EastMoney -> 中证指数 -> EastMoney 历史
    if index_code.startswith("000") or index_code.startswith("399"):
        return ["sina_daily", "tx_daily", "eastmoney_daily", "csindex", "eastmoney_hist"]

    # 其他指数（如上交所指数）
    # Sina -> 腾讯 -> EastMoney -> 中证指数 -> EastMoney 历史
    return ["sina_daily", "tx_daily", "eastmoney_daily", "csindex", "eastmoney_hist"]


def get_valuation_source_priority(index_code: str) -> List[str]:
    """
    根据指数代码返回估值数据源优先级列表

    Args:
        index_code: 指数代码（6位）

    Returns:
        数据源名称列表，按优先级排序
    """
    # 93xxxx: 中证行业指数，直接走中证指数历史行情
    if index_code.startswith("93"):
        return ["csindex"]

    # 000xxx 或 399xxx: 深交所指数
    # 乐咕乐股 -> 中证指数 -> 证监会行业
    if index_code.startswith("000") or index_code.startswith("399"):
        return ["legulegu", "csindex"]

    # 其他指数（如上交所指数）
    # 乐咕乐股 -> 中证指数 -> 证监会行业
    return ["legulegu", "csindex"]


def fetch_index_history_data(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Optional[pd.DataFrame]:
    """
    获取指数历史行情数据（内部辅助函数）

    Args:
        code: 指数代码（6位）
        start_date: 开始日期，格式 YYYYMMDD
        end_date: 结束日期，格式 YYYYMMDD

    Returns:
        历史行情 DataFrame，包含日期、收盘价等字段
        失败返回 None
    """
    end_date = end_date or datetime.now().strftime("%Y%m%d")
    symbol_candidates = _get_history_symbol_candidates(code)

    # 获取数据源优先级
    source_priority = get_history_source_priority(code)

    # 根据优先级构建数据源列表
    source_fetchers = []
    for source_name in source_priority:
        if source_name == "sina_daily":
            for symbol in symbol_candidates:
                source_fetchers.append(
                    (f"sina_daily:{symbol}",
                     lambda symbol=symbol: ak.stock_zh_index_daily(symbol=symbol),
                     1)
                )
        elif source_name == "tx_daily":
            for symbol in symbol_candidates:
                source_fetchers.append(
                    (f"tx_daily:{symbol}",
                     lambda symbol=symbol: ak.stock_zh_index_daily_tx(symbol=symbol),
                     1)
                )
        elif source_name == "eastmoney_daily":
            for symbol in symbol_candidates:
                source_fetchers.append(
                    (f"eastmoney_daily:{symbol}",
                     lambda symbol=symbol: ak.stock_zh_index_daily_em(
                         symbol=symbol,
                         start_date=start_date or "19900101",
                         end_date=end_date,
                     ),
                     2)
                )
        elif source_name == "csindex":
            source_fetchers.append(
                ("csindex",
                 lambda: ak.stock_zh_index_hist_csindex(
                     symbol=code,
                     start_date=start_date or "20180526",
                     end_date=end_date,
                 ),
                 2)
            )
        elif source_name == "eastmoney_hist":
            source_fetchers.append(
                ("eastmoney_hist",
                 lambda: ak.index_zh_a_hist(
                     symbol=code,
                     period="daily",
                     start_date=start_date or "19900101",
                     end_date=end_date,
                 ),
                 3)
            )

    # 按优先级尝试数据源
    for source_name, fetcher, retries in source_fetchers:
        df_hist = _fetch_history_with_retry(fetcher, source_name=source_name, retries=retries)
        normalized = _normalize_history_frame(df_hist, source_name=source_name)
        if normalized is not None and not normalized.empty:
            filtered = _filter_history_window(normalized, start_date=start_date, end_date=end_date)
            if filtered is not None and not filtered.empty:
                return filtered

    return None

# 辅助函数：获取指数上下文信息 why?
def _get_index_context(code: str) -> Dict:
    """
    获取指数上下文信息

    Args:
        code: 指数代码（6位）

    Returns:
        指数信息字典，未找到返回 None
    """
    from . import get_all_stock_indices

    all_indices = get_all_stock_indices()
    return get_index_info(all_indices, code)

# 指数函数：查询指数基本信息
def get_index_query(
    code: str,
    df_hist: Optional[pd.DataFrame] = None,
    index_info: Optional[Dict] = None,
) -> Dict:
    """
    获取指数查询基础数据（基本信息 + 当前值 + 业绩表现）

    Args:
        code: 指数代码（6位），如 "000300", "000905"
        df_hist: 可选历史行情（用于复用）
        index_info: 可选指数基础信息（用于复用）

    Returns:
        基础查询结果
    """
    result = {
        "status": "success",
        "代码": code,
    }

    try:
        if index_info is None:
            index_info = _get_index_context(code)

        if not index_info:
            return {
                "status": "error",
                "message": f"未找到指数 {code}",
            }

        result["名称"] = index_info["name"]
        result["分类"] = index_info["category"]
        result["指数类别"] = index_info.get("index_class", "")
        result["发布日期"] = index_info.get("publish_date", "")

        query_start_date, query_end_date = _get_index_query_window()

        if df_hist is None or df_hist.empty:
            logger.info(f"正在获取指数 {code} 的历史行情...")
            df_hist = fetch_index_history_data(
                code,
                start_date=query_start_date,
                end_date=query_end_date,
            )
        else:
            df_hist = _filter_history_window(
                df_hist,
                start_date=query_start_date,
                end_date=query_end_date,
            )

        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据",
            }

        latest = df_hist.iloc[-1]
        current_price = float(latest["收盘"])

        latest_date = pd.to_datetime(latest["日期"])
        result["日期"] = str(latest_date.date())

        # 检查数据新鲜度：如果最新数据超过 1 年，认为数据不可用
        days_old = (datetime.now() - latest_date).days
        if days_old > 365:
            return {
                "status": "error",
                "message": f"指数 {code} 的数据太旧（最新数据来自 {days_old} 天前的 {latest_date.date()}），无法查询",
            }

        result["收盘点位"] = round(current_price, 2)
        result["涨跌幅"] = round(float(latest["涨跌幅"]), 2)

        logger.info(f"正在计算指数 {code} 的收益率...")
        returns = get_index_returns(df_hist, current_price=current_price)
        result.update(returns)

        result["数据点数"] = len(df_hist)

    except Exception as e:
        logger.error(f"获取指数 {code} 基础查询失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}",
        }

    return result

# 指数函数：获得指数估值数据
def get_index_valuation(
    code: str,
    df_hist: Optional[pd.DataFrame] = None,
    index_info: Optional[Dict] = None,
    include_dividend: bool = True,
) -> Dict:
    """
    获取指数估值数据（估值 + 股息率 + 分位 + 口径规则）

    Args:
        code: 指数代码（6位）
        df_hist: 可选历史行情（用于复用）
        index_info: 可选指数基础信息（用于复用）
        include_dividend: 是否获取股息率（默认True，设为False可跳过慢速接口）

    Returns:
        估值结果
    """
    result = {
        "status": "success",
        "代码": code,
    }

    try:
        if index_info is None:
            index_info = _get_index_context(code)

        if not index_info:
            return {
                "status": "error",
                "message": f"未找到指数 {code}",
            }

        result["名称"] = index_info["name"]

        # 使用统一的多数据源 fallback 机制获取估值数据
        valuation_data = fetch_index_valuation_with_fallback(
            code,
            index_info["name"],
            publish_date=index_info.get("publish_date"),
        )

        if valuation_data.get("status") == "error":
            return valuation_data

        result.update(valuation_data)

        # 获取股息率（从中证指数）- 可选功能，因为接口较慢
        if include_dividend:
            logger.debug(f"正在获取指数 {code} 的股息率...")
            dividend_yield = _get_dividend_yield(code)
            if dividend_yield:
                result.update(dividend_yield)
                result.setdefault("估值口径", {})
                result["估值口径"].update({
                    "股息率1": "中证指数 stock_zh_index_value_csindex 的 D/P1（总股本口径）",
                    "股息率2": "中证指数 stock_zh_index_value_csindex 的 D/P2（计算用股本口径）",
                })
        else:
            logger.debug(f"跳过指数 {code} 的股息率获取（include_dividend=False）")

        # 如果有传入历史数据，记录数据点数
        if df_hist is not None and not df_hist.empty:
            result["数据点数"] = len(df_hist)

    except Exception as e:
        logger.error(f"获取指数 {code} 估值数据失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}",
        }

    return result

# 指数函数：获取指数完整详情（基础查询 + 估值分析）
def get_index_details(code: str) -> Dict:
    """
    获取指数完整详情

    Args:
        code: 指数代码（6位），如 "000300", "000905"

    Returns:
        指数详情字典，包含：
        - 基本信息: 代码、名称、分类、发布日期
        - 当前值: 收盘点位、日期、涨跌幅
        - 业绩表现: 各时间段收益率
        - 估值数据: PE、PB及分位
        - 估值等级: 低估/合理/合理偏上/偏高/高估
    """
    try:
        index_info = _get_index_context(code)
        if not index_info:
            return {
                "status": "error",
                "message": f"未找到指数 {code}",
            }

        df_hist = fetch_index_history_data(code)
        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据",
            }

        query_result = get_index_query(code, df_hist=df_hist, index_info=index_info)
        if query_result.get("status") == "error":
            return query_result

        valuation_result = get_index_valuation(code, df_hist=df_hist, index_info=index_info)
        if valuation_result.get("status") == "error":
            return valuation_result

        result = dict(query_result)
        for key, value in valuation_result.items():
            if key != "status":
                result[key] = value

    except Exception as e:
        logger.error(f"获取指数 {code} 详情失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}"
        }

    return result

# 辅助函数：批量获取指数详情
def get_index_details_batch(codes: List[str]) -> Dict[str, Dict]:
    """
    批量获取指数详情

    Args:
        codes: 指数代码列表

    Returns:
        批量查询结果 {code: details}
    """
    results = {}

    for code in codes:
        results[code] = get_index_details(code)

    return results

# 辅助函数：计算年化波动率
def _calc_volatility(df: pd.DataFrame, period_days: int = 252) -> Optional[float]:
    """
    计算年化波动率

    Args:
        df: 历史行情数据
        period_days: 年化交易日数（默认252）

    Returns:
        年化波动率（百分比）
    """
    if df is None or len(df) < 2:
        return None

    try:
        # 计算日收益率
        closes = df["收盘"].astype(float)
        returns = closes.pct_change().dropna()

        # 年化波动率 = 日收益率标准差 * sqrt(252)
        volatility = returns.std() * np.sqrt(period_days) * 100
        return round(float(volatility), 2)

    except Exception as e:
        logger.warning(f"计算波动率失败: {e}")
        return None


def _calc_max_drawdown(df: pd.DataFrame) -> Dict[str, any]:
    """
    计算最大回撤

    Args:
        df: 历史行情数据

    Returns:
        {
            "最大回撤": -25.5,  # 百分比
            "回撤开始日期": "2021-02-18",
            "回撤结束日期": "2022-04-26",
            "回撤持续天数": 432
        }
    """
    if df is None or len(df) < 2:
        return {}

    try:
        closes = df["收盘"].astype(float)
        dates = df["日期"]

        # 计算累计最高点
        cummax = closes.cummax()

        # 计算回撤
        drawdown = (closes - cummax) / cummax * 100

        # 找到最大回撤
        max_dd_idx = drawdown.idxmin()
        max_dd_value = drawdown.loc[max_dd_idx]

        # 找到回撤开始点（最高点）
        peak_idx = closes[:max_dd_idx].idxmax()

        # 找到回撤结束点（如果已经恢复）
        recovery_idx = None
        recovery_date = None
        recovery_days = None

        if max_dd_idx < len(df) - 1:
            # 检查是否恢复到回撤前的高点
            for i in range(max_dd_idx + 1, len(df)):
                if closes.loc[i] >= closes.loc[peak_idx]:
                    recovery_idx = i
                    break

        peak_date = dates.loc[peak_idx].strftime("%Y-%m-%d")
        bottom_date = dates.loc[max_dd_idx].strftime("%Y-%m-%d")

        result = {
            "最大回撤": round(float(max_dd_value), 2),
            "回撤开始日期": peak_date,
            "回撤最低日期": bottom_date,
            "回撤持续天数": int((dates.loc[max_dd_idx] - dates.loc[peak_idx]).days),
        }

        if recovery_idx is not None:
            recovery_date = dates.loc[recovery_idx].strftime("%Y-%m-%d")
            recovery_days = int((dates.loc[recovery_idx] - dates.loc[peak_idx]).days)
            result["回撤修复日期"] = recovery_date
            result["回撤修复天数"] = recovery_days
        else:
            # 未恢复，计算截至现在的天数
            result["回撤修复日期"] = None
            result["回撤修复天数"] = None
            result["未恢复天数"] = int((dates.iloc[-1] - dates.loc[peak_idx]).days)

        return result

    except Exception as e:
        logger.warning(f"计算最大回撤失败: {e}")
        return {}


def _calc_drawdown_recovery_periods(df: pd.DataFrame) -> Dict[str, any]:
    """
    分析历史回撤修复周期

    Args:
        df: 历史行情数据

    Returns:
        {
            "平均回撤修复天数": 150,
            "最长回撤修复天数": 400,
            "最短回撤修复天数": 30,
            "未恢复回撤数": 1
        }
    """
    if df is None or len(df) < 2:
        return {}

    try:
        closes = df["收盘"].astype(float)
        dates = df["日期"]

        # 找到所有显著回撤（超过5%）
        cummax = closes.cummax()
        drawdown = (closes - cummax) / cummax * 100

        # 找回撤开始点
        drawdown_starts = []
        in_drawdown = False
        threshold = -5  # 5%以上才算显著回撤

        for i in range(len(drawdown)):
            if not in_drawdown and drawdown.iloc[i] <= threshold:
                drawdown_starts.append(i)
                in_drawdown = True
            elif in_drawdown and drawdown.iloc[i] > threshold:
                in_drawdown = False

        recovery_periods = []
        unrecovered_count = 0

        for start_idx in drawdown_starts:
            peak_price = closes.loc[start_idx]

            # 向前找最高点
            actual_peak_idx = closes[:start_idx].idxmax()

            # 向后找恢复点
            recovered = False
            for i in range(start_idx, len(df)):
                if closes.loc[i] >= peak_price:
                    recovery_days = int((dates.loc[i] - dates.loc[actual_peak_idx]).days)
                    recovery_periods.append(recovery_days)
                    recovered = True
                    break

            if not recovered:
                unrecovered_count += 1

        if recovery_periods:
            return {
                "显著回撤次数": len(drawdown_starts),
                "平均回撤修复天数": round(sum(recovery_periods) / len(recovery_periods)),
                "最长回撤修复天数": max(recovery_periods),
                "最短回撤修复天数": min(recovery_periods),
                "未恢复回撤数": unrecovered_count,
            }
        else:
            return {}

    except Exception as e:
        logger.warning(f"计算回撤修复周期失败: {e}")
        return {}


def _calc_sharpe_ratio(df: pd.DataFrame, risk_free_rate: float = 0.03) -> Optional[float]:
    """
    计算夏普比率（年化）

    Args:
        df: 历史行情数据
        risk_free_rate: 无风险利率（年化，默认3%）

    Returns:
        夏普比率
    """
    if df is None or len(df) < 2:
        return None

    try:
        closes = df["收盘"].astype(float)

        # 计算日收益率
        returns = closes.pct_change().dropna()

        # 年化收益率 = 日收益率均值 * 252
        annual_return = returns.mean() * 252

        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252)

        if annual_volatility == 0:
            return None

        # 夏普比率 = (年化收益 - 无风险利率) / 年化波动率
        excess_return = annual_return - risk_free_rate
        sharpe = excess_return / annual_volatility

        return round(float(sharpe), 2)

    except Exception as e:
        logger.warning(f"计算夏普比率失败: {e}")
        return None


def get_index_risk(code: str, df_hist: Optional[pd.DataFrame] = None) -> Dict:
    """
    获取指数风险分析

    Args:
        code: 指数代码（6位）
        df_hist: 可选的历史行情数据（复用已有数据，避免重复网络调用）

    Returns:
        风险分析字典，包含：
        - 收益率: 近1月/3月/6月/1年收益率
        - 波动率: 年化波动率
        - 最大回撤: 回撤幅度、时间、修复情况
        - 回撤分析: 历史回撤修复周期统计
        - 夏普比率: 风险调整后收益
    """
    result = {
        "status": "success",
        "代码": code,
    }

    try:
        # 1. 获取历史行情数据（复用已有数据或重新获取）
        if df_hist is None or df_hist.empty:
            logger.info(f"正在获取指数 {code} 的历史行情...")
            df_hist = fetch_index_history_data(code)

        if df_hist is None or df_hist.empty:
            return {
                "status": "error",
                "message": f"未找到指数 {code} 的历史行情数据"
            }

        # 2. 获取指数基本信息
        from . import get_all_stock_indices
        all_indices = get_all_stock_indices()
        index_info = get_index_info(all_indices, code)

        if index_info:
            result["名称"] = index_info["name"]

        latest = df_hist.iloc[-1]
        current_price = float(latest["收盘"])

        # 3. 计算各时间段收益率
        logger.info(f"正在计算指数 {code} 的收益率...")
        returns = get_index_returns(df_hist, current_price=current_price)
        result.update({
            "近1月收益率": returns.get("1月_收益率"),
            "近3月收益率": returns.get("3月_收益率"),
            "近6月收益率": returns.get("6月_收益率"),
            "近1年收益率": returns.get("1年_收益率"),
        })

        # 4. 计算年化波动率（按时间段）
        logger.info(f"正在计算指数 {code} 的波动率...")
        for period_name, days in [("1年", 252), ("3年", 756)]:
            if len(df_hist) > days:
                df_period = df_hist.tail(days)
                vol = _calc_volatility(df_period)
                result[f"近{period_name}波动率"] = vol

        # 全历史波动率
        result["历史波动率"] = _calc_volatility(df_hist)

        # 5. 计算最大回撤
        logger.info(f"正在计算指数 {code} 的最大回撤...")
        max_dd = _calc_max_drawdown(df_hist)
        result.update(max_dd)

        # 6. 分析回撤修复周期
        logger.info(f"正在分析指数 {code} 的回撤修复周期...")
        recovery_analysis = _calc_drawdown_recovery_periods(df_hist)
        if recovery_analysis:
            result["回撤修复分析"] = recovery_analysis

        # 7. 计算夏普比率
        logger.info(f"正在计算指数 {code} 的夏普比率...")
        sharpe = _calc_sharpe_ratio(df_hist)
        if sharpe is not None:
            result["夏普比率"] = sharpe

        # 8. 数据完整性
        result["数据点数"] = len(df_hist)
        result["数据起始日期"] = str(df_hist.iloc[0]["日期"].date())
        result["数据截止日期"] = str(df_hist.iloc[-1]["日期"].date())

    except Exception as e:
        logger.error(f"获取指数 {code} 风险分析失败: {e}")
        return {
            "status": "error",
            "message": f"查询失败: {str(e)}"
        }

    return result


# ============================================================
# 指数便捷函数
# ============================================================

def get_broad_indices() -> List[Dict]:
    """获取宽基指数列表（规模类）"""
    from . import get_index_list
    data = get_index_list()
    return data.get("broad", [])


def get_industry_indices() -> List[Dict]:
    """获取行业指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("industry", [])


def get_sector_indices() -> List[Dict]:
    """获取主题指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("sector", [])


def get_strategy_indices() -> List[Dict]:
    """获取策略指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("strategy", [])


def get_style_indices() -> List[Dict]:
    """获取风格指数列表"""
    from . import get_index_list
    data = get_index_list()
    return data.get("style", [])


def get_all_stock_indices() -> List[Dict]:
    """获取所有股票指数"""
    from . import get_index_list
    data = get_index_list()
    all_indices = []
    for cat in ["broad", "industry", "sector", "strategy", "style", "other"]:
        all_indices.extend(data.get(cat, []))
    return all_indices


def get_index_info_by_code(code: str) -> Dict:
    """
    根据代码获取指数详情

    Args:
        code: 指数代码

    Returns:
        指数信息字典，未找到返回 None
    """
    all_indices = get_all_stock_indices()
    return get_index_info(all_indices, code)
