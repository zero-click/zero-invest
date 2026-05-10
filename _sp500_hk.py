
import os, re, json

# 清除代理
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

import requests

# 港股标普500 ETF正确的代码：
# 2840.HK = SPDR S&P 500 ETF (但看起来02840在东方财富里是SPDR金...)
# 让我搜索一下

print("=== 搜索港股标普500相关ETF ===")

# 用东方财富搜索
try:
    # 搜索关键词
    resp = requests.get(
        "https://searchapi.eastmoney.com/api/suggest/get?input=标普500&type=116&token=D43BF722C8E33BDC906FB84D85E326E8&count=20",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get('QuotationCodeTable', {}).get('Data', []):
            code = item.get('Code', '')
            name = item.get('Name', '')
            mkt = item.get('MktNum', '')
            if '116' in str(mkt) or 'hk' in str(mkt).lower():
                print(f"  {mkt}.{code} = {name}")
except Exception as e:
    print(f"搜索失败: {e}")

# 也搜索SPY
print("\n=== 搜索SPY ===")
try:
    resp = requests.get(
        "https://searchapi.eastmoney.com/api/suggest/get?input=SPY&type=116&token=D43BF722C8E33BDC906FB84D85E326E8&count=20",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get('QuotationCodeTable', {}).get('Data', []):
            code = item.get('Code', '')
            name = item.get('Name', '')
            mkt = item.get('MktNum', '')
            print(f"  {mkt}.{code} = {name}")
except Exception as e:
    print(f"搜索失败: {e}")

# 搜索S&P 500
print("\n=== 搜索S&P ===")
try:
    resp = requests.get(
        "https://searchapi.eastmoney.com/api/suggest/get?input=S%26P&type=116&token=D43BF722C8E33BDC906FB84D85E326E8&count=20",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    if resp.status_code == 200:
        data = resp.json()
        for item in data.get('QuotationCodeTable', {}).get('Data', []):
            code = item.get('Code', '')
            name = item.get('Name', '')
            mkt = item.get('MktNum', '')
            print(f"  {mkt}.{code} = {name}")
except Exception as e:
    print(f"搜索失败: {e}")

# 直接查几个已知的港股标普ETF代码
print("\n=== 直接查询已知的港股标普ETF ===")
known_codes = {
    '02845': 'iShares Core S&P 500 HKD ETF?',  # 实际上是GX中国电车?
    '02840': 'SPDR S&P 500?',  # SPDR金?
    '03140': '华夏标普?',
    '03042': '南方东英标普500?',
    '00733': 'iShares S&P 500?',
    '02825': 'iShares S&P 500?',
    '03040': '南方东英标普500?',
    '03042': '南方东英标普500?',
}

for code, expected in known_codes.items():
    try:
        secid = f"116.{code}"
        resp = requests.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f57,f58,f170",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        if resp.status_code == 200:
            d = resp.json().get('data', {})
            if d and d.get('f58'):
                name = d['f58']
                price = d.get('f43', 0)
                price = price / 1000 if price else 'N/A'
                chg = d.get('f170', 0)
                chg = chg / 100 if chg else 'N/A'
                print(f"  {code}: {name} | 价格:{price} | 涨跌:{chg}%")
    except:
        pass
