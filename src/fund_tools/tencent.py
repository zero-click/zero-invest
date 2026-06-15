# -*- coding: utf-8 -*-
"""腾讯财经API行情模块 — 纯HTTP, 不封IP, 批量查询"""

import urllib.request
from typing import Optional


def tencent_quote(codes: list[str]) -> dict[str, dict]:
    """腾讯财经批量行情

    GET https://qt.gtimg.cn/q=sh600519,sz000001
    idx31=涨跌额, idx32=涨跌幅, idx38=换手率, idx39=PE(TTM),
    idx43=振幅, idx44=总市值(亿), idx45=流通市值(亿), idx46=PB,
    idx47=涨停价, idx48=跌停价, idx49=量比, idx52=PE(静)
    """
    if not codes:
        return {}

    prefixed = [_prefix(c) for c in codes]
    url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read().decode("gbk", errors="replace")

    results = {}
    for line in raw.strip().split("\n"):
        if "=" not in line:
            continue
        try:
            var_part, value_part = line.split("=", 1)
            qt_code = var_part.split("_")[-1]
            code = qt_code[2:]
            fields = value_part.strip('";\n').split("~")
            if len(fields) < 50:
                continue
            results[code] = _parse(code, fields)
        except (ValueError, IndexError):
            continue
    return results


def tencent_spot(code: str) -> Optional[dict]:
    """单只股票腾讯行情"""
    results = tencent_quote([code])
    return results.get(code)


def _prefix(code: str) -> str:
    if code.startswith("6"):
        return "sh" + code
    elif code.startswith("0") or code.startswith("3"):
        return "sz" + code
    elif code.startswith("8"):
        return "bj" + code
    return "sz" + code


def _parse(code: str, f: list[str]) -> dict:
    def flt(i):
        try:
            return float(f[i]) if i < len(f) and f[i] else None
        except (ValueError, IndexError):
            return None

    name = f[1] if len(f) > 1 else ""
    pe_ttm = flt(39)
    pe_static = flt(52)
    total_mv = flt(44)
    float_mv = flt(45)
    pb = flt(46)

    return {
        "代码": code,
        "名称": name,
        "最新价": flt(3),
        "涨跌额": flt(31),
        "涨跌幅": flt(32),
        "换手率": flt(38),
        "市盈率": pe_ttm or pe_static,
        "市盈率(TTM)": pe_ttm,
        "市盈率(静)": pe_static,
        "市净率": pb,
        "总市值": total_mv * 1e8 if total_mv else None,
        "流通市值": float_mv * 1e8 if float_mv else None,
        "振幅": flt(43),
        "涨停价": flt(47),
        "跌停价": flt(48),
        "量比": flt(49),
    }
