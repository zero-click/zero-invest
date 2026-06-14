# -*- coding: utf-8 -*-
"""共享工具函数"""

from datetime import datetime


def get_current_year() -> str:
    """获取当前年份作为字符串"""
    return str(datetime.now().year)


def print_banner(subtitle: str = ""):
    """打印横幅

    Args:
        subtitle: 可选副标题，显示在横幅下方
    """
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                📊 zero-invest 中国投资信息查询工具 v2.3                   ║
║                基于 akshare 数据源                                        ║
║                                                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")
    if subtitle:
        print(f"\n  ── {subtitle} ──\n")


def _fmt_amount(val) -> str:
    """格式化金额（亿元），自动对齐正负"""
    if val is None:
        return "N/A"
    try:
        v = float(val)
    except (ValueError, TypeError):
        return str(val)
    if v >= 0:
        return f"+{v:,.2f}亿"
    return f"{v:,.2f}亿"
