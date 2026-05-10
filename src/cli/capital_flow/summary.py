# -*- coding: utf-8 -*-
"""沪深港通资金流总览命令"""

import typer

from . import cf_app
from ..helpers import print_banner, _fmt_amount


def print_capital_flow_summary(result: dict):
    """打印沪深港通资金流总览"""
    if result.get('status') == 'error':
        print(f"  ❌ {result.get('message', '查询失败')}")
        return

    date = result.get('date', '')
    channels = result.get('channels', [])

    print(f"  📊 沪深港通资金流总览（{date}）")
    print("  " + "-" * 80)

    if not channels:
        print("  ℹ️  暂无明细数据")
        return

    # 按方向分组（akshare 只返回 北向/南向，其他方向做 fallback）
    northbound = [c for c in channels if c.get('direction') == '北向']
    southbound = [c for c in channels if c.get('direction') == '南向']
    other = [c for c in channels if c.get('direction') not in ('北向', '南向')]

    def _print_group(label, items):
        if not items:
            return
        print(f"\n  {label}")
        print(f"  {'通道':<14}{'净买额(亿)':<14}{'净流入(亿)':<14}{'余额(亿)':<14}{'上涨':<8}{'下跌':<8}{'指数':<12}{'涨跌%':<8}")
        print("  " + "-" * 86)
        for ch in items:
            name = ch.get('name', 'N/A')
            net_buy = _fmt_amount(ch.get('net_buy'))
            fund_inflow = _fmt_amount(ch.get('fund_inflow'))
            balance = _fmt_amount(ch.get('balance'))
            up = ch.get('up_count', 'N/A')
            down = ch.get('down_count', 'N/A')
            idx_name = ch.get('index_name', 'N/A')
            idx_pct = ch.get('index_change_pct')
            idx_pct_str = f"{idx_pct:.2f}" if idx_pct is not None else 'N/A'

            print(f"  {name:<14}{net_buy:<14}{fund_inflow:<14}{balance:<14}{str(up):<8}{str(down):<8}{idx_name:<12}{idx_pct_str:<8}")

        # 汇总
        total_net_buy = sum(c.get('net_buy') or 0 for c in items)
        total_inflow = sum(c.get('fund_inflow') or 0 for c in items)
        total_up = sum(c.get('up_count') or 0 for c in items)
        total_down = sum(c.get('down_count') or 0 for c in items)
        print(f"  {'合计':<14}{_fmt_amount(total_net_buy):<14}{_fmt_amount(total_inflow):<14}{'':<14}{str(total_up):<8}{str(total_down):<8}")

    _print_group("🟢 北向资金（外资买入A股）", northbound)
    if northbound:
        print("  ⚠️  北向净买额自 2024-08-19 起不再公布，以上数据仅供参考")
    _print_group("🔵 南向资金（内地买入港股）", southbound)
    _print_group("⚪ 其他", other)

    # 交易状态（过滤空值）
    statuses = {c.get('trade_status', '') for c in channels if c.get('trade_status')}
    if statuses:
        print(f"\n  交易状态: {', '.join(statuses)}")
    print()


@cf_app.command("summary")
def summary():
    """沪深港通资金流总览（返回所有方向数据）"""
    from fund_tools import get_capital_flow_summary

    print_banner()
    print("💰 沪深港通资金流总览")
    print()

    result = get_capital_flow_summary()
    print_capital_flow_summary(result)
