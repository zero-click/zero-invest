# -*- coding: utf-8 -*-
"""
行业与宽基估值热力图

约束:
  - 宽基指数数据统一复用 index.py 的公开函数
  - 保留热力图输出
  - 不生成投资建议
"""

from datetime import datetime
from typing import Any, Dict, List

from .index import get_csrc_industry_pe_snapshot, get_index_details

# 证监会行业映射（主要行业）
CSRC_INDUSTRY_MAP = {
    "农、林、牧、渔业": "农业",
    "采矿业": "资源",
    "制造业": "制造",
    "电力、热力、燃气及水生产和供应业": "公用事业",
    "建筑业": "建筑",
    "批发和零售业": "商贸",
    "交通运输、仓储和邮政业": "物流",
    "住宿和餐饮业": "消费",
    "信息传输、软件和信息技术服务业": "科技",
    "金融业": "金融",
    "房地产业": "地产",
    "租赁和商务服务业": "服务",
    "科学研究和技术服务业": "科研",
    "水利、环境和公共设施管理业": "环保",
    "居民服务、修理和其他服务业": "服务",
    "教育": "教育",
    "卫生和社会工作": "医疗",
    "文化、体育和娱乐业": "文体",
    "综合": "综合",
}

KEY_INDUSTRIES = {
    "煤炭开采和洗选业": ("煤炭", "资源"),
    "石油和天然气开采业": ("油气", "资源"),
    "黑色金属矿采选业": ("钢铁", "资源"),
    "有色金属矿采选业": ("有色", "资源"),
    "酒、饮料和精制茶制造业": ("白酒", "消费"),
    "医药制造业": ("医药", "医疗"),
    "计算机、通信和其他电子设备制造业": ("电子", "科技"),
    "电气机械和器材制造业": ("电气", "制造"),
    "汽车制造业": ("汽车", "制造"),
    "货币金融服务": ("银行", "金融"),
    "资本市场服务": ("证券", "金融"),
    "保险业": ("保险", "金融"),
    "软件和信息技术服务业": ("软件", "科技"),
    "互联网和相关服务": ("互联网", "科技"),
    "零售业": ("零售", "消费"),
    "房地产业": ("地产", "地产"),
}

BROAD_INDEX_MAP = {
    "000300": ("沪深300", "宽基"),
    "000905": ("中证500", "宽基"),
    "000852": ("中证1000", "宽基"),
    "000016": ("上证50", "宽基"),
    "399673": ("创业板50", "成长"),
    "000015": ("上证红利", "红利"),
    "000922": ("中证红利", "红利"),
    "000010": ("上证180", "宽基"),
    "000009": ("上证380", "宽基"),
    "000903": ("中证100", "宽基"),
    "000906": ("中证800", "宽基"),
    "399330": ("深证100", "宽基"),
}

VALUATION_ORDER = {"低": 1, "中": 2, "高": 3, "极高": 4, "未知": 5}


def _valuation_bucket(pe_value: Any) -> str:
    pe = float(pe_value) if pe_value is not None else None
    if pe is None:
        return "未知"
    if pe < 15:
        return "低"
    if pe < 25:
        return "中"
    if pe < 40:
        return "高"
    return "极高"


def _build_csrc_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in get_csrc_industry_pe_snapshot():
        raw_name = str(item.get("行业名称", "")).strip()
        if not raw_name:
            continue

        if raw_name in KEY_INDUSTRIES:
            display_name, category = KEY_INDUSTRIES[raw_name]
        else:
            display_name = raw_name
            category = CSRC_INDUSTRY_MAP.get(raw_name, "其他")

        pe_value = item.get("静态PE")
        rows.append(
            {
                "代码": f"CSRC::{raw_name}",
                "名称": display_name,
                "分类": category,
                "日期": item.get("日期"),
                "收盘点位": None,
                "PE": pe_value,
                "PB": None,
                "股息率": None,
                "估值温度": _valuation_bucket(pe_value),
                "数据源": item.get("数据源", "证监会行业"),
            }
        )

    return rows


def _build_broad_index_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for code, (expected_name, category) in BROAD_INDEX_MAP.items():
        details = get_index_details(code)
        if details.get("status") == "error":
            continue

        pe_value = details.get("PE_TTM")
        rows.append(
            {
                "代码": code,
                "名称": details.get("名称", expected_name),
                "分类": category,
                "日期": details.get("日期"),
                "收盘点位": details.get("收盘点位"),
                "PE": pe_value,
                "PB": details.get("PB"),
                "股息率": details.get("股息率1") or details.get("股息率2"),
                "估值温度": details.get("估值等级") if details.get("估值等级") not in (None, "N/A") else _valuation_bucket(pe_value),
                "数据源": details.get("估值数据源", "未知"),
            }
        )

    return rows


def get_industry_valuation_matrix() -> Dict[str, Any]:
    """
    获取行业与宽基估值矩阵
    """
    rows = _build_csrc_rows() + _build_broad_index_rows()
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for item in rows:
        key = (item.get("代码"), item.get("名称"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(deduped),
        "data": deduped,
    }


def get_valuation_heatmap(category: str = "全部", sort_by: str = "pe") -> Dict[str, Any]:
    """
    获取估值热力图数据
    """
    matrix = get_industry_valuation_matrix()
    rows = list(matrix["data"])

    if category != "全部":
        rows = [item for item in rows if item.get("分类") == category]

    if sort_by == "pb":
        rows.sort(key=lambda x: x.get("PB") if x.get("PB") is not None else float("inf"))
    elif sort_by == "dividend":
        rows.sort(key=lambda x: x.get("股息率") if x.get("股息率") is not None else -float("inf"), reverse=True)
    elif sort_by == "valuation":
        rows.sort(key=lambda x: VALUATION_ORDER.get(str(x.get("估值温度")), 99))
    elif sort_by == "category":
        rows.sort(key=lambda x: (str(x.get("分类", "")), str(x.get("名称", ""))))
    else:
        sort_by = "pe"
        rows.sort(key=lambda x: x.get("PE") if x.get("PE") is not None else float("inf"))

    summary = {
        "低": sum(1 for item in rows if item.get("估值温度") == "低"),
        "中": sum(1 for item in rows if item.get("估值温度") == "中"),
        "高": sum(1 for item in rows if item.get("估值温度") == "高"),
        "极高": sum(1 for item in rows if item.get("估值温度") == "极高"),
        "未知": sum(1 for item in rows if item.get("估值温度") == "未知"),
    }

    return {
        "timestamp": matrix["timestamp"],
        "total": len(rows),
        "sort_by": sort_by,
        "category": category,
        "summary": summary,
        "data": rows,
    }


def format_heatmap_table(heatmap: Dict[str, Any], limit: int = 30) -> str:
    """
    格式化热力图表格输出
    """
    lines = []
    lines.append("=" * 92)
    lines.append(f"指数估值热力图 | 分类: {heatmap['category']} | 排序: {heatmap['sort_by']}")
    lines.append("=" * 92)
    lines.append(f"{'名称':<16} {'分类':<10} {'PE':<8} {'PB':<8} {'股息率':<8} {'数据源':<12} {'估值':<12}")
    lines.append("-" * 92)

    for item in heatmap["data"][:limit]:
        name = str(item.get("名称", ""))
        if len(name) > 15:
            name = name[:12] + "..."
        pe = item.get("PE")
        pb = item.get("PB")
        dy = item.get("股息率")
        lines.append(
            f"{name:<16} "
            f"{str(item.get('分类', '')):<10} "
            f"{(f'{pe:.2f}' if pe is not None else 'N/A'):<8} "
            f"{(f'{pb:.2f}' if pb is not None else 'N/A'):<8} "
            f"{(f'{dy:.2f}' if dy is not None else 'N/A'):<8} "
            f"{str(item.get('数据源', '')):<12} "
            f"{str(item.get('估值温度', '')):<12}"
        )

    lines.append("-" * 92)
    lines.append(
        f"共 {heatmap['total']} 条 | 低 {heatmap['summary']['低']} | 中 {heatmap['summary']['中']} "
        f"| 高 {heatmap['summary']['高']} | 极高 {heatmap['summary']['极高']} | 未知 {heatmap['summary']['未知']}"
    )
    return "\n".join(lines)
