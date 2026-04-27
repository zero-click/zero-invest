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

    # 从网络获取
    from . import index

    try:
        logger.info("正在从中证指数官网获取指数列表...")
        data = index.fetch_indices_from_csindex()

        # 添加元数据
        from datetime import datetime
        data["updated_at"] = datetime.now().strftime("%Y-%m-%d")
        data["total"] = sum(len(indices) for indices in data.values() if isinstance(indices, list))

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
