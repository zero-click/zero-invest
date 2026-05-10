
import os, re, json, time

# === Part 1: S&P500 估值 (需代理) ===
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'

import requests
headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

print("=== 标普500估值 ===")

# 用multpl.com的API端点
urls = {
    'PE': 'https://www.multpl.com/s-p-500-pe-ratio',
    'Shiller PE': 'https://www.multpl.com/shiller-pe', 
    '股息率': 'https://www.multpl.com/s-p-500-dividend-yield',
}

results = {}
for name, url in urls.items():
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 200:
            # 提取font标签中的数值
            nums = re.findall(r'<font[^>]*>\s*([\d.]+)%?\s*</font>', resp.text)
            # 提取描述文字中的信息
            info = re.findall(r'<b>([^<]+)</b>\s*(?:is|was)\s*(?:currently at\s*)?<font[^>]*>([^<]+)</font>', resp.text)
            if nums:
                results[name] = nums[0]
                print(f"{name}: {nums[0]}")
            else:
                # 尝试其他pattern
                nums2 = re.findall(r'([\d.]+)', resp.text[resp.text.find('<body'):resp.text.find('<body')+2000] if '<body' in resp.text else resp.text[:3000])
                if nums2:
                    results[name] = nums2[0]
                    print(f"{name}: {nums2[0]} (alt)")
        else:
            print(f"{name}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"{name}: 失败 - {e}")

# === Part 2: 2845.HK 行情 (用web直接拉) ===
# 清除代理
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

print("\n=== 2845.HK / 2840.HK / 3140.HK 行情 ===")

# 用东方财富港股单个查询
hk_codes = {
    '02845': 'iShares Core S&P 500',
    '02840': 'SPDR S&P 500', 
    '03140': '南方东英标普500',
}

for code, name in hk_codes.items():
    try:
        # 东方财富港股实时行情API
        secid = f"116.{code}"
        resp = requests.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60,f116,f117,f162,f170,f171",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=10
        )
        if resp.status_code == 200:
            d = resp.json().get('data', {})
            if d:
                price = d.get('f43', 0) / 1000 if d.get('f43') else 'N/A'
                change_pct = d.get('f170', 0) / 100 if d.get('f170') else 'N/A'
                high = d.get('f44', 0) / 1000 if d.get('f44') else 'N/A'
                low = d.get('f45', 0) / 1000 if d.get('f45') else 'N/A'
                open_ = d.get('f46', 0) / 1000 if d.get('f46') else 'N/A'
                volume = d.get('f47', 0) or 'N/A'
                amount = d.get('f48', 0) or 'N/A'
                name_cn = d.get('f58', name)
                mktcap = d.get('f116', 0) or 'N/A'
                pe = d.get('f162', 0) / 100 if d.get('f162') else 'N/A'
                
                print(f"\n{code} {name_cn}:")
                print(f"  最新价: {price} HKD")
                print(f"  涨跌幅: {change_pct}%")
                print(f"  开盘: {open_} | 最高: {high} | 最低: {low}")
                print(f"  成交量: {volume} | 成交额: {amount}")
                if mktcap != 'N/A':
                    print(f"  市值: {mktcap/1e8:.1f}亿")
                if pe != 'N/A':
                    print(f"  PE: {pe}")
    except Exception as e:
        print(f"{code}: 失败 - {e}")

# === Part 3: S&P 500 近期走势 ===
print("\n=== S&P 500 (.SPX) 近期走势 ===")
try:
    secid = "100.SPX"
    resp = requests.get(
        f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f60,f170",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    if resp.status_code == 200:
        d = resp.json().get('data', {})
        if d:
            print(f"指数: {d.get('f58', 'S&P 500')}")
            print(f"最新: {d.get('f43', 'N/A')/100 if d.get('f43') else 'N/A'}")
            print(f"涨跌幅: {d.get('f170', 'N/A')/100 if d.get('f170') else 'N/A'}%")
except Exception as e:
    print(f"S&P500行情失败: {e}")

# === Part 4: 用akshare快速拉标普500历史数据算分位 ===
print("\n=== S&P 500 PE历史分位 ===")
try:
    import akshare as ak
    # 用index_pe_hist拉标普500历史PE
    df = ak.index_us_stock_sina(symbol=".INX")
    if df is not None and len(df) > 0:
        latest = df.iloc[-1]
        print(f"标普500最新收盘: {latest.get('close', latest.get('收盘', 'N/A'))}")
        print(f"日期: {latest.get('date', latest.get('日期', 'N/A'))}")
except Exception as e:
    print(f"akshare标普失败: {e}")

print("\n=== 完成 ===")
