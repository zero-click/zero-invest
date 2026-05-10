
import os
for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

import akshare as ak

print("=== 港股搜索标普500 ===")
df = ak.stock_hk_spot_em()

# 搜索名称含"标普"的
sp = df[df['名称'].str.contains('标普', na=False)]
print("含'标普'的港股:")
for _, row in sp.iterrows():
    print(f"  {row['代码']} {row['名称']} 价格:{row.get('最新价','N/A')} 涨跌:{row.get('涨跌幅','N/A')}%")

# 搜索含"500"的
print("\n含'500'的港股:")
sp3 = df[df['名称'].str.contains('500', na=False)]
for _, row in sp3.iterrows():
    print(f"  {row['代码']} {row['名称']} 价格:{row.get('最新价','N/A')}")

# 搜索iShares
print("\n含'iShares'的港股:")
sp4 = df[df['名称'].str.contains('iShares|ishares|ISHARES', na=False, case=False)]
for _, row in sp4.iterrows():
    print(f"  {row['代码']} {row['名称']} 价格:{row.get('最新价','N/A')}")
