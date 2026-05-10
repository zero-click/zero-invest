
import os, sys
sys.path.insert(0, '/Users/woosley/code/ttjj-fund')

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

import akshare as ak
import requests

# === 1. 恒生指数历史PE/PB ===
print("=== 恒生指数估值 ===")
try:
    # 中证指数官网查港股指数
    # 恒生指数代码在港交所是HSI
    # 用akshare的港股指数估值
    df = ak.stock_zh_index_value_csindex(symbol="H30550")  # 沪港深通金融
    if df is not None:
        print(f"沪港深通金融: {df.iloc[0].to_dict()}")
except Exception as e:
    print(f"中证港股指数: {e}")

# === 2. 用恒指历史数据算分位 ===
print("\n=== 恒生指数历史点位 ===")
try:
    # 用东方财富拉恒指历史(如果还能用)
    resp = requests.get(
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=100.HSI&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57&klt=102&fqt=1&end=20500101&lmt=120",
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
        timeout=15
    )
    if resp.status_code == 200:
        data = resp.json().get('data', {})
        klines = data.get('klines', [])
        if klines:
            print(f"恒指月线数据: {len(klines)}个月")
            for k in klines[-12:]:
                parts = k.split(',')
                print(f"  {parts[0]}: {parts[2]}")
            
            # 算10年分位
            closes = [float(k.split(',')[2]) for k in klines]
            import numpy as np
            current = closes[-1]
            percentile = sum(1 for c in closes if c < current) / len(closes) * 100
            print(f"\n  当前恒指: {current}")
            print(f"  10年分位: {percentile:.0f}%")
            print(f"  10年最高: {max(closes)}")
            print(f"  10年最低: {min(closes)}")
            print(f"  10年中位数: {np.median(closes):.0f}")
        else:
            print("无月线数据")
    else:
        print(f"HTTP {resp.status_code}")
except Exception as e:
    print(f"恒指月线: {e}")

# === 3. 拉近2年周线 ===
print("\n=== 恒生指数周线(近2年) ===")
try:
    resp = requests.get(
        "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=100.HSI&fields1=f1,f2,f3&fields2=f51,f52,f53,f54,f55,f56,f57&klt=102&fqt=1&end=20500101&lmt=24",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=15
    )
    if resp.status_code == 200:
        data = resp.json().get('data', {})
        klines = data.get('klines', [])
        if klines:
            for k in klines[-12:]:
                parts = k.split(',')
                print(f"  {parts[0]}: 收{parts[2]}")
except Exception as e:
    print(f"周线: {e}")
