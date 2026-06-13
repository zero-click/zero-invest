# ttjj-fund

中国公募基金与 A 股指数信息查询工具，基于 `akshare` 数据源。项目提供命令行 CLI 工具，适合做基金研究、指数估值查询、候选指数基金筛选和本地数据缓存。

## 主要功能

### 基金分析

- 基金搜索：按代码、名称、拼音搜索公募基金。
- 基金详情：查询基金基本信息、规模、基金经理、成立日期、类型。
- 业绩表现：近 1 周、1 月、3 月、6 月、1 年、3 年、今年、成立以来收益。
- 风险指标：标准差、夏普比率、最大回撤等。
- 持仓分析：十大重仓股、持仓集中度、季度持仓变化。
- 资产配置：行业配置、股票/债券持仓样本。
- 费用信息：管理费、托管费、申购费、赎回费。
- 流动性与评级：申赎状态、到账时间、机构评级。

### 指数管理

- 多源指数数据库：聚合中证指数、东方财富、Sina、akshare 指数信息表并本地缓存。
- 指数搜索：按代码或名称搜索宽基、行业、主题、策略、风格等指数。
- 指数查询：基本信息、当前点位、涨跌幅、历史收益。
- 指数估值：PE-TTM、PB、股息率、历史分位、估值温度。
- 指数风险：波动率、最大回撤、回撤修复周期、夏普比率。
- 候选基金池：根据指数匹配相关指数基金。
- 估值热力图：输出宽基和行业估值表，支持按 PE、PB、股息率、估值等级排序。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 初始化缓存

```bash
# 更新基金数据库
python cli.py bond update

# 更新指数数据库
python cli.py index update
```

缓存文件会写到项目根目录：

- `fund_database.json`
- `index_database.json`

## CLI 使用

### 基金命令

```bash
# 搜索基金
python cli.py bond search "华夏"
python cli.py bond search "沪深300" --all

# 查询基金
python cli.py bond query 000001
python cli.py bond query 000001 --detail

# 基金排行榜
python cli.py bond ranking --type 股票型 --top 10

# 专项查询
python cli.py bond performance 000001
python cli.py bond risk 000001
python cli.py bond top-holdings 000001
python cli.py bond manager 000001
python cli.py bond fee 000001
python cli.py bond liquidity 000001
python cli.py bond rating 000001

# 投资组合分析
python cli.py bond holdings 000001
python cli.py bond allocation 000001
python cli.py bond portfolio 000001

# 更新基金数据库
python cli.py bond update
```

### 指数命令

```bash
# 更新多源指数数据库
python cli.py index update

# 搜索指数
python cli.py index search "红利"
python cli.py index search "上证50" --all

# 查询指数基本信息、当前值、业绩
python cli.py index query 000300

# 查询完整指数信息：query + valuation + risk
python cli.py index query 000300 -d

# 查询估值
python cli.py index valuation 000300

# 查询风险
python cli.py index risk 000300

# 批量查询
python cli.py index batch 000300 000905 000852

# 查询指数候选基金池
python cli.py index listfund 000300
python cli.py index listfund 000300 --all

# 估值热力图
python cli.py index heatmap
python cli.py index heatmap --sort-by pb --limit 20
python cli.py index heatmap --category 宽基 --sort-by pe --limit 30
python cli.py index heatmap --CSRC
```

### 个股命令

```bash
# 搜索股票
python cli.py stock search "平安"
python cli.py stock search "贵州"

# 查询股票基本信息
python cli.py stock query 600519

# 查询历史K线/区间涨跌
python cli.py stock hist 600519

# 估值概览（PE/PB/PS/EV）
python cli.py stock valuation 600519

# 场景分析
python cli.py stock scenario-a 600519  # 稳定成长型：Forward PE / PEG
python cli.py stock scenario-b 600519  # 成长/亏损型：PS + FCF反算
python cli.py stock scenario-c 600519  # 强周期型：DOI/EV/EBITDA/PB

# 股票类型查询（本工具不预测类型）
python cli.py stock classify 600519

# 个股准入检查（需指定类型）
python cli.py stock checklist 600519 --type a  # a=稳定成长型, b=高速成长型, c=强周期型

# 回撤分析
python cli.py stock drawdown 600519

# 持仓状态检查
python cli.py stock status 600519

# 逻辑破坏检查
python cli.py stock check-logic 600519

# 退出评估
python cli.py stock exit-eval 600519

# 查看缓存状态
python cli.py stock cache
```

### Debug 模式

```bash
python cli.py --debug bond query 000001
python cli.py --debug index valuation 000300
```

## 数据来源

- 基金列表、基金详情、费率、持仓、排行：东方财富、天天基金等 akshare 数据源。
- 指数列表：中证指数、东方财富指数实时行情、Sina 指数实时行情、akshare 指数信息表。
- 指数历史行情：优先使用 Sina / 腾讯 / 东方财富日线接口，缺失时 fallback 到中证指数 `stock_zh_index_hist_csindex` 和东方财富 `index_zh_a_hist`。
- 指数估值分位：乐咕乐股 PE/PB 数据。
- 默认热力图：行业指数代码 + 宽基指数代码，统一走指数估值链路。
- `index heatmap --CSRC`：证监会行业静态 PE 快照。

数据依赖第三方公开接口，可能存在延迟、缺失、接口变更或临时不可用。

## 测试

```bash
# 运行全部测试
pytest tests -v

# 多源指数缓存单元测试
pytest -q tests/test_index_cache_multisource.py

# 指数热力图集成测试，需要网络
pytest -q tests/test_industry_heatmap.py -m integration
```

项目测试包含真实网络请求。运行集成测试前需要确认网络可访问对应数据源。

## 项目结构

```text
ttjj-fund/
├── cli.py                         # CLI 入口
├── requirements.txt               # Python 依赖
├── src/fund_tools/
│   ├── __init__.py
│   ├── cache.py                   # 基金/指数/香港基金本地缓存
│   ├── core.py                    # 基金核心函数
│   ├── index.py                   # 指数查询、估值、风险、历史行情
│   ├── hk_fund.py                 # 香港基金：排行、搜索、历史净值
│   ├── hk_index.py                # 港股指数：实时行情、历史行情
│   ├── capital_flow.py            # 沪深港通资金流
│   └── industry_valuation.py      # 指数估值热力图
└── tests/                         # 单元测试与集成测试
```

## 注意事项

- 本项目仅用于学习和研究，不构成投资建议。
- 基金费率、规模、持仓、评级等信息以基金公司公告和销售渠道披露为准。
- 持仓数据通常按季度更新，存在滞后。
- 第三方数据接口可能临时失败；CLI 会尽量降级处理，但不能保证所有字段始终可用。
- 如果使用代理环境变量访问国内数据源出现连接异常，可以先清理 `http_proxy`、`https_proxy` 等环境变量。

## Changelog

### 2026-05-16

- 移除 MCP 服务能力，项目简化为纯 CLI 工具。
- 删除 `fund_mcp_server.py` 和 `start_mcp.sh`。
- 更新文档，移除所有 MCP 相关说明。

### 2026-04-27

- 新增多源指数数据库缓存，合并中证指数、东方财富、Sina 和 akshare 指数信息表。
- 修复单一指数源无法覆盖上证50、创业板50等常见指数的问题。
- 新增指数历史行情 fallback：中证历史行情缺失时使用东方财富历史行情。
- 新增 `python cli.py index heatmap` 指数估值热力图。
- 将行业估值热力图迁移到 `src/fund_tools/industry_valuation.py`。
- 删除旧的根目录 `index_valuation.py`、`industry_valuation.py`。

### 2026-04-26

- 重构指数 CLI 为 `query / valuation / risk`。
- 新增 `python cli.py index query <code> -d` 完整指数输出。
- 移除旧的 `index details`、`index info` 入口。
- 移除旧 `src/fund_tools/valuation.py`，估值逻辑合并到 `src/fund_tools/index.py`。

### 2026-04-19

- 初始 CLI 工具。
- 支持基金搜索、基金详情、持仓、费用、风险和评级查询。

## Author

zero-click

## License

MIT License. 这是一个宽松的开源协议，允许使用、复制、修改、合并、发布、分发、再授权和商业使用，但需要保留版权声明和许可声明。
