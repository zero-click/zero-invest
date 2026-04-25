# -*- coding: utf-8 -*-
"""
行业估值矩阵模块 - 增强版
基于可用的akshare数据源获取行业估值

数据源:
  - 证监会行业PE数据 (stock_industry_pe_ratio_cninfo): 116个行业
  - 乐咕乐股指数PB数据 (stock_index_pb_lg): 多个宽基指数
  - 乐咕乐股指数PE数据 (stock_index_pe_lg): 12个宽基指数

输出:
  - 行业估值热力图（表格格式）
  - 估值分位矩阵（JSON格式）
  - 投资建议（基于估值温度）
"""

import os
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import akshare as ak
import pandas as pd

# 抑制警告
warnings.filterwarnings("ignore")

# 移除代理环境变量（akshare需要直连）
for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY"]:
    os.environ.pop(k, None)

# ============================================================
# 行业估值矩阵配置
# ============================================================

# 证监会行业映射（主要行业）
CSRC_INDUSTRY_MAP = {
    # 一级行业
    "农、林、牧、渔业": "农业",
    "采矿业": "资源",
    "制造业": "制造",
    "电力、热力、燃气及水生产和供应业": "公用事业",
    "建筑业": "建筑",
    "批发和零售业": "商贸",
    "交通运输、仓储和邮政业": "物流",
    "住宿和餐饮业": "消费",
    "信息传输、软件和信息技术服务业": "科技",
    "金融业": "金融",
    "房地产业": "地产",
    "租赁和商务服务业": "服务",
    "科学研究和技术服务业": "科研",
    "水利、环境和公共设施管理业": "环保",
    "居民服务、修理和其他服务业": "服务",
    "教育": "教育",
    "卫生和社会工作": "医疗",
    "文化、体育和娱乐业": "文体",
    "综合": "综合",
}

# 重点关注的二级行业
KEY_INDUSTRIES = {
    # 资源类
    "煤炭开采和洗选业": ("煤炭", "资源"),
    "石油和天然气开采业": ("油气", "资源"),
    "黑色金属矿采选业": ("钢铁", "资源"),
    "有色金属矿采选业": ("有色", "资源"),
    
    # 制造类
    "酒、饮料和精制茶制造业": ("白酒", "消费"),
    "医药制造业": ("医药", "医疗"),
    "计算机、通信和其他电子设备制造业": ("电子", "科技"),
    "电气机械和器材制造业": ("电气", "制造"),
    "汽车制造业": ("汽车", "制造"),
    
    # 金融类
    "货币金融服务": ("银行", "金融"),
    "资本市场服务": ("证券", "金融"),
    "保险业": ("保险", "金融"),
    
    # 科技类
    "软件和信息技术服务业": ("软件", "科技"),
    "互联网和相关服务": ("互联网", "科技"),
    
    # 消费类
    "零售业": ("零售", "消费"),
    "房地产业": ("地产", "地产"),
}

# 乐咕乐股支持的宽基指数
LG_INDEX_MAP = {
    "000300": ("沪深300", "大盘蓝筹"),
    "000905": ("中证500", "中小盘"),
    "000852": ("中证1000", "小盘"),
    "000016": ("上证50", "大盘蓝筹"),
    "399006": ("创业板50", "成长科技"),
    "000015": ("上证红利", "高股息"),
    "000922": ("深证红利", "高股息"),
    "000010": ("上证180", "大盘蓝筹"),
    "000009": ("上证380", "中小盘"),
    "000903": ("中证100", "大盘蓝筹"),
    "000906": ("中证800", "大盘+中小盘"),
    "399673": ("创业板50", "成长科技"),
    "399330": ("深证100", "大盘蓝筹"),
}

# 乐咕乐股名称映射
LG_NAME_MAP = {
    "沪深300": "沪深300",
    "中证500": "中证500",
    "中证1000": "中证1000",
    "上证50": "上证50",
    "创业板50": "创业板50",
    "上证红利": "上证红利",
    "深证红利": "深证红利",
    "上证180": "上证180",
    "上证380": "上证380",
    "中证100": "中证100",
    "中证800": "中证800",
    "深证100": "深证100",
}

def get_csrc_industry_pe() -> List[Dict]:
    """
    获取证监会行业PE数据（使用2026年数据）
    """
    try:
        # 尝试获取2026年的数据
        # 从今天开始往前找，直到找到可用的数据
        base_date = datetime.now()
        
        for days_back in range(0, 30):  # 最多往前找30天
            test_date = (base_date - timedelta(days=days_back)).strftime("%Y%m%d")
            try:
                df = ak.stock_industry_pe_ratio_cninfo(symbol='证监会行业分类', date=test_date)
                if df is not None and not df.empty:
                    data_date = df['变动日期'].iloc[0] if '变动日期' in df.columns else test_date
                    print(f"证监会行业PE数据获取成功，日期: {data_date} (请求日期: {test_date})")
                    
                    results = []
                    for _, row in df.iterrows():
                        industry_name = row.get('行业名称', '')
                        if not industry_name or industry_name == '中国上市公司协会上市公司行业分类标准':
                            continue
                        
                        # 获取行业分类
                        category = CSRC_INDUSTRY_MAP.get(industry_name, '其他')
                        if industry_name in KEY_INDUSTRIES:
                            display_name, category = KEY_INDUSTRIES[industry_name]
                        else:
                            display_name = industry_name
                        
                        # 获取PE数据（优先使用加权平均）
                        pe_weighted = row.get('静态市盈率-加权平均')
                        pe_median = row.get('静态市盈率-中位数')
                        pe = pe_weighted if not pd.isna(pe_weighted) else pe_median
                        
                        if pd.isna(pe):
                            continue
                        
                        results.append({
                            "指数代码": f"CSRC_{industry_name[:10]}",
                            "指数名称": display_name,
                            "分类": category,
                            "日期": str(data_date),
                            "静态PE": float(pe),
                            "滚动PE": None,  # 证监会数据没有滚动PE
                            "PB": None,      # 需要从其他数据源获取
                            "股息率": None,   # 需要从其他数据源获取
                            "收盘点位": None,
                            "数据源": "证监会行业",
                        })
                    
                    return results
                    
            except Exception as e:
                # 这个日期可能没有数据，继续尝试下一个
                continue
        
        # 如果30天内都没有数据，尝试2024年的数据作为备选
        print("2026年数据不可用，尝试2024年数据...")
        try:
            df = ak.stock_industry_pe_ratio_cninfo(symbol='证监会行业分类', date='20240419')
            if df is not None and not df.empty:
                print(f"使用2024年备选数据，日期: {df['变动日期'].iloc[0]}")
                
                results = []
                for _, row in df.iterrows():
                    industry_name = row.get('行业名称', '')
                    if not industry_name or industry_name == '中国上市公司协会上市公司行业分类标准':
                        continue
                    
                    category = CSRC_INDUSTRY_MAP.get(industry_name, '其他')
                    if industry_name in KEY_INDUSTRIES:
                        display_name, category = KEY_INDUSTRIES[industry_name]
                    else:
                        display_name = industry_name
                    
                    pe_weighted = row.get('静态市盈率-加权平均')
                    pe_median = row.get('静态市盈率-中位数')
                    pe = pe_weighted if not pd.isna(pe_weighted) else pe_median
                    
                    if pd.isna(pe):
                        continue
                    
                    results.append({
                        "指数代码": f"CSRC_{industry_name[:10]}",
                        "指数名称": display_name,
                        "分类": category,
                        "日期": "2024-04-19",
                        "静态PE": float(pe),
                        "滚动PE": None,
                        "PB": None,
                        "股息率": None,
                        "收盘点位": None,
                        "数据源": "证监会行业(2024)",
                    })
                
                return results
        except:
            pass
        
        print("证监会行业PE数据不可用，跳过")
        return []
        
    except Exception as e:
        print(f"获取证监会行业PE数据失败: {e}")
        return []

def get_lg_index_valuation() -> List[Dict]:
    """
    获取乐咕乐股指数估值数据（PE + PB）
    """
    results = []
    
    for code, (name, category) in LG_INDEX_MAP.items():
        try:
            # 获取PE数据
            lg_name = LG_NAME_MAP.get(name, name)
            pe_data = None
            pb_data = None
            
            # 获取PE
            try:
                pe_df = ak.stock_index_pe_lg(symbol=lg_name)
                if pe_df is not None and not pe_df.empty:
                    latest_pe = pe_df.iloc[-1]
                    pe_rolling = latest_pe.get('滚动市盈率')
                    pe_static = latest_pe.get('静态市盈率')
                    close_price = latest_pe.get('指数')
            except:
                pe_rolling = pe_static = close_price = None
            
            # 获取PB
            try:
                pb_df = ak.stock_index_pb_lg(symbol=lg_name)
                if pb_df is not None and not pb_df.empty:
                    latest_pb = pb_df.iloc[-1]
                    pb = latest_pb.get('市净率')
            except:
                pb = None
            
            if pe_rolling is None and pe_static is None and pb is None:
                continue
            
            results.append({
                "指数代码": code,
                "指数名称": name,
                "分类": category,
                "日期": datetime.now().strftime("%Y-%m-%d"),
                "滚动PE": float(pe_rolling) if not pd.isna(pe_rolling) else None,
                "静态PE": float(pe_static) if not pd.isna(pe_static) else None,
                "PB": float(pb) if not pd.isna(pb) else None,
                "股息率": None,  # 乐咕乐股没有股息率数据
                "收盘点位": float(close_price) if not pd.isna(close_price) else None,
                "数据源": "乐咕乐股",
            })
            
        except Exception as e:
            print(f"获取{name}({code})估值数据失败: {e}")
    
    return results

def get_industry_valuation_matrix() -> Dict:
    """
    获取完整的行业估值矩阵
    """
    # 获取证监会行业PE数据
    csrc_data = get_csrc_industry_pe()
    
    # 获取乐咕乐股指数估值数据
    lg_data = get_lg_index_valuation()
    
    # 合并数据
    all_data = csrc_data + lg_data
    
    # 去重（按指数名称）
    seen = set()
    unique_data = []
    for item in all_data:
        name = item["指数名称"]
        if name not in seen:
            seen.add(name)
            unique_data.append(item)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total": len(unique_data),
        "data": unique_data,
    }

def get_valuation_heatmap(sort_by: str = "pe") -> Dict:
    """
    生成估值热力图数据
    """
    matrix = get_industry_valuation_matrix()
    
    data = matrix["data"]
    
    # 根据排序字段排序
    if sort_by == "pe":
        # 优先使用滚动PE，其次静态PE
        data.sort(key=lambda x: x.get("滚动PE") or x.get("静态PE") or float("inf"))
    elif sort_by == "pb":
        data.sort(key=lambda x: x.get("PB") or float("inf"))
    elif sort_by == "category":
        data.sort(key=lambda x: x.get("分类", ""))
    
    # 计算估值温度
    for item in data:
        pe = item.get("滚动PE") or item.get("静态PE")
        if pe:
            if pe < 15:
                item["估值温度"] = "低"
            elif pe < 25:
                item["估值温度"] = "中"
            else:
                item["估值温度"] = "高"
        else:
            item["估值温度"] = "未知"
    
    return {
        "timestamp": matrix["timestamp"],
        "total": len(data),
        "sort_by": sort_by,
        "data": data,
    }

def format_heatmap_table(heatmap: Dict) -> str:
    """
    格式化热力图表格输出
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"行业估值热力图 (基于{heatmap['sort_by'].upper()}排序)")
    lines.append("=" * 80)
    lines.append(f"{'行业':<16} {'分类':<10} {'PE':<8} {'PB':<8} {'数据源':<12} {'估值':<6}")
    lines.append("-" * 80)
    
    for item in heatmap["data"][:30]:  # 显示前30个
        pe = item.get("滚动PE") or item.get("静态PE")
        pb = item.get("PB")
        
        pe_str = f"{pe:.1f}" if pe is not None else "N/A"
        pb_str = f"{pb:.2f}" if pb is not None else "N/A"
        
        # 截断过长的行业名称
        name = item['指数名称']
        if len(name) > 15:
            name = name[:12] + "..."
        
        lines.append(f"{name:<16} {item['分类']:<10} {pe_str:<8} {pb_str:<8} {item['数据源']:<12} {item['估值温度']:<6}")
    
    lines.append("=" * 80)
    lines.append(f"共 {heatmap['total']} 个行业 | 显示前30个 | 更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(lines)

def get_investment_suggestions(heatmap: Dict) -> str:
    """
    生成投资建议 (兼容CLI)
    """
    return get_investment_advice(heatmap)

def get_investment_advice(heatmap: Dict) -> str:
    """
    生成投资建议
    """
    low_valuation = [item for item in heatmap["data"] if item["估值温度"] == "低"]
    high_valuation = [item for item in heatmap["data"] if item["估值温度"] == "高"]
    
    advice = []
    advice.append("=" * 80)
    advice.append("投资建议")
    advice.append("=" * 80)
    
    if low_valuation:
        advice.append("【低估机会】")
        for item in low_valuation[:5]:  # 取前5个
            pe = item.get("滚动PE") or item.get("静态PE")
            advice.append(f"  • {item['指数名称']} ({item['分类']}): PE={pe:.1f}")
    
    if high_valuation:
        advice.append("\n【高估风险】")
        for item in high_valuation[:5]:  # 取前5个
            pe = item.get("滚动PE") or item.get("静态PE")
            advice.append(f"  • {item['指数名称']} ({item['分类']}): PE={pe:.1f}")
    
    # 行业配置建议
    advice.append("\n【行业配置建议】")
    advice.append("  1. 低估值行业: 适合左侧布局，长期持有")
    advice.append("  2. 中等估值: 适合定投，均衡配置")
    advice.append("  3. 高估值行业: 谨慎参与，等待回调")
    advice.append("  4. 关注政策导向: 科技、新能源、高端制造")
    
    advice.append("=" * 80)
    
    return "\n".join(advice)

if __name__ == "__main__":
    # 测试代码
    heatmap = get_valuation_heatmap(sort_by="pe")
    print(format_heatmap_table(heatmap))
    print()
    print(get_investment_advice(heatmap))