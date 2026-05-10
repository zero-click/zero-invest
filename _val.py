import akshare as ak
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

indices = [
    ("000300", "沪深300"),
    ("000905", "中证500"),
    ("000016", "上证50"),
    ("000819", "中证有色金属"),
    ("930052", "中证机器人"),
    ("H30550", "沪港深通金融"),
    ("000922", "中证红利"),
]

for code, name in indices:
    try:
        df = ak.stock_zh_index_value_csindex(symbol=code)
        latest = df.iloc[0]
        pe = latest.get("市盈率1", "N/A")
        pb = latest.get("市净率1", "N/A")
        dy = latest.get("股息率1", "N/A")
        pe_vals = pd.to_numeric(df["市盈率1"], errors="coerce").dropna()
        pct = (pe_vals < float(pe)).sum() / len(pe_vals) * 100 if len(pe_vals) > 0 and pe != "N/A" else -1
        print(f"{name}|PE={pe}|PB={pb}|DY={dy}|PE%={pct:.0f}")
    except Exception as e:
        print(f"{name}|ERR:{e}")
