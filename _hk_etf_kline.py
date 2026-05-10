
import os, re, json, requests
import numpy as np

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# 用东方财富K线API拉港股ETF数据
def get_hk_kline(code, days=60):
    """拉取港股K线"""
    secid = f"116.{code}"
    resp = requests.get(
        f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1,f2,f3,f4,f5,f6,f7&fields2=f51,f52,f53,f54,f55,f56,f57&klt=101&fqt=1&end=20500101&lmt={days}",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=10
    )
    data = resp.json().get('data', {})
    name = data.get('name', 'N/A')
    klines = data.get('klines', [])
    return name, klines

def get_hk_snapshot(code):
    """港股实时快照"""
    secid = f"116.{code}"
    resp = requests.get(
        f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f57,f58,f116,f162,f167,f170",
        headers={'User-Agent': 'Mozilla/5.0'},
        timeout=5
    )
    return resp.json().get('data', {})

# 港股高股息ETF候选
candidates = {
    # 确认是高息ETF的:
    '02825': 'iShares安硕恒生高股息率ETF',
    '06969': '南方东英恒生高股息率ETF', 
    '03110': 'SPDR恒生股息率ETF',
    '09070': '平安香港高息-U',
    '04350': '南方东英亚太低碳高股息',
    # 对比基准:
    '02800': '盈富基金(恒指ETF)',
    '02805': 'iShares安硕恒指ETF',
    '03032': '华夏恒生科技ETF',
}

print("=== 港股高股息ETF对比 ===\n")

results = []
for code, expected_name in candidates.items():
    try:
        name, klines = get_hk_kline(code, 120)
        snap = get_hk_snapshot(code)
        
        if not klines:
            print(f"  {code} {expected_name}: 无K线数据")
            continue
        
        latest = klines[-1].split(',')
        first = klines[0].split(',')
        
        price = float(latest[2])
        date = latest[0]
        
        # 收益率计算
        ret_60d = (price / float(first[2]) - 1) * 100
        ret_20d = (price / float(klines[-20].split(',')[2]) - 1) * 100 if len(klines) >= 20 else 0
        ret_5d = (price / float(klines[-5].split(',')[2]) - 1) * 100 if len(klines) >= 5 else 0
        
        # 波动率
        closes = [float(k.split(',')[2]) for k in klines]
        daily_rets = [(closes[i]/closes[i-1]-1)*100 for i in range(1, len(closes))]
        vol = np.std(daily_rets) if daily_rets else 0
        
        # 最高最低
        high_60 = max([float(k.split(',')[3]) for k in klines])
        low_60 = min([float(k.split(',')[4]) for k in klines])
        
        # 成交额(最新)
        amount = float(latest[6]) if latest[6] else 0
        avg_amount = np.mean([float(k.split(',')[6]) for k in klines[-20]]) if len(klines) >= 20 else amount
        
        # 市值
        mktcap = snap.get('f116', 0) or 0
        
        # PE
        pe = snap.get('f162', 0)
        pe = pe / 100 if pe else 'N/A'
        
        print(f"  {code} {name}")
        print(f"    价格: {price} HKD ({date})")
        print(f"    涨跌: 5日{ret_5d:+.1f}% | 20日{ret_20d:+.1f}% | 60日{ret_60d:+.1f}%")
        print(f"    波动率(日): {vol:.2f}%")
        print(f"    60日高/低: {high_60} / {low_60}")
        print(f"    日均成交: {avg_amount/1e6:.1f}M HKD")
        if mktcap:
            print(f"    规模: {mktcap/1e8:.1f}亿")
        print(f"    PE: {pe}")
        print()
        
        results.append({
            'code': code, 'name': name, 'price': price,
            'ret_60d': ret_60d, 'vol': vol, 'avg_amount': avg_amount,
            'mktcap': mktcap, 'high_60': high_60, 'low_60': low_60
        })
    except Exception as e:
        print(f"  {code} {expected_name}: {e}\n")

# 综合评分
print("=" * 50)
print("=== 综合对比表 ===")
print(f"{'代码':<8} {'名称':<25} {'价格':>8} {'60日涨':>8} {'波动率':>8} {'日均成交M':>10} {'规模亿':>8}")
for r in results:
    mcap = f"{r['mktcap']/1e8:.0f}" if r['mktcap'] else 'N/A'
    print(f"{r['code']:<8} {r['name']:<25} {r['price']:>8.2f} {r['ret_60d']:>+7.1f}% {r['vol']:>7.2f}% {r['avg_amount']/1e6:>9.1f} {mcap:>8}")
