# -*- coding: utf-8 -*-
"""共享工具函数"""

from datetime import datetime


def get_current_year() -> str:
    """获取当前年份作为字符串"""
    return str(datetime.now().year)


def print_banner():
    """打印横幅"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                📊 中国基金和指数信息查询工具 v2.3                         ║
║                基于 akshare + MCP Python SDK                           ║
║                                                                      ║
╚════════════════════════════════════════════════════════════════════════════╝
""")


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
