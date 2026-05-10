# Capability Contract — Capital Flow Analysis (Gate 1.5)

**Feature:** 沪深港通资金流分析
**PRD:** docs/prd/capital-flow-analysis.md
**Status:** Approved → Ready for Gate 2 Technical Design
**Author:** Hermes Agent
**Date:** 2026-05-10

---

## 1. Capability Restatement

Provide **three** user-facing capabilities for 沪深港通 (Shanghai-Shenzhen-Hong Kong Stock Connect) capital flow data, exposed through both MCP tools and CLI subcommands:

| # | Capability | One-line summary |
|---|-----------|-----------------|
| C1 | **Today's Summary** | Snapshot of all channels' net-buy amounts, balances, and related index moves for the current (or most recent trading) day |
| C2 | **Historical Flow** | N-day historical series for a chosen direction (northbound / southbound / sub-channels), with computed aggregates (cumulative, daily avg, trend) |
| C3 | **Sector Rank** | Top-N sector/concept-board ranking by northbound capital increment over configurable time windows |

All three capabilities consume **public, real-time data** from 东方财富 via akshare. No authentication, no private data, no new external dependencies.

---

## 2. Constraints

### 2.1 Fixed Rules (Invariants)

| ID | Rule |
|----|------|
| INV-1 | Every public function returns `{status: "success" | "error", ...}` — matches the existing project convention (`core.py`, `index.py`, `industry_valuation.py`) |
| INV-2 | MCP tool wrappers use `@mcp.tool()` with `json_response=True` (already set on the FastMCP instance) and return `{success: bool, ...}` at the MCP layer |
| INV-3 | All monetary amounts from akshare are in **亿元**; no unit conversion is performed |
| INV-4 | `stock_hsgt_hist_em()` returns the **entire** history — no server-side date filter. Client-side slicing by `days` parameter is mandatory |
| INV-5 | Since 2024-08-19, columns `当日成交净买额`, `买入成交额`, `卖出成交额` may be empty strings for recent rows. All numeric extraction must use `pd.to_numeric(errors='coerce')` |
| INV-6 | No caching layer for v1 — every call is a live API hit. Cache can be added later without interface change |
| INV-7 | No new pip dependencies — `akshare`, `pandas`, `numpy` are already installed |
| INV-8 | Test strategy: **real API integration tests** only, no mocks — matches project convention (`tests/test_fund_tools.py`, `tests/test_industry_heatmap.py`) |

### 2.2 Boundaries

| Boundary | Value |
|----------|-------|
| `days` range | 1–365 (default 20); values > 365 are silently clamped |
| `top_n` range | 1–100 (default 10) |
| `direction` enum | `["北向资金", "沪股通", "深股通", "南向资金", "港股通沪", "港股通深"]` |
| `board_type` enum | `["行业板块", "概念板块"]` |
| `indicator` enum | `["今日", "3日", "5日", "10日", "1月", "1季", "1年"]` |
| API rate limit | No explicit limit known; recommend ≥ 1s between rapid successive calls (advisory, not enforced in code) |

### 2.3 Excluded (by design)

- Minute-level real-time flow (discontinued May 2024)
- Individual-stock northbound holding tracking
- Quantitative trading signal generation
- Southbound sector ranking (akshare has no corresponding API)
- Any caching strategy (deferred to v2)

---

## 3. Implementation Contract

### 3.1 Actors

| Actor | Description |
|-------|-------------|
| **End User** | Invokes CLI subcommands or asks Claude Desktop questions about capital flow |
| **Claude Desktop / MCP Client** | Calls MCP tool endpoints exposed by `fund_mcp_server.py` |
| **capital_flow.py** | New module in `src/fund_tools/` — all business logic lives here |
| **akshare (东方财富)** | Upstream data source — 3 API calls (`stock_hsgt_fund_flow_summary_em`, `stock_hsgt_hist_em`, `stock_hsgt_board_rank_em`) |

### 3.2 Surfaces

| Surface | File | What changes |
|---------|------|-------------|
| Business logic | `src/fund_tools/capital_flow.py` | **New file** — 3 public functions |
| Package export | `src/fund_tools/__init__.py` | Add imports + `__all__` entries for the 3 functions |
| MCP tools | `fund_mcp_server.py` | Add 3 `@mcp.tool()` functions |
| CLI | `cli.py` | Add `capital-flow` subcommand group with `summary`, `history`, `sector-rank` |
| Tests | `tests/test_capital_flow_integration.py` | **New file** — integration tests |
| Docs | `CLAUDE.md` | Add capital-flow section to project docs |

### 3.3 States

The feature is **stateless**. No cache, no local database, no background jobs. Each function call triggers a live akshare API request and returns immediately.

### 3.4 Interfaces

#### 3.4.1 `get_capital_flow_summary() -> dict`

```
No parameters.
Returns: {
  status: "success",
  data_date: str,            # "2026-05-09"
  channels: [
    {
      "通道": str,            # e.g. "北向资金"
      "当日成交净买额": float | None,
      "资金流入": float | None,
      "当日余额": float | None,
      "上涨家数": int | None,
      "下跌家数": int | None,
      "相关指数": str | None,
      "指数涨跌幅": str | None,
    },
    ...                      # 6 channels total
  ]
}
```

#### 3.4.2 `get_capital_flow_history(direction: str, days: int = 20) -> dict`

```
Parameters:
  direction: one of ["北向资金", "沪股通", "深股通", "南向资金", "港股通沪", "港股通深"]
  days: 1–365, default 20

Returns: {
  status: "success",
  direction: str,
  days: int,
  data_date_range: [str, str],   # ["2026-04-10", "2026-05-09"]
  records: [
    {
      "日期": str,
      "当日成交净买额": float | None,
      "买入成交额": float | None,
      "卖出成交额": float | None,
      "历史累计净买额": float | None,
    },
    ...                           # `days` rows, newest first
  ],
  summary: {
    "cumulative_net_buy": float,  # sum of 当日成交净买额 over the window
    "daily_avg_net_buy": float,
    "trend": str,                 # "持续流入" | "持续流出" | "震荡"
  }
}
```

#### 3.4.3 `get_northbound_sector_rank(board_type: str, indicator: str = "今日", top_n: int = 10) -> dict`

```
Parameters:
  board_type: "行业板块" | "概念板块"
  indicator: "今日" | "3日" | "5日" | "10日" | "1月" | "1季" | "1年"
  top_n: 1–100, default 10

Returns: {
  status: "success",
  board_type: str,
  indicator: str,
  data_date: str,
  sectors: [
    {
      "序号": int,
      "板块名称": str,
      "北向增持市值": float | None,
      "增持比例": str | None,
      "最新价": float | None,
      "涨跌幅": str | None,
      "领涨股": str | None,
      "领涨股涨跌幅": str | None,
    },
    ...                           # top_n rows
  ]
}
```

---

## 4. Non-Goals

1. **Real-time minute-level monitoring** — data discontinued since 2024-05
2. **Individual stock northbound holdings** — out of scope for this PRD
3. **Automated analysis reports** combining flow + valuation + holdings — deferred to a future enhancement
4. **Southbound sector ranking** — akshare provides no API
5. **Caching or TTL logic** — pure live queries for v1; can be retrofitted without breaking interfaces
6. **Frontend / chart visualization** — only structured data output (CLI text, MCP JSON)

---

## 5. Open Questions

| # | Question | Default / Recommendation | Resolution needed by |
|---|---------|--------------------------|---------------------|
| OQ-1 | Should we add in-memory TTL cache (e.g., 60s) for the summary endpoint to avoid redundant calls during a single conversation turn? | No for v1; add if rate-limiting becomes an issue | v2 planning |
| OQ-2 | The trend classification logic ("持续流入"/"持续流出"/"震荡") needs a threshold — what ratio of positive days qualifies as "持续"? | ≥ 70% same-sign days = 持续; otherwise 震荡 | Implementation (can adjust later) |
| OQ-3 | Should `data_date` in summary reflect the actual data date from akshare (may differ from today on non-trading days)? | Yes — extract from the returned DataFrame directly | Implementation |
| OQ-4 | akshare `stock_hsgt_board_rank_em` column names may vary across versions — do we pin akshare version? | Defensive: use column-name mapping with fallback | Implementation |

---

## 6. Handoff

This contract is **handed off to Gate 2 (Technical Design)**. The technical design document at `docs/design/capital-flow-analysis.md` must:

1. Specify exact Python function signatures with type hints matching §3.4
2. Define the akshare call pattern for each function
3. Specify DataFrame column→output-field mappings
4. Provide CLI argparse definitions
5. Provide MCP tool decorator+docstring templates
6. List integration test cases with assertions
7. Address all open questions from §5 with concrete implementation decisions
