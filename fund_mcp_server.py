# -*- coding: utf-8 -*-
"""
基于 MCP Python SDK 的基金信息查询服务器
使用 FastMCP 快速创建符合 MCP 标准的服务
"""

from mcp.server.fastmcp import FastMCP
import logging
from typing import Optional
import sys
import os

# 添加 src 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
import fund_tools as fund_tool

# === 配置日志 ===
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === 创建 MCP 服务器 ===
# 使用 json_response=True 让返回值自动转换为 JSON
mcp = FastMCP(
    name="中国基金信息查询 Pro",
    json_response=True
)

# === MCP 工具定义 ===

@mcp.tool()
def search_funds(keyword: str, limit: int = 50) -> dict:
    """
    搜索中国公募基金

    Args:
        keyword: 搜索关键词（支持基金代码、名称、拼音缩写）
        limit: 返回结果数量限制，默认50

    Returns:
        包含搜索结果的字典，包含基金代码、名称、类型等信息
    """
    logger.info(f"🔍 搜索基金: {keyword}")

    result = fund_tool.search_funds(keyword)

    if result['status'] == 'error':
        return {
            "success": False,
            "error": result['message']
        }

    # 限制返回数量
    result['data'] = result['data'][:limit]
    result['count'] = len(result['data'])

    logger.info(f"✅ 找到 {result['count']} 只基金")
    return {
        "success": True,
        "count": result['count'],
        "funds": result['data']
    }

@mcp.tool()
def get_fund_details(code: str) -> dict:
    """
    获取基金的详细信息

    Args:
        code: 6位基金代码

    Returns:
        基金详细信息，包括：
        - 基本信息（名称、类型、成立日期）
        - 基金规模和经理
        - 费率信息
        - 业绩表现（各阶段收益率）
        - 风险指标（波动率、夏普比率、最大回撤）
        - 十大重仓股
    """
    logger.info(f"📊 查询基金详情: {code}")

    data = fund_tool.query_fund_details(code)

    if data.get("status") == "error":
        logger.error(f"❌ 查询失败: {data.get('message')}")
        return {
            "success": False,
            "error": data.get("message")
        }

    logger.info(f"✅ 成功获取基金 {code} 的详细信息")
    return {
        "success": True,
        "fund": data
    }

@mcp.tool()
def get_fund_rankings(fund_type: str = "全部", limit: int = 100) -> dict:
    """
    获取基金业绩排行榜

    Args:
        fund_type: 基金类型（全部/股票型/混合型/债券型/指数型/QDII/FOF）
        limit: 返回结果数量限制，默认100

    Returns:
        基金排行榜数据，包含基金代码、名称、净值、各阶段收益率等
    """
    logger.info(f"🏆 获取{fund_type}基金排行榜")

    result = fund_tool.get_fund_rankings(fund_type)

    if result['status'] == 'error':
        return {
            "success": False,
            "error": result['message']
        }

    # 限制返回数量
    result['data'] = result['data'][:limit]
    result['count'] = len(result['data'])

    logger.info(f"✅ 成功获取 {result['count']} 只基金的排行榜数据")
    return {
        "success": True,
        "count": result['count'],
        "rankings": result['data']
    }

@mcp.tool()
def get_fund_rating(code: str) -> dict:
    """
    获取基金的评级信息

    Args:
        code: 基金代码

    Returns:
        基金评级数据（上海证券、招商证券、济安金信、晨星评级等）
    """
    logger.info(f"⭐ 查询基金评级: {code}")

    result = fund_tool.get_fund_rating(code)

    if result['status'] == 'error':
        return {
            "success": False,
            "error": result['message']
        }

    logger.info(f"✅ 成功获取基金 {code} 的评级信息")
    return {
        "success": True,
        "rating": result.get('ratings')
    }

@mcp.tool()
def refresh_fund_cache() -> dict:
    """
    刷新基金数据缓存

    当基金数据过期或需要最新数据时调用此工具

    Returns:
        刷新结果，包含更新的基金数量
    """
    logger.info("🔄 正在刷新基金数据缓存...")

    # 清除内存缓存和磁盘缓存，强制重新从网络加载
    fund_tool.get_fund_list.cache_clear()
    fund_tool.search_funds.cache_clear()
    import os
    if os.path.exists(fund_tool.FUND_DB_FILE):
        os.remove(fund_tool.FUND_DB_FILE)

    # 重新加载
    try:
        fund_list = fund_tool.get_fund_list()
        if fund_list.empty:
            return {
                "success": False,
                "error": "刷新失败：无法获取基金数据"
            }

        logger.info(f"✅ 成功刷新 {len(fund_list)} 只基金数据")
        return {
            "success": True,
            "count": len(fund_list),
            "message": f"成功刷新 {len(fund_list)} 只基金数据"
        }
    except Exception as e:
        logger.error(f"❌ 刷新失败: {e}")
        return {
            "success": False,
            "error": f"刷新失败: {str(e)}"
        }

# === 新增工具：基金经理、持仓、配置、费用、流动性 ===

@mcp.tool()
def get_fund_manager_details(code: str) -> dict:
    """
    获取基金经理深度信息

    Args:
        code: 6位基金代码

    Returns:
        基金经理详细信息，包括：
        - 姓名、所属公司
        - 累计从业时间
        - 现任基金资产总规模
        - 现任基金最佳回报
        - 管理的其他基金
    """
    logger.info(f"👤 查询基金经理详情: {code}")

    result = fund_tool.get_fund_manager_details(code)

    if result.get('status') == 'error':
        return {
            "success": False,
            "error": result.get('message')
        }

    return {
        "success": True,
        "managers": result.get('managers', []),
        "manager_count": result.get('manager_count', 0)
    }

@mcp.tool()
def get_fund_holdings_analysis(code: str, periods: int = 4) -> dict:
    """
    获取持仓动态分析

    Args:
        code: 6位基金代码
        periods: 分析最近几个季度，默认4

    Returns:
        持仓动态分析数据，包括：
        - 持仓集中度（前10大持仓占比）
        - 持仓变化趋势（按季度）
        - 最新重仓股列表
    """
    logger.info(f"📊 分析基金持仓动态: {code}")

    result = fund_tool.get_fund_holdings_analysis(code, periods)

    if result.get('status') == 'error':
        return {
            "success": False,
            "error": result.get('message')
        }

    return {
        "success": True,
        "code": code,
        "concentration": result.get('concentration', {}),
        "holdings_change_by_quarter": result.get('holdings_change_by_quarter', {}),
        "latest_top_holdings": result.get('latest_top_holdings', [])
    }

@mcp.tool()
def get_fund_asset_allocation(code: str, date: str = "2024") -> dict:
    """
    获取资产配置结构

    Args:
        code: 6位基金代码
        date: 年份，默认2024

    Returns:
        资产配置数据，包括：
        - 投资风格（成长/价值/平衡）
        - 行业配置分布
        - 股票持仓样本
        - 债券持仓样本
    """
    logger.info(f"🎯 查询基金资产配置: {code}")

    result = fund_tool.get_fund_asset_allocation(code, date)

    if result.get('status') == 'error':
        return {
            "success": False,
            "error": result.get('message')
        }

    return {
        "success": True,
        "code": code,
        "date": date,
        "investment_style": result.get('investment_style', ''),
        "industry_allocation": result.get('industry_allocation', []),
        "stock_holdings_sample": result.get('stock_holdings_sample', []),
        "bond_holdings_sample": result.get('bond_holdings_sample', [])
    }

@mcp.tool()
def get_fund_fee_details(code: str) -> dict:
    """
    获取费用明细

    Args:
        code: 6位基金代码

    Returns:
        费用明细，包括：
        - 认购费率
        - 申购费率
        - 赎回费率（分档）
        - 管理费率
        - 托管费率
    """
    logger.info(f"💰 查询基金费用明细: {code}")

    result = fund_tool.get_fund_fee_details(code)

    if result.get('status') == 'error':
        return {
            "success": False,
            "error": result.get('message')
        }

    return {
        "success": True,
        "code": code,
        "fee_details": result.get('fee_details', {})
    }

@mcp.tool()
def get_fund_liquidity_info(code: str) -> dict:
    """
    获取流动性信息

    Args:
        code: 6位基金代码

    Returns:
        流动性信息，包括：
        - 申赎状态（开放/暂停）
        - 申赎时间（T+N）
        - 最低申购金额
        - 申购确认时间
        - 赎回到账时间
    """
    logger.info(f"💧 查询基金流动性信息: {code}")

    result = fund_tool.get_fund_liquidity_info(code)

    if result.get('status') == 'error':
        return {
            "success": False,
            "error": result.get('message')
        }

    return {
        "success": True,
        "code": code,
        "liquidity_info": result.get('liquidity_info', {})
    }

# === 新增工具：行业估值热力图 ===

@mcp.tool()
def get_industry_valuation_heatmap(
    category: str = "全部",
    sort_by: str = "pe",
    limit: int = 20,
    include_suggestions: bool = False
) -> dict:
    """
    获取行业估值热力图

    Args:
        category: 行业分类筛选（全部/宽基/科技/成长/消费/医药/资源/金融/军工/红利）
        sort_by: 排序方式（pe/pb/dividend/valuation）
        limit: 返回结果数量限制，默认20
        include_suggestions: 兼容旧参数，当前版本忽略

    Returns:
        行业估值热力图数据，包括：
        - 行业列表（名称、分类、PE、PB、股息率、估值等级）
        - 统计摘要
    """
    logger.info(f"📈 获取行业估值热力图 | 分类: {category} | 排序: {sort_by}")

    try:
        heatmap_data = fund_tool.get_valuation_heatmap(category=category, sort_by=sort_by)
        industries = [
            {
                "行业名称": item.get("名称"),
                "行业分类": item.get("分类"),
                "PE": item.get("PE"),
                "PB": item.get("PB"),
                "股息率": item.get("股息率"),
                "估值等级": item.get("估值温度"),
                "原始数据": item,
            }
            for item in heatmap_data.get("data", [])[:limit]
        ]

        result = {
            "success": True,
            "category": category,
            "sort_by": sort_by,
            "total_industries": len(industries),
            "industries": industries,
            "summary": heatmap_data["summary"]
        }

        logger.info(f"✅ 成功获取 {len(industries)} 个行业的估值数据")
        return result
    except Exception as e:
        logger.error(f"❌ 获取行业估值热力图失败: {e}")
        return {
            "success": False,
            "error": f"获取行业估值热力图失败: {str(e)}"
        }

# === 投资组合分析工具 ===

@mcp.tool()
def get_portfolio_deviation() -> dict:
    """
    获取四账户偏离度分析。

    读取投资组合Excel持仓数据，计算安全账户/稳定现金流/成长账户/机会账户
    的实际占比与目标占比的偏离度。使用相对偏离度（偏离/目标）判断状态。

    数据源: ~/code/skyebee/Investment/current.xlsx

    Returns:
        四账户偏离度数据，包括：
        - accounts: 每个账户的实际/目标占比、绝对偏离、相对偏离、状态
        - alerts: 告警列表（紧急/关注）
        - total: 总资产
    """
    logger.info("📊 获取四账户偏离度分析")

    try:
        from portfolio_analysis import read_portfolio_from_excel, calculate_deviation

        portfolio = read_portfolio_from_excel()
        deviation = calculate_deviation(portfolio)

        alert_count = len(deviation.get("alerts", []))
        logger.info(f"✅ 偏离度分析完成: 总资产¥{deviation['total']:,.0f}, {alert_count}条告警")
        return deviation

    except Exception as e:
        logger.error(f"❌ 偏离度分析失败: {e}")
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_us_index_valuation() -> dict:
    """
    获取标普500估值数据（含PE/PB历史分位）。

    从 multpl.com 获取标普500的月度PE/PB/股息率历史数据，
    计算10年/5年/3年历史分位，判断估值等级。

    数据源: multpl.com（需代理访问）

    Returns:
        标普500估值数据，包括：
        - PE (TTM) + 10/5/3年分位 + 估值等级
        - PB + 10/5年分位 + 估值等级
        - 股息率 + 分位
    """
    logger.info("🇺🇸 获取标普500估值数据")

    try:
        from portfolio_analysis import get_us_index_valuation as _get_us

        result = _get_us()

        if result.get("status") == "ok":
            sp = result.get("标普500", {})
            logger.info(
                f"✅ 标普500: PE={sp.get('PE', 'N/A')} "
                f"(10年分位={sp.get('PE分位_10年', 'N/A')}% {sp.get('估值等级_PE', '')})"
            )
        return result

    except Exception as e:
        logger.error(f"❌ 标普500估值获取失败: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_hk_index_valuation() -> dict:
    """
    获取港股/中概相关指数估值。

    通过中证指数官网获取中国互联网、内地民营、沪港深通金融等
    港股相关指数的PE、滚动PE、股息率。

    数据源: 中证指数官网（akshare）

    Returns:
        港股/中概指数估值数据
    """
    logger.info("🇭🇰 获取港股/中概指数估值")

    try:
        from portfolio_analysis import get_hk_index_valuation as _get_hk

        result = _get_hk()
        logger.info(f"✅ 港股估值获取完成")
        return result

    except Exception as e:
        logger.error(f"❌ 港股估值获取失败: {e}")
        return {"status": "error", "error": str(e)}


@mcp.tool()
def get_portfolio_analysis() -> dict:
    """
    投资组合综合分析：偏离度 + 美股估值 + 港股估值。

    一次性获取所有投资组合相关的分析数据：
    1. 四账户偏离度（安全/稳定/成长/机会的实际vs目标占比）
    2. 标普500估值（PE/PB/股息率 + 历史分位）
    3. 港股/中概指数估值（中国互联网等）

    Returns:
        综合分析报告，包括 deviation、us_valuation、hk_valuation、summary
    """
    logger.info("📋 获取投资组合综合分析")

    try:
        from portfolio_analysis import get_portfolio_analysis as _get_full

        result = _get_full()
        logger.info(f"✅ 综合分析完成")
        return result

    except Exception as e:
        logger.error(f"❌ 综合分析失败: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# 指数查询工具
# ============================================================

@mcp.tool()
def search_indices_all(keyword: str, limit: int = 50) -> dict:
    """
    搜索中国A股指数（宽基、行业、主题、策略、风格）

    Args:
        keyword: 搜索关键词（支持指数代码、名称）
        limit: 返回结果数量限制，默认50

    Returns:
        包含搜索结果的字典，包含指数代码、名称、分类等信息
    """
    logger.info(f"🔍 搜索指数: {keyword}")

    results = fund_tool.search_indices_all(keyword)

    if not results:
        logger.warning(f"⚠️ 未找到与 '{keyword}' 相关的指数")
        return {
            "success": False,
            "error": f"未找到与 '{keyword}' 相关的指数"
        }

    # 限制返回数量
    results = results[:limit]

    logger.info(f"✅ 找到 {len(results)} 个指数")
    return {
        "success": True,
        "count": len(results),
        "indices": results
    }


@mcp.tool()
def get_index_info(code: str) -> dict:
    """
    获取指数的基本信息

    Args:
        code: 6位指数代码

    Returns:
        指数基本信息，包括：
        - 代码、名称
        - 分类（broad/industry/sector/strategy/style）
        - 指数类别（规模/行业/主题/策略/风格）
        - 资产类别
        - 基日、发布日期
    """
    logger.info(f"📊 查询指数基本信息: {code}")

    info = fund_tool.get_index_info_by_code(code)

    if not info:
        logger.error(f"❌ 未找到指数 {code}")
        return {
            "success": False,
            "error": f"未找到指数 {code}"
        }

    logger.info(f"✅ 成功获取指数 {code} 的基本信息")
    return {
        "success": True,
        "index": info
    }


@mcp.tool()
def get_index_details(code: str) -> dict:
    """
    获取指数的完整详情

    Args:
        code: 6位指数代码

    Returns:
        指数详细信息，包括：
        - 基本信息（代码、名称、分类、发布日期）
        - 当前值（收盘点位、日期、涨跌幅）
        - 业绩表现（1周/1月/3月/6月/1年/3年/今年收益率）
        - 估值数据（PE-TTM、PB）
        - 历史分位（PE/PB的3年/5年/10年百分位）
        - 估值等级（低估/合理/高估）
        - 数据源
    """
    logger.info(f"📊 查询指数完整详情: {code}")

    details = fund_tool.get_index_details(code)

    if details.get("status") == "error":
        logger.error(f"❌ 查询失败: {details.get('message')}")
        return {
            "success": False,
            "error": details.get("message")
        }

    logger.info(f"✅ 成功获取指数 {code} 的详细信息")
    return {
        "success": True,
        "index": details
    }


@mcp.tool()
def get_index_details_batch(codes: list) -> dict:
    """
    批量获取多个指数的完整详情

    Args:
        codes: 指数代码列表

    Returns:
        批量查询结果，包含每个指数的详细信息
    """
    logger.info(f"📊 批量查询指数详情: {', '.join(codes)}")

    results = fund_tool.get_index_details_batch(codes)

    success_count = sum(1 for r in results.values() if r.get("status") == "success")
    logger.info(f"✅ 批量查询完成，成功 {success_count}/{len(codes)}")

    return {
        "success": True,
        "total": len(codes),
        "success_count": success_count,
        "indices": results
    }


@mcp.tool()
def get_index_risk(code: str) -> dict:
    """
    获取指数风险分析

    Args:
        code: 指数代码（6位），如 "000300", "000905"

    Returns:
        风险分析结果，包含：
        - 收益率: 近1月/3月/6月/1年收益率
        - 波动率: 近1年/3年/历史年化波动率
        - 最大回撤: 回撤幅度、开始/最低日期、持续/修复天数
        - 回撤修复分析: 历史显著回撤次数、平均/最长/最短修复天数
        - 夏普比率: 风险调整后收益指标
        - 数据范围: 起始/截止日期、数据点数
    """
    logger.info(f"⚠️  查询指数风险分析: {code}")

    result = fund_tool.get_index_risk(code)

    if result.get("status") == "success":
        logger.info(f"✅ 成功获取指数 {code} 的风险分析")
    else:
        logger.warning(f"❌ 获取指数 {code} 风险分析失败: {result.get('message')}")

    return result


# === 沪深港通资金流分析工具 ===

@mcp.tool()
def get_capital_flow_summary() -> dict:
    """
    获取沪深港通今日资金流总览。

    返回沪股通、深股通、港股通各通道的当日净买额、资金流入、余额及涨跌家数。

    Returns:
        资金流总览，包含:
        - date: 数据日期
        - channels: 各通道资金流明细（北向: 沪股通+深股通, 南向: 港股通沪+港股通深）
          每个通道包含: net_buy(净买额), fund_inflow(资金流入), balance(余额),
          up_count(上涨数), down_count(下跌数), index_name(相关指数), index_change_pct(涨跌幅)
    """
    logger.info("📊 查询沪深港通资金流总览")
    result = fund_tool.get_capital_flow_summary()
    if result.get("status") == "success":
        logger.info(f"✅ 成功获取资金流总览 ({result.get('date')})")
    else:
        logger.warning(f"❌ 获取资金流总览失败: {result.get('message')}")
    return result


@mcp.tool()
def get_capital_flow_history(direction: str = "南向", days: int = 20) -> dict:
    """
    查询沪深港通历史资金流趋势。

    支持北向/南向/沪股通/深股通方向，返回近N日逐日数据及趋势分析。
    注意: 2024-08-19 后北向方向 data_available=False，净买额不再公布。

    Args:
        direction: 资金方向，可选: 南向(默认)、北向、沪股通、深股通、港股通沪、港股通深
        days: 返回天数，默认20，最大365

    Returns:
        历史资金流数据，包含:
        - summary: 趋势分析（持续流入/持续流出/震荡）, 累计净买额, 日均净买额
        - data: 逐日净买额、买入/卖出额、累计净买额
        - data_available: 北向方向为 False
    """
    logger.info(f"📊 查询历史资金流: direction={direction}, days={days}")
    result = fund_tool.get_capital_flow_history(direction=direction, days=days)
    if result.get("status") == "success":
        logger.info(f"✅ 成功获取 {direction} 历史资金流 ({len(result.get('data', []))}天)")
    else:
        logger.warning(f"❌ 获取历史资金流失败: {result.get('message')}")
    return result


# === MCP 资源定义（可选） ===

@mcp.resource("fund://list")
def get_fund_list_resource() -> str:
    """
    获取所有基金的列表作为资源

    返回完整的基金列表JSON字符串
    """
    logger.info("📋 提供基金列表资源")
    df = fund_tool.get_fund_list()
    return df.to_json(orient='records', force_ascii=False, indent=2)

@mcp.resource("fund://overview")
def get_service_overview() -> str:
    """
    服务概述资源

    返回服务的基本信息和使用说明
    """
    return """
# 中国基金信息查询服务

基于 akshare 和 MCP Python SDK 的公募基金数据查询服务。

## 主要功能

1. **基金搜索** - 按代码、名称、拼音搜索基金
2. **详细信息** - 查询基金的净值、业绩、持仓、风险等
3. **业绩排行** - 各类型基金的业绩排行榜
4. **基金评级** - 多家机构的评级数据

## 数据来源

东方财富天天基金网 (fund.eastmoney.com)

## 技术栈

- MCP Python SDK (FastMCP)
- akshare (数据获取)
- FastAPI (HTTP传输)
- pandas (数据处理)

## 使用方法

通过 MCP 客户端（如 Claude Desktop）连接到本服务，即可使用上述工具查询基金信息。
    """

# === 启动服务器 ===

if __name__ == "__main__":
    import sys

    logger.info("")
    logger.info("=" * 70)
    logger.info("🚀 基金信息查询 MCP 服务 (基于 MCP Python SDK)")
    logger.info("=" * 70)
    logger.info("")
    logger.info("📖 服务名称: " + mcp.name)
    logger.info("")
    logger.info("🛠️  可用工具:")
    logger.info("  • search_funds - 搜索基金")
    logger.info("  • get_fund_details - 获取基金详情")
    logger.info("  • get_fund_rankings - 获取排行榜")
    logger.info("  • get_fund_rating - 获取基金评级")
    logger.info("  • get_fund_manager_details - 获取基金经理详情")
    logger.info("  • get_fund_holdings_analysis - 获取持仓动态分析")
    logger.info("  • get_fund_asset_allocation - 获取资产配置")
    logger.info("  • get_fund_fee_details - 获取费用明细")
    logger.info("  • get_fund_liquidity_info - 获取流动性信息")
    logger.info("  • get_industry_valuation_heatmap - 获取行业估值热力图")
    logger.info("  • get_portfolio_deviation - 四账户偏离度分析")
    logger.info("  • get_us_index_valuation - 标普500估值（PE/PB/股息率+历史分位）")
    logger.info("  • get_hk_index_valuation - 港股/中概指数估值")
    logger.info("  • get_portfolio_analysis - 投资组合综合分析")
    logger.info("  • refresh_fund_cache - 刷新缓存")
    logger.info("")
    logger.info("  === 指数查询工具 ===")
    logger.info("  • search_indices_all - 搜索指数")
    logger.info("  • get_index_info - 获取指数基本信息")
    logger.info("  • get_index_details - 获取指数完整详情")
    logger.info("  • get_index_details_batch - 批量获取指数详情")
    logger.info("  • get_index_risk - 获取指数风险分析")
    logger.info("")
    logger.info("  === 沪深港通资金流分析工具 ===")
    logger.info("  • get_capital_flow_summary - 沪深港通今日资金流总览")
    logger.info("  • get_capital_flow_history - 历史资金流趋势分析（默认南向）")
    logger.info("")
    logger.info("📦 可用资源:")
    logger.info("  • fund://list - 基金列表")
    logger.info("  • fund://overview - 服务概述")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")

    # 预加载基金数据
    logger.info("🔄 正在预加载基金数据...")
    try:
        fund_list = fund_tool.get_fund_list()
        if not fund_list.empty:
            logger.info(f"✅ 成功预加载 {len(fund_list)} 只基金数据")
        else:
            logger.warning("⚠️  基金数据预加载失败，将在首次请求时加载")
    except Exception as e:
        logger.error(f"❌ 预加载失败: {e}")

    logger.info("")
    logger.info("🎉 服务已就绪，等待 MCP 客户端连接...")
    logger.info("")

    # 启动 MCP 服务器
    # transport 选项: "stdio", "sse", "streamable-http"
    mcp.run(transport="streamable-http")
