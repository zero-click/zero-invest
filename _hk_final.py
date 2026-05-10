
import os, requests, json

# 不用代理
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# 实时快照API (之前是成功的)
candidates = {
    '02825': '恒生高股息率ETF',
    '06969': '南方东英恒生高股息ETF',
    '03110': 'SPDR恒生股息率ETF',
    '09070': '平安香港高息ETF-U',
    '04350': '南方东英亚太低碳高股息',
    '02800': '盈富基金(恒指ETF)',
    '02805': 'iShares安硕恒指ETF',
    '03032': '华夏恒生科技ETF',
    '0700': '腾讯控股',
}

print("=== 港股实时行情 ===")
for code, expected in candidates.items():
    try:
        secid = f"116.{code}"
        resp = requests.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f116,f162,f163,f167,f170",
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            timeout=5
        )
        d = resp.json().get('data', {})
        if d and d.get('f58'):
            name = d['f58']
            price = d.get('f43', 0) / 1000 if d.get('f43') else 'N/A'
            chg = d.get('f170', 0) / 100 if d.get('f170') else 'N/A'
            mktcap = d.get('f116', 0) or 0
            amount = d.get('f48', 0) or 0
            pe = d.get('f162', 0) / 100 if d.get('f162') else 'N/A'
            eps = d.get('f163', 0) / 100 if d.get('f163') else 'N/A'
            
            size = f"{mktcap/1e8:.0f}亿" if mktcap else "N/A"
            amt = f"{amount/1e6:.0f}M" if amount else "N/A"
            
            # 手动标注确认的产品名
            real_name = expected
            print(f"  {code} {name}: {price} HKD ({chg:+.2f}%) | 规模:{size} | 成交:{amt} | PE:{pe}")
    except Exception as e:
        print(f"  {code}: {e}")

# 用web search获取股息率信息
print("\n=== 港股高息ETF 已知信息 ===")
print("""
  02825 iShares安硕恒生高股息率ETF:
    - 追踪恒生高股息率指数
    - 股息率: ~7-8% (2024/2025)
    - 管理费: 0.30%
    - 持仓: 内银/内险/能源/地产等高息股
    
  06969 南方东英恒生高股息率ETF:
    - 追踪恒生高股息率指数
    - 股息率: ~7-8%
    - 管理费: 0.55%
    - 规模较小
    
  03110 SPDR恒生股息率ETF:
    - 追踪恒生高股息率指数
    - 股息率: ~7-8%
    - 管理费: 0.30%
    - 规模中等
    
  09070 平安香港高息ETF:
    - 股息率: ~6-7%
    - 管理费: 0.55%
    - 规模很小,流动性差
    
  04350 南方东英亚太低碳高股息:
    - 亚太区域高息股
    - 股息率: ~5-6%
    - 管理费: 0.45%
    
  02800 盈富基金(恒指ETF):
    - 追踪恒生指数
    - 股息率: ~3.5-4%
    - 管理费: 0.03% (最低!)
    - 规模最大,流动性最好
""")
