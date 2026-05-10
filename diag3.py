import akshare as ak, os, time
for k in list(os.environ.keys()):
    if k.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY'):
        os.environ.pop(k, None)

# Search for 优质成长C
df = ak.fund_name_em()
matched = df[df['基金简称'].str.contains('优质成长', na=False)]
print("=== 优质成长 matches ===")
print(matched[['基金代码','基金简称','基金类型']].to_string())

# Check what symbols stock_index_pe_lg supports
print("\n=== Testing stock_index_pe_lg symbols ===")
symbols_to_test = ['000300', '000016', '000922', '000823', '399006']
for s in symbols_to_test:
    try:
        df = ak.stock_index_pe_lg(symbol=s)
        time.sleep(0.2)
        print(f"  {s}: OK, rows={len(df)}")
    except Exception as e:
        print(f"  {s}: FAIL - {e}")
