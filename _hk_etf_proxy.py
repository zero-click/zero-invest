
import os, requests, json, numpy as np

# 试加代理
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'

print("=== 尝试通过代理拉港股K线 ===")

code = '02825'
secid = f"116.{code}"
try:
    resp = requests.get(
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6,f7&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500101&lmt=10",
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
        timeout=15
    )
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        data = resp.json()
        print(f"Name: {data.get('data',{}).get('name','N/A')}")
        print(f"Klines: {data.get('data',{}).get('klines',[])[:3]}")
except Exception as e:
    print(f"代理也失败: {e}")

# 清除代理,试yahoo finance API
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

print("\n=== 试用港交所API ===")
try:
    # 港交所没有公开API, 试用其他源
    # 用Finnhub (可能需要key)
    # 用hk.finance.yahoo.com
    resp = requests.get(
        "https://query1.finance.yahoo.com/v8/finance/chart/2825.HK?range=3mo&interval=1d",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        meta = data.get('chart',{}).get('result',[{}])[0].get('meta',{})
        print(f"Yahoo: {meta.get('symbol','N/A')} price={meta.get('regularMarketPrice','N/A')}")
        indicators = data.get('chart',{}).get('result',[{}])[0].get('indicators',{})
        closes = indicators.get('quote',[{}])[0].get('close',[])
        if closes:
            print(f"Recent closes: {closes[-5:]}")
    else:
        print(f"Yahoo HTTP {resp.status_code}")
except Exception as e:
    print(f"Yahoo: {e}")

# 试香港雅虎
print("\n=== 试用hk.yahoo ===")
try:
    os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
    codes_to_check = ['2825.HK', '6969.HK', '3110.HK', '2800.HK', '0700.HK']
    for sym in codes_to_check:
        resp = requests.get(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10
        )
        if resp.status_code == 200:
            data = resp.json()
            meta = data.get('chart',{}).get('result',[{}])[0].get('meta',{})
            price = meta.get('regularMarketPrice', 'N/A')
            prev = meta.get('previousClose', 'N/A')
            chg = ((price/prev)-1)*100 if price and prev and prev > 0 else 'N/A'
            print(f"  {sym}: {price} HKD ({chg:+.2f}%)" if isinstance(chg, float) else f"  {sym}: {price}")
        else:
            print(f"  {sym}: HTTP {resp.status_code}")
except Exception as e:
    print(f"Yahoo proxy: {e}")
