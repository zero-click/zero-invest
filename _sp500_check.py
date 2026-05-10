
import os, sys, re, json
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'
import requests

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

# 1. 拉取标普500 PE
print("=== 标普500估值 ===")
try:
    resp = requests.get('https://www.multpl.com/s-p-500-pe-ratio', headers=headers, timeout=20)
    if resp.status_code == 200:
        # 尝试提取当前PE
        pe_match = re.search(r'id="current"[^>]*>([^<]+)', resp.text)
        if not pe_match:
            pe_match = re.search(r'pe-ratio.*?<font[^>]*>([^<]+)', resp.text)
        if not pe_match:
            # 更宽泛的匹配
            pe_match = re.search(r'([\d.]+)\s*<', resp.text[:3000])
        
        # 提取中间的大数字
        all_nums = re.findall(r'<font[^>]*>\s*([\d.]+)\s*</font>', resp.text)
        if all_nums:
            print(f"当前PE: {all_nums[0]}")
        
        # 提取日期
        date_match = re.search(r'As of[^>]*>([^<]+)<', resp.text)
        if date_match:
            print(f"日期: {date_match[1]}")
        
        # 提取mean和median
        mean_match = re.findall(r'Mean:.*?<font[^>]*>([^<]+)<', resp.text)
        median_match = re.findall(r'Median:.*?<font[^>]*>([^<]+)<', resp.text)
        if mean_match:
            print(f"历史均值: {mean_match[0]}")
        if median_match:
            print(f"历史中位数: {median_match[0]}")
        
        # 打印前2000字符供debug
        # print(resp.text[:2000])
except Exception as e:
    print(f"PE请求失败: {e}")

# 2. Shiller PE (CAPE)
print("\n=== Shiller PE (CAPE) ===")
try:
    resp2 = requests.get('https://www.multpl.com/shiller-pe', headers=headers, timeout=20)
    if resp2.status_code == 200:
        nums2 = re.findall(r'<font[^>]*>\s*([\d.]+)\s*</font>', resp2.text)
        if nums2:
            print(f"当前Shiller PE: {nums2[0]}")
except Exception as e:
    print(f"Shiller PE请求失败: {e}")

# 3. S&P 500 股息率
print("\n=== 标普500股息率 ===")
try:
    resp3 = requests.get('https://www.multpl.com/s-p-500-dividend-yield', headers=headers, timeout=20)
    if resp3.status_code == 200:
        nums3 = re.findall(r'<font[^>]*>\s*([\d.]+)%?\s*</font>', resp3.text)
        if nums3:
            print(f"当前股息率: {nums3[0]}%")
except Exception as e:
    print(f"股息率请求失败: {e}")

# 4. 用akshare拉2845.HK的行情（清除代理）
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

print("\n=== 2845.HK 行情 ===")
try:
    import akshare as ak
    # 个股实时行情
    df = ak.stock_hk_spot_em()
    target = df[df['代码'] == '02845']
    if len(target) > 0:
        row = target.iloc[0]
        print(f"名称: {row.get('名称', 'N/A')}")
        print(f"最新价: {row.get('最新价', 'N/A')}")
        print(f"涨跌幅: {row.get('涨跌幅', 'N/A')}%")
        print(f"涨跌额: {row.get('涨跌额', 'N/A')}")
        print(f"今开: {row.get('今开', 'N/A')}")
        print(f"最高: {row.get('最高', 'N/A')}")
        print(f"最低: {row.get('最低', 'N/A')}")
        print(f"成交量: {row.get('成交量', 'N/A')}")
        print(f"成交额: {row.get('成交额', 'N/A')}")
    else:
        print("未找到02845")
        # 搜索
        matches = df[df['名称'].str.contains('标普', na=False) | df['名称'].str.contains('S&P', na=False) | df['名称'].str.contains('SP', na=False)]
        if len(matches) > 0:
            print("相关标的:")
            for _, m in matches.iterrows():
                print(f"  {m['代码']} {m['名称']} 价格:{m.get('最新价','N/A')}")
except Exception as e:
    print(f"2845行情失败: {e}")

# 5. 对比港股其他标普500 ETF
print("\n=== 港股标普500 ETF对比 ===")
try:
    codes = ['02845', '02840', '03140']
    for code in codes:
        target = df[df['代码'] == code]
        if len(target) > 0:
            row = target.iloc[0]
            print(f"{row['代码']} {row['名称']}: 价格={row.get('最新价','N/A')}, 涨跌幅={row.get('涨跌幅','N/A')}%")
except Exception as e:
    print(f"对比失败: {e}")
