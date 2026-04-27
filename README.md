# 中国基金和指数信息查询 MCP 服务

基于 **akshare** 和 **MCP Python SDK** 的中国公募基金和A股指数数据查询服务，可作为 **MCP 工具**接入 Claude Desktop，也可作为**独立 CLI** 使用。

## 🎯 核心能力

### 1. 基金深度分析

本项目的第一个核心能力是**获取单只基金的完整信息**，通过一个命令即可获得基金的全方位分析：

```bash
# CLI 方式
python cli.py bond query 000001 --detail

# MCP 方式（在 Claude Desktop 中）
get_fund_details(code="000001", detail=True)
```

**一次性获取以下所有信息：**

| 类别 | 数据项 |
|------|--------|
| 📋 **基本信息** | 基金代码、名称、类型、成立日期、规模、基金经理 |
| 📈 **业绩表现** | 近1周/1月/3月/6月/1年/3年/今年/成立以来收益率 |
| ⚠️ **风险指标** | 标准差、夏普比率、最大回撤等 |
| 💰 **费率信息** | 管理费、托管费、申购费、赎回费详细表 |
| 💼 **十大重仓股** | 最新前10大持仓股票及占比 |
| 👤 **基金经理详情** | 从业年限、管理规模、最佳回报、现任基金 |
| 📊 **持仓分析** | 前10大持仓集中度、本年+前一年季度持仓变化 |
| 🎯 **资产配置** | 行业配置分布、股票/债券持仓样本 |
| 💰 **费用明细** | 申购费率表、赎回费率表、管理费率、托管费率 |
| 💧 **流动性信息** | 申赎状态、交易时间、最低金额、到账时间 |
| ⭐ **基金评级** | 上海证券、招商证券、济安金信、晨星等机构评级 |

### 2. 指数查询/估值/风险 ⭐

第二个核心能力是将指数分析拆分为 `query / valuation / risk` 三段，并支持 `query -d` 一次输出全量信息：

```bash
# CLI 方式
python cli.py index query 000300
python cli.py index valuation 000300
python cli.py index risk 000300
python cli.py index query 000300 -d

# MCP 方式（在 Claude Desktop 中）
get_index_details(code="000300")
```

**一次性获取以下所有信息：**

| 类别 | 数据项 |
|------|--------|
| 📊 **基本信息** | 指数代码、名称、分类（宽基/行业/主题/策略/风格）、发布日期 |
| 💹 **当前值** | 收盘点位、日期、涨跌幅 |
| 📈 **业绩表现** | 近1周/1月/3月/6月/1年/3年/今年收益率 |
| 💰 **估值数据** | PE-TTM、PB |
| 📊 **历史分位** | PE/PB 的3年/5年/10年历史百分位 |
| 🌡️ **估值等级** | 极度低估 ~ 极度高估（7级温度计） |
| 📍 **数据源** | 乐咕乐股 or 中证指数 |

**适用场景：**
- 投资者进行指数配置决策
- 理财顾问快速获取指数资料
- 量化研究和因子分析
- 指数对比和筛选

---

## 其他功能

除了核心的基金和指数深度分析，还提供以下辅助功能：

- **基金搜索** — 按代码/名称/拼音搜索（26000+ 基金）
- **指数搜索** — 按代码/名称搜索（1500+ A股指数）
- **业绩排行** — 各类型基金业绩排行榜
- **机构评级** — 多家评级机构评级汇总
- **专项查询** — 单独查看业绩、风险、重仓股、费用等
- **指数估值** — 宽基与行业指数 PE/PB 历史分位

## ✨ 特性

- 🎯 **标准化 MCP 实现** - 使用官方 MCP Python SDK（FastMCP）
- 📊 **丰富的基金数据** - 覆盖 26000+ 只公募基金
- 🔬 **专业级分析** - 基金经理、持仓动态、资产配置、费用、流动性深度分析
- 💾 **本地智能缓存** - 基金列表缓存到本地 JSON（7天 TTL）
- 🔌 **多种传输协议** - 支持 stdio、streamable-http
- 🚀 **模块化设计** - 清晰的代码结构，易于扩展

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
python cli.py bond update
# 从东方财富拉取全量基金列表（26000+）并保存到 fund_database.json
# 此后 CLI 调用直接读本地文件，搜索速度极快
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

### 核心工具

| 工具 | 说明 |
|------|------|
| **基金分析** ||| `get_fund_details` | **完整基金分析**（包含所有专业分析） |
| `search_funds` | 按代码、名称、拼音搜索基金 |
| `get_fund_portfolio_analysis` | **投资组合完整分析**（持仓+资产配置合并） |
| **指数分析** ||| `get_index_details` | **指数完整详情**（当前值、业绩、PE/PB、历史分位） ⭐ |
| `search_indices` | 按代码、名称搜索指数（1500+ A股指数） |
| `get_index_info` | 指数基本信息 |
| `get_index_details_batch` | 批量查询指数详情 |

### 专项分析工具

| 工具 | 说明 |
|------|------|
| `get_fund_performance` | 业绩表现（各时间段收益率） |
| `get_fund_risk_metrics` | 风险指标（标准差、夏普比率等） |
| `get_fund_top_holdings` | 十大重仓股 |
| `get_fund_manager_details` | 基金经理详情 |
| `get_fund_fee_details` | 费用明细（申购/赎回/管理/托管费） |
| `get_fund_liquidity_info` | 流动性信息（申赎状态、到账时间） |
| `get_fund_asset_allocation` | 资产配置结构（行业配置、股债分布） |
| `get_fund_holdings_analysis` | 持仓动态分析（集中度、季度变化） |

### 辅助工具

| 工具 | 说明 |
|------|------|
| `get_fund_rankings` | 各类型基金业绩排行榜 |
| `get_fund_rating` | 上海证券、招商证券、济安金信等评级 |
| `refresh_fund_cache` | 强制刷新本地基金数据库 |

### 指数工具

| 工具 | 说明 |
|------|------|
| `search_indices` | 搜索指数（1500+ A股指数） |
| `get_index_info` | 指数基本信息 |
| `get_index_details` | **指数完整详情**（当前值、业绩、PE/PB、分位） |
| `get_index_details_batch` | 批量查询指数详情 |

## 💻 命令行使用

### 基金查询命令

```bash
# 搜索基金
python cli.py bond search "华夏"

# 查询基金详情
python cli.py bond query 000001
python cli.py bond query 000001 --detail

# 排行榜
python cli.py bond ranking --type 股票型 --top 10

# 基金经理
python cli.py bond manager 000001

# 投资组合分析
python cli.py bond portfolio 000001

# 更新数据库
python cli.py bond update
```

### 指数查询命令 ⭐

```bash
# 搜索指数
python cli.py index search "红利"
python cli.py index search "300"

# 指数查询（基本信息 + 当前值 + 业绩）
python cli.py index query 000300

# 指数估值
python cli.py index valuation 000300

# 指数风险
python cli.py index risk 000300

# 一次输出完整信息
python cli.py index query 000300 -d

# 批量查询指数详情
python cli.py index batch 000300 000905 000852
```

---

## 📖 完整命令参考

### 基金查询（bond 命名空间）

```bash
# 搜索基金
python cli.py bond search <keyword>
python cli.py bond search "华夏" --all

# 查询基金
python cli.py bond query <code>
python cli.py bond query 000001 --detail

# 排行榜
python cli.py bond ranking --type 股票型 --top 10

# 专项查询
python cli.py bond performance <code>
python cli.py bond risk <code>
python cli.py bond top-holdings <code>
python cli.py bond manager <code>
python cli.py bond fee <code>
python cli.py bond liquidity <code>

# 投资组合分析
python cli.py bond holdings <code>
python cli.py bond allocation <code>
python cli.py bond portfolio <code>

# 更新数据库
python cli.py bond update
```

### 指数查询（index 命名空间）

```bash
# 搜索指数
python cli.py index search <keyword>
python cli.py index search "红利" --all

# 查询基础信息（基本信息 + 当前值 + 业绩）
python cli.py index query <code>
python cli.py index query 000300

# 查询估值模块
python cli.py index valuation <code>
python cli.py index valuation 000300

# 查询风险模块
python cli.py index risk <code>
python cli.py index risk 000300

# 查询完整信息
python cli.py index query <code> -d
python cli.py index query 000300 -d

# 批量查询
python cli.py index batch <code1> <code2> ...
python cli.py index batch 000300 000905 000852
```

---

## 🎯 使用示例

### 示例 1：基金深度分析

```bash
# 获取基金的完整分析
python cli.py bond query 000001 --detail
```

输出包含：
- 📋 基本信息（名称、类型、规模、经理）
- 📈 业绩表现（1周~成立以来收益率）
- ⚠️ 风险指标（标准差、夏普比率）
- 💼 十大重仓股
- 👤 基金经理详情
- 💰 费用明细
- 💧 流动性信息

### 示例 2：指数估值分析

```bash
# 获取指数估值模块
python cli.py index valuation 000300
```

输出包含：
- 💰 估值数据（PE-TTM、PB）
- 📊 历史分位（3年/5年/10年百分位）
- 📏 10年历史参考（当前/中位数/最低/最高）
- 🌡️ 估值温度（低估/合理/高估）

### 示例 3：批量指数对比

```bash
# 批量查询多个指数
python cli.py index batch 000300 000905 000852
```

可以快速对比不同指数的：
- 收盘点位
- 收益率表现
- 估值分位
- 估值温度

---

## 🎓 数据源说明

### 投资组合分析（推荐）

```bash
# 获取完整的投资组合分析（持仓+资产配置）
python cli.py bond portfolio 000001
```

### 专项查询

```bash
# 基金业绩
python cli.py bond performance 000001

# 风险指标
python cli.py bond risk 000001

# 十大重仓股
python cli.py bond top-holdings 000001

# 基金经理
python cli.py bond manager 000001

# 费用明细
python cli.py bond fee 000001

# 流动性信息
python cli.py bond liquidity 000001

# 基金评级
python cli.py bond rating 000001
```

### 基础功能

```bash
# 更新本地基金数据库
python cli.py bond update

# 搜索基金
python cli.py bond search "华夏"

# 排行榜
python cli.py bond ranking --type 股票型 --top 10
```

### Debug 模式

```bash
# 显示详细日志
python cli.py --debug bond query 000001
```

## 📊 数据来源说明

- **基金列表**：东方财富（26000+ 只基金）
- **基金详情**：东方财富、天天基金
- **持仓数据**：按季度更新，存在滞后性
- **业绩数据**：每日更新
- **费率信息**：基金合同和公告

### 持仓变化说明

持仓变化功能会自动获取**本年和前一年**的完整季度数据：
- 如果查询年份为 2026，会获取 2025 + 2026 两年的持仓变化
- 如果查询年份为 2025，会获取 2024 + 2025 两年的持仓变化

## 📁 项目结构

## TODO

- [ ] 新增“候选基金对比表”函数 `compare_index_funds(index_code: str)`，输出字段至少包含：基金代码、名称、管理费、托管费、规模、近1年收益、ETF 成交额、折溢价。
- [ ] 新增“跟踪误差”函数 `calc_tracking_error(fund_code, index_code, window=252)`，按“基金日收益 - 指数日收益”的年化标准差计算。
- [ ] 新增 CLI 命令 `python cli.py index funds 000300`，输出候选列表、对比表和简短结论。

```
ttjj-fund/
├── cli.py                       # 命令行入口
├── fund_mcp_server.py           # MCP 服务器
├── requirements.txt
├── start_mcp.sh
├── pytest.ini
├── src/
│   └── fund_tools/
│       ├── __init__.py
│       ├── cache.py             # 基金列表缓存
│       ├── search.py            # 基金搜索
│       ├── details.py           # 基金详情
│       ├── rankings.py          # 排行榜
│       ├── managers.py          # 基金经理
│       ├── holdings.py          # 持仓分析
│       ├── allocation.py        # 资产配置
│       ├── fees.py              # 费用明细
│       ├── liquidity.py         # 流动性信息
│       ├── core.py              # 核心函数（已合并）
│       └── performance.py       # 业绩分析
└── tests/
    ├── conftest.py
    └── test_fund_tools.py       # 集成测试
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/test_fund_tools.py -v

# 运行特定测试类
pytest tests/test_fund_tools.py::TestFundPortfolioAnalysis -v

# 覆盖率报告
pytest --cov=src/fund_tools --cov-report=html
```

**测试覆盖：**
- ✅ 58 个测试用例全部通过
- ✅ 包含真实 API 集成测试
- ✅ 核心功能完整覆盖

## 🔧 故障排除

**SSL 证书错误**：某些数据源偶发 SSL 错误，不影响核心功能（东方财富数据源正常）。

**依赖安装失败**：
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

**虚拟环境未激活**：
```bash
source .venv/bin/activate
```

**基金数据未找到**：
```bash
# 更新本地数据库
python cli.py bond update
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
5. 持仓变化数据会获取本年和前一年的完整数据

---

**版本**: v2.4 | **更新日期**: 2026-04-27

## 📝 更新日志

### v2.4 (2026-04-27)
- ♻️ CLI 指数入口重构为 `query / valuation / risk`
- 🧩 新增 `python cli.py index query <code> -d` 全量输出
- 🧹 移除旧 `index details` / `index info` CLI 入口
- 🗑️ 移除 `src/fund_tools/valuation.py`，估值逻辑合并到 `src/fund_tools/index.py`

### v2.3 (2026-04-26)
- ✨ **核心功能重构**：合并持仓分析和资产配置为单一函数
- 🚀 **性能优化**：减少重复 API 调用，提升查询效率
- 📊 **持仓变化增强**：自动获取本年和前一年的完整数据
- 🐛 **Bug 修复**：修复 akshare 认购费率 bug，移除有问题的接口
- ✅ **测试完善**：新增投资组合分析测试，58 个测试全部通过

### v2.2 (2026-04-19)
- 初始 MCP 服务实现
