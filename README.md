# 中国基金信息查询 MCP 服务

基于 **akshare** 和 **MCP Python SDK** 的中国公募基金数据查询服务。

## ✨ 特性

- 🎯 **标准化 MCP 实现** - 使用官方 MCP Python SDK
- 📊 **丰富的基金数据** - 实时净值、历史业绩、持仓分析、风险指标
- 🚀 **简单易用** - 装饰器语法定义工具，代码简洁清晰
- 🔌 **多种传输协议** - 支持 stdio、SSE、HTTP
- 💾 **智能缓存** - 自动缓存基金列表，提升响应速度

## 🛠️ 技术栈

- **MCP Python SDK** - Model Context Protocol 官方实现
- **akshare** - 中国金融数据接口
- **pandas/numpy** - 数据处理

## 📦 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 方式一：使用启动脚本（推荐）
./start_mcp.sh

# 方式二：直接运行
python fund_mcp_server.py
```

### 3. 配置 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fund-info": {
      "command": "python",
      "args": ["/Users/woosleyxu/code/ttjj-fund/fund_mcp_server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

重启 Claude Desktop 即可使用。

## 🛠️ 可用工具

### 1. `search_funds` - 搜索基金
搜索关键词：基金代码、名称、拼音缩写

### 2. `get_fund_details` - 基金详情
获取完整信息：净值、业绩、持仓、风险指标等

### 3. `get_fund_rankings` - 基金排行榜
各类型基金的业绩排行榜

### 4. `get_fund_rating` - 基金评级
上海证券、招商证券、济安金信等机构评级

### 5. `refresh_fund_cache` - 刷新缓存
更新基金数据缓存

## 📁 项目结构

```
ttjj-fund/
├── fund_tool_akshare.py    # 核心数据获取逻辑
├── fund_mcp_server.py      # MCP 服务器
├── requirements.txt        # 依赖列表
├── mcp_manifest.json       # MCP 清单
├── start_mcp.sh            # 启动脚本
├── pytest.ini             # 测试配置
├── test_fund_tool.py      # 测试文件
├── QUICKSTART.md          # 快速指南
└── README.md              # 本文档
```

## 🧪 测试

```bash
# 运行测试
pytest test_fund_tool.py -v

# 生成覆盖率报告
pytest test_fund_tool.py --cov=fund_tool_akshare --cov-report=html
```

## 📚 更多文档

- [README_MCP.md](README_MCP.md) - 详细的 MCP 使用文档
- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南
- [TEST_REPORT.md](TEST_REPORT.md) - 测试报告说明

## 📖 参考资料

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://modelcontextprotocol.github.io/python-sdk/)
- [akshare 文档](https://akshare.akfamily.xyz/)

---

**注意**: 本服务仅供学习和研究使用，不构成投资建议。
