
import os
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

import akshare as ak

# 方法: 用akshare的港股ETF基金列表
print("=== 搜索港股标普500 ETF ===")

# 试 stock_hk_index_spot_em (港股指数)
try:
    df = ak.stock_hk_index_spot_em()
    if df is not None and len(df) > 0:
        print("港股指数列表:")
        sp = df[df['名称'].str.contains('标普|S&P|SP 500|500', na=False, case=False)]
        for _, row in sp.iterrows():
            print(f"  {row.get('代码','')} {row.get('名称','')} {row.get('最新价','')}")
except Exception as e:
    print(f"指数列表失败: {e}")

# 试 fund_etf_category_em (ETF基金分类)
print("\n=== 搜索QDII标普500基金 ===")
try:
    df = ak.fund_etf_category_em(symbol="QDII基金")
    if df is not None and len(df) > 0:
        sp = df[df['名称'].str.contains('标普', na=False)]
        print(f"QDII中标普基金 ({len(sp)}只):")
        for _, row in sp.iterrows():
            print(f"  {row.get('基金代码','')} {row.get('名称','')} 价格:{row.get('最新价','')} 涨跌:{row.get('涨跌幅','')}%")
except Exception as e:
    print(f"QDII ETF失败: {e}")

# 也可以直接搜 fund_name_em
print("\n=== 搜索所有基金中标普500 ===")
try:
    df = ak.fund_name_em()
    sp = df[df['基金简称'].str.contains('标普500', na=False)]
    print(f"共{len(sp)}只标普500基金:")
    for _, row in sp.head(20).iterrows():
        print(f"  {row['基金代码']} {row['基金简称']} {row.get('基金类型','')}")
except Exception as e:
    print(f"fund_name失败: {e}")
