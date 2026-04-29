# -*- coding: utf-8 -*-
"""
行业指数与宽基指数估值热力图

约束:
  - 默认热力图统一复用 index.py 的指数估值链路
  - 证监会行业静态 PE 快照独立为单独报表
  - 不生成投资建议
"""

from datetime import datetime
from typing import Any, Dict, List

from tabulate import tabulate

from .index import VALUATION_LEVELS, get_csrc_industry_pe_snapshot

# 证监会行业映射（用于独立快照报表）
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

CSRC_DISPLAY_MAP = {
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

INDUSTRY_INDEX_MAP = {
#    "399986": ("银行", "金融"),
#    "399975": ("证券", "金融"),
#    "932136": ("保险", "金融"),
#    "399998": ("煤炭", "资源"),
#    "399439": ("油气", "资源"),
#    "931935": ("钢铁", "资源"),
#    "000819": ("有色", "资源"),
#    "000991": ("医药", "医疗"),
#    "399997": ("白酒", "消费"),
#    "932127": ("零售", "消费"),
#    "399811": ("电子", "科技"),
#    "930601": ("软件", "科技"),
#    "930604": ("互联网", "科技"),
#    "932139": ("半导体", "科技"),
#    "000994": ("通信", "科技"),
#    "931528": ("光伏", "制造"),
#    "931932": ("电气", "制造"),
#    "930607": ("汽车", "制造"),
#    "931775": ("地产", "地产"),
#    "399971": ("传媒", "文体"),
#    "399967": ("军工", "制造"),
#    "000941": ("新能源", "制造"),
#    "931931": ("建筑", "建筑"),
}

# 用于热力图排序，顺序直接复用 index.py 的估值等级定义，避免两边分叉。
VALUATION_ORDER = {
    desc: order
    for order, desc in enumerate(VALUATION_LEVELS.values(), start=1)
}
VALUATION_ORDER.update({
    "未知": 99,
    "N/A": 99,
})


def _valuation_bucket(pe_value: Any) -> str:
    pe = float(pe_value) if pe_value is not None else None
    if pe is None:
        return "未知"
    # 行业快照只有静态 PE，没有完整历史分位，这里只能做绝对值分档。
    if pe < 10:
        return "极度低估 🥶"
    if pe < 15:
        return "低估 🟢"
    if pe < 20:
        return "偏低 🟡"
    if pe < 30:
        return "合理 🟠"
    if pe < 40:
        return "偏高 🔴"
    if pe < 60:
        return "高估 🔥"
    return "极度高估 🚨"


def _build_valuation_summary(rows: List[Dict[str, Any]], field: str) -> Dict[str, int]:
    return {
        "极度低估": sum(1 for item in rows if item.get(field) == "极度低估 🥶"),
        "低估": sum(1 for item in rows if item.get(field) == "低估 🟢"),
        "偏低": sum(1 for item in rows if item.get(field) == "偏低 🟡"),
        "合理": sum(1 for item in rows if item.get(field) == "合理 🟠"),
        "偏高": sum(1 for item in rows if item.get(field) == "偏高 🔴"),
        "高估": sum(1 for item in rows if item.get(field) == "高估 🔥"),
        "极度高估": sum(1 for item in rows if item.get(field) == "极度高估 🚨"),
        "未知": sum(1 for item in rows if item.get(field) in ("未知", "N/A", None)),
    }


def _normalize_valuation_level(value: Any) -> str:
    if value in (None, "N/A"):
        return "未知"
    return str(value)


def _build_index_rows(index_map: Dict[str, Any], source_type: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    from .index import get_index_valuation
    import time

    for code, (expected_name, category) in index_map.items():
        details = get_index_valuation(code)
        # 只在获取失败时延迟，避免频繁失败导致限流
        if details.get("估值数据源") == "无" or details.get("PE_TTM") is None:
            time.sleep(0.3)
        if details.get("status") == "error":
            continue

        rows.append(
            {
                "代码": code,
                "内部标识": code,
                "名称": details.get("名称", expected_name),
                "分类": category,
                "日期": None,
                "收盘点位": None,
                "PE": details.get("PE_TTM"),
                "PB": details.get("PB"),
                "股息率": details.get("股息率1") or details.get("股息率2"),
                "PE估值温度": _normalize_valuation_level(
                    details.get("PE估值等级") or details.get("估值等级_PE") or details.get("估值等级")
                ),
                "PB估值温度": _normalize_valuation_level(
                    details.get("PB估值等级") or details.get("估值等级_PB")
                ),
                "估值温度": _normalize_valuation_level(
                    details.get("PE估值等级") or details.get("估值等级_PE") or details.get("估值等级")
                ),
                "数据源": details.get("估值数据源", "未知"),
                "类型": source_type,
            }
        )

    return rows


def _build_csrc_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for item in get_csrc_industry_pe_snapshot():
        raw_name = str(item.get("行业名称", "")).strip()
        if not raw_name:
            continue

        if raw_name in CSRC_DISPLAY_MAP:
            display_name, category = CSRC_DISPLAY_MAP[raw_name]
        else:
            display_name = raw_name
            category = CSRC_INDUSTRY_MAP.get(raw_name, "其他")

        pe_value = item.get("静态PE")
        rows.append(
            {
                "代码": "",
                "内部标识": f"CSRC::{raw_name}",
                "名称": display_name,
                "分类": category,
                "日期": item.get("日期"),
                "收盘点位": None,
                "PE": pe_value,
                "PB": None,
                "股息率": None,
                "PE估值温度": _valuation_bucket(pe_value),
                "PB估值温度": "未知",
                "估值温度": _valuation_bucket(pe_value),
                "数据源": item.get("数据源", "证监会行业"),
                "类型": "csrc",
            }
        )

    return rows


def get_industry_valuation_matrix() -> Dict[str, Any]:
    """
    获取行业指数与宽基指数估值矩阵
    """
    rows = _build_index_rows(INDUSTRY_INDEX_MAP, source_type="industry") + _build_index_rows(
        BROAD_INDEX_MAP,
        source_type="broad",
    )
    deduped: List[Dict[str, Any]] = []
    seen = set()
    for item in rows:
        key = item.get("内部标识") or (item.get("代码"), item.get("名称"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(deduped),
        "data": deduped,
    }


def get_csrc_valuation_matrix() -> Dict[str, Any]:
    rows = _build_csrc_rows()
    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(rows),
        "data": rows,
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
        rows.sort(key=lambda x: VALUATION_ORDER.get(str(x.get("PE估值温度")), 99))
    elif sort_by == "category":
        rows.sort(key=lambda x: (str(x.get("分类", "")), str(x.get("名称", ""))))
    else:
        sort_by = "pe"
        rows.sort(key=lambda x: x.get("PE") if x.get("PE") is not None else float("inf"))

    summary_pe = _build_valuation_summary(rows, "PE估值温度")
    summary_pb = _build_valuation_summary(rows, "PB估值温度")

    return {
        "timestamp": matrix["timestamp"],
        "total": len(rows),
        "sort_by": sort_by,
        "category": category,
        "title": "指数估值热力图",
        "summary": summary_pe,
        "summary_pe": summary_pe,
        "summary_pb": summary_pb,
        "data": rows,
    }


def get_csrc_valuation_heatmap(category: str = "全部", sort_by: str = "pe") -> Dict[str, Any]:
    matrix = get_csrc_valuation_matrix()
    rows = list(matrix["data"])

    if category != "全部":
        rows = [item for item in rows if item.get("分类") == category]

    if sort_by == "category":
        rows.sort(key=lambda x: (str(x.get("分类", "")), str(x.get("名称", ""))))
    elif sort_by == "valuation":
        rows.sort(key=lambda x: VALUATION_ORDER.get(str(x.get("PE估值温度")), 99))
    else:
        sort_by = "pe"
        rows.sort(key=lambda x: x.get("PE") if x.get("PE") is not None else float("inf"))

    summary_pe = _build_valuation_summary(rows, "PE估值温度")
    summary_pb = _build_valuation_summary(rows, "PB估值温度")

    return {
        "timestamp": matrix["timestamp"],
        "total": len(rows),
        "sort_by": sort_by,
        "category": category,
        "title": "证监会行业静态PE热力图",
        "summary": summary_pe,
        "summary_pe": summary_pe,
        "summary_pb": summary_pb,
        "data": rows,
    }


def format_heatmap_table(heatmap: Dict[str, Any], limit: int = 30) -> str:
    """
    格式化热力图表格输出
    """
    def _fmt_number(value: Any) -> str:
        if value is None:
            return "N/A"
        return f"{float(value):.2f}"

    def _truncate_text(value: Any, max_chars: int = 18) -> str:
        text = str(value or "")
        if len(text) <= max_chars:
            return text
        return text[: max_chars - 3] + "..."

    lines = []
    title = heatmap.get("title", "指数估值热力图")
    lines.append(f"{title} | 分类: {heatmap['category']} | 排序: {heatmap['sort_by']}")
    table_rows = []
    for item in heatmap["data"][:limit]:
        table_rows.append(
            [
                str(item.get("代码", "")),
                _truncate_text(item.get("名称", ""), max_chars=18),
                str(item.get("分类", "")),
                _fmt_number(item.get("PE")),
                _fmt_number(item.get("PB")),
                _fmt_number(item.get("股息率")),
                str(item.get("数据源", "")),
                str(item.get("PE估值温度", "")),
                str(item.get("PB估值温度", "")),
            ]
        )

    lines.append(
        tabulate(
            table_rows,
            headers=["代码", "名称", "分类", "PE", "PB", "股息率", "数据源", "PE估值", "PB估值"],
            tablefmt="simple",
            disable_numparse=True,
        )
    )

    summary_pe = heatmap["summary_pe"]
    summary_pb = heatmap["summary_pb"]

    lines.append(
        f"PE口径: 共 {heatmap['total']} 条 | 低估 {summary_pe.get('极度低估', 0) + summary_pe.get('低估', 0)} "
        f"| 合理 {summary_pe.get('偏低', 0) + summary_pe.get('合理', 0)} "
        f"| 高估 {summary_pe.get('偏高', 0) + summary_pe.get('高估', 0) + summary_pe.get('极度高估', 0)} "
        f"| 未知 {summary_pe.get('未知', 0)}"
    )
    lines.append(
        f"PB口径: 共 {heatmap['total']} 条 | 低估 {summary_pb.get('极度低估', 0) + summary_pb.get('低估', 0)} "
        f"| 合理 {summary_pb.get('偏低', 0) + summary_pb.get('合理', 0)} "
        f"| 高估 {summary_pb.get('偏高', 0) + summary_pb.get('高估', 0) + summary_pb.get('极度高估', 0)} "
        f"| 未知 {summary_pb.get('未知', 0)}"
    )
    return "\n".join(lines)
