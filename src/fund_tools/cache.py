# -*- coding: utf-8 -*-
"""
基金数据缓存模块
提供本地磁盘缓存和内存缓存功能
"""

import akshare as ak
import pandas as pd
import json
import os
import time
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

# === 本地磁盘缓存配置 ===
FUND_DB_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "fund_database.json")
FUND_DB_TTL = 7 * 24 * 3600  # 7天过期


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
