# ttjj-fund 项目文档

## 项目概述

**ttjj-fund** 是基于 **akshare** 和 **MCP Python SDK** 的中国公募基金与 A 股指数数据查询服务，可作为 MCP 工具接入 Claude Desktop，也可作为独立 CLI 使用。

**核心能力：**
- 通过一个命令获取单只基金的完整分析报告（基本信息、业绩、风险、持仓、费用、评级等 11 个维度）
- 管理 A 股指数数据库，查询指数基本面、估值、风险、候选基金池和估值热力图

## 技术栈

- **MCP Python SDK (FastMCP)** - Model Context Protocol 官方实现
- **akshare** - 中国金融数据接口
- **pandas/numpy** - 数据处理
- **pytest** - 测试框架（58 个集成测试）

## 项目结构

```
ttjj-fund/
├── cli.py                       # CLI 入口（命令行接口）
├── fund_mcp_server.py           # MCP 服务器（Claude Desktop 接口）
├── requirements.txt
├── README.md                    # 用户文档
├── CLAUDE.md                    # 本文件（AI 助手项目文档）
│
├── src/fund_tools/              # 核心业务逻辑模块
│   ├── __init__.py
│   ├── cache.py                 # 基金/指数本地缓存
│   ├── core.py                  # 基金核心函数
│   ├── index.py                 # 指数查询、估值、风险、历史行情
│   └── industry_valuation.py    # 指数估值热力图
└── tests/
    ├── conftest.py
    └── test_*.py                # 单元测试 + 真实 API 集成测试
```

## 核心功能模块

### 1. 基金深度分析（核心能力）

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

**适用场景：**
- 投资者进行基金研究和决策
- 理财顾问快速获取基金资料
- 数据分析和量化研究
- 基金对比和筛选


**主函数：** `get_fund_details(code: str, year: str, detail: bool = False)`

- **标准模式**：基本信息 + 业绩表现
- **完整模式** (`detail=True`)：额外包含持仓、风险、费用、流动性、评级等

**完整模式调用路径：**
```python
get_fund_details(code, year, detail=True)
  ├── get_fund_performance(code)          # 业绩
  ├── get_fund_risk_metrics(code)         # 风险
  ├── get_fund_top_holdings(code)         # 重仓股
  ├── get_fund_manager_details(code)      # 基金经理
  ├── get_fund_fee_details(code)          # 费用
  ├── get_fund_liquidity_info(code)       # 流动性
  ├── get_fund_asset_allocation(code)     # 资产配置
  ├── get_fund_holdings_analysis(code)    # 持仓分析（向后兼容）
  └── get_fund_portfolio_analysis(code)   # 投资组合分析（合并函数）
```

### 2. 指数管理与分析（核心能力）

指数模块负责维护本地指数数据库，并提供指数查询、估值、风险、候选基金池和热力图能力。

**本地指数数据库：**
- 缓存文件：`index_database.json`
- 缓存模块：`src/fund_tools/cache.py`
- 缓存策略：多源聚合、按指数代码去重、30 天 TTL、`cache_version` 控制结构升级
- 数据源：中证指数、东方财富指数实时行情、Sina 指数实时行情、akshare 指数信息表
- 目标：解决单一 `ak.index_csindex_all()` 覆盖不足的问题，例如补齐上证50、创业板50等常见宽基指数

**指数分析能力：**

| 类别 | 数据项 |
|------|--------|
| 基本信息 | 指数代码、名称、分类、指数类别、发布日期 |
| 当前值 | 收盘点位、日期、涨跌幅 |
| 业绩表现 | 近1周/1月/3月/6月/1年/3年/今年收益率 |
| 估值数据 | PE-TTM、PB、股息率、历史分位、估值温度 |
| 风险分析 | 波动率、最大回撤、回撤修复周期、夏普比率 |
| 候选基金池 | 按指数匹配对应指数基金候选列表 |
| 估值热力图 | 宽基 + 行业估值表，支持按 PE/PB/股息率/估值等级排序 |

**核心函数：**
```python
get_index_query(code)                   # 基本信息 + 当前值 + 业绩
get_index_valuation(code)               # 估值 + 股息率 + 分位 + 口径规则
get_index_risk(code)                    # 波动率 + 回撤 + 夏普 + 修复周期
get_index_details(code)                 # 查询 + 估值聚合
get_index_details_batch(codes)          # 批量查询详情
get_index_candidate_funds(code)         # 指数候选基金池
get_valuation_heatmap(category, sort_by) # 指数估值热力图
```

**历史行情容错：**
- 优先使用中证指数历史行情
- 中证历史行情缺失时 fallback 到东方财富 `ak.index_zh_a_hist`
- 乐咕乐股用于宽基 PE/PB 历史分位，失败时不应阻断整体热力图输出

## CLI 使用

### 基本命令

```bash
# 更新本地基金数据库（26000+ 基金）
python cli.py bond update

# 搜索基金
python cli.py bond search "华夏"

# 查询基金（标准模式）
python cli.py bond query 000001

# 查询基金（完整模式 - 包含所有专业分析）
python cli.py bond query 000001 --detail

# 投资组合完整分析
python cli.py bond portfolio 000001

# 专项查询
python cli.py bond performance 000001
python cli.py bond risk 000001
python cli.py bond top-holdings 000001
python cli.py bond manager 000001
python cli.py bond fee 000001
python cli.py bond liquidity 000001

# 指数查询
python cli.py index update
python cli.py index search "红利"
python cli.py index query 000300
python cli.py index valuation 000300
python cli.py index risk 000300
python cli.py index query 000300 -d
python cli.py index listfund 000300
python cli.py index heatmap
python cli.py index heatmap --sort-by pb --limit 20
python cli.py index batch 000300 000905 000852

# Debug 模式（显示详细日志）
python cli.py --debug bond query 000001
```

### 指数命令说明

```bash
# 更新多源指数数据库
python cli.py index update

# 搜索指数
python cli.py index search "红利"
python cli.py index search "上证50" --all

# 查询指数基本信息、当前值、业绩
python cli.py index query 000300

# 查询指数完整信息（query + valuation + risk）
python cli.py index query 000300 -d

# 单独查询估值模块
python cli.py index valuation 000300

# 单独查询风险模块
python cli.py index risk 000300

# 查询指数候选基金池
python cli.py index listfund 000300
python cli.py index listfund 000300 --all

# 估值热力图
python cli.py index heatmap
python cli.py index heatmap --category 宽基 --sort-by pe --limit 30
python cli.py index heatmap --sort-by pb --limit 20

# 批量查询
python cli.py index batch 000300 000905 000852
```

## MCP 服务

### 启动方式

```bash
# 交互式启动（选择传输协议）
./start_mcp.sh

# 直接启动（streamable-http，端口 8000）
python fund_mcp_server.py
```

## 代码规范

### 函数设计原则

1. **单个职责**：每个函数只做一件事
2. **避免重复 API 调用**：合并相似功能（如 `get_fund_portfolio_analysis`）
3. **向后兼容**：重构后保留旧函数作为包装器
4. **统一返回格式**：所有函数返回 `dict`，包含 `status` 字段（`"success"` 或 `"error"`）
5. **显式传时间参数**：调用 akshare 的历史行情、估值、快照类函数时，必须检查 `start_date` / `end_date` / `date` 等时间参数，显式传入当前业务需要的时间窗口，不能依赖库函数默认值

### 返回格式示例

```python
# 成功
{
    "status": "success",
    "code": "000001",
    "name": "华夏成长混合",
    # ... 其他字段
}

# 失败
{
    "status": "error",
    "message": "未找到基金 000001"
}
```

## 测试策略


### 测试编写原则
直接做基于网络的真实测试，不mock 数据

### 测试文件

`tests/test_fund_tools.py` - 58 个集成测试

### 运行测试

```bash
# 运行所有测试
pytest tests/*.py -v

# 运行特定测试类
pytest tests/test_fund_tools.py::TestFundPortfolioAnalysis -v

# 覆盖率报告
pytest --cov=src/fund_tools --cov-report=html
```

### 测试覆盖

- ✅ 58 个测试用例全部通过
- ✅ 包含真实 API 集成测试
- ✅ 核心功能完整覆盖

### 测试基金

```python
TEST_FUNDS = ["000001", "110022", "163406", "588000", "161725"]
```

## 已知问题与解决方案

### 1. akshare 认购费率 Bug

**问题：** `fund_fee_em(symbol=code, indicator="认购费率（前端）")` 报错：
```
Columns must be same length as key
```

**原因：** akshare 内部 bug，期望 "序号" 列但数据中不存在

**解决方案：** 移除此指标（`src/fund_tools/core.py:634`）
```python
fee_indicators = ["申购费率（前端）", "赎回费率"]  # 移除 "认购费率（前端）"
```

## 开发工作流

### 修改核心逻辑

1. 编辑 `src/fund_tools/` 下的相应模块
2. 更新 `src/fund_tools/__init__.py` 导出（如需要）
3. 更新 `cli.py` CLI 命令（如需要）
4. 更新 `fund_mcp_server.py` MCP 工具（如需要）
5. **运行测试**：`pytest tests/*  -v`

### 添加新功能

1. 在 `src/fund_tools/` 创建新模块或函数
2. 在 `__init__.py` 中导出
3. 在 `cli.py` 添加 CLI 命令
4. 在 `fund_mcp_server.py` 添加 MCP 工具
5. 在 `tests/` 添加测试

### 更新文档

- **用户文档**：README.md（面向用户）
- **项目文档**：CLAUDE.md（本文件，面向 AI 助手）
- **更新日志**：README.md 末尾的版本历史

## Git 提交规范

提交代码时必须生成带详细功能说明的 git commit。commit message 不只写一句标题，还要在正文里说明：

1. 本次 commit 实现了什么用户可见能力或内部能力
2. 关键代码改动点和涉及模块
3. 行为变化、数据源变化、兼容性处理或删除的旧逻辑
4. 已运行的测试或未能运行测试的原因

推荐格式：

```bash
git commit -m "feat: 简短说明本次能力" -m "实现内容：

1. 功能能力
- 说明新增/修改的能力，以及用户如何使用。

2. 实现细节
- 说明核心模块、数据流、缓存、CLI/MCP 接入等关键变更。

3. 验证
- 说明运行过的测试命令和结果。
```

```bash
# 功能添加
git commit -m "feat: 添加投资组合完整分析功能"

# Bug 修复
git commit -m "fix: 修复 akshare 认购费率 bug"

# 文档更新
git commit -m "docs: 更新 README，突出核心能力"

# 重构
git commit -m "refactor: 合并持仓分析和资产配置函数"

# 测试
git commit -m "test: 添加投资组合分析测试"
```

## 注意事项

1. **数据延迟**：部分数据可能存在延迟，以基金公司公告为准
2. **费率调整**：费率信息可能调整，以基金合同和最新公告为准
3. **持仓滞后**：持仓数据按季度更新，存在滞后性
4. **仅供学习**：本服务仅供学习和研究使用，不构成投资建议
5. **代理设置**：`src/fund_tools/index.py` 会移除代理（访问国内网站）
6. **测试环境**：测试会调用真实 API，注意频率限制
7. **⚠️ akshare 默认时间参数**：某些 akshare 函数有硬编码的默认日期参数（如 `ak.stock_zh_index_hist_csindex` 默认 `end_date="20240604"`），**必须显式传入当前日期**才能获取最新数据。例如：
   ```python
   # ❌ 错误：使用默认参数（返回过期数据）
   df = ak.stock_zh_index_hist_csindex(symbol="000300")

   # ✅ 正确：传入当前日期
   from datetime import datetime
   end_date = datetime.now().strftime("%Y%m%d")
   df = ak.stock_zh_index_hist_csindex(symbol="000300", end_date=end_date)
   ```

---

**最后更新：** 2026-04-27
**维护者：** woosley
**项目状态：** 活跃开发中
