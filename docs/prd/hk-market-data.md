# 香港市场基金与指数数据拉取 PRD

## 1. Background

ttjj-fund 目前已实现大陆市场的公募基金深度分析（11 维度）和 A 股指数管理（估值、风险、热力图）。项目基于 akshare 数据源 + MCP SDK，同时提供 CLI 和 MCP Server 两种使用方式。

用户现需扩展到**香港市场**，拉取港股基金和港股指数数据。

## 2. Problem Statement

- 当前项目仅覆盖大陆市场（A 股指数、公募基金），无法查询香港市场的基金和指数
- 用户需要一站式查询大陆 + 香港两个市场的投资数据
- 香港市场使用不同的数据源和接口，需独立模块但复用现有架构

## 3. Goals

1. 提供香港基金的排行查询、搜索、历史净值查询能力
2. 提供港股指数的实时行情查询、历史行情查询能力
3. 复用现有 CLI 命令体系和 MCP Server 架构，保持一致的用户体验
4. 通过数据源 fallback 机制确保接口可靠性（新浪 → 东财，新浪为主数据源）

## 3.5 Dependencies / Technical Constraints

- **akshare >= 1.18.57**：所有香港市场接口已在 akshare 1.18.57 上验证可用
- 已验证可用的接口：`fund_hk_rank_em()`, `fund_hk_fund_hist_em()`, `stock_hk_index_spot_sina()`, `stock_hk_index_daily_sina()`
- 已知不稳定的接口：`stock_hk_index_spot_em()`, `stock_hk_index_daily_em()`（东方财富港股指数接口偶发连接超时）
- 复用现有 `_fetch_table_with_retry()` 和 `_clear_proxy_env()` 工具函数

## 4. Non-Goals

- 不做港股个股数据（仅做基金和指数）
- 不做港股 ETF 实时行情（超出 akshare 免费数据范围）
- 不做香港基金的估值/风险分析（数据源不足，与大陆基金分析深度不同）
- 不做港股指数的估值分位/PE/PB（港股指数无免费历史估值数据源）
- 不修改现有大陆市场功能的接口和行为

## 5. Users / Personas

| Persona | 场景 |
|---------|------|
| 个人投资者 | 通过 CLI 或 MCP 查询港股基金净值、指数行情，辅助投资决策 |
| 量化研究员 | 批量拉取港股指数历史数据做回测分析 |

## 6. User Stories

### US-1: 香港基金排行
作为投资者，我想查看香港基金的排行榜（含收益率排名），以便筛选优质基金。

### US-2: 香港基金搜索
作为投资者，我想按关键字搜索香港基金，以便快速定位目标基金。

### US-3: 香港基金历史净值
作为投资者，我想查询某只香港基金的历史净值和分红记录，以便了解其长期表现。

### US-4: 港股指数实时行情
作为投资者，我想查看港股指数的实时行情列表，以便掌握市场动态。

### US-5: 港股指数历史行情
作为投资者，我想查询某只港股指数的历史行情数据，以便做趋势分析。

## 7. Scope

### In Scope

| 模块 | 功能 | 数据源 |
|------|------|--------|
| 香港基金排行 | 全量排行 + 按收益率排序 | `fund_hk_rank_em()` |
| 香港基金搜索 | 按名称/代码关键字搜索 | 本地缓存 |
| 香港基金历史净值 | 历史净值明细 + 分红送配 | `fund_hk_fund_hist_em()` |
| 港股指数实时行情 | 全部指数实时行情 | `stock_hk_index_spot_sina()` (主) / `stock_hk_index_spot_em()` (备) |
| 港股指数历史行情 | 单只指数历史日线 | `stock_hk_index_daily_sina()` (主) / `stock_hk_index_daily_em()` (备) |

### Out of Scope

- 港股个股行情、ETF 行情
- 港股指数估值（PE/PB/分位/温度）
- 港股指数风险分析（波动率/回撤/夏普）
- 港股指数候选基金池
- 香港基金经理信息

## 8. Functional Requirements

### FR-1: 香港基金排行 (`get_hk_fund_rankings`)

- 调用 `ak.fund_hk_rank_em()` 获取全量排行数据
- 返回字段：基金代码、基金简称、币种、日期、单位净值、日增长率、近1周/1月/3月/6月/1年/2年/3年/今年/成立来收益率、可购买状态
- 支持按收益率字段排序

### FR-2: 香港基金搜索 (`search_hk_funds`)

- 从排行数据中按基金代码或基金简称关键字搜索
- 返回匹配的基金列表
- 支持本地缓存，避免频繁 API 调用

### FR-3: 香港基金历史净值 (`get_hk_fund_history`)

- 调用 `ak.fund_hk_fund_hist_em(code, symbol)` 获取数据
- `symbol` 支持 "历史净值明细" 和 "分红送配详情"
- 注意：`code` 参数需要使用 `香港基金代码`（从排行数据获取），不是6位基金代码

### FR-4: 港股指数实时行情 (`get_hk_index_spot`)

- 主数据源：`ak.stock_hk_index_spot_sina()` — 返回代码、名称、最新价、涨跌额、涨跌幅、昨收、今开、最高、最低
- 备用数据源：`ak.stock_hk_index_spot_em()` — 东财接口
- 主数据源失败时自动 fallback

### FR-5: 港股指数历史行情 (`get_hk_index_daily`)

- 主数据源：`ak.stock_hk_index_daily_sina(symbol)` — 返回 date, open, high, low, close, volume, amount
- 备用数据源：`ak.stock_hk_index_daily_em(symbol)` — 东财接口
- 支持指定日期范围（最近 N 天）

### FR-6: CLI 命令

新增 `hk` 命令组，结构：

```
python cli.py hk fund ranking [--sort-by 近1年] [--limit 20]
python cli.py hk fund search "摩根"
python cli.py hk fund history 968063 [--type 历史净值明细]
python cli.py hk fund history 968063 --type 分红送配详情
python cli.py hk index spot
python cli.py hk index daily CES100 [--days 30]
```

### FR-7: MCP 工具

新增 MCP 工具：

- `get_hk_fund_rankings` — 香港基金排行
- `search_hk_funds` — 香港基金搜索
- `get_hk_fund_history` — 香港基金历史净值
- `get_hk_index_spot` — 港股指数实时行情
- `get_hk_index_daily` — 港股指数历史行情

## 9. Acceptance Criteria

### AC-1: 香港基金排行
- Given 用户调用 `get_hk_fund_rankings()`，When 接口正常响应，Then 返回 `status: "success"` 且 `count >= 100`
- Given 用户指定 `sort_by="近1年"`，When 接口正常响应，Then 结果按近1年收益率降序排列
- Given 排行 API 请求失败，When 函数内部重试耗尽，Then 返回 `status: "error"` 且 message 包含失败原因

### AC-2: 香港基金搜索
- Given 本地排行缓存已存在，When 用户搜索 `"摩根"`，Then 返回 `status: "success"` 且所有结果的 `基金简称` 包含"摩根"
- Given 本地排行缓存不存在（首次使用），When 用户搜索 `"摩根"`，Then 自动拉取排行数据缓存后再搜索，返回匹配结果

### AC-3: 香港基金历史净值
- Given 用户传入有效香港基金代码 + `type="历史净值明细"`，When 接口正常，Then 返回 `status: "success"` 且包含 `净值日期`、`单位净值`、`日增长率` 字段的历史列表
- Given 用户传入有效香港基金代码 + `type="分红送配详情"`，When 接口正常，Then 返回 `status: "success"` 且包含分红送配记录
- Given 用户传入无效代码，When 接口报错，Then 返回 `status: "error"` 和有意义的错误信息

### AC-4: 港股指数实时行情
- Given 调用 `get_hk_index_spot()`，When 新浪数据源可用，Then 返回 `status: "success"` 且 `count >= 30`，每条记录包含 `代码`、`名称`、`最新价`、`涨跌幅`
- Given 新浪数据源不可用，When 东财数据源可用，Then 自动 fallback 返回数据，`source` 字段标注实际数据源
- Given 新浪和东财数据源均不可用，When 双源均失败，Then 返回 `status: "error"` 且 message 提示"港股指数行情暂时不可用，请稍后重试"

### AC-5: 港股指数历史行情
- Given 用户传入有效指数代码如 "CES100" + `days=30`，When 接口正常，Then 返回 `status: "success"` 且包含最近 30 天的 date/open/high/low/close/volume 数据
- Given 用户传入无效指数代码，When 接口报错，Then 返回 `status: "error"` 和有意义的错误信息
- Given 用户传入 `days=0` 或负数，When 参数校验失败，Then 返回 `status: "error"` 且 message 提示 "days 必须 > 0"

### AC-6: CLI 命令
- Given 执行 `python cli.py hk fund ranking`，When 接口正常，Then 进程 exit code 为 0 且 stdout 输出包含排行表格
- Given 执行 `python cli.py hk fund search "摩根"`，When 有匹配结果，Then stdout 输出包含匹配的基金列表
- Given 执行 `python cli.py hk index spot`，When 接口正常，Then stdout 输出包含指数行情表格
- Given 执行 `python cli.py hk fund history 968063`，When 接口正常，Then stdout 输出包含历史净值记录
- Given 执行 `python cli.py hk index daily CES100 --days 30`，When 接口正常，Then stdout 输出包含历史行情数据

### AC-7: MCP 工具
- Given 启动 MCP Server，When 列出已注册工具，Then 包含 `get_hk_fund_rankings`、`search_hk_funds`、`get_hk_fund_history`、`get_hk_index_spot`、`get_hk_index_daily` 共 5 个工具
- Given 通过 MCP 客户端调用任一工具，When 参数合法，Then 返回 JSON 格式的 `{status: "success", ...}`
- Given 通过 MCP 客户端调用任一工具，When 参数不合法或 API 失败，Then 返回 JSON 格式的 `{status: "error", message: "..."}`

## 10. Edge Cases / Failure Modes

| 场景 | 处理方式 |
|------|---------|
| 东财港股指数接口连接超时 | fallback 到新浪数据源 |
| 新浪数据源被限流/封IP | 返回友好错误信息，提示 10 分钟后重试 |
| 香港基金代码混淆（6位代码 vs 香港基金代码） | 文档和函数签名中明确区分，搜索功能自动映射 |
| 网络代理干扰 | 复用 `_clear_proxy_env()` 清除代理 |
| API 返回空数据 | 返回 `status: "error"` + "暂无数据" 信息 |

## 11. Security / Privacy Notes

- 无用户认证需求（公开市场数据）
- 不涉及个人金融数据
- 注意 API 调用频率，避免被封禁

## 12. Rollout & Migration Notes

- 纯新增模块，不影响现有功能
- 新增 `src/fund_tools/hk_fund.py` 和 `src/fund_tools/hk_index.py`
- 新增 `src/cli/hk/` 命令目录
- 更新 `fund_mcp_server.py` 注册新工具
- 更新 `CLAUDE.md` 和 `README.md`

## 13. Metrics / Success Signals

- 所有新 CLI 命令可正常执行
- 所有新 MCP 工具可通过 Claude Desktop 调用
- 测试覆盖：至少 8 个集成测试（覆盖每个主要功能）
- 数据源 fallback 机制正常工作

## 14. Open Questions

1. **基金代码映射**：排行数据中有 `基金代码`（6位）和 `香港基金代码`（长码），历史净值接口使用长码。是否需要在缓存中建立映射关系，让用户用6位码也能查历史净值？
   → **倾向方案**：是，在排行数据缓存中同时保存两种代码，搜索时自动建立映射

2. **指数代码标准化**：港股指数代码格式不统一（CES100 vs HSI 等），是否需要标准化？
   → **倾向方案**：保持原格式，与 akshare 数据源一致

3. **缓存策略**：香港基金排行数据是否需要本地磁盘缓存？
   → **倾向方案**：是，复用现有 cache.py 模式，TTL 设为 1 天

4. **数据延迟披露**：港股指数"实时行情"可能有 15 分钟延迟（免费数据源），是否需要在返回中标注？
   → **倾向方案**：是，在返回数据中添加 `data_delay_note` 字段提示可能延迟

5. **MCP Server 拆分**：`fund_mcp_server.py` 已经 878 行，新增 5 个工具后超过 1100 行。是否将 HK 工具拆到独立模块？
   → **倾向方案**：暂不拆分，保持单文件 MCP Server 结构一致性；如后续工具超过 30 个再拆分
