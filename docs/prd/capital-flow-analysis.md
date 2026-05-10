# 沪深港通资金流分析 PRD

## 1. Background

沪深港通（北向资金 = 外资通过沪/深股通买入 A 股，南向资金 = 内地资金通过港股通买入港股）是 A 股市场重要的风向标。北向资金被视为"聪明钱"，其行业偏好和流入流出趋势对投资决策有重要参考价值。

ttjj-fund 项目已具备基金深度分析和 A 股指数管理能力，但缺少资金流维度的分析。在 `_full_analysis.py` 和 `_tencent_analysis.py` 中已有 POC 级别的 `ak.stock_hsgt_hist_em()` 调用，但未产品化为正式的 MCP 工具。

## 2. Problem Statement

用户（投资者/分析师）目前无法通过 ttjj-fund MCP 服务获取沪深港通资金流数据，无法将北向/南向资金流信息与基金持仓、行业估值等信息结合分析。

## 3. Goals

1. 提供沪深港通（北向/南向）历史资金流查询能力
2. 提供北向资金行业/概念板块增持排行分析
3. 提供今日资金流快照总览
4. 所有能力通过 MCP 工具和 CLI 命令两种方式暴露

## 4. Non-Goals

- 不做分钟级实时资金流监控（2024 年 5 月已停更）
- 不做个股级别的北向持仓追踪
- 不做量化交易信号生成
- 不做南向资金的行业排行（akshare 暂无对应接口）

## 5. Users / Personas

| Persona | 需求 |
|---------|------|
| **个人投资者** | 快速了解北向资金今日流入流出、近期趋势 |
| **基金研究员** | 结合北向行业偏好筛选基金 |
| **AI 助手（Claude）** | 通过 MCP 工具调用，为用户生成资金流分析报告 |

## 6. User Stories

### US-1: 查看今日资金流总览
作为投资者，我想查看今日沪深港通各通道的资金流入流出汇总，以便快速了解市场外资动向。

### US-2: 查询历史资金流趋势
作为投资者，我想查询指定方向（北向/南向）最近 N 天的资金流历史数据，以便分析趋势。

### US-3: 查看北向资金行业偏好
作为基金研究员，我想查看北向资金在各行业/概念板块的增持排行，以便了解外资偏好方向。

### US-4: 通过 MCP 调用
作为 AI 助手，我需要通过 MCP 工具调用上述所有能力，以便为用户生成综合分析报告。

## 7. Scope

### In Scope

- 新增 `src/fund_tools/capital_flow.py` 模块
- 3 个核心函数 + 对应 MCP 工具 + CLI 命令
- 集成测试
- CLAUDE.md 文档更新

### Out of Scope

- 分钟级实时数据
- 个股北向持仓
- 南向行业排行
- 前端可视化

## 8. Functional Requirements

### FR-1: 今日资金流总览

- 调用 `ak.stock_hsgt_fund_flow_summary_em()` 获取当日汇总
- 返回各通道（北向、南向、沪股通、深股通、港股通沪、港股通深）的：当日净买额、资金流入、当日余额、上涨/下跌家数、相关指数及涨跌幅
- 返回格式遵循项目 `{status, data}` 约定

### FR-2: 历史资金流查询

- 调用 `ak.stock_hsgt_hist_em(symbol)` 获取历史数据
- 支持 symbol 参数：`"北向资金"`, `"沪股通"`, `"深股通"`, `"南向资金"`, `"港股通沪"`, `"港股通深"`
- 支持 `days` 参数控制返回天数（默认 20，最大 365）
- 返回每日：日期、当日成交净买额、买入成交额、卖出成交额、历史累计净买额
- 额外计算：近 N 日累计净买额、日均净买额、趋势判断（持续流入/流出/震荡）
- 处理 2024-08-19 后数据格式变更（部分字段可能为空）

### FR-3: 北向资金行业/概念排行

- 调用 `ak.stock_hsgt_board_rank_em(symbol, indicator)` 获取排行
- 支持板块类型：行业板块、概念板块
- 支持时间周期：今日、3日、5日、10日、1月、1季、1年
- 返回各板块：板块名称、北向增持市值、增持比例、最新价、涨跌幅、领涨股
- 默认返回 Top 10，可配置

### FR-4: MCP 工具注册

- 在 `fund_mcp_server.py` 注册 3 个新工具
- 工具描述清晰，参数有中文说明
- 遵循现有 `json_response=True` 模式

### FR-5: CLI 命令

- 在 `cli.py` 添加 `capital-flow` 子命令组
- 子命令：`summary`, `history`, `sector-rank`
- 遵循现有 CLI 命令风格

## 9. Acceptance Criteria

### AC-1: 今日总览
**Given** 交易日的交易时段之后，**When** 调用 `get_capital_flow_summary()`，**Then** 返回 `status: "success"` 且包含北向、南向各通道的当日净买额和资金流入数据。

### AC-2: 历史查询
**Given** akshare API 可用，**When** 调用 `get_capital_flow_history(direction="北向", days=20)`，**Then** 返回最近 20 个交易日的逐日数据，且 `cumulative_net_buy` 和 `daily_avg_net_buy` 字段计算正确（与原始数据加总一致，误差 < 0.01 亿元）。

### AC-3: 行业排行
**Given** akshare API 可用，**When** 调用 `get_northbound_sector_rank(board_type="行业板块", indicator="5日")`，**Then** 返回 Top 10 行业板块的增持市值排行，每条记录包含板块名称和增持市值。

### AC-4: MCP 可调用
**Given** MCP Server 运行中，**When** AI 助手调用 `get_capital_flow_summary` 工具，**Then** 返回与直接调用 Python 函数一致的结果。

### AC-5: 错误处理
**Given** akshare API 返回空 DataFrame 或网络错误，**When** 调用任一资金流函数，**Then** 返回 `status: "error"` 和明确的错误信息，不抛出未捕获异常。

## 10. Edge Cases / Failure Modes

| 场景 | 处理方式 |
|------|---------|
| 非交易日调用 summary | 返回最近交易日数据（akshare 行为），说明数据日期 |
| 2024-08-19 后部分字段为空 | 只返回可用字段，缺失字段标为 `null` |
| days 参数 > 365 | 截断为 365 并返回 |
| 无效的 direction 参数 | 返回 `error` + 支持的参数列表 |
| akshare API 超时/失败 | 返回 `status: "error"` + 错误信息 |
| DataFrame 为空 | 返回 `status: "error"` + "暂无数据" |

## 11. Security / Privacy / Permission Notes

- 所有数据来自东方财富公开接口，无认证需求
- 不涉及用户隐私数据
- 无额外权限要求

## 12. Rollout & Migration Notes

- 纯增量功能，不影响现有工具
- 新增模块 `capital_flow.py`，修改 `__init__.py` 导出、`fund_mcp_server.py` 工具注册、`cli.py` 命令
- akshare 为现有依赖，无需新增依赖

## 13. Metrics / Success Signals

- 3 个新 MCP 工具可被 Claude Desktop 成功调用
- 所有集成测试通过
- CLI 命令可正常执行并返回结构化数据

## 14. Open Questions

1. **数据频率**：是否需要缓存策略？（当前 POC 未使用缓存，每次实时查询）
   - 建议：初期不加缓存，后续按需添加
2. **分析深度**：是否需要自动生成"资金流分析报告"（结合行业排行 + 历史趋势 + 指数估值的综合分析）？
   - 建议：作为后续增强，当前先提供原始数据查询
