
import os, re, json, requests

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# 港股高股息ETF - 查主要标的
# 常见港股高息ETF:
# 2822.HK - iShares FTSE High Dividend Yield ETF
# 2837.HK - Global X DCM China High Dividend Yield ETF 
# 3110.HK - SPDR S&P Asia Pacific Dividend
# 4350.HK - 南方东英银河联昌富时亚太低碳高股息
# 900.HK - AAOFFEE HK High Dividend 
# 8318.HK - 招商局商业房地产投资信托基金
# 02825 - 标智香港100
# 02820 - iShares 安硕A50中国指数ETF
# 2800.HK - 盈富基金 (恒指ETF)
# 2825.HK - iShares安硕恒生高股息率ETF
# 6969.HK - 南方东英恒生高股息率ETF
# 2855.HK - iShares安硕恒生科技ETF

# 先查一批可能的高息ETF
hk_codes = [
    '02825',  # iShares安硕恒生高股息率ETF
    '06969',  # 南方东英恒生高股息率ETF
    '02822',  # iShares FTSE High Dividend
    '02837',  # Global X 中国高股息
    '02800',  # 盈富基金(恒指)
    '02820',  # iShares A50
    '02805',  # iShares安硕恒生指数ETF
    '03032',  # 南方东英恒生指数ETF
    '04350',  # 南方东英亚太低碳高股息
    '03110',  # SPDR亚太高股息
    '08318',  # 南方东英华夏港股通高股息
    '09070',  # 华夏港股通高股息
    '03456',  # 南方东英华泰柏瑞中证红利低波
    '02845',  # 之前确认是GX中国电车
    '03040',  # 之前确认是GX中国
]

print("=== 港股ETF行情查询 ===")
for code in hk_codes:
    try:
        secid = f"116.{code}"
        resp = requests.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f116,f162,f167,f170",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        d = resp.json().get('data', {})
        if d and d.get('f58'):
            name = d['f58']
            price = d.get('f43', 0)
            price = price / 1000 if price else 'N/A'
            chg = d.get('f170', 0)
            chg = chg / 100 if chg else 'N/A'
            mktcap = d.get('f116', 0) or 0
            pe = d.get('f162', 0) / 100 if d.get('f162') else 'N/A'
            volume = d.get('f47', 0) or 0
            amount = d.get('f48', 0) or 0
            size_info = f"市值{mktcap/1e8:.1f}亿" if mktcap > 0 else ""
            vol_info = f"成交{amount/1e6:.1f}M" if amount > 0 else ""
            print(f"  {code} {name}: {price} HKD ({chg:+.2f}%) PE:{pe} {size_info} {vol_info}")
    except:
        pass

# 也查几个大蓝筹个股的股息率作参考
print("\n=== 港股高息蓝筹参考 ===")
blue_chips = {
    '00005': '汇丰控股',
    '01299': 'AIA',
    '00016': '新鸿基地产',
    '00011': '恒生银行',
    '00003': '香港中华煤气',
    '00941': '中国移动',
    '03988': '中国银行',
    '01398': '工商银行',
    '00883': '中海油',
}
for code, expected_name in blue_chips.items():
    try:
        secid = f"116.{code}"
        resp = requests.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f58,f162,f170",
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=5
        )
        d = resp.json().get('data', {})
        if d and d.get('f58'):
            name = d['f58']
            price = d.get('f43', 0) / 1000 if d.get('f43') else 'N/A'
            chg = d.get('f170', 0) / 100 if d.get('f170') else 'N/A'
            pe = d.get('f162', 0) / 100 if d.get('f162') else 'N/A'
            print(f"  {code} {name}: {price} HKD ({chg:+.2f}%) PE:{pe}")
    except:
        pass
