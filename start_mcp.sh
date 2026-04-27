#!/bin/bash

# =================================================================
# 基金信息查询 MCP 服务 - 启动脚本 (基于 MCP Python SDK)
# =================================================================

set -e

echo ""
echo "======================================================================"
echo "🚀 基金信息查询 MCP 服务 - 启动脚本"
echo "======================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "${BLUE}📋 检查 Python 环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 Python 3，请先安装 Python 3.10+${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✅ Python 版本: $PYTHON_VERSION${NC}"
echo ""

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}⚠️  建议在虚拟环境中运行${NC}"
    echo ""
    echo "创建虚拟环境:"
    echo "  python3 -m venv .venv"
    echo "  source .venv/bin/activate  # Linux/macOS"
    echo "  .venv\\Scripts\\activate     # Windows"
    echo ""
    read -p "是否继续？(y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 安装依赖
echo -e "${BLUE}📦 检查并安装依赖...${NC}"
if [ -f "requirements.txt" ]; then
    echo "正在安装依赖包..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${RED}❌ 未找到 requirements.txt${NC}"
    exit 1
fi
echo ""

# 测试 MCP SDK 导入
echo -e "${BLUE}🔍 测试 MCP SDK...${NC}"
python3 -c "import mcp; print('✅ MCP SDK 版本:', mcp.__version__)" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  MCP SDK 未安装，正在安装...${NC}"
    pip install mcp
}
echo ""

# 选择传输协议
echo ""
echo "======================================================================"
echo -e "${BLUE}选择传输协议:${NC}"
echo "======================================================================"
echo ""
echo "1) streamable-http - HTTP 传输 (推荐用于开发和测试)"
echo "   服务地址: http://localhost:8000/mcp"
echo "   可以用浏览器和 MCP Inspector 访问"
echo ""
echo "2) stdio - 标准输入输出 (推荐用于生产环境)"
echo "   通过 stdin/stdout 与 Claude Desktop 等客户端通信"
echo ""
read -p "请选择 (1 或 2，默认 1): " transport_choice
transport_choice=${transport_choice:-1}

if [ "$transport_choice" = "2" ]; then
    TRANSPORT="stdio"
    echo -e "${GREEN}✅ 使用 stdio 传输${NC}"
else
    TRANSPORT="streamable-http"
    echo -e "${GREEN}✅ 使用 streamable-http 传输${NC}"
fi
echo ""

# 预热数据
echo -e "${BLUE}🔄 预热数据缓存（可选）...${NC}"
read -p "是否预热数据？这可能需要10-30秒 (y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 -c "from src.fund_tools import get_fund_list; get_fund_list()" && {
        echo -e "${GREEN}✅ 数据预热完成${NC}"
    } || {
        echo -e "${YELLOW}⚠️  数据预热失败，服务启动时将自动加载${NC}"
    }
else
    echo "跳过数据预热"
fi
echo ""

# 启动服务
echo "======================================================================"
echo -e "${GREEN}🎉 正在启动 MCP 服务器...${NC}"
echo "======================================================================"
echo ""

if [ "$TRANSPORT" = "streamable-http" ]; then
    echo "服务信息:"
    echo "  • MCP 端点: http://localhost:8000/mcp"
    echo "  • 传输协议: streamable-http"
    echo ""
    echo "测试方法:"
    echo "  1. 安装 MCP Inspector:"
    echo "     npx -y @modelcontextprotocol/inspector"
    echo "  2. 在 Inspector 中连接到: http://localhost:8000/mcp"
    echo ""
else
    echo "服务信息:"
    echo "  • 传输协议: stdio"
    echo "  • 通信方式: 标准输入输出"
    echo ""
    echo "配置方法 (Claude Desktop):"
    echo "  在 claude_desktop_config.json 中添加:"
    echo ''
    echo '  {'
    echo '    "mcpServers": {'
    echo '      "fund-info": {'
    echo '        "command": "python3",'
    echo '        "args": ["/path/to/fund_mcp_server.py"]'
    echo '      }'
    echo '    }'
    echo '  }'
    echo ''
fi

echo "按 Ctrl+C 停止服务"
echo ""
echo "======================================================================"
echo ""

# 设置传输协议环境变量
export MCP_TRANSPORT=$TRANSPORT

# 启动服务器
python3 fund_mcp_server.py
