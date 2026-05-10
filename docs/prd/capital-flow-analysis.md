# 沪深港通资金流分析 PRD

## 1. Background

沪深港通（北向资金 = 外资通过沪/深股通买入 A 股，南向资金 = 内地资金通过港股通买入港股）是 A 股市场重要的风向标。

**⚠️ 重大数据源变更（2024-08-19）：** 沪深港交易所分两阶段调整了信息披露机制：
- **2024-05-13**：取消北向资金实时交易数据披露
- **2024-08-19**：连盘后净买入/净卖出金额也不再公布，仅披露成交总额、前十大活跃股
- 影响：akshare 的 `stock_hsgt_fund_flow_summary_em()` 北向通道净买额返回 0，`stock_hsgt_board_rank_em()` 仅支持北向板块排行但数据基于已停止公布的净买额
- **南向数据不受影响**，港股通持股、资金流等数据正常公布

基于此变更，本 PRD 从"沪深港通双向分析"调整为**南向资金流分析**，移除所有依赖北向净买额的功能。

## 2. Problem Statement

用户（投资者/分析师）需要通过 ttjj-fund 获取**南向资金流数据**（港股通持股、资金流入流出趋势），以便分析内地资金对港股的配置动向。北向资金因政策原因已不再公布净买额数据，相关功能需移除。

## 3. Goals

1. 提供南向资金历史资金流查询能力
2. 提供今日南向资金流快照总览（从 summary 中提取南向通道）
3. 所有能力通过 MCP 工具和 CLI 命令暴露

## 4. Non-Goals

- ❌ 北向资金行业/概念排行（数据源已断）
- ❌ 北向历史净买额趋势分析（2024-08-19 后数据为空/零值）
- ❌ 分钟级实时资金流监控
- ❌ 个股级别的南向持仓追踪
- ❌ 南向行业排行聚合（akshare 无港股行业分类接口，需自行映射，复杂度高）
- ❌ 量化交易信号生成

## 5. Users / Personas

| Persona | 需求 |
|---------|------|
| **个人投资者** | 快速了解南向资金今日流入流出、近期趋势 |
| **基金研究员** | 结合南向资金配置偏好分析港股基金投资价值 |
| **AI 助手（Claude）** | 通过 MCP 工具调用，为用户生成南向资金流分析报告 |

## 6. User Stories

### US-1: 查看今日南向资金流总览
作为投资者，我想查看今日港股通各通道的资金流入流出汇总，以便快速了解内地资金对港股的配置动向。

### US-2: 查询南向历史资金流趋势
作为投资者，我想查询南向资金最近 N 天的资金流历史数据，以便分析趋势。

### US-3: 通过 MCP 调用
作为 AI 助手，我需要通过 MCP 工具调用上述所有能力，以便为用户生成综合分析报告。

## 7. Scope

### In Scope

- 修改 `src/fund_tools/capital_flow.py`：移除 `get_northbound_sector_rank`，清理北向相关常量
- 修改 `get_capital_flow_summary()`：明确标注北向数据不可用
- 修改 `get_capital_flow_history()`：默认方向改为"南向"，保留全部 6 个方向但北向返回数据说明
- 移除 CLI `sector-rank` 子命令
- 移除 MCP `get_northbound_sector_rank` 工具
- 更新测试

### Out of Scope

- 北向数据功能（已移除）
- 南向行业排行
- 前端可视化

## 8. Functional Requirements

### FR-1: 今日南向资金流总览

- 调用 `ak.stock_hsgt_fund_flow_summary_em()` 获取当日汇总
- 返回南向通道（港股通沪、港股通深）的：当日净买额、资金流入、当日余额、上涨/下跌家数、相关指数及涨跌幅
- 北向通道（沪股通、深股通）返回的字段值为 0，需在输出中明确标注"北向净买额数据自 2024-08-19 起不再公布"
- 返回格式遵循项目 `{status, data}` 约定

### FR-2: 南向历史资金流查询

- 调用 `ak.stock_hsgt_hist_em(symbol)` 获取历史数据
- 支持 symbol 参数：`"南向资金"`, `"港股通沪"`, `"港股通深"`
- 仍支持 `"北向资金"`, `"沪股通"`, `"深股通"`，但返回时附带数据可用性说明
- 支持 `days` 参数控制返回天数（默认 20，最大 365）
- 默认方向改为 `"南向"`
- 返回每日：日期、当日成交净买额、买入成交额、卖出成交额、历史累计净买额
- 额外计算：近 N 日累计净买额、日均净买额、趋势判断

### FR-3: MCP 工具注册

- 保留 `get_capital_flow_summary` 和 `get_capital_flow_history` 工具
- 移除 `get_northbound_sector_rank` 工具
- 工具描述中注明数据可用性变更

### FR-4: CLI 命令

- 保留 `capital-flow summary` 和 `capital-flow history` 子命令
- 移除 `capital-flow sector-rank` 子命令
- `history` 默认方向改为"南向"

## 9. Acceptance Criteria

### AC-1: 南向总览
**Given** 交易日的交易时段之后，**When** 调用 `get_capital_flow_summary()`，**Then** 返回 `status: "success"` 且包含南向各通道的当日净买额和资金流入数据。北向通道返回但字段标注为不可用。

### AC-2: 南向历史查询
**Given** akshare API 可用，**When** 调用 `get_capital_flow_history(direction="南向", days=20)`，**Then** 返回最近 20 个交易日的逐日数据，且 `cumulative_net_buy` 和 `daily_avg_net_buy` 字段计算正确。

### AC-3: MCP 可调用
**Given** MCP Server 运行中，**When** AI 助手调用 `get_capital_flow_summary` 工具，**Then** 返回与直接调用 Python 函数一致的结果。

### AC-4: 北向数据标注
**Given** 调用任何资金流函数涉及北向数据，**Then** 返回中包含 `data_available: false` 和说明信息，而非静默返回 0。

### AC-5: 错误处理
**Given** akshare API 返回空 DataFrame 或网络错误，**When** 调用任一资金流函数，**Then** 返回 `status: "error"` 和明确的错误信息。

### AC-6: sector-rank 已移除
**Given** 用户尝试调用 `get_northbound_sector_rank` 或 CLI `capital-flow sector-rank`，**Then** 该功能不可用（函数已删除，CLI 命令已移除）。

## 10. Edge Cases / Failure Modes

| 场景 | 处理方式 |
|------|---------|
| 非交易日调用 summary | 返回最近交易日数据（akshare 行为），说明数据日期 |
| days 参数 > 365 | 截断为 365 并返回 |
| 无效的 direction 参数 | 返回 `error` + 支持的参数列表 |
| akshare API 超时/失败 | 返回 `status: "error"` + 错误信息 |
| DataFrame 为空 | 返回 `status: "error"` + "暂无数据" |

## 11. Migration / Breaking Changes

| 变更 | 影响 | 迁移方式 |
|------|------|----------|
| 移除 `get_northbound_sector_rank()` | MCP 调用会报错 | 移除该工具注册 |
| 移除 CLI `sector-rank` 子命令 | 用户脚本会报错 | 更新使用文档 |
| `get_capital_flow_history` 默认方向改为"南向" | 不传 direction 时行为变化 | 无破坏（之前默认北向返回的也是空值） |
| `get_capital_flow_summary` 北向标注不可用 | 输出新增字段 | 向后兼容（新增字段，不删除） |
| 移除 `BOARD_TYPE_MAP`, `VALID_INDICATORS` 常量 | 直接引用会报错 | 内部常量，无外部影响 |

## 12. Security / Privacy / Permission Notes

- 所有数据来自东方财富公开接口，无认证需求
- 不涉及用户隐私数据
- 无额外权限要求

## 13. Metrics / Success Signals

- 2 个 MCP 工具可正常调用（summary + history）
- 所有集成测试通过
- CLI 命令可正常执行并返回南向数据

## 14. Open Questions

1. ~~是否需要南向行业排行？~~ → 当前 akshare 无港股行业分类接口，暂不做
2. **是否需要利用 `stock_hsgt_stock_statistics_em(symbol='南向持股')` 做个股级南向持仓查询？** → 独立 PRD
