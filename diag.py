import akshare as ak
import os
for k in list(os.environ.keys()):
    if k.upper() in ('HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY'):
        os.environ.pop(k, None)

# Check fund_name_em
df = ak.fund_name_em()
print("Columns:", list(df.columns))
print("Shape:", df.shape)
print("Head:")
print(df.head(2).to_string())

# Check industry PE function
funcs = [f for f in dir(ak) if 'industry' in f.lower() or 'pe' in f.lower()]
print("\nFunctions with industry/PE:")
for f in funcs:
    print(f"  {f}")
