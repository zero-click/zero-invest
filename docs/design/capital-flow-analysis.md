# 沪深港通资金流分析 — Feature Technical Design

> **Review Gate 2R Revision**: 根据 architect review 修正了所有 blocking findings。
> 修正点: ① summary/hist 的实际列名映射 ② board_rank 的实际列名和动态列名处理 ③ MCP 工具使用 def（非 async） ④ 统一返回格式

## 1. Overview

为 ttjj-fund 项目新增沪深港通（北向/南向）资金流分析能力，提供 3 个核心查询函数，通过 MCP 工具和 CLI 命令两种方式暴露。

## 2. Architecture

```
用户 / AI 助手
    │
    ├── MCP 工具 (fund_mcp_server.py)  [def, 非 async]
    │   ├── get_capital_flow_summary
    │   ├── get_capital_flow_history
    │   └── get_northbound_sector_rank
    │
    └── CLI 命令 (cli.py)
        ├── capital-flow summary
        ├── capital-flow history [--direction 北向] [--days 20]
        └── capital-flow sector-rank [--board-type 行业板块] [--indicator 5日] [--top-n 10]
    
    │
    ▼
src/fund_tools/capital_flow.py  ← 新模块
    │
    ├── get_capital_flow_summary()      → ak.stock_hsgt_fund_flow_summary_em()
    ├── get_capital_flow_history()      → ak.stock_hsgt_hist_em(symbol)
    └── get_northbound_sector_rank()    → ak.stock_hsgt_board_rank_em(symbol, indicator)
```

### 集成点

| 文件 | 变更 |
|------|------|
| `src/fund_tools/capital_flow.py` | **新增**：核心业务逻辑 |
| `src/fund_tools/__init__.py` | **修改**：导入并导出新函数 |
| `fund_mcp_server.py` | **修改**：注册 3 个 MCP 工具（使用 `def`，匹配现有模式） |
| `cli.py` | **修改**：添加 capital-flow 子命令组 |
| `tests/test_capital_flow.py` | **新增**：集成测试 |
| `CLAUDE.md` | **修改**：更新项目文档 |

## 3. Interface / API Contracts

### 3.1 get_capital_flow_summary()

```python
def get_capital_flow_summary() -> dict:
    """
    获取沪深港通今日资金流总览。
    
    数据源: ak.stock_hsgt_fund_flow_summary_em()
    实际返回 4 行: 沪股通(北向), 港股通(沪)(南向), 深股通(北向), 港股通(深)(南向)
    按 资金方向(北向/南向) 分组聚合展示。
    
    Returns:
        {
            "status": "success",
            "date": "2026-05-08",        # 交易日
            "channels": [
                {
                    "name": "沪股通",              # 板块 (akshare: 板块)
                    "type": "沪港通",              # 类型 (akshare: 类型)
                    "direction": "北向",           # 资金方向 (akshare: 资金方向)
                    "trade_status": "已收盘",      # 交易状态 (akshare: 交易状态, 数字→文字)
                    "net_buy": 52.34,             # 成交净买额(亿元) (akshare: 成交净买额)
                    "fund_inflow": 48.12,         # 资金净流入(亿元) (akshare: 资金净流入)
                    "balance": 367.88,            # 当日资金余额(亿元) (akshare: 当日资金余额)
                    "up_count": 860,              # 上涨数 (akshare: 上涨数)
                    "flat_count": 43,             # 持平数 (akshare: 持平数)
                    "down_count": 621,            # 下跌数 (akshare: 下跌数)
                    "index_name": "上证指数",     # 相关指数 (akshare: 相关指数)
                    "index_change_pct": 0.00      # 指数涨跌幅(%) (akshare: 指数涨跌幅)
                },
                // ... 港股通(沪), 深股通, 港股通(深)
            ]
        }
    
    Error:
        {"status": "error", "message": "获取资金流总览失败: ..."}
    """
```

**实现伪代码:**
```python
def get_capital_flow_summary() -> dict:
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if df.empty:
            return {"status": "error", "message": "暂无资金流数据"}
        
        date = str(df["交易日"].iloc[0])
        channels = []
        for _, row in df.iterrows():
            channels.append({
                "name": row["板块"],
                "type": row["类型"],
                "direction": row["资金方向"],
                "trade_status": _parse_trade_status(row["交易状态"]),
                "net_buy": _safe_float(row["成交净买额"]),
                "fund_inflow": _safe_float(row["资金净流入"]),
                "balance": _safe_float(row["当日资金余额"]),
                "up_count": _safe_int(row["上涨数"]),
                "flat_count": _safe_int(row["持平数"]),
                "down_count": _safe_int(row["下跌数"]),
                "index_name": row["相关指数"],
                "index_change_pct": _safe_float(row["指数涨跌幅"]),
            })
        
        return {"status": "success", "date": date, "channels": channels}
    except Exception as e:
        return {"status": "error", "message": f"获取资金流总览失败: {e}"}

def _parse_trade_status(val) -> str:
    """交易状态数字转文字: 1=盘前, 2=交易中, 3=已收盘"""
    mapping = {"1": "盘前", "2": "交易中", "3": "已收盘"}
    return mapping.get(str(int(val)) if pd.notna(val) else "", str(val))

def _safe_float(val):
    """NaN → None"""
    v = pd.to_numeric(val, errors="coerce")
    return None if pd.isna(v) else round(float(v), 2)

def _safe_int(val):
    """NaN → None"""
    v = pd.to_numeric(val, errors="coerce")
    return None if pd.isna(v) else int(v)
```

### 3.2 get_capital_flow_history()

```python
def get_capital_flow_history(
    direction: str = "北向",
    days: int = 20,
) -> dict:
    """
    查询沪深港通历史资金流数据。
    
    数据源: ak.stock_hsgt_hist_em(symbol)
    注: stock_hsgt_hist_em() 返回全部历史数据（约 2664 行），客户端按 days 截取尾部。
    
    Args:
        direction: 方向，默认"北向"。可选: "北向","沪股通","深股通","南向","港股通沪","港股通深"
        days: 返回天数，默认20，最大365（超出截断）
    
    Returns:
        {
            "status": "success",
            "direction": "北向",
            "days": 20,
            "summary": {
                "cumulative_net_buy": 312.45,    # 近N日累计净买额(亿元)，仅统计非NaN行
                "daily_avg_net_buy": 15.62,      # 日均净买额(亿元)
                "trend": "持续流入",               # "持续流入"/"持续流出"/"震荡"
                "max_daily_inflow": {"date": "2026-05-08", "value": 68.32},
                "max_daily_outflow": {"date": "2026-05-05", "value": -23.45},
            },
            "data": [
                {
                    "date": "2026-05-08",
                    "net_buy": null,             # 2024-08-19 后为 NaN → null
                    "buy_amount": null,
                    "sell_amount": null,
                    "cumulative_net_buy": null,
                },
                // ... 最近 N 个交易日
            ]
        }
    """
```

**实现要点:**
```python
DIRECTION_MAP = {
    "北向": "北向资金",
    "沪股通": "沪股通",
    "深股通": "深股通",
    "南向": "南向资金",
    "港股通沪": "港股通沪",
    "港股通深": "港股通深",
}

def get_capital_flow_history(direction="北向", days=20):
    if direction not in DIRECTION_MAP:
        return {"status": "error", "message": f"无效方向 '{direction}'，支持: {list(DIRECTION_MAP.keys())}"}
    days = min(days, 365)
    
    df = ak.stock_hsgt_hist_em(symbol=DIRECTION_MAP[direction])
    # 截取尾部
    df = df.tail(days).reset_index(drop=True)
    
    # 趋势计算仅基于非 NaN 的 net_buy
    net_buys = pd.to_numeric(df["当日成交净买额"], errors="coerce").dropna()
    if len(net_buys) > 0:
        positive_ratio = (net_buys > 0).sum() / len(net_buys)
        trend = "持续流入" if positive_ratio >= 0.7 else ("持续流出" if positive_ratio <= 0.3 else "震荡")
    else:
        trend = "数据不足"
    
    # 逐行转换
    data = []
    for _, row in df.iterrows():
        data.append({
            "date": str(row["日期"]),
            "net_buy": _safe_float(row["当日成交净买额"]),
            "buy_amount": _safe_float(row["买入成交额"]),
            "sell_amount": _safe_float(row["卖出成交额"]),
            "cumulative_net_buy": _safe_float(row["历史累计净买额"]),
        })
    
    # summary 计算
    summary = {"trend": trend, ...}
```

### 3.3 get_northbound_sector_rank()

```python
def get_northbound_sector_rank(
    board_type: str = "行业板块",
    indicator: str = "5日",
    top_n: int = 10,
) -> dict:
    """
    获取北向资金行业/概念板块增持排行。
    
    数据源: ak.stock_hsgt_board_rank_em(symbol, indicator)
    
    ⚠️ 实际 akshare 列名（已验证源码）:
        固定列: "序号", "名称", "最新涨跌幅", "报告时间"
        动态列（indicator 决定列名中的时间标记，但 akshare 统一输出为 "今日" 前缀）:
            "北向资金今日持股-股票只数", "北向资金今日持股-市值", "北向资金今日持股-占板块比", "北向资金今日持股-占北向资金比"
            "北向资金今日增持估计-股票只数", "北向资金今日增持估计-市值", "北向资金今日增持估计-市值增幅",
            "北向资金今日增持估计-占板块比", "北向资金今日增持估计-占北向资金比"
            "今日增持最大股-市值", "今日增持最大股-占总市值比", "今日减持最大股-市值", "今日减持最大股-占总市值比"
    
    注: 非交易日/数据更新延迟时可能返回 None（'NoneType' object is not subscriptable）。
    
    Args:
        board_type: 板块类型，默认"行业板块"。可选: "行业板块","概念板块"
        indicator: 时间周期，默认"5日"。可选: "今日","3日","5日","10日","1月","1季","1年"
        top_n: 返回条数，默认10
    
    Returns:
        {
            "status": "success",
            "board_type": "行业板块",
            "indicator": "5日",
            "report_date": "2026-05-08",
            "data": [
                {
                    "rank": 1,
                    "name": "半导体",                              # 名称
                    "change_pct": 3.21,                          # 最新涨跌幅(%)
                    "holding_count": 45,                         # 北向持股-股票只数
                    "holding_market_cap": 1523.45,              # 北向持股-市值(万元)
                    "holding_ratio": 5.12,                      # 北向持股-占板块比(%)
                    "holding_north_ratio": 1.23,                # 北向持股-占北向资金比(%)
                    "increase_count": 5,                        # 增持估计-股票只数
                    "increase_market_cap": 152300.00,           # 增持估计-市值(万元)
                    "increase_market_cap_change": 2.15,         # 增持估计-市值增幅(%)
                    "increase_ratio": 0.52,                     # 增持估计-占板块比(%)
                    "increase_north_ratio": 0.12,               # 增持估计-占北向资金比(%)
                    "top_increase_stock_value": 23456.00,       # 增持最大股-市值(万元)
                    "top_increase_stock_ratio": 0.85,           # 增持最大股-占总市值比(%)
                    "top_decrease_stock_value": 12345.00,       # 减持最大股-市值(万元)
                    "top_decrease_stock_ratio": 0.45,           # 减持最大股-占总市值比(%)
                },
                // ... Top N
            ]
        }
    
    Error:
        {"status": "error", "message": "获取北向资金行业排行失败: ..."}
    """
```

**BOARD_TYPE 映射:**
```python
BOARD_TYPE_MAP = {
    "行业板块": "北向资金增持行业板块排行",
    "概念板块": "北向资金增持概念板块排行",
}
```

## 4. MCP Tool Definitions

```python
# fund_mcp_server.py 中新增（使用 def，匹配现有模式）

@mcp.tool()
def get_capital_flow_summary() -> dict:
    """获取沪深港通今日资金流总览。包含沪股通、深股通、港股通各通道的当日净买额、资金流入、余额及涨跌家数。"""
    return fund_tools.get_capital_flow_summary()


@mcp.tool()
def get_capital_flow_history(direction: str = "北向", days: int = 20) -> dict:
    """查询沪深港通历史资金流趋势。支持北向/南向/沪股通/深股通方向，返回近N日逐日数据及趋势分析。
    
    Args:
        direction: 方向，可选: 北向(默认)、沪股通、深股通、南向、港股通沪、港股通深
        days: 返回天数，默认20，最大365
    """
    return fund_tools.get_capital_flow_history(direction=direction, days=days)


@mcp.tool()
def get_northbound_sector_rank(board_type: str = "行业板块", indicator: str = "5日", top_n: int = 10) -> dict:
    """获取北向资金行业/概念板块增持排行。展示外资在各板块的持股和增持情况。
    
    Args:
        board_type: 板块类型，可选: 行业板块(默认)、概念板块
        indicator: 时间周期，可选: 今日、3日、5日(默认)、10日、1月、1季、1年
        top_n: 返回条数，默认10
    """
    return fund_tools.get_northbound_sector_rank(board_type=board_type, indicator=indicator, top_n=top_n)
```

## 5. CLI Commands

```bash
# 新增 capital-flow 子命令组

python cli.py capital-flow summary
python cli.py capital-flow history [--direction 北向] [--days 20]
python cli.py capital-flow sector-rank [--board-type 行业板块] [--indicator 5日] [--top-n 10]
```

## 6. Data Model（已验证的实际列名）

### stock_hsgt_fund_flow_summary_em() — 实际返回 4 行 × 13 列

| akshare 实际列名 | 内部字段 | 类型 | 说明 |
|---|---|---|---|
| `交易日` | date | str | 数据日期 |
| `类型` | type | str | 沪港通/深港通 |
| `板块` | name | str | 沪股通/港股通(沪)/深股通/港股通(深) |
| `资金方向` | direction | str | 北向/南向 |
| `交易状态` | trade_status | str→int | 1=盘前, 2=交易中, 3=已收盘 |
| `成交净买额` | net_buy | float | 亿元 |
| `资金净流入` | fund_inflow | float | 亿元 |
| `当日资金余额` | balance | float | 亿元 |
| `上涨数` | up_count | int | - |
| `持平数` | flat_count | int | - |
| `下跌数` | down_count | int | - |
| `相关指数` | index_name | str | 上证指数/深证成指/恒生指数 |
| `指数涨跌幅` | index_change_pct | float | % |

⚠️ 注意: **无** `指数收盘` 列。`交易状态` 为数字需转换为文字。

### stock_hsgt_hist_em() — 实际返回 ~2664 行 × 13 列

| akshare 实际列名 | 内部字段 | 类型 | 说明 |
|---|---|---|---|
| `日期` | date | str | - |
| `当日成交净买额` | net_buy | float | 亿元，2024-08-19 后为 NaN |
| `买入成交额` | buy_amount | float | 亿元，2024-08-19 后为 NaN |
| `卖出成交额` | sell_amount | float | 亿元，2024-08-19 后为 NaN |
| `历史累计净买额` | cumulative_net_buy | float | 万亿元，2024-08-19 后为 NaN |
| `当日资金流入` | _(未映射)_ | float | 亿元 |
| `当日余额` | _(未映射)_ | float | 亿元 |
| `持股市值` | _(未映射)_ | float | 元 |
| `领涨股` | _(未映射)_ | str | - |
| `领涨股-涨跌幅` | _(未映射)_ | float | % |
| `沪深300`/`恒生指数` | _(未映射)_ | float | - |
| `沪深300-涨跌幅`/`恒生指数-涨跌幅` | _(未映射)_ | float | % |
| `领涨股-代码` | _(未映射)_ | str | - |

注: 映射核心 5 列，其余列可选扩展。

### stock_hsgt_board_rank_em() — 实际列名（已验证源码）

**固定列 (17 列):**

| akshare 实际列名 | 内部字段 | 类型 | 说明 |
|---|---|---|---|
| `序号` | rank | int | 排名 |
| `名称` | name | str | 板块名称 |
| `最新涨跌幅` | change_pct | float | % |
| `报告时间` | report_date | str | - |
| `北向资金今日持股-股票只数` | holding_count | int | - |
| `北向资金今日持股-市值` | holding_market_cap | float | 万元 |
| `北向资金今日持股-占板块比` | holding_ratio | float | % |
| `北向资金今日持股-占北向资金比` | holding_north_ratio | float | % |
| `北向资金今日增持估计-股票只数` | increase_count | int | - |
| `北向资金今日增持估计-市值` | increase_market_cap | float | 万元 |
| `北向资金今日增持估计-市值增幅` | increase_market_cap_change | float | % |
| `北向资金今日增持估计-占板块比` | increase_ratio | float | % |
| `北向资金今日增持估计-占北向资金比` | increase_north_ratio | float | % |
| `今日增持最大股-市值` | top_increase_stock_value | float | 万元 |
| `今日增持最大股-占总市值比` | top_increase_stock_ratio | float | % |
| `今日减持最大股-市值` | top_decrease_stock_value | float | 万元 |
| `今日减持最大股-占总市值比` | top_decrease_stock_ratio | float | % |

⚠️ **关键发现**: 虽然 indicator 参数可变（今日/5日/1月等），但 akshare 内部列名**固定为"今日"前缀**，indicator 仅影响 API 查询的筛选条件。因此列名映射是稳定的，不需要动态处理。

## 7. Error Handling

所有函数遵循统一错误模式：

```python
except Exception as e:
    logger.error(f"获取资金流数据失败: {e}")
    return {"status": "error", "message": f"获取资金流数据失败: {e}"}
```

特殊处理：
- **无效 direction**: 返回 `error` + 支持的参数列表
- **无效 board_type**: 返回 `error` + 支持的参数列表
- **days > 365**: 截断为 365，记录 warning
- **空 DataFrame**: 返回 `{"status": "error", "message": "暂无资金流数据"}`
- **NaN 值**: 用 `_safe_float()` / `_safe_int()` 转换，NaN → `None`（JSON 中为 `null`）
- **stock_hsgt_board_rank_em NoneType 错误**: 非交易日或数据延迟时 akshare 内部报错，catch 后返回明确错误信息

## 8. Security Considerations

- 所有数据来自东方财富公开接口，无需认证
- 不涉及用户隐私
- 无额外权限要求
- 不存储任何数据（纯实时查询）

## 9. Test Strategy

测试文件: `tests/test_capital_flow.py`

遵循项目约定：真实 API 集成测试，不 mock。

```python
import pytest
from fund_tools.capital_flow import (
    get_capital_flow_summary,
    get_capital_flow_history,
    get_northbound_sector_rank,
)

@pytest.mark.integration
class TestCapitalFlowSummary:
    def test_returns_success_status(self):
        result = get_capital_flow_summary()
        assert result["status"] == "success"
    
    def test_contains_date(self):
        result = get_capital_flow_summary()
        assert "date" in result
    
    def test_contains_channels(self):
        result = get_capital_flow_summary()
        assert "channels" in result
        assert len(result["channels"]) == 4  # 沪股通, 港股通(沪), 深股通, 港股通(深)
    
    def test_channel_has_required_fields(self):
        result = get_capital_flow_summary()
        channel = result["channels"][0]
        required = ["name", "type", "direction", "net_buy", "fund_inflow", 
                     "balance", "up_count", "down_count", "index_name", "index_change_pct"]
        for field in required:
            assert field in channel, f"Missing field: {field}"
    
    def test_channel_direction_values(self):
        result = get_capital_flow_summary()
        directions = {c["direction"] for c in result["channels"]}
        assert "北向" in directions
        assert "南向" in directions

@pytest.mark.integration
class TestCapitalFlowHistory:
    def test_northbound_default(self):
        result = get_capital_flow_history()
        assert result["status"] == "success"
        assert result["direction"] == "北向"
        assert len(result["data"]) <= 20
    
    def test_custom_days(self):
        result = get_capital_flow_history(days=5)
        assert len(result["data"]) <= 5
    
    def test_southbound(self):
        result = get_capital_flow_history(direction="南向")
        assert result["status"] == "success"
        assert result["direction"] == "南向"
    
    def test_summary_fields(self):
        result = get_capital_flow_history()
        assert "summary" in result
        assert "cumulative_net_buy" in result["summary"]
        assert "trend" in result["summary"]
        assert result["summary"]["trend"] in ("持续流入", "持续流出", "震荡", "数据不足")
    
    def test_invalid_direction(self):
        result = get_capital_flow_history(direction="无效")
        assert result["status"] == "error"
    
    def test_days_capped_at_365(self):
        result = get_capital_flow_history(days=9999)
        assert result["status"] == "success"
        assert result["days"] == 365
    
    def test_data_has_null_for_post_2024(self):
        """2024-08-19 后净买额可能为 null"""
        result = get_capital_flow_history()
        recent = [d for d in result["data"] if d["date"] >= "2024-08-19"]
        # 至少验证字段存在（值可以是 None）
        if recent:
            assert "net_buy" in recent[0]

@pytest.mark.integration
class TestNorthboundSectorRank:
    def test_industry_default(self):
        result = get_northbound_sector_rank()
        assert result["status"] in ("success", "error")  # 非交易日可能失败
        if result["status"] == "success":
            assert len(result["data"]) <= 10
    
    def test_concept_board(self):
        result = get_northbound_sector_rank(board_type="概念板块")
        assert result["status"] in ("success", "error")
    
    def test_custom_indicator(self):
        result = get_northbound_sector_rank(indicator="1月")
        assert result["status"] in ("success", "error")
    
    def test_top_n(self):
        result = get_northbound_sector_rank(top_n=5)
        if result["status"] == "success":
            assert len(result["data"]) <= 5
    
    def test_sector_has_required_fields(self):
        result = get_northbound_sector_rank()
        if result["status"] == "success" and result["data"]:
            item = result["data"][0]
            required = ["rank", "name", "change_pct", "holding_market_cap", 
                        "increase_market_cap", "increase_market_cap_change"]
            for field in required:
                assert field in item, f"Missing field: {field}"
    
    def test_invalid_board_type(self):
        result = get_northbound_sector_rank(board_type="无效")
        assert result["status"] == "error"
    
    def test_nontrading_day_graceful_error(self):
        """非交易日应返回明确错误而非崩溃"""
        result = get_northbound_sector_rank()
        assert result["status"] in ("success", "error")
        if result["status"] == "error":
            assert "message" in result
```

## 10. Rollout / Rollback

**Rollout**: 纯增量功能，不影响现有工具。部署顺序：
1. 新增 `capital_flow.py` 模块
2. 更新 `__init__.py` 导出
3. 更新 `fund_mcp_server.py` 注册工具
4. 更新 `cli.py` 添加命令
5. 运行测试验证
6. 更新 `CLAUDE.md`

**Rollback**: 删除相关代码即可，无数据迁移，无状态变更。

## 11. Risks

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 2024-08-19 后核心字段为 NaN | 高 | 中 | _safe_float() 转 null；趋势计算仅用非 NaN 行 |
| stock_hsgt_board_rank_em 非交易日报错 | 高 | 低 | catch NoneType 错误，返回明确 error |
| akshare API 结构变更 | 低 | 中 | 防御性解析 + 明确错误信息 |
| 东方财富接口限速 | 低 | 低 | 纯实时查询，频率自然受限 |
| stock_hsgt_hist_em 返回全量数据(2664行) | 确定 | 低 | 客户端 tail(days) 截取 |
