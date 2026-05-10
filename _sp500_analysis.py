
import os
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

import akshare as ak
import requests

# 1. 标普500 QDII基金净值和收益
print("=== 标普500 QDII基金行情 ===")
sp500_funds = [
    ('050025', '博时标普500ETF联接A'),
    ('006075', '博时标普500ETF联接C'),
    ('007721', '天弘标普500A'),
    ('012860', '易方达标普500C'),
    ('017641', '摩根标普500A'),
    ('017028', '国泰标普500ETF联接A'),
    ('018064', '华夏标普500ETF联接A'),
    ('018738', '博时标普500ETF联接E'),
]

for code, name in sp500_funds:
    try:
        df = ak.fund_open_fund_info_em(symbol=code, indicator="单位净值走势")
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            price = latest['单位净值']
            date = latest['净值日期']
            ret_1m = ret_3m = ret_6m = ret_1y = 'N/A'
            if len(df) > 22:
                ret_1m = f"{(price/df.iloc[-22]['单位净值']-1)*100:.2f}%"
            if len(df) > 66:
                ret_3m = f"{(price/df.iloc[-66]['单位净值']-1)*100:.2f}%"
            if len(df) > 132:
                ret_6m = f"{(price/df.iloc[-132]['单位净值']-1)*100:.2f}%"
            if len(df) > 250:
                ret_1y = f"{(price/df.iloc[-250]['单位净值']-1)*100:.2f}%"
            print(f"  {code} {name}: 净值={price:.4f} ({date}) 1m:{ret_1m} 3m:{ret_3m} 6m:{ret_6m} 1y:{ret_1y}")
    except Exception as e:
        print(f"  {code} {name}: {e}")

# 2. S&P 500指数
print("\n=== S&P 500 指数 ===")
try:
    resp = requests.get(
        "https://push2.eastmoney.com/api/qt/stock/get?secid=100.SPX&fields=f43,f44,f45,f46,f57,f58,f60,f170",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    d = resp.json().get('data', {})
    if d:
        price = d.get('f43',0)/100
        chg = d.get('f170',0)/100
        name = d.get('f58','')
        print(f"  {name}: {price:.2f} ({chg:.2f}%)")
except Exception as e:
    print(f"  SPX: {e}")

# 3. 标普500估值分位 (需代理)
print("\n=== 标普500估值分位 ===")
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'
try:
    from portfolio_analysis import get_us_index_valuation
    val = get_us_index_valuation()
    if val:
        for k, v in val.items():
            print(f"  {k}: {v}")
    else:
        print("  返回空")
except Exception as e:
    print(f"  估值失败: {e}")

# 4. 基金费率
print("\n=== 费率对比 ===")
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)
    
for code, name in sp500_funds[:6]:
    try:
        info = ak.fund_individual_basic_info_xq(symbol=code)
        if info is not None and len(info) > 0:
            mgmt = info[info['item'] == '管理费率']['value'].values
            custody = info[info['item'] == '托管费率']['value'].values
            service = info[info['item'] == '销售服务费率']['value'].values
            m = mgmt[0] if len(mgmt) else 'N/A'
            c = custody[0] if len(custody) else 'N/A'
            s = service[0] if len(service) else '0'
            print(f"  {code} {name}: 管理={m} 托管={c} 销售服务={s}")
    except Exception as e:
        print(f"  {code}: {e}")
