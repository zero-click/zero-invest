# -*- coding: utf-8 -*-

import requests
import json
import re
import os
import argparse
from datetime import datetime
import numpy as np

# --- 常量定义 ---
FUND_CODE_LIST_URL = "https://fund.eastmoney.com/js/fundcode_search.js"
FUND_DB_FILE = "fund_database.json"
FUND_DETAIL_API_TPL = "https://fund.eastmoney.com/pingzhongdata/{code}.js"

# --- 核心功能函数 ---

def update_fund_database():
    """下载最新的 fundcode_search.js 文件, 解析并生成本地的 fund_database.json"""
    print("正在从天天基金网下载最新的基金列表...")
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    try:
        response = requests.get(FUND_CODE_LIST_URL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"网络错误: 无法下载基金列表。 {e}"}

    match = re.search(r"var r = (.*\]);", response.text)
    if not match:
        return {"status": "error", "message": "解析错误: 无法在返回的内容中找到基金数据。"}

    try:
        fund_raw_list = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {"status": "error", "message": "解析错误: 基金数据格式不正确, 无法解析。"}

    fund_database = [{"code": item[0], "pinyin_short": item[1], "name": item[2], "type": item[3], "pinyin_full": item[4]} for item in fund_raw_list if len(item) >= 5]

    try:
        with open(FUND_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(fund_database, f, ensure_ascii=False, indent=2)
    except IOError as e:
        return {"status": "error", "message": f"文件写入错误: 无法保存基金数据库到 {FUND_DB_FILE}。 {e}"}

    return {"status": "success", "count": len(fund_database), "path": os.path.abspath(FUND_DB_FILE)}

def search_funds(keyword: str):
    """在本地基金数据库中搜索包含关键词的基金"""
    if not os.path.exists(FUND_DB_FILE):
        return {"status": "error", "message": f"本地数据库({FUND_DB_FILE})不存在. 请先运行 'update' 命令来创建数据库."}
    
    try:
        with open(FUND_DB_FILE, 'r', encoding='utf-8') as f:
            fund_database = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"status": "error", "message": f"本地数据库({FUND_DB_FILE})格式错误或不存在. 请尝试重新运行 'update' 命令."}

    keyword_lower = keyword.lower()
    results = [f for f in fund_database if keyword_lower in f["code"] or keyword in f["name"] or keyword_lower in f["pinyin_short"].lower() or keyword_lower in f["pinyin_full"].lower()]

    return results

def _search_and_extract(pattern, text, group_index=1, flags=0):
    """一个简单的正则搜索和提取帮助函数"""
    match = re.search(pattern, text, flags)
    return match.group(group_index) if match else None

def _calculate_risk_metrics(net_worth_data, risk_free_rate=0.015):
    """计算风险指标"""
    if not net_worth_data or len(net_worth_data) < 2:
        return None
    
    try:
        navs = np.array([item['y'] for item in net_worth_data])
        daily_returns = (navs[1:] - navs[:-1]) / navs[:-1]
        
        annualized_volatility = np.std(daily_returns) * np.sqrt(252)
        
        annualized_return = np.mean(daily_returns) * 252
        sharpe_ratio = (annualized_return - risk_free_rate) / annualized_volatility if annualized_volatility != 0 else 0
        
        cumulative_returns = np.cumprod(1 + daily_returns)
        peak = np.maximum.accumulate(cumulative_returns)
        drawdown = (cumulative_returns - peak) / peak
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        return {
            "年化波动率": f"{annualized_volatility:.2%}",
            "夏普比率": f"{sharpe_ratio:.2f}",
            "最大回撤": f"{max_drawdown:.2%}"
        }
    except Exception:
        return None

def query_fund_details(code: str):
    """查询指定基金代码的详细信息"""
    if not re.fullmatch(r"\d{6}", code):
        return {"status": "error", "message": f"无效的基金代码格式: '{code}' (应为6位数字)"}
        
    if not os.path.exists(FUND_DB_FILE):
        return {"status": "error", "message": f"本地数据库({FUND_DB_FILE})不存在。请先运行 'update' 命令。"}
    
    try:
        with open(FUND_DB_FILE, 'r', encoding='utf-8') as f:
            fund_database = json.load(f)
            fund_static_info = next((fund for fund in fund_database if fund['code'] == code), None)
    except (json.JSONDecodeError, FileNotFoundError):
        return {"status": "error", "message": f"本地数据库({FUND_DB_FILE})格式错误或不存在。"}

    if not fund_static_info:
        return {"status": "error", "message": f"在本地数据库中未找到基金代码: {code}。"}

    # --- 获取并解析 JS 文件 ---
    url = FUND_DETAIL_API_TPL.format(code=code)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36', 'Referer': f'http://fund.eastmoney.com/{code}.html'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"网络错误: 查询基金详情JS接口失败。 {e}"}

    content = response.text
    
    result = {"查询代码": code, **fund_static_info}
    result.update({"数据更新日期": None, "最新净值": None, "日增长率": None, "基金规模": None, "基金经理": None, "业绩评估": None, "资产配置": None, "十大重仓股详情": None, "成立日期": None, "业绩比较基准": None, "风险指标": None})
    
    result["阶段涨幅"] = {
        "近1周": _search_and_extract(r'var syl_1z\s*=\s*"([^"]+)"', content), "近1月": _search_and_extract(r'var syl_1y\s*=\s*"([^"]+)"', content),
        "近3月": _search_and_extract(r'var syl_3y\s*=\s*"([^"]+)"', content), "近6月": _search_and_extract(r'var syl_6y\s*=\s*"([^"]+)"', content),
        "近1年": _search_and_extract(r'var syl_1n\s*=\s*"([^"]+)"', content), "近2年": _search_and_extract(r'var syl_2n\s*=\s*"([^"]+)"', content),
        "近3年": _search_and_extract(r'var syl_3n\s*=\s*"([^"]+)"', content), "成立以来": _search_and_extract(r'var syl_ln\s*=\s*"([^"]+)"', content),
    }

    # --- 解析JS数据 ---
    try:
        net_worth_trend_str = _search_and_extract(r'var Data_netWorthTrend\s*=\s*(\[.*?\]);', content, flags=re.DOTALL)
        net_worth_data = json.loads(net_worth_trend_str) if net_worth_trend_str else []
        if net_worth_data:
            latest_data = net_worth_data[-1]
            result["数据更新日期"] = datetime.fromtimestamp(latest_data.get('x') / 1000).strftime('%Y-%m-%d')
            result["最新净值"] = latest_data.get('y')
            result["日增长率"] = f"{float(latest_data.get('equityReturn', 0))}%"
            result["风险指标"] = _calculate_risk_metrics(net_worth_data)
        
        scale_str = _search_and_extract(r'var Data_fluctuationScale\s*=\s*(\{.*?\})\s*;', content, flags=re.DOTALL)
        if scale_str:
            scale_data = json.loads(scale_str)
            if scale_data.get('series') and isinstance(scale_data.get('series'), list) and scale_data['series']:
                latest_scale_point = scale_data['series'][-1]
                if latest_scale_point.get('y') is not None:
                    result["基金规模"] = f"{latest_scale_point.get('y')}亿元 (截止至 {scale_data['categories'][-1]})"

        manager_str = _search_and_extract(r'var Data_currentFundManager\s*=\s*(\[.*?\s*\])\s*;', content, flags=re.DOTALL)
        if manager_str:
            result["基金经理"] = [{"姓名": m.get("name"), "任职时间": m.get("workTime")} for m in json.loads(manager_str)]
        
        perf_eval_str = _search_and_extract(r'var Data_performanceEvaluation\s*=\s*(\{.*?\})\s*;', content, flags=re.DOTALL)
        if perf_eval_str:
            perf_data = json.loads(perf_eval_str)
            result["业绩评估"] = {cat: val for cat, val in zip(perf_data.get("categories", []), perf_data.get("data", []))}
            result["业绩评估"]["综合评分"] = perf_data.get("avr")

        asset_alloc_str = _search_and_extract(r'var Data_assetAllocation\s*=\s*(\{.*?\})\s*;', content, flags=re.DOTALL)
        if asset_alloc_str:
            asset_data = json.loads(asset_alloc_str)
            if asset_data.get('series'):
                result["资产配置"] = {item['name']: f"{item['data'][-1]}%" for item in asset_data['series'] if item.get('name') and item.get('data')}
        
    except Exception as e:
        print(f"  [!] 解析警告: 解析核心JS数据时发生错误: {e}")

    # --- 抓取HTML页面补充信息 ---
    try:
        html_url = f"http://fundf10.eastmoney.com/jbgk_{code}.html"
        html_response = requests.get(html_url, headers=headers)
        html_response.encoding = 'utf-8'
        if html_response.status_code == 200:
            html_content = html_response.text
            inception_date_raw = _search_and_extract(r'<th>成立日期/规模</th><td>(.*?) / ', html_content)
            if inception_date_raw:
                result["成立日期"] = inception_date_raw.replace('年', '-').replace('月', '-').replace('日', '')
            else:
                result["成立日期"] = None
            result["管理费率"] = _search_and_extract(r'<th>管理费率</th><td>(.*?%)[（<]', html_content)
            result["托管费率"] = _search_and_extract(r'<th>托管费率</th><td>(.*?%)[（<]', html_content)
            benchmark_raw = _search_and_extract(r'<th>业绩比较基准</th><td[^>]*>(.*?)</td>', html_content, flags=re.DOTALL)
            if benchmark_raw:
                result["业绩比较基准"] = re.sub('<[^<]+?>', '', benchmark_raw).strip()
        
        html_url_main = f"http://fund.eastmoney.com/{code}.html"
        html_response_main = requests.get(html_url_main, headers=headers)
        html_response_main.encoding = 'utf-8'
        if html_response_main.status_code == 200:
            html_content_main = html_response_main.text
            holdings_table_match = re.search(r"id='position_shares'.*?<table class='ui-table-hover'[^>]*>(.*?)</table>", html_content_main, re.DOTALL)
            if holdings_table_match:
                holdings_html = holdings_table_match.group(1)
                rows = re.findall(r'<tr>(.*?)</tr>', holdings_html, re.DOTALL)[1:] # Skip header
                holdings_list = []
                for row in rows:
                    cols = re.findall(r'<td.*?>(.*?)</td>', row, re.DOTALL)
                    if len(cols) > 1:
                        stock_name_match = re.search(r'<a[^>]*>(.*?)</a>', cols[0])
                        stock_name = stock_name_match.group(1).strip() if stock_name_match else ""
                        percentage_match = re.search(r'(\d+\.\d+)%', cols[1])
                        percentage = percentage_match.group(0) if percentage_match else ""
                        if stock_name and percentage:
                           holdings_list.append(f"{stock_name} ({percentage})")
                result["十大重仓股详情"] = holdings_list
    except Exception as e:
        print(f"  [!] 解析警告: 抓取HTML页面补充信息失败: {e}")
        
    return result

def main():
    parser = argparse.ArgumentParser(description="天天基金信息查询命令行工具", formatter_class=argparse.RawTextHelpFormatter, epilog="""
使用示例:
  1. 更新本地基金数据库 (首次使用或需要更新时运行):
     python %(prog)s update

  2. 按名称或代码搜索基金:
     python %(prog)s search "华夏成长"

  3. 查询基金详细信息:
     python %(prog)s query 000001
""")
    subparsers = parser.add_subparsers(dest='command', help='可用的命令')
    subparsers.add_parser('update', help='下载并更新本地的基金数据库')
    search_parser = subparsers.add_parser('search', help='根据关键词搜索基金')
    search_parser.add_argument('keyword', type=str, help='要搜索的基金代码、名称或拼音缩写')
    query_parser = subparsers.add_parser('query', help='查询指定基金代码的详细信息')
    query_parser.add_argument('code', type=str, help='要查询的基金代码')

    args = parser.parse_args()
    if args.command == 'update':
        result = update_fund_database()
        if result['status'] == 'success':
            print(f"  [✔] 基金数据库更新成功! 共找到 {result['count']} 只基金。")
            print(f"  数据已保存到: {result['path']}")
        else:
            print(f"  [!] {result['message']}")
    elif args.command == 'search':
        results = search_funds(args.keyword)
        if isinstance(results, dict) and results.get('status') == 'error':
            print(f"  [!] {results['message']}")
            return

        if not results:
            print(f"  [i] 未找到与 '{args.keyword}' 相关的基金。")
            return

        print(f"  查询到 {len(results)} 个匹配结果:")
        print("-" * 60)
        print(f"{ '代码':<10}{'名称':<30}{'类型':<20}")
        print(f"{'-'*8:<10}{'-'*28:<30}{'-'*18:<20}")

        for fund in results:
            name = fund['name']
            if len(name.encode('gbk', 'ignore')) > 28:
                name = name[:13] + '…'
            print(f"{fund['code']:<10}{name:<30}{fund['type']:<20}")
        print("-" * 60)

    elif args.command == 'query':
        result = query_fund_details(args.code)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
