
import os, sys
sys.path.insert(0, '/Users/woosley/code/ttjj-fund')

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

import requests

# 1. S&P 500 当前价格
print("=== S&P 500 指数 ===")
resp = requests.get(
    "https://push2.eastmoney.com/api/qt/stock/get?secid=100.SPX&fields=f43,f44,f45,f46,f57,f58,f60,f170",
    headers={'User-Agent': 'Mozilla/5.0'},
    timeout=10
)
d = resp.json().get('data', {})
if d:
    price = d.get('f43',0)/100
    chg = d.get('f170',0)/100
    print(f"  S&P 500: {price:.2f} ({chg:+.2f}%)")

# 2. 用multpl.com拉PE (需代理)
print("\n=== S&P 500 PE (multpl.com) ===")
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'

import requests as req2

# 试用简单的JSON API
try:
    resp2 = req2.get('https://www.multpl.com/api/table/pe-ratio.json', timeout=15)
    if resp2.status_code == 200:
        data = resp2.json()
        if isinstance(data, list) and len(data) > 0:
            latest = data[0]
            print(f"  PE: {latest}")
        elif isinstance(data, dict):
            print(f"  PE: {data}")
    else:
        print(f"  API HTTP {resp2.status_code}")
except Exception as e:
    print(f"  JSON API: {e}")

# 试直接爬HTML
try:
    resp3 = req2.get('https://www.multpl.com/s-p-500-pe-ratio', 
                     headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}, 
                     timeout=20)
    if resp3.status_code == 200:
        text = resp3.text
        # 找 "is currently" 或类似描述
        import re
        # Pattern: "XX.XX (X mon DD, YYYY)"
        m = re.search(r'([\d.]+)\s*\(.*?\d{4}\)', text[:5000])
        if m:
            print(f"  当前PE: {m.group(1)}")
        
        # 找 mean/median
        mean_m = re.search(r'Mean:\s*([\d.]+)', text)
        med_m = re.search(r'Median:\s*([\d.]+)', text)
        if mean_m:
            print(f"  历史均值: {mean_m.group(1)}")
        if med_m:
            print(f"  历史中位数: {med_m.group(1)}")
        
        # 打印前3000看看结构
        # print(text[:3000])
        
        # 找 all numbers in first 3000 chars
        nums = re.findall(r'>(\d{1,2}\.\d{1,2})<', text[:5000])
        print(f"  提取到的数字: {nums[:10]}")
except Exception as e:
    print(f"  HTML爬取: {e}")

# 3. 用 wsj 或其他API
print("\n=== S&P 500 估值 (其他源) ===")
try:
    # 试用stooq
    resp4 = req2.get('https://stooq.com/q/?s=^spx&c=1y&t=l&a=lg&b=0', timeout=15)
    if resp4.status_code == 200:
        print(f"  stooq: HTTP {resp4.status_code}, len={len(resp4.text)}")
except Exception as e:
    print(f"  stooq: {e}")

# 4. 清除代理，查基金费率
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

print("\n=== 基金费率 (fund_tool_akshare) ===")
try:
    from src.fund_tools.core import get_fund_fee_details
    for code, name in [('050025','博时标普500ETF联接A'), ('018738','博时标普500ETF联接E'), ('017641','摩根标普500A')]:
        result = get_fund_fee_details(code)
        if result.get('status') == 'success':
            fees = result.get('费用明细', {})
            print(f"\n  {code} {name}:")
            print(f"    管理费率: {fees.get('管理费率', 'N/A')}")
            print(f"    托管费率: {fees.get('托管费率', 'N/A')}")
            sub_fee = fees.get('申购费率', {})
            red_fee = fees.get('赎回费率', {})
            if sub_fee:
                print(f"    申购费率: {sub_fee}")
            if red_fee:
                print(f"    赎回费率: {red_fee}")
except Exception as e:
    print(f"  费率: {e}")
    import traceback
    traceback.print_exc()
