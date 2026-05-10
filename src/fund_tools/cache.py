# -*- coding: utf-8 -*-
"""
基金和指数数据缓存模块
提供本地磁盘缓存和内存缓存功能
"""

import akshare as ak
import pandas as pd
import json
import os
import time
import logging
from functools import lru_cache
from typing import Dict, List

logger = logging.getLogger(__name__)

# === 本地磁盘缓存配置 ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 基金缓存
FUND_DB_FILE = os.path.join(BASE_DIR, "fund_database.json")
FUND_DB_TTL = 7 * 24 * 3600  # 7天过期

# 指数缓存
INDEX_DB_FILE = os.path.join(BASE_DIR, "index_database.json")
INDEX_DB_TTL = 30 * 24 * 3600  # 30天过期
INDEX_DB_SCHEMA_VERSION = 2

# 常见宽基指数的补充映射
_EXTRA_BROAD_INDEXES = {
    "000300": {"name": "沪深300", "index_class": "规模", "publish_date": "2005-04-08"},
    "000905": {"name": "中证500", "index_class": "规模", "publish_date": "2007-01-15"},
    "000852": {"name": "中证1000", "index_class": "规模", "publish_date": "2014-10-31"},
    "000016": {"name": "上证50", "index_class": "规模", "publish_date": "2004-01-02"},
    "399673": {"name": "创业板50", "index_class": "规模", "publish_date": "2014-06-18"},
    "000015": {"name": "上证红利", "index_class": "风格", "publish_date": "2006-11-20"},
    "000922": {"name": "中证红利", "index_class": "风格", "publish_date": "2008-01-02"},
    "000010": {"name": "上证180", "index_class": "规模", "publish_date": "2002-07-01"},
    "000009": {"name": "上证380", "index_class": "规模", "publish_date": "2010-11-15"},
    "000903": {"name": "中证100", "index_class": "规模", "publish_date": "2005-01-04"},
    "000906": {"name": "中证800", "index_class": "规模", "publish_date": "2007-01-15"},
    "399330": {"name": "深证100", "index_class": "规模", "publish_date": "2006-01-24"},
}


def _load_fund_db_from_disk() -> pd.DataFrame:
    """从磁盘读取基金列表缓存，过期或不存在则返回空 DataFrame"""
    if not os.path.exists(FUND_DB_FILE):
        return pd.DataFrame()
    try:
        mtime = os.path.getmtime(FUND_DB_FILE)
        if time.time() - mtime > FUND_DB_TTL:
            logger.info(f"本地基金数据库已超过7天，需要更新")
            return pd.DataFrame()
        with open(FUND_DB_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)
        df = pd.DataFrame(records)
        logger.info(f"从本地缓存加载 {len(df)} 只基金信息")
        return df
    except Exception as e:
        logger.warning(f"读取本地基金数据库失败: {e}")
        return pd.DataFrame()


def _save_fund_db_to_disk(df: pd.DataFrame) -> None:
    """将基金列表保存到磁盘"""
    try:
        records = df.to_dict("records")
        with open(FUND_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
        logger.info(f"基金数据库已保存到 {FUND_DB_FILE}")
    except Exception as e:
        logger.warning(f"保存本地基金数据库失败: {e}")


@lru_cache(maxsize=1)
def get_fund_list() -> pd.DataFrame:
    """
    获取基金列表（优先读本地磁盘缓存，缓存超过7天或不存在时才请求网络）
    """
    df = _load_fund_db_from_disk()
    if not df.empty:
        return df

    try:
        logger.info("正在从东方财富获取基金列表...")
        df = ak.fund_name_em()
        logger.info(f"成功获取 {len(df)} 只基金信息")
        _save_fund_db_to_disk(df)
        return df
    except Exception as e:
        logger.error(f"获取基金列表失败: {e}")
        return pd.DataFrame()


# ============================================================
# 指数缓存管理
# ============================================================

def _load_index_db_from_disk() -> Dict:
    """从磁盘读取指数列表缓存，过期或不存在则返回空 Dict"""
    if not os.path.exists(INDEX_DB_FILE):
        return {}

    try:
        mtime = os.path.getmtime(INDEX_DB_FILE)
        if time.time() - mtime > INDEX_DB_TTL:
            logger.info(f"本地指数数据库已超过{INDEX_DB_TTL//86400}天，需要更新")
            return {}

        with open(INDEX_DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("cache_version") != INDEX_DB_SCHEMA_VERSION:
            logger.info("本地指数数据库版本过旧，需要重建")
            return {}

        total = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
        logger.info(f"从本地缓存加载指数数据库: {total} 个指数")
        return data

    except Exception as e:
        logger.warning(f"读取本地指数数据库失败: {e}")
        return {}


def _save_index_db_to_disk(data: Dict) -> None:
    """将指数列表保存到磁盘"""
    try:
        with open(INDEX_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"指数数据库已保存到 {INDEX_DB_FILE}")
    except Exception as e:
        logger.warning(f"保存本地指数数据库失败: {e}")


def _normalize_index_code(code: str) -> str:
    """统一指数代码格式"""
    raw = str(code).strip()
    if not raw:
        return ""
    if raw.lower().startswith(("sh", "sz")) and len(raw) > 2:
        raw = raw[2:]
    if raw.isdigit():
        return raw.zfill(6)
    return raw


def _append_index_record(bucket: Dict[str, Dict], record: Dict) -> None:
    """按代码合并指数记录"""
    code = _normalize_index_code(record.get("code", ""))
    if not code:
        return

    merged = dict(bucket.get(code, {}))
    merged["code"] = code

    for key, value in record.items():
        if key == "code":
            continue
        if value in ("", None, [], {}):
            continue
        if key == "sources":
            existing = merged.get("sources", [])
            merged["sources"] = sorted(set(existing) | set(value))
            continue
        if not merged.get(key):
            merged[key] = value

    sources = set(merged.get("sources", []))
    source = record.get("source")
    if source:
        sources.add(source)
    if sources:
        merged["sources"] = sorted(sources)

    bucket[code] = merged


def _infer_extra_category(code: str, name: str) -> Dict[str, str]:
    """给无法从中证指数分类的常见宽基补一个类别"""
    code = _normalize_index_code(code)
    meta = _EXTRA_BROAD_INDEXES.get(code)
    if meta:
        return {
            "category": "broad",
            "index_class": meta["index_class"],
            "base_date": "",
            "publish_date": meta["publish_date"],
        }
    return {
        "category": "other",
        "index_class": "",
        "base_date": "",
        "publish_date": "",
    }


def _build_index_record(
    code: str,
    name: str,
    *,
    category: str = "",
    index_class: str = "",
    asset_class: str = "股票",
    base_date: str = "",
    publish_date: str = "",
    source: str = "",
    **extra: Dict,
) -> Dict:
    """统一指数记录字段"""
    code = _normalize_index_code(code)
    record = {
        "code": code,
        "name": str(name).strip(),
        "category": category,
        "index_class": index_class,
        "asset_class": asset_class,
        "base_date": base_date,
        "publish_date": publish_date,
        "source": source,
    }
    for key, value in extra.items():
        if value not in ("", None, [], {}):
            record[key] = value
    return record


def _fetch_index_spot_sources() -> List[Dict]:
    """
    从东方财富/新浪/指数信息表聚合股票指数列表

    Returns:
        {code: merged_record}
    """
    merged: Dict[str, Dict] = {}

    # 1) 东方财富实时行情
    try:
        spot_em = ak.stock_zh_index_spot_em()
        for _, row in spot_em.iterrows():
            code = _normalize_index_code(row.get("代码", ""))
            if not code:
                continue
            name = str(row.get("名称", "")).strip()
            category_info = _infer_extra_category(code, name)
            _append_index_record(
                merged,
                _build_index_record(
                    code,
                    name,
                    category=category_info["category"],
                    index_class=category_info["index_class"],
                    source="eastmoney_spot_em",
                    latest_price=row.get("最新价"),
                    change_pct=row.get("涨跌幅"),
                    turnover=row.get("成交额"),
                ),
            )
    except Exception as e:
        logger.warning(f"获取东方财富指数实时行情失败: {e}")

    # 2) 新浪实时行情
    try:
        spot_sina = ak.stock_zh_index_spot_sina()
        for _, row in spot_sina.iterrows():
            raw_code = str(row.get("代码", "")).strip()
            code = _normalize_index_code(raw_code)
            if not code:
                continue
            name = str(row.get("名称", "")).strip()
            category_info = _infer_extra_category(code, name)
            _append_index_record(
                merged,
                _build_index_record(
                    code,
                    name,
                    category=category_info["category"],
                    index_class=category_info["index_class"],
                    source="sina_spot",
                    latest_price=row.get("最新价"),
                    change_pct=row.get("涨跌幅"),
                    turnover=row.get("成交额"),
                ),
            )
    except Exception as e:
        logger.warning(f"获取新浪指数实时行情失败: {e}")

    # 3) 指数信息表，补充发布日期
    try:
        info_df = ak.index_stock_info()
        for _, row in info_df.iterrows():
            code = _normalize_index_code(row.get("index_code", ""))
            if not code:
                continue
            name = str(row.get("display_name", "")).strip()
            category_info = _infer_extra_category(code, name)
            _append_index_record(
                merged,
                _build_index_record(
                    code,
                    name,
                    category=category_info["category"],
                    index_class=category_info["index_class"],
                    source="index_stock_info",
                    publish_date=str(row.get("publish_date", "")).strip(),
                ),
            )
    except Exception as e:
        logger.warning(f"获取指数信息表失败: {e}")

    return list(merged.values())


def _fetch_csindex_source() -> List[Dict]:
    """获取中证指数列表并标准化"""
    from . import index as index_module

    records: List[Dict] = []
    data = index_module.fetch_indices_from_csindex()
    for category, items in data.items():
        if not isinstance(items, list):
            continue
        for item in items:
            records.append(
                _build_index_record(
                    item.get("code", ""),
                    item.get("name", ""),
                    category=category,
                    index_class=item.get("index_class", ""),
                    asset_class=item.get("asset_class", "股票"),
                    base_date=item.get("base_date", ""),
                    publish_date=item.get("publish_date", ""),
                    source="csindex",
                )
            )
    return records


def _finalize_index_catalog(records: List[Dict]) -> Dict[str, List[Dict]]:
    """按分类整理为缓存结构"""
    catalog = {
        "broad": [],
        "industry": [],
        "sector": [],
        "strategy": [],
        "style": [],
        "other": [],
    }

    merged: Dict[str, Dict] = {}
    for record in records:
        _append_index_record(merged, record)

    for record in merged.values():
        category = record.get("category", "other") or "other"
        if category not in catalog:
            category = "other"
        catalog[category].append(record)

    for key in catalog:
        catalog[key].sort(key=lambda x: (str(x.get("code", "")), str(x.get("name", ""))))

    return catalog


@lru_cache(maxsize=1)
def get_index_list() -> Dict[str, List[Dict]]:
    """
    获取指数列表（优先读本地磁盘缓存，缓存超过30天或不存在时才请求网络）

    Returns:
        {
            "broad": [...],      # 宽基指数
            "industry": [...],   # 行业指数
            "sector": [...],     # 主题指数
            "strategy": [...],   # 策略指数
            "style": [...],      # 风格指数
            "updated_at": "2026-04-26",
            "total": 1488,
        }
    """
    # 尝试从磁盘加载
    cached_data = _load_index_db_from_disk()
    if cached_data:
        return cached_data

    try:
        logger.info("正在从多源接口获取指数列表...")
        records = []
        records.extend(_fetch_csindex_source())
        records.extend(_fetch_index_spot_sources())

        data = _finalize_index_catalog(records)

        # 添加元数据
        from datetime import datetime
        data["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        data["cache_version"] = INDEX_DB_SCHEMA_VERSION
        data["total"] = sum(
            len(indices)
            for key, indices in data.items()
            if key not in {"updated_at", "total"} and isinstance(indices, list)
        )

        # 保存到磁盘
        _save_index_db_to_disk(data)

        return data

    except Exception as e:
        logger.error(f"获取指数列表失败: {e}")
        return {}


def update_index_cache() -> Dict:
    """
    强制更新指数缓存

    Returns:
        更新后的指数数据
    """
    # 清除内存缓存
    get_index_list.cache_clear()

    # 删除磁盘缓存
    if os.path.exists(INDEX_DB_FILE):
        os.remove(INDEX_DB_FILE)
        logger.info(f"已删除过期缓存: {INDEX_DB_FILE}")

    # 重新获取
    return get_index_list()


# === 香港基金缓存 ===

HK_FUND_DB_FILE = os.path.join(BASE_DIR, "hk_fund_database.json")
HK_FUND_DB_TTL = 1 * 24 * 3600  # 1天过期（排行数据每日变化）
HK_FUND_DB_SCHEMA_VERSION = 1


def _load_hk_fund_db_from_disk() -> pd.DataFrame:
    """从磁盘加载香港基金排行缓存，过期或不存在则返回空 DataFrame"""
    if not os.path.exists(HK_FUND_DB_FILE):
        return pd.DataFrame()
    try:
        mtime = os.path.getmtime(HK_FUND_DB_FILE)
        if time.time() - mtime > HK_FUND_DB_TTL:
            logger.info("香港基金排行缓存已超过1天，需要更新")
            return pd.DataFrame()
        with open(HK_FUND_DB_FILE, "r", encoding="utf-8") as f:
            cached = json.load(f)
        # 检查 schema version
        if isinstance(cached, dict):
            if cached.get("schema_version") != HK_FUND_DB_SCHEMA_VERSION:
                logger.info("香港基金排行缓存 schema 不匹配，需要更新")
                return pd.DataFrame()
            records = cached.get("data", [])
        else:
            records = cached
        df = pd.DataFrame(records)
        logger.info(f"从本地缓存加载 {len(df)} 只香港基金信息")
        return df
    except Exception as e:
        logger.warning(f"加载香港基金缓存失败: {e}")
        return pd.DataFrame()


def _save_hk_fund_db_to_disk(df: pd.DataFrame) -> None:
    """保存香港基金排行到本地缓存"""
    try:
        # 将 date 等非 JSON 可序列化类型转为字符串
        df_clean = df.copy()
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(
                lambda x: x.isoformat() if hasattr(x, "isoformat") else x
            )
        records = df_clean.to_dict("records")
        cached = {
            "schema_version": HK_FUND_DB_SCHEMA_VERSION,
            "updated_at": time.strftime("%Y-%m-%d"),
            "total": len(records),
            "data": records,
        }
        with open(HK_FUND_DB_FILE, "w", encoding="utf-8") as f:
            json.dump(cached, f, ensure_ascii=False, indent=2)
        logger.info(f"已缓存 {len(records)} 只香港基金到 {HK_FUND_DB_FILE}")
    except Exception as e:
        logger.error(f"保存香港基金缓存失败: {e}")


@lru_cache(maxsize=1)
def get_hk_fund_list() -> pd.DataFrame:
    """
    获取香港基金排行数据（带磁盘缓存）

    Returns:
        香港基金排行 DataFrame，包含 基金代码、基金简称、币种、单位净值、
        各期收益率、可购买状态、香港基金代码 等字段
    """
    # 尝试从磁盘加载
    df = _load_hk_fund_db_from_disk()
    if not df.empty:
        return df

    try:
        logger.info("正在获取香港基金排行数据...")
        import akshare as ak
        df = ak.fund_hk_rank_em()
        if df is not None and not df.empty:
            _save_hk_fund_db_to_disk(df)
            return df
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"获取香港基金排行数据失败: {e}")
        return pd.DataFrame()


def update_hk_fund_cache() -> Dict:
    """
    强制更新香港基金排行缓存

    Returns:
        更新结果
    """
    get_hk_fund_list.cache_clear()

    if os.path.exists(HK_FUND_DB_FILE):
        os.remove(HK_FUND_DB_FILE)
        logger.info(f"已删除过期缓存: {HK_FUND_DB_FILE}")

    df = get_hk_fund_list()
    if df.empty:
        return {"status": "error", "message": "更新香港基金缓存失败"}
    return {"status": "success", "count": len(df)}
