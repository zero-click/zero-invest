
import os, requests

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# 东方财富实时行情里有每手股数信息(f55)
codes = {
    '02800': '盈富基金',
    '03110': 'SPDR恒生股息',
    '03032': '恒生科技ETF',
    '0700': '腾讯控股',
}

for code, name in codes.items():
    try:
        secid = f"116.{code}"
        resp = requests.get(
            f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f55,f58,f170",
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'},
            timeout=5
        )
        d = resp.json().get('data', {})
        if d and d.get('f58'):
            name_cn = d['f58']
            price = d.get('f43', 0) / 1000 if d.get('f43') else 0
            lot = d.get('f55', 0)  # 每手股数
            chg = d.get('f170', 0) / 100 if d.get('f170') else 0
            lot_cost = price * lot if price and lot else 0
            print(f"  {code} {name_cn}: 价格{price} HKD | 每手{lot}股 | 一手={lot_cost:.0f} HKD | 今日{chg:+.2f}%")
    except Exception as e:
        print(f"  {code}: {e}")
