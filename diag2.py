import akshare as ak
import os
for k in list(os.environ.keys()):
    if k.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY'):
        os.environ.pop(k, None)

print("=== stock_industry_pe_ratio_cninfo ===")
try:
    df = ak.stock_industry_pe_ratio_cninfo()
    print("Type:", type(df))
    if hasattr(df, 'columns'):
        print("Columns:", df.columns.tolist())
    print(df.head(5))
except Exception as e:
    print("Error:", e)

print()
print("=== stock_index_pe_lg ===")
try:
    df2 = ak.stock_index_pe_lg(symbol='上证50')
    print("Type:", type(df2))
    if hasattr(df2, 'columns'):
        print("Columns:", df2.columns.tolist())
    print(df2.tail(5))
except Exception as e:
    print("Error:", e)
