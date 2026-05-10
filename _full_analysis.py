#!/usr/bin/env python3
"""全量六步投资分析脚本 - 2026-05-08"""

import os
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

import akshare as ak
import pandas as pd
from datetime import date, datetime
import requests
import time
import warnings
warnings.filterwarnings('ignore')

# ====== STEP 2: 指数估值 ======
print("="*60)
print("STEP 2: 指数估值分位")
print("="*60)

# A股主要指数
index_codes = [
    ('000300', '沪深300'),
    ('000905', '中证500'),
    ('000922', '中证红利'),
    ('000016', '上证50'),
    ('000819', '中证有色金属'),
    ('930052', '中证机器人'),
    ('H30550', '沪港深通金融'),
    ('H11136', '中国互联网'),
]

for code, name in index_codes:
    try:
        df = ak.stock_zh_index_value_csindex(symbol=code)
        latest = df.iloc[0]
        pe = latest.get('市盈率1', 'N/A')
        pb = latest.get('市净率1', 'N/A')
        dy = latest.get('股息率1', 'N/A')
        # Calculate percentile
        pe_values = pd.to_numeric(df['市盈率1'], errors='coerce').dropna()
        if len(pe_values) > 0 and pe != 'N/A':
            pe_pct = (pe_values < float(pe)).sum() / len(pe_values) * 100
        else:
            pe_pct = -1
        print(f"  {name}({code}): PE={pe}, PB={pb}, 股息率={dy}, PE分位={pe_pct:.0f}%")
        time.sleep(0.5)
    except Exception as e:
        print(f"  {name}({code}): 获取失败 - {e}")

# S&P500 via eastmoney
try:
    resp = requests.get(
        "https://push2.eastmoney.com/api/qt/stock/get?secid=100.SPX&fields=f43,f44,f170",
        headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    d = resp.json().get('data', {})
    spx_price = d.get('f43', 0) / 100
    spx_chg = d.get('f170', 0) / 100
    print(f"  标普500: {spx_price:.0f} ({spx_chg:+.2f}%)")
except Exception as e:
    print(f"  标普500: 获取失败 - {e}")

# HSI via eastmoney
try:
    resp = requests.get(
        "https://push2.eastmoney.com/api/qt/stock/get?secid=100.HSI&fields=f43,f44,f170",
        headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
    d = resp.json().get('data', {})
    hsi_price = d.get('f43', 0) / 100
    hsi_chg = d.get('f170', 0) / 100
    print(f"  恒生指数: {hsi_price:.0f} ({hsi_chg:+.2f}%)")
except Exception as e:
    print(f"  恒生指数: 获取失败 - {e}")

# ====== STEP 3: 基金持仓健康检查 ======
print()
print("="*60)
print("STEP 3: 基金持仓健康检查")
print("="*60)

# Fund code mapping via name search
print("正在查找基金代码...")
name_map = ak.fund_name_em()

fund_mapping = {}
search_names = [
    ('华泰柏瑞中证红利低波ETF联接A', '红利低波'),
    ('汇添富丰润中短债A', '丰润中短债'),
    ('大成稳安60天滚动持有债券A', '大成稳安60'),
    ('华夏稳享增利6个月滚动持有债A', '华夏稳享增利'),
    ('汇添富沪深300安中指数A', '沪深300安中'),
    ('汇添富经典成长定开混合', '经典成长定开'),
    ('汇添富优质成长C', '优质成长C'),
    ('易方达上证50增强A', '上证50增强A'),
    ('易方达蓝筹精选混合', '蓝筹精选'),
    ('广发中证港股通非银ETF联接C', '港股通非银'),
    ('易方达中证海外互联网50ETF联接', '海外互联网50'),
    ('华夏中证电网设备主题ETF联接A', '电网设备'),
    ('华安黄金ETF联接A', '华安黄金'),
    ('天弘中证工业有色金属主题ETF联接A', '工业有色金属'),
    ('天弘中证机器人ETF联接A', '机器人'),
]

for full_name, short in search_names:
    for _, row in name_map.iterrows():
        if short in str(row['基金简称']):
            fund_mapping[short] = (row['基金代码'], row['基金简称'])
            print(f"  {short} -> {row['基金代码']} {row['基金简称']}")
            break
    if short not in fund_mapping:
        print(f"  {short} -> 未找到!")

# Get returns for equity & mixed funds
print()
print("--- 近1年/6月/3月收益 ---")
equity_shorts = ['红利低波', '沪深300安中', '经典成长定开', '优质成长C', 
                 '上证50增强A', '蓝筹精选', '港股通非银', '海外互联网50',
                 '电网设备', '华安黄金', '工业有色金属', '机器人']

for short in equity_shorts:
    if short not in fund_mapping:
        continue
    code, fname = fund_mapping[short]
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator='单位净值走势')
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        latest = df.iloc[-1]
        latest_date = latest['净值日期']
        latest_nav = float(latest['单位净值'])
        
        # Find points ~1yr, 6mo, 3mo ago
        yr_ago = latest_date - pd.Timedelta(days=365)
        mo6_ago = latest_date - pd.Timedelta(days=183)
        mo3_ago = latest_date - pd.Timedelta(days=92)
        
        yr_row = df[df['净值日期'] <= yr_ago].iloc[-1] if len(df[df['净值日期'] <= yr_ago]) > 0 else None
        mo6_row = df[df['净值日期'] <= mo6_ago].iloc[-1] if len(df[df['净值日期'] <= mo6_ago]) > 0 else None
        mo3_row = df[df['净值日期'] <= mo3_ago].iloc[-1] if len(df[df['净值日期'] <= mo3_ago]) > 0 else None
        
        ret_1y = (latest_nav - float(yr_row['单位净值'])) / float(yr_row['单位净值']) * 100 if yr_row is not None else float('nan')
        ret_6m = (latest_nav - float(mo6_row['单位净值'])) / float(mo6_row['单位净值']) * 100 if mo6_row is not None else float('nan')
        ret_3m = (latest_nav - float(mo3_row['单位净值'])) / float(mo3_row['单位净值']) * 100 if mo3_row is not None else float('nan')
        
        print(f"  {fname}: 1Y={ret_1y:+.1f}% 6M={ret_6m:+.1f}% 3M={ret_3m:+.1f}%")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {fname}: 获取失败 - {e}")

# ====== STEP 4: 资金流向 ======
print()
print("="*60)
print("STEP 4: 资金流向")
print("="*60)

# 南向资金
try:
    # 港股通沪
    df_sh = ak.stock_hsgt_hist_em(symbol='港股通沪')
    recent_sh = df_sh.tail(20)
    recent_sum_sh = pd.to_numeric(recent_sh['当日成交净买额'], errors='coerce').sum()
    
    # 港股通深
    df_sz = ak.stock_hsgt_hist_em(symbol='港股通深')
    recent_sz = df_sz.tail(20)
    recent_sum_sz = pd.to_numeric(recent_sz['当日成交净买额'], errors='coerce').sum()
    
    total = recent_sum_sh + recent_sum_sz
    print(f"  南向近20日净买入: ¥{total/1e8:.0f}亿 (沪:{recent_sum_sh/1e8:.0f}亿 + 深:{recent_sum_sz/1e8:.0f}亿)")
    
    # Monthly
    latest_date = pd.to_datetime(df_sz['日期']).max()
    month_start = latest_date.replace(day=1)
    month_sz = df_sz[pd.to_datetime(df_sz['日期']) >= month_start]
    month_sum_sz = pd.to_numeric(month_sz['当日成交净买额'], errors='coerce').sum()
    month_sh = df_sh[pd.to_datetime(df_sh['日期']) >= month_start]
    month_sum_sh = pd.to_numeric(month_sh['当日成交净买额'], errors='coerce').sum()
    month_total = month_sum_sh + month_sum_sz
    print(f"  南向当月净买入: ¥{month_total/1e8:.0f}亿")
    
    if month_total > 1000e8:
        print("  ⚠️ 月净买入>1000亿 → 🟢 港股看多信号(参考)")
    else:
        print("  月净买入未达1000亿阈值")
except Exception as e:
    print(f"  南向资金获取失败: {e}")

# ====== STEP 5: 行业景气度 ======
print()
print("="*60)
print("STEP 5: 行业景气度")
print("="*60)

# Check industry PE for relevant sectors
industry_indices = [
    ('399967', '中证军工'),
    ('930901', '中证机器人'),
    ('930707', '中证有色'),
    ('930708', '中证有色金属'),
    ('H30035', '中证钢铁'),
    ('399986', '中证银行'),
]

for code, name in industry_indices:
    try:
        df = ak.stock_zh_index_value_csindex(symbol=code)
        latest = df.iloc[0]
        pe = latest.get('市盈率1', 'N/A')
        pe_values = pd.to_numeric(df['市盈率1'], errors='coerce').dropna()
        if len(pe_values) > 0 and pe != 'N/A':
            pe_pct = (pe_values < float(pe)).sum() / len(pe_values) * 100
        else:
            pe_pct = -1
        print(f"  {name}: PE={pe}, PE分位={pe_pct:.0f}%")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {name}: 获取失败 - {e}")

# Additional industry check via CSRC
print()
print("--- 证监会行业PE快照(前15) ---")
try:
    df_ind = ak.stock_industry_pe_csrc()
    # It returns a dict of DataFrames by industry category
    if isinstance(df_ind, dict):
        all_pe = []
        for cat, d in df_ind.items():
            if isinstance(d, pd.DataFrame) and '行业名称' in d.columns:
                for _, row in d.iterrows():
                    all_pe.append((str(row['行业名称']), row.get('市盈率', 'N/A'), cat))
        # Show relevant ones
        relevant = ['有色','机器人','电网','互联网','金融','银行','半导体','计算机','传媒','电子']
        for item in all_pe:
            for kw in relevant:
                if kw in item[0]:
                    print(f"  [{item[2]}] {item[0]}: PE={item[1]}")
                    break
    else:
        print(f"  Unexpected type: {type(df_ind)}")
except Exception as e:
    print(f"  行业PE快照获取失败: {e}")

# ====== SUMMARY ======
print()
print("="*60)
print("分析完成")
print("="*60)
