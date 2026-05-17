#!/usr/bin/env python3
"""获取基金收益数据和行业估值快照"""
import time
import sys
import datetime as dt
import os

# 清除代理
for k in list(os.environ.keys()):
    if k.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY'):
        os.environ.pop(k, None)

import akshare as ak
import pandas as pd

# ====== 基金名称列表 ======
fund_names = [
    "华泰柏瑞中证红利低波ETF联接A",
    "汇添富沪深300安中指数A",
    "易方达蓝筹精选混合",
    "广发中证港股通非银ETF联接C",
    "易方达中证海外互联网50ETF联接",
    "华安黄金ETF联接A",
    "天弘中证工业有色金属主题ETF联接A",
    "天弘中证机器人ETF联接A",
    "易方达上证50增强A",
    "汇添富优质成长C",
    "华夏中证电网设备主题ETF联接A",
    "汇添富经典成长定开混合",
]

# ====== Step 1: 搜索基金代码 ======
print("=== 搜索基金代码 ===")
fund_codes = {}
for name in fund_names:
    try:
        df = ak.fund_name_em()
        matched = df[df['基金名称'].str.contains(name.replace("ETF联接A", "").replace("ETF联接C", "").replace("定开混合", "").strip(), na=False)]
        if len(matched) == 0:
            matched = df[df['基金名称'].str.contains(name[:6], na=False)]
        if len(matched) > 0:
            code = str(matched.iloc[0]['基金代码'])
            full_name = matched.iloc[0]['基金名称']
            fund_codes[name] = (code, full_name)
            print(f"  {name} -> {code} ({full_name})")
        else:
            print(f"  {name} -> 未找到")
        time.sleep(0.2)
    except Exception as e:
        print(f"  {name} -> 错误: {e}")

print(f"\n共找到 {len(fund_codes)} 只基金")

# ====== Step 2: 获取净值并计算收益 ======
today = dt.date.today()
yr_ago = today - dt.timedelta(days=365)
mon6_ago = today - dt.timedelta(days=183)
mon3_ago = today - dt.timedelta(days=92)

print(f"\n今天: {today}")
print(f"近1年目标日期: {yr_ago}")
print(f"近6月目标日期: {mon6_ago}")
print(f"近3月目标日期: {mon3_ago}")

print("\n=== 获取净值并计算收益 ===")
results = []
for name, (code, full_name) in fund_codes.items():
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator='单位净值走势')
        time.sleep(0.2)
        
        if df is None or len(df) == 0:
            results.append((name, "无数据", "", "", "净值数据为空"))
            continue
        
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期').reset_index(drop=True)
        
        latest = df.iloc[-1]
        latest_date = latest['净值日期']
        latest_nav = float(latest['单位净值'])
        
        def find_closest(df, target_date):
            df_before = df[df['净值日期'] <= pd.Timestamp(target_date)]
            if len(df_before) > 0:
                return df_before.iloc[-1]
            return None
        
        row_1y = find_closest(df, yr_ago)
        row_6m = find_closest(df, mon6_ago)
        row_3m = find_closest(df, mon3_ago)
        
        ret_1y = ((latest_nav - float(row_1y['单位净值'])) / float(row_1y['单位净值']) * 100) if row_1y is not None else None
        ret_6m = ((latest_nav - float(row_6m['单位净值'])) / float(row_6m['单位净值']) * 100) if row_6m is not None else None
        ret_3m = ((latest_nav - float(row_3m['单位净值'])) / float(row_3m['单位净值']) * 100) if row_3m is not None else None
        
        ret_1y_str = f"{ret_1y:+.2f}%" if ret_1y is not None else "N/A"
        ret_6m_str = f"{ret_6m:+.2f}%" if ret_6m is not None else "N/A"
        ret_3m_str = f"{ret_3m:+.2f}%" if ret_3m is not None else "N/A"
        
        note = f"最新净值:{latest_nav:.4f} 日期:{str(latest_date)[:10]}"
        results.append((name, ret_1y_str, ret_6m_str, ret_3m_str, note))
        print(f"  {name}: 1Y={ret_1y_str} 6M={ret_6m_str} 3M={ret_3m_str} | {note}")
        
    except Exception as e:
        results.append((name, "错误", "", "", str(e)[:80]))
        print(f"  {name} -> 错误: {e}")

# ====== Step 3: 获取行业PE ======
print("\n=== 行业PE (证监会分类) ===")
try:
    df_pe = ak.stock_industry_pe_csrc()
    time.sleep(0.2)
    
    keywords = ['有色', '机器人', '电网', '互联网', '金融', '银行', '保险', '证券', '黄金', '红利', '煤炭', '钢铁', '电力', '非银', '酒', '饮料', '上证50', '沪深300']
    for kw in keywords:
        matched = df_pe[df_pe['行业名称'].str.contains(kw, na=False)]
        if len(matched) > 0:
            for _, row in matched.iterrows():
                print(f"  {row['行业名称']}: PE={row.get('市盈率', 'N/A')}, 日期={row.get('日期', 'N/A')}")
except Exception as e:
    print(f"  行业PE获取失败: {e}")

# ====== 最终输出 ======
print("\n" + "="*80)
print("基金名|1Y|6M|3M|备注")
print("-"*80)
for r in results:
    print(f"{r[0]}|{r[1]}|{r[2]}|{r[3]}|{r[4]}")
print("="*80)
