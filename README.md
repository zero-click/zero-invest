# 中国基金信息查询 MCP 服务

基于 **akshare** 和 **MCP Python SDK** 的中国公募基金数据查询服务。

## ✨ 特性

- 🎯 **标准化 MCP 实现** - 使用官方 MCP Python SDK
- 📊 **丰富的基金数据** - 实时净值、历史业绩、持仓分析、风险指标
- 🔬 **专业分析工具** - 基金经理、持仓动态、资产配置、费用、流动性等深度分析
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

### 基础功能

#### 1. `search_funds` - 搜索基金
搜索关键词：基金代码、名称、拼音缩写

#### 2. `get_fund_details` - 基金详情
获取完整信息：净值、业绩、持仓、风险指标等

#### 3. `get_fund_rankings` - 基金排行榜
各类型基金的业绩排行榜

#### 4. `get_fund_rating` - 基金评级
上海证券、招商证券、济安金信等机构评级

#### 5. `refresh_fund_cache` - 刷新缓存
更新基金数据缓存

---

## 🔬 专业分析功能

从专业基金资产管理角度，提供5个核心深度分析功能：

### 1. `get_fund_manager_details` - 基金经理深度信息

**功能描述**
获取基金经理的详细背景信息，帮助评估基金经理的能力和经验。

**返回信息**
- **姓名**: 基金经理姓名
- **所属公司**: 所在基金公司
- **累计从业时间**: 从业天数
- **现任基金资产总规模**: 管理的所有基金资产规模
- **现任基金最佳回报**: 管理基金中的最佳历史回报

**使用场景**
- 评估基金经理的经验水平
- 判断是否"一拖多"（管理过多基金）
- 对比基金经理的历史业绩

**MCP调用**
```json
{
  "tool": "get_fund_manager_details",
  "arguments": {"code": "000001"}
}
```

---

### 2. `get_fund_holdings_analysis` - 持仓动态分析

**功能描述**
分析基金的持仓变化趋势和集中度，了解基金经理的投资风格和调仓频率。

**返回信息**
- **持仓集中度**:
  - 前10大持仓占比
  - 集中度评估（高/中/低）

- **持仓变化趋势**: 按季度展示
  - 季度买入明细
  - 股票名称、代码、买入金额

- **最新持仓**: 当前前10大重仓股列表

**使用场景**
- 判断基金风格（集中 vs 分散）
- 识别基金经理的调仓节奏
- 发现潜在的重仓股风险

**MCP调用**
```json
{
  "tool": "get_fund_holdings_analysis",
  "arguments": {"code": "000001", "periods": 4}
}
```

---

### 3. `get_fund_asset_allocation` - 资产配置结构

**功能描述**
深入了解基金的资产配置结构，包括行业分布、股债比例等。

**返回信息**
- **投资风格**: 成长/价值/平衡型
- **行业配置**: 各行业占净值比例
- **股票持仓样本**: 代表性股票持仓
- **债券持仓样本**: 代表性债券持仓

**使用场景**
- 判断基金的行业偏好
- 评估风险分散程度
- 了解股债配置比例

**MCP调用**
```json
{
  "tool": "get_fund_asset_allocation",
  "arguments": {"code": "000001", "date": "2024"}
}
```

---

### 4. `get_fund_fee_details` - 费用明细

**功能描述**
获取基金的所有费用明细，帮助投资者准确评估投资成本。

**返回信息**
- **认购费率**: 新基金发行时的费率
- **申购费率**: 日常申购费率（可能分档）
- **赎回费率**: 按持有期限分档
- **管理费率**: 年度管理费用
- **托管费率**: 年度托管费用

**使用场景**
- 计算投资成本
- 对比不同基金的费用
- 评估费用对收益的影响

**MCP调用**
```json
{
  "tool": "get_fund_fee_details",
  "arguments": {"code": "000001"}
}
```

---

### 5. `get_fund_liquidity_info` - 流动性信息

**功能描述**
了解基金的流动性状况和交易规则，确保资金安排合理。

**返回信息**
- **申赎状态**: 开放/暂停
- **申赎时间**: T+N确认模式
- **交易场所**: 场外/场内
- **最低申购金额**: 起购门槛
- **申购确认时间**: 确认时长
- **赎回到账时间**: 资金到账时长

**使用场景**
- 规划资金进出时间
- 避免申赎限制影响资金使用
- 选择适合的基金类型

**MCP调用**
```json
{
  "tool": "get_fund_liquidity_info",
  "arguments": {"code": "000001"}
}
```

---

## 💻 命令行使用

本项目也可以作为独立的命令行工具使用：

### 基础命令

```bash
# 搜索基金
python fund_tool_akshare.py search "华夏"

# 查询详情（基本信息）
python fund_tool_akshare.py query 000001

# 查询完整详情（包含所有专业分析）⭐ 推荐
python fund_tool_akshare.py query 000001 --detail
python fund_tool_akshare.py query 000001 -d

# 查看排行榜
python fund_tool_akshare.py ranking --type 股票型 --top 10

# 查询评级
python fund_tool_akshare.py rating 000001
```

### 专业分析命令

如果只需要特定维度的分析，可以使用单独的命令：

```bash
# 基金经理详情
python fund_tool_akshare.py manager 000001

# 持仓动态分析
python fund_tool_akshare.py holdings 000001 --periods 4

# 资产配置结构
python fund_tool_akshare.py allocation 000001 --year 2024

# 费用明细
python fund_tool_akshare.py fee 000001

# 流动性信息
python fund_tool_akshare.py liquidity 000001
```

**完整命令行指南**: 查看 [CLI_GUIDE.md](CLI_GUIDE.md)

## 📁 项目结构

```
ttjj-fund/
├── fund_tool_akshare.py    # 核心数据获取逻辑 + CLI工具
├── fund_mcp_server.py      # MCP 服务器
├── requirements.txt        # 依赖列表
├── mcp_manifest.json       # MCP 清单
├── start_mcp.sh            # 启动脚本
├── pytest.ini             # 测试配置
├── test_fund_tool.py      # 测试文件
├── QUICKSTART.md          # 快速指南
├── CLI_GUIDE.md           # 命令行使用指南
└── README.md              # 本文档
```

## 🧪 测试

```bash
# 运行所有测试
pytest test_fund_tool.py -v

# 运行特定功能测试
pytest test_fund_tool.py::TestGetFundManagerDetails -v
pytest test_fund_tool.py::TestGetFundHoldingsAnalysis -v
pytest test_fund_tool.py::TestGetFundAssetAllocation -v
pytest test_fund_tool.py::TestGetFundFeeDetails -v
pytest test_fund_tool.py::TestGetFundLiquidityInfo -v

# 生成覆盖率报告
pytest test_fund_tool.py --cov=fund_tool_akshare --cov-report=html
```

测试覆盖：30个测试用例，包括原有功能和新增专业分析功能。

## 📚 更多文档

- [QUICKSTART.md](QUICKSTART.md) - 快速开始指南
- [CLI_GUIDE.md](CLI_GUIDE.md) - 命令行完整使用指南
- [TEST_REPORT.md](TEST_REPORT.md) - 测试报告说明

## 📖 参考资料

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://modelcontextprotocol.github.io/python-sdk/)
- [akshare 文档](https://akshare.akfamily.xyz/)

## ⚠️ 注意事项

1. 部分数据可能存在延迟，具体以基金公司公告为准
2. 费率信息可能调整，请以基金合同和最新公告为准
3. 持仓数据通常按季度更新，存在一定滞后性
4. 建议结合多个维度进行综合分析，不应依赖单一指标

---

**版本**: v2.1
**更新日期**: 2026-01-20
**注意**: 本服务仅供学习和研究使用，不构成投资建议。
