#!/usr/bin/env python3
"""获取基金收益数据和行业估值快照 v2"""
import time, sys, datetime as dt, os, warnings
warnings.filterwarnings('ignore')

for k in list(os.environ.keys()):
    if k.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY'):
        os.environ.pop(k, None)

import akshare as ak
import pandas as pd

# ====== Step 1: 搜索基金代码 ======
print("=== 搜索基金代码 ===")
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

df_all = ak.fund_name_em()
time.sleep(0.2)

fund_codes = {}
for name in fund_names:
    try:
        # Try exact match first
        matched = df_all[df_all['基金简称'] == name]
        if len(matched) == 0:
            # Try contains match
            search_term = name.replace("ETF联接A", "").replace("ETF联接C", "").replace("定开混合", "").strip()
            matched = df_all[df_all['基金简称'].str.contains(search_term[:8], na=False)]
        if len(matched) > 0:
            code = str(matched.iloc[0]['基金代码'])
            full_name = matched.iloc[0]['基金简称']
            fund_codes[name] = (code, full_name)
            print(f"  {name} -> {code} ({full_name})")
        else:
            print(f"  {name} -> 未找到")
    except Exception as e:
        print(f"  {name} -> 错误: {e}")

print(f"\n共找到 {len(fund_codes)} 只基金")

# ====== Step 2: 获取净值并计算收益 ======
today = dt.date.today()
yr_ago = today - dt.timedelta(days=365)
mon6_ago = today - dt.timedelta(days=183)
mon3_ago = today - dt.timedelta(days=92)

print(f"\n今天: {today}")

print("\n=== 获取净值并计算收益 ===")
results = []
for name, (code, full_name) in fund_codes.items():
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator='单位净值走势')
        time.sleep(0.3)
        
        if df is None or len(df) == 0:
            results.append((name, "无数据", "", "", "净值数据为空"))
            continue
        
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期').reset_index(drop=True)
        
        latest = df.iloc[-1]
        latest_date = latest['净值日期']
        latest_nav = float(latest['单位净值'])
        
        yr_ago_ts = pd.Timestamp(yr_ago)
        mon6_ago_ts = pd.Timestamp(mon6_ago)
        mon3_ago_ts = pd.Timestamp(mon3_ago)
        
        # Find closest dates <= target
        df_yr = df[df['净值日期'] <= yr_ago_ts]
        df_6m = df[df['净值日期'] <= mon6_ago_ts]
        df_3m = df[df['净值日期'] <= mon3_ago_ts]
        
        if len(df_yr) > 0:
            nav_yr = float(df_yr.iloc[-1]['单位净值'])
            ret_1y = (latest_nav - nav_yr) / nav_yr * 100
            ret_1y_str = f"{ret_1y:+.2f}%"
        else:
            ret_1y_str = "N/A"
            
        if len(df_6m) > 0:
            nav_6m = float(df_6m.iloc[-1]['单位净值'])
            ret_6m = (latest_nav - nav_6m) / nav_6m * 100
            ret_6m_str = f"{ret_6m:+.2f}%"
        else:
            ret_6m_str = "N/A"
            
        if len(df_3m) > 0:
            nav_3m = float(df_3m.iloc[-1]['单位净值'])
            ret_3m = (latest_nav - nav_3m) / nav_3m * 100
            ret_3m_str = f"{ret_3m:+.2f}%"
        else:
            ret_3m_str = "N/A"
        
        note = f"净值:{latest_nav:.4f}@{str(latest_date)[:10]}"
        results.append((name, ret_1y_str, ret_6m_str, ret_3m_str, note))
        print(f"  {name}: 1Y={ret_1y_str} 6M={ret_6m_str} 3M={ret_3m_str} | {note}")
        
    except Exception as e:
        results.append((name, "错误", "", "", str(e)[:100]))
        print(f"  {name} -> 错误: {e}")

# ====== Step 3: 获取行业PE ======
print("\n=== 行业指数PE (乐咕乐股/中证) ===")
indexes = {
    '上证50': '000016',
    '沪深300': '000300',
    '中证红利': '000922',
    '中证有色': '000823',
    '中证机器人': 'H30590',
    '中证互联网': 'H30536',
    '中证金融': '000934',
    '中证电力': '000937',
    '创业板指': '399006',
}
try:
    for idx_name in indexes:
        try:
            df_pe = ak.stock_index_pe_lg(symbol=idx_name)
            time.sleep(0.3)
            if df_pe is not None and len(df_pe) > 0:
                latest_pe = df_pe.iloc[-1]
                pe_val = latest_pe.get('滚动市盈率', 'N/A')
                pe_date = str(latest_pe.get('日期', ''))[:10]
                print(f"  {idx_name}: PE(TTM)={pe_val}, 日期={pe_date}")
        except Exception as e:
            print(f"  {idx_name}: 获取失败 - {e}")
except Exception as e:
    print(f"  行业PE获取失败: {e}")

# ====== 最终输出 ======
print("\n" + "="*90)
print(f"{'基金名':<32} | {'1Y':>8} | {'6M':>8} | {'3M':>8} | 备注")
print("-"*90)
for r in results:
    print(f"{r[0]:<32} | {r[1]:>8} | {r[2]:>8} | {r[3]:>8} | {r[4]}")
print("="*90)
