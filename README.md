# 中国基金信息查询 MCP 服务

基于 **akshare** 和 **MCP Python SDK** 的中国公募基金数据查询服务，可作为 **MCP 工具**接入 Claude Desktop，也可作为**独立 CLI** 使用。

主要功能：
- **基金搜索与详情** — 按代码/名称/拼音搜索，查询净值、业绩、风险指标、十大重仓股
- **专业分析** — 基金经理背景、持仓集中度与季度变化、行业配置、费用明细、流动性信息
- **排行榜与评级** — 各类型基金业绩排行、上海证券/招商证券/晨星等多家机构评级
- **指数估值** — 宽基与行业指数 PE/PB 历史分位（10年/5年/3年）、估值温度计

## ✨ 特性

- 🎯 **标准化 MCP 实现** - 使用官方 MCP Python SDK（FastMCP）
- 📊 **丰富的基金数据** - 实时净值、历史业绩、持仓分析、风险指标
- 🔬 **专业分析工具** - 基金经理、持仓动态、资产配置、费用、流动性深度分析
- 💹 **指数估值** - 宽基/行业指数 PE/PB 历史分位、估值温度计
- 💾 **本地磁盘缓存** - 基金列表缓存到本地 JSON（7天 TTL），CLI 调用无需重复联网
- 🔌 **多种传输协议** - 支持 stdio、streamable-http

## 🛠️ 技术栈

- **MCP Python SDK** - Model Context Protocol 官方实现
- **akshare** - 中国金融数据接口
- **pandas/numpy** - 数据处理

## 📦 快速开始

### 1. 安装依赖

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 初始化本地基金数据库（推荐）

```bash
python fund_tool_akshare.py update
# 从东方财富拉取全量基金列表并保存到 fund_database.json
# 此后 CLI 调用直接读本地文件，无需联网
```

### 3. 启动 MCP 服务

```bash
# 方式一：交互式启动脚本（可选传输协议）
./start_mcp.sh

# 方式二：直接运行（streamable-http，默认端口 8000）
python fund_mcp_server.py
```

用 MCP Inspector 调试：

```bash
npx -y @modelcontextprotocol/inspector
# 连接到: http://localhost:8000/mcp
```

### 4. 配置 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fund-info": {
      "command": "/path/to/ttjj-fund/.venv/bin/python",
      "args": ["/path/to/ttjj-fund/fund_mcp_server.py"]
    }
  }
}
```

将 `/path/to/ttjj-fund` 替换为实际路径，重启 Claude Desktop 即可使用。

## 🛠️ 可用工具（MCP）

| 工具 | 说明 |
|------|------|
| `search_funds` | 按代码、名称、拼音搜索基金 |
| `get_fund_details` | 净值、业绩、持仓、风险指标 |
| `get_fund_rankings` | 各类型基金业绩排行榜 |
| `get_fund_rating` | 上海证券、招商证券、济安金信等评级 |
| `get_fund_manager_details` | 经理从业年限、管理规模、最佳回报 |
| `get_fund_holdings_analysis` | 持仓集中度、季度持仓变化趋势 |
| `get_fund_asset_allocation` | 行业配置、股债持仓分布 |
| `get_fund_fee_details` | 认购/申购/赎回/管理/托管费率 |
| `get_fund_liquidity_info` | 申赎状态、到账时间、最低申购额 |
| `refresh_fund_cache` | 强制刷新本地基金数据库 |

## 💹 指数估值（`index_valuation.py`）

```python
from index_valuation import get_index_pe, get_portfolio_index_valuation

# 单个指数（PE/PB + 10/5/3年历史分位）
result = get_index_pe("沪深300")

# 一键获取投资组合相关所有指数估值
result = get_portfolio_index_valuation()
```

支持的宽基指数：沪深300、中证500、中证1000、上证50、创业板50 等。
支持的行业指数：科创50、中证军工、有色金属、中证白酒、全指医药、中证半导 等。

## 💻 命令行使用

```bash
# 更新本地基金数据库
python fund_tool_akshare.py update

# 搜索基金
python fund_tool_akshare.py search "华夏"

# 查询基金详情
python fund_tool_akshare.py query 000001
python fund_tool_akshare.py query 000001 --detail   # 含所有专业分析

# 排行榜
python fund_tool_akshare.py ranking --type 股票型 --top 10

# 评级
python fund_tool_akshare.py rating 000001

# 专项分析
python fund_tool_akshare.py manager 000001
python fund_tool_akshare.py holdings 000001 --periods 4
python fund_tool_akshare.py allocation 000001 --year 2024
python fund_tool_akshare.py fee 000001
python fund_tool_akshare.py liquidity 000001
```

## 📁 项目结构

```
ttjj-fund/
├── fund_tool_akshare.py    # 核心数据获取逻辑 + CLI
├── fund_mcp_server.py      # MCP 服务器
├── index_valuation.py      # 指数估值模块（PE/PB历史分位）
├── requirements.txt
├── start_mcp.sh
├── pytest.ini
├── tests/
│   ├── conftest.py
│   ├── test_fund_tool.py
│   └── test_index_valuation.py
└── README.md
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定模块
pytest tests/test_fund_tool.py -v
pytest tests/test_index_valuation.py -v

# 覆盖率报告
pytest --cov=fund_tool_akshare --cov-report=html
```

## 🔧 故障排除

**SSL 证书错误**：雪球网数据接口偶发 SSL 错误，不影响核心功能（东方财富数据源正常）。

**依赖安装失败**：
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

**虚拟环境未激活**：
```bash
source .venv/bin/activate
```

## 📖 参考资料

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://modelcontextprotocol.github.io/python-sdk/)
- [akshare 文档](https://akshare.akfamily.xyz/)

## ⚠️ 注意事项

1. 部分数据可能存在延迟，具体以基金公司公告为准
2. 费率信息可能调整，请以基金合同和最新公告为准
3. 持仓数据通常按季度更新，存在一定滞后性
4. 本服务仅供学习和研究使用，不构成投资建议

---

**版本**: v2.2 | **更新日期**: 2026-04-19

