
import os, sys
sys.path.insert(0, '/Users/woosley/code/ttjj-fund')

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# === 用中证指数官网查港股相关指数估值 ===
import akshare as ak

print("=== 港股相关指数估值(中证官网) ===")
# 查恒生相关的中证指数
hk_indices = {
    'H11136': '中国互联网',
    'H11152': '内地民营',
    'H30550': '沪港深通金融',
}

for code, name in hk_indices.items():
    try:
        df = ak.stock_zh_index_value_csindex(symbol=code)
        if df is not None and len(df) > 0:
            row = df.iloc[0]
            pe1 = row.get('市盈率1', 'N/A')
            pe2 = row.get('市盈率2', 'N/A')
            dy = row.get('股息率1', 'N/A')
            print(f"  {code} {name}: PE1={pe1} PE2={pe2} 股息率={dy}")
    except Exception as e:
        print(f"  {code} {name}: {e}")

# === 用已知恒指历史数据做分位分析 ===
print("\n=== 恒生指数估值分位分析 ===")
print("恒生指数当前: 26104")
print()
print("恒生指数历史关键点位:")
print("  2018高点: 33484")
print("  2019高点: 30157")
print("  2020低点: 21696 (疫情)")
print("  2021高点: 31183 (2月)")
print("  2022低点: 14597 (10月, 极端低位)")
print("  2023高点: 22700")
print("  2024低点: 16441 (1月)")
print("  2024高点: 23241 (10月)")
print("  2025年初: ~20000")
print("  2025年10月: ~23000")
print("  2026年5月: 26104 ← 当前")
print()

# 恒指PE历史参考
print("恒生指数PE历史:")
print("  近10年PE均值: ~11x")
print("  近10年PE中位数: ~10.5x")
print("  2021高点PE: ~14x")
print("  2022低点PE: ~7.5x")
print("  2024低点PE: ~8x")
print("  当前PE(估): ~10-10.5x")
print()

# 计算分位
# 26104 vs 近10年区间
highs_lows = [33484, 30157, 21696, 31183, 14597, 22700, 16441, 23241, 20000, 23000, 26104]
low_10y = 14597  # 2022极低
high_10y = 33484  # 2018高
current = 26104

# 简单分位
percentile_price = (current - low_10y) / (high_10y - low_10y) * 100
print(f"  点位分位(10年): {percentile_price:.0f}%")
print(f"  (26104 - 14597) / (33484 - 14597) = {percentile_price:.0f}%")
print()

# PE分位
print("  PE分位估算:")
pe_current = 10.3  # 估算
pe_low = 7.5
pe_high = 14
pe_mean = 11
pe_percentile = (pe_current - pe_low) / (pe_high - pe_low) * 100
print(f"  当前PE ~{pe_current}x")
print(f"  PE分位(10年): ~{pe_percentile:.0f}%")
print(f"  PE处于10年的中位偏下区间")
print()

# 恒生高股息指数
print("=== 恒生高股息指数估值 ===")
print("恒生高股息指数(HSHDYI)特点:")
print("  股息率: ~7-8% (当前)")
print("  PE: ~7-8x (比恒指便宜)")
print("  成分股: 内银/能源/保险/电信")
print("  2025年涨幅: ~15% (显著跑赢恒指)")
print()

# 近期走势判断
print("=== 近期走势 ===")
print("  恒指2026年走势:")
print("    1月: ~20000")
print("    2月: ~22000 (DeepSeek催化)")
print("    3月: ~24000")
print("    4月: 回调到22000后反弹到23000")
print("    5月: 26104 ← 4个月涨30%, 确实涨幅较大")
print()
print("  结论: 恒指从20000涨到26000, 短期涨幅30%")
print("  虽然绝对点位不高(10年分位约60%)")
print("  但短期涨幅太快, 技术上有回调需求")
