
import os, re, json, requests

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# 用akshare查港股ETF历史数据, 确认真实身份
import akshare as ak

print("=== 用akshare确认港股ETF身份 ===")

# 这些是确认的高息ETF代码(港交所)
etf_list = {
    '02825': 'iShares安硕恒生高股息率ETF (预期)',
    '06969': '南方东英恒生高股息率ETF (预期)',
    '03110': 'SPDR恒生股息率ETF (预期)',
    '09070': '平安香港高息ETF-U (预期)',
    '04350': '南方东英亚太低碳高股息 (预期)',
    '02800': '盈富基金(恒指ETF) (预期)',
    '02805': 'iShares安硕恒生指数ETF (预期)',
    '03032': '华夏恒生科技ETF (预期)',
}

for code, expected in etf_list.items():
    try:
        df = ak.stock_hk_hist(symbol=code, period='daily', adjust='', start_date='20260401', end_date='20260510')
        if df is not None and len(df) > 0:
            latest = df.iloc[-1]
            # 取近30天数据算波动和收益
            first = df.iloc[0]
            ret = (latest['收盘'] / first['开盘'] - 1) * 100
            print(f"\n  {code} {expected}")
            print(f"    最新收盘: {latest['收盘']} HKD ({latest['日期']})")
            print(f"    4月以来涨幅: {ret:.1f}%")
            print(f"    成交额(最新): {latest.get('成交额', 'N/A')}")
            
            # 算近期波动
            if len(df) >= 5:
                rets = [(df.iloc[i]['收盘']/df.iloc[i-1]['收盘']-1)*100 for i in range(1, min(20, len(df)))]
                import numpy as np
                vol = np.std(rets) if rets else 0
                print(f"    日波动率: {vol:.2f}%")
                max_p = df['收盘'].max()
                min_p = df['收盘'].min()
                print(f"    4月最高: {max_p} | 最低: {min_p}")
    except Exception as e:
        print(f"  {code}: {e}")

# 用akshare搜香港ETF
print("\n=== 搜索港股ETF - 高股息 ===")
try:
    # 搜索ETF列表
    df = ak.fund_etf_hist_em(symbol="02825", period="daily", adjust="", start_date="20260401", end_date="20260510")
    if df is not None:
        print(f"  02825 最新: {df.iloc[-1]['收盘']} ({df.iloc[-1]['日期']})")
except:
    pass
