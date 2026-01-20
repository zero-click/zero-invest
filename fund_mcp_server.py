# -*- coding: utf-8 -*-
"""
基于 MCP Python SDK 的基金信息查询服务器
使用 FastMCP 快速创建符合 MCP 标准的服务
"""

from mcp.server.fastmcp import FastMCP
import logging
from typing import Optional
import fund_tool_akshare as fund_tool

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

    # 清除缓存
    fund_tool.get_fund_list.cache_clear()
    fund_tool.search_funds.cache_clear()

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
    logger.info("  • refresh_fund_cache - 刷新缓存")
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
