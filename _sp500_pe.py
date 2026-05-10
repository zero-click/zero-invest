
import os

# 用已知的S&P500 earnings数据估算PE
# S&P 500 当前 ~5650, 2024年EPS ~$240 -> forward PE ~23.5
# 但现在是2026年5月, S&P500 = 7259

# 试用yfinance
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:10810'
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:10810'

print("=== 标普500估值 ===")
try:
    import yfinance as yf
    sp500 = yf.Ticker("^GSPC")
    info = sp500.info
    print(f"  trailingPE: {info.get('trailingPE', 'N/A')}")
    print(f"  forwardPE: {info.get('forwardPE', 'N/A')}")
    print(f"  trailingEps: {info.get('trailingEps', 'N/A')}")
    print(f"  forwardEps: {info.get('forwardEps', 'N/A')}")
    print(f"  priceToBook: {info.get('priceToBook', 'N/A')}")
    print(f"  dividendYield: {info.get('dividendYield', 'N/A')}")
except ImportError:
    print("  yfinance未安装")
except Exception as e:
    print(f"  yfinance: {e}")

# 备用: 直接用requests拉multpl的页面,打印原始HTML分析
print("\n=== multpl.com HTML分析 ===")
import requests
try:
    resp = requests.get('https://www.multpl.com/s-p-500-pe-ratio', 
                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'},
                        timeout=20)
    # 打印关键区域
    text = resp.text
    # 找所有 <b> 标签
    import re
    bolds = re.findall(r'<b>([^<]+)</b>', text[:10000])
    print(f"  Bold texts: {bolds[:15]}")
    
    # 找所有数字模式
    nums = re.findall(r'\b(\d{1,2}\.\d{1,3})\b', text[:5000])
    print(f"  Numbers in first 5000: {nums[:20]}")
    
    # 找 h1/h2 标签
    headers_tag = re.findall(r'<h[12][^>]*>([^<]+)</h[12]>', text[:5000])
    print(f"  Headers: {headers_tag}")
    
    # 打印前1000字符
    print(f"\n  First 1000 chars:\n{text[:1000]}")
except Exception as e:
    print(f"  multpl: {e}")
