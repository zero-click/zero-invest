
import os, re, json

# === Part 1: S&P 500 估值 (需代理) ===
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'

import requests
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# S&P 500 PE - multpl.com
print("=== 标普500估值 (multpl.com) ===")
try:
    resp = requests.get('https://www.multpl.com/s-p-500-pe-ratio', headers=headers, timeout=20)
    text = resp.text
    # 打印前5000字符分析结构
    # 找所有含有数字的span/p标签
    # 尝试更精确的提取
    # multpl.com usually has: <div id="current"><h1>S&P 500 PE Ratio</h1><font>XX.XX</font>
    current_section = text[text.find('id="current"'):text.find('id="current"')+2000] if 'id="current"' in text else text[:5000]
    
    # Extract all numbers from current section
    nums = re.findall(r'>([\d.]+)<', current_section)
    print(f"Current section numbers: {nums[:10]}")
    
    # 也试试提取描述
    descs = re.findall(r'<p[^>]*>([^<]+)</p>', current_section)
    for d in descs[:5]:
        if any(c.isdigit() for c in d):
            print(f"Description: {d.strip()}")
            
except Exception as e:
    print(f"multpl PE失败: {e}")

# 试用ycharts API
print("\n=== 标普500估值 (ycharts) ===")
try:
    resp = requests.get('https://ycharts.com/indicators/sp_500_pe_ratio', headers=headers, timeout=15)
    if resp.status_code == 200:
        pe_match = re.search(r'([\d.]+)\s*\(as of', resp.text)
        if pe_match:
            print(f"当前PE: {pe_match.group(1)}")
except:
    pass

# 用gurufocus
print("\n=== 标普500估值 (gurufocus) ===")
try:
    resp = requests.get('https://www.gurufocus.com/term/PE10/SP500/Shiller-PE/SPX', headers=headers, timeout=15)
    if resp.status_code == 200:
        # Extract Shiller PE
        nums = re.findall(r'font-weight:bold[^>]*>([\d.]+)<', resp.text)
        if nums:
            print(f"Shiller PE: {nums[0]}")
except Exception as e:
    print(f"gurufocus失败: {e}")

# === Part 2: 用东方财富直接查S&P 500指数 ===
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

print("\n=== S&P 500 指数 ===")
try:
    resp = requests.get(
        "https://push2.eastmoney.com/api/qt/stock/get?secid=100.SPX&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f116,f117,f162,f170,f171",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    d = resp.json().get('data', {})
    if d:
        price = d.get('f43', 0)
        chg = d.get('f170', 0)
        name = d.get('f58', '')
        print(f"{name}: {price/100:.2f} ({chg/100:.2f}%)")
except Exception as e:
    print(f"SPX失败: {e}")

# === Part 3: 查询已知的港股标普500 ETF ===
# 港股标普500 ETF的正确代码:
# 需要确认: 港股的iShares Core S&P 500 ETF 代码实际是 2845.HK (2845.HK在港交所)
# 但东方财富市场代码116可能映射不对
# 让我试不同的市场代码

print("\n=== 尝试不同市场代码查港股标普ETF ===")
# 港股市场代码可能是: 116 (港交所)
# ETF搜索
import itertools

# 已知港股标普500ETF:
# iShares Core S&P 500 ETF: HKEX 2845
# 南方东英标普500: 可能在HKEX
# 让我用港交所的搜索

for code in ['02845', '02840']:
    for mkt in ['116', '128', '129']:  # 不同港股市场代码
        try:
            secid = f"{mkt}.{code}"
            resp = requests.get(
                f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f57,f58,f170",
                headers={'User-Agent': 'Mozilla/5.0'},
                timeout=5
            )
            d = resp.json().get('data', {})
            if d and d.get('f58'):
                print(f"  {mkt}.{code}: {d['f58']} 价格:{d.get('f43',0)/1000 if d.get('f43') else 'N/A'}")
        except:
            pass

# 最后手段: 用web_extract
print("\n=== 用akshare单只查询 ===")
try:
    import akshare as ak
    # 单只港股行情
    df = ak.stock_hk_hist(symbol='02845', period='daily', adjust='qfq')
    if df is not None and len(df) > 0:
        latest = df.iloc[-1]
        print(f"02845 最新数据: 日期={latest.get('日期','N/A')} 收盘={latest.get('收盘','N/A')}")
except Exception as e:
    print(f"akshare 02845失败: {e}")

try:
    df2 = ak.stock_hk_hist(symbol='02840', period='daily', adjust='qfq')
    if df2 is not None and len(df2) > 0:
        latest = df2.iloc[-1]
        print(f"02840 最新数据: 日期={latest.get('日期','N/A')} 收盘={latest.get('收盘','N/A')} 名称={latest.get('股票名称','N/A')}")
except Exception as e:
    print(f"akshare 02840失败: {e}")
