
import os, re, json, requests

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# === 1. 腾讯 0700.HK 实时行情 ===
print("=== 腾讯控股 0700.HK ===")
try:
    resp = requests.get(
        "https://push2.eastmoney.com/api/qt/stock/get?secid=116.00700&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f163,f167,f168,f170,f171,f292",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    d = resp.json().get('data', {})
    if d:
        price = d.get('f43', 0)
        price_hkd = price / 1000 if price else 'N/A'
        chg_pct = d.get('f170', 0) / 100 if d.get('f170') else 'N/A'
        high = d.get('f44', 0) / 1000 if d.get('f44') else 'N/A'
        low = d.get('f45', 0) / 1000 if d.get('f45') else 'N/A'
        open_ = d.get('f46', 0) / 1000 if d.get('f46') else 'N/A'
        volume = d.get('f47', 0) or 'N/A'
        amount = d.get('f48', 0) or 'N/A'
        name = d.get('f58', 'N/A')
        mktcap = d.get('f116', 0) or 'N/A'
        pe = d.get('f162', 0) / 100 if d.get('f162') else 'N/A'
        pb = d.get('f167', 0) / 100 if d.get('f167') else 'N/A'
        turnover = d.get('f168', 0) / 100 if d.get('f168') else 'N/A'
        eps = d.get('f163', 0) / 100 if d.get('f163') else 'N/A'
        
        print(f"  名称: {name}")
        print(f"  最新价: {price_hkd} HKD")
        print(f"  涨跌幅: {chg_pct}%")
        print(f"  开盘: {open_} | 最高: {high} | 最低: {low}")
        print(f"  成交量: {volume}")
        print(f"  成交额: {amount}")
        if mktcap != 'N/A':
            print(f"  总市值: {mktcap/1e8:.0f}亿 (港币)")
            print(f"  总市值: ~{mktcap/1e8/7.8:.0f}亿 (美元)")
            print(f"  总市值: ~{mktcap/1e8/0.92:.0f}亿 (人民币)")
        print(f"  PE(TTM): {pe}")
        print(f"  PB: {pb}")
        print(f"  EPS: {eps}")
        print(f"  换手率: {turnover}%")
except Exception as e:
    print(f"  行情失败: {e}")

# === 2. 腾讯近期K线 (近60日) ===
print("\n=== 腾讯近60日走势 ===")
try:
    resp = requests.get(
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=116.00700&fields1=f1,f2,f3,f4,f5,f6,f7&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500101&lmt=60",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    data = resp.json().get('data', {})
    klines = data.get('klines', [])
    if klines:
        # 最近5天
        print("  最近5个交易日:")
        for k in klines[-5:]:
            parts = k.split(',')
            print(f"    {parts[0]}: 开{parts[1]} 收{parts[2]} 高{parts[3]} 低{parts[4]} 量{parts[5]}")
        
        # 算区间收益
        first_close = float(klines[0].split(',')[2])
        last_close = float(klines[-1].split(',')[2])
        ret = (last_close / first_close - 1) * 100
        
        # 近20日
        d20_close = float(klines[-20].split(',')[2]) if len(klines) >= 20 else first_close
        ret_20 = (last_close / d20_close - 1) * 100
        
        print(f"\n  近60日收益: {ret:.1f}%")
        print(f"  近20日收益: {ret_20:.1f}%")
        print(f"  60日区间: {klines[0].split(',')[0]} -> {klines[-1].split(',')[0]}")
        
        # 近60日最高最低
        highs = [float(k.split(',')[3]) for k in klines]
        lows = [float(k.split(',')[4]) for k in klines]
        print(f"  60日最高: {max(highs)}")
        print(f"  60日最低: {min(lows)}")
except Exception as e:
    print(f"  K线失败: {e}")

# === 3. 港股通资金流向 (腾讯) ===
print("\n=== 南向资金近期 ===")
try:
    import akshare as ak
    # 沪港通
    df_sh = ak.stock_hsgt_hist_em(symbol="港股通沪")
    df_sz = ak.stock_hsgt_hist_em(symbol="港股通深")
    
    # 最近5个交易日
    if df_sh is not None and len(df_sh) > 0:
        print("  沪港通最近5日:")
        for _, row in df_sh.tail(5).iterrows():
            date = row.get('日期', row.iloc[0])
            net = row.get('当日成交净买额', 'N/A')
            print(f"    {date}: 净买额 {net}")
    
    if df_sz is not None and len(df_sz) > 0:
        print("  深港通最近5日:")
        for _, row in df_sz.tail(5).iterrows():
            date = row.get('日期', row.iloc[0])
            net = row.get('当日成交净买额', 'N/A')
            print(f"    {date}: 净买额 {net}")
except Exception as e:
    print(f"  南向资金: {e}")

# === 4. 恒生指数估值参考 ===
print("\n=== 恒生指数 ===")
try:
    resp = requests.get(
        "https://push2.eastmoney.com/api/qt/stock/get?secid=100.HSI&fields=f43,f44,f45,f46,f57,f58,f170",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    d = resp.json().get('data', {})
    if d:
        price = d.get('f43', 0) / 100
        chg = d.get('f170', 0) / 100
        print(f"  恒生指数: {price:.2f} ({chg:+.2f}%)")
except:
    pass
