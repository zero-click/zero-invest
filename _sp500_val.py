
import os, sys
sys.path.insert(0, '/Users/woosley/code/ttjj-fund')

# 标普500估值 (需代理)
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'

try:
    from portfolio_analysis import get_us_index_valuation
    val = get_us_index_valuation()
    print("=== 标普500估值 ===")
    if val:
        for k, v in val.items():
            print(f"  {k}: {v}")
    else:
        print("  返回空")
except Exception as e:
    print(f"  估值失败: {e}")
    import traceback
    traceback.print_exc()
