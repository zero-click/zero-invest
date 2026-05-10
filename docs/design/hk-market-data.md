# 香港市场基金与指数数据拉取 — Feature Design

## Overview

在现有大陆市场模块基础上，新增香港市场基金和指数数据拉取能力。新增 2 个核心模块 + 1 个 CLI 命令组 + 5 个 MCP 工具，完全复用现有架构模式。

## Architecture

### 模块结构

```
src/fund_tools/
├── core.py              # 现有 — 大陆基金
├── index.py             # 现有 — 大陆指数
├── cache.py             # 扩展 — 新增 HK 基金缓存
├── capital_flow.py      # 现有 — 资金流向
├── hk_fund.py           # 新增 — 香港基金
└── hk_index.py          # 新增 — 港股指数

src/cli/
├── bond/                # 现有
├── index/               # 现有
├── capital_flow/        # 现有
├── hk/                  # 新增 — 香港市场命令组
│   ├── __init__.py      # hk app 注册 (fund + index 子组)
│   ├── fund/            # 香港基金命令
│   │   ├── __init__.py  # fund 子组注册
│   │   ├── ranking.py
│   │   ├── search.py
│   │   └── history.py
│   └── index/           # 港股指数命令
│       ├── __init__.py  # index 子组注册
│       ├── spot.py
│       └── daily.py
└── main.py              # 扩展 — 注册 hk app
```

### 数据源优先级

```
港股指数实时行情: stock_hk_index_spot_sina → stock_hk_index_spot_em (fallback)
港股指数历史行情: stock_hk_index_daily_sina → stock_hk_index_daily_em (fallback)
香港基金排行:     fund_hk_rank_em (单源)
香港基金历史净值: fund_hk_fund_hist_em (单源)
```

### 数据流

```
用户 → CLI / MCP → hk_fund.py / hk_index.py → akshare API → 返回标准 dict
                    ↑ cache.py (HK 基金排行缓存)
```

## Interface / API Contracts

### hk_fund.py

```python
def get_hk_fund_rankings(sort_by: str = "近1年", limit: int = 50) -> Dict[str, Any]:
    """
    获取香港基金排行榜
    Args:
        sort_by: 排序字段，可选值：近1周/近1月/近3月/近6月/近1年/近2年/近3年/今年来/成立来
        limit: 返回数量上限
    Returns:
        成功: {status, count, sort_by, data: [{基金代码, 基金简称, 币种, 日期, 单位净值, 日增长率,
               近1周, 近1月, 近3月, 近6月, 近1年, 近2年, 近3年, 今年来, 成立来, 可购买, 香港基金代码}]}
        失败: {status: "error", message: "获取香港基金排行失败: ..."}
    Note: sort_by 无效字段时返回 {status: "error", message: "不支持的排序字段: ...，可选值: ..."}
    """

def search_hk_funds(keyword: str) -> Dict[str, Any]:
    """
    搜索香港基金（按基金代码或基金简称）
    Args:
        keyword: 搜索关键字
    Returns:
        成功: {status, count, data: [{基金代码, 基金简称, ...}]}
        失败: {status: "error", message: "搜索香港基金失败: ..."}
    Note: 自动拉取并缓存排行数据（如本地缓存不存在）
    """

def get_hk_fund_history(code: str, history_type: str = "历史净值明细") -> Dict[str, Any]:
    """
    获取香港基金历史净值/分红送配
    Args:
        code: 基金代码（6位），函数内部自动查找对应的香港基金代码
        history_type: "历史净值明细" 或 "分红送配详情"
    Returns:
        历史净值: {status, code, name, type, count, data: [{净值日期, 单位净值, 日增长值, 日增长率, 单位}]}
        分红送配: {status, code, name, type, count, data: [{...}]}
    Error responses:
        - 缓存为空且无法获取排行数据: {status: "error", message: "香港基金数据不可用，请稍后重试"}
        - 6位代码在缓存中不存在: {status: "error", message: "未找到基金代码 {code}，请通过 search_hk_funds 搜索确认"}
        - 代码存在但香港基金代码为空: {status: "error", message: "基金 {code} 缺少香港基金代码映射"}
        - history_type 无效: {status: "error", message: "不支持的类型: {history_type}，可选值: 历史净值明细, 分红送配详情"}
    """
```

### hk_index.py

```python
def get_hk_index_spot() -> Dict[str, Any]:
    """
    获取港股指数实时行情
    Returns:
        成功: {status, source, count, data_delay_note: "数据可能有15分钟延迟，仅供参考", 
               data: [{代码, 名称, 最新价, 涨跌额, 涨跌幅, 昨收, 今开, 最高, 最低}]}
        双源均失败: {status: "error", message: "港股指数行情暂时不可用，请稍后重试"}
    """

def get_hk_index_daily(symbol: str, days: int = 30) -> Dict[str, Any]:
    """
    获取港股指数历史行情
    Args:
        symbol: 指数代码（如 CES100）
        days: 返回最近多少天的数据（范围 1-365，默认 30）
    Returns:
        成功: {status, symbol, count, data: [{date, open, high, low, close, volume, amount}]}
        参数错误: {status: "error", message: "days 必须 > 0"} 或 "days 不能超过 365"
        接口失败: {status: "error", message: "获取港股指数历史行情失败: ..."}
    """
```

### cache.py 扩展

```python
# 新增常量
HK_FUND_DB_FILE = os.path.join(BASE_DIR, "hk_fund_database.json")
HK_FUND_DB_TTL = 1 * 24 * 3600  # 1天过期（排行数据每日变化）
HK_FUND_DB_SCHEMA_VERSION = 1

def get_hk_fund_list() -> pd.DataFrame:
    """获取香港基金排行数据（带磁盘缓存）"""

def update_hk_fund_cache() -> Dict[str, Any]:
    """强制刷新香港基金排行缓存（force-refresh，类似 update_index_cache）"""

def _save_hk_fund_db_to_disk(df: pd.DataFrame) -> None:
    """保存香港基金排行到本地缓存（含 schema_version 标记）"""

def _load_hk_fund_db_from_disk() -> pd.DataFrame:
    """从磁盘加载香港基金排行缓存（含 schema_version 校验）"""
```

### `__init__.py` 扩展

必须将 5 个新函数添加到 `src/fund_tools/__init__.py` 的 import + `__all__` 列表：

```python
from .hk_fund import get_hk_fund_rankings, search_hk_funds, get_hk_fund_history
from .hk_index import get_hk_index_spot, get_hk_index_daily
```

### CLI 命令

| 命令 | 对应函数 |
|------|---------|
| `python cli.py hk fund ranking [--sort-by 近1年] [--limit 50]` | `get_hk_fund_rankings()` |
| `python cli.py hk fund search "摩根"` | `search_hk_funds()` |
| `python cli.py hk fund history 968063 [--type 历史净值明细]` | `get_hk_fund_history()` |
| `python cli.py hk index spot` | `get_hk_index_spot()` |
| `python cli.py hk index daily CES100 [--days 30]` | `get_hk_index_daily()` |

### MCP 工具

| 工具名 | 对应函数 |
|--------|---------|
| `get_hk_fund_rankings` | `get_hk_fund_rankings(sort_by, limit)` |
| `search_hk_funds` | `search_hk_funds(keyword)` |
| `get_hk_fund_history` | `get_hk_fund_history(code, history_type)` |
| `get_hk_index_spot` | `get_hk_index_spot()` |
| `get_hk_index_daily` | `get_hk_index_daily(symbol, days)` |

## Data Model Implications

### 磁盘缓存文件

- **新增** `hk_fund_database.json` — 存储香港基金排行数据（~172条记录），TTL 1天
- 格式与现有 `fund_database.json` 一致（JSON 数组）
- 不影响现有缓存文件

### 无数据库变更

- 纯 API 调用 + 内存/磁盘缓存，不引入数据库

## Security Considerations

- 复用 `_clear_proxy_env()` 清除代理环境变量
- 无用户输入渲染（无 XSS 风险）
- API 调用使用 HTTPS
- 注意调用频率，避免被数据源封禁 IP

## Test Strategy

### 测试文件

- `tests/test_hk_market.py` — 集成测试（真实 API 调用）
- `tests/test_hk_unit.py` — 单元测试（mock fallback 和参数验证）

### 集成测试（至少 8 个）

| # | 测试 | 覆盖 AC |
|---|------|---------|
| 1 | `test_get_hk_fund_rankings` | AC-1 (正常排行) |
| 2 | `test_get_hk_fund_rankings_sort` | AC-1 (排序) |
| 3 | `test_search_hk_funds` | AC-2 (搜索) |
| 4 | `test_get_hk_fund_history_nav` | AC-3 (历史净值) |
| 5 | `test_get_hk_fund_history_dividend` | AC-3 (分红送配) |
| 6 | `test_get_hk_index_spot` | AC-4 (实时行情) |
| 7 | `test_get_hk_index_daily` | AC-5 (历史行情) |
| 8 | `test_get_hk_fund_history_invalid_code` | AC-3 (错误处理) |

### 单元测试（至少 5 个）

| # | 测试 | 覆盖内容 |
|---|------|---------|
| U1 | `test_sort_by_validation` | sort_by 参数验证（无效字段返回 error） |
| U2 | `test_days_validation` | days 参数验证（0、负数、超大值返回 error） |
| U3 | `test_code_mapping_not_found` | 6位代码不在缓存中返回 error |
| U4 | `test_index_spot_fallback` | Mock sina 失败 → EM 成功 → source="em" |
| U5 | `test_index_spot_both_fail` | Mock 双源均失败 → status="error" |
| U6 | `test_history_type_validation` | 无效 history_type 返回 error |
| U7 | `test_search_cold_cache` | 缓存不存在时自动拉取后搜索 |

### 测试数据

- 测试基金代码：`968063`（摩根太平洋科技美元）
- 测试指数代码：`CES100`（中华港股通精选100指数）

## Rollout / Rollback

### Rollout

1. 新增文件不影响现有功能
2. 部署顺序：core modules → CLI → MCP tools → tests → docs

### Rollback

- 删除 `hk_fund.py`, `hk_index.py`, `src/cli/hk/` 目录
- 撤销 `cache.py` 的 HK 缓存扩展
- 撤销 `main.py` 的 hk app 注册
- 撤销 `fund_mcp_server.py` 的 HK 工具注册
- 删除 `hk_fund_database.json`

## Risks

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| 东财港股指数接口不稳定 | 指数实时行情可能全部依赖新浪 | 新浪为主源，东财为备源；双源均失败返回友好错误 |
| 新浪港股指数数据被限流 | 临时无法获取指数行情 | 文档提示 10 分钟后重试；缓存 TTL 延长 |
| akshare 接口签名变化 | 运行时报错 | 锁定 akshare 版本；接口变更时更新 |
| 基金代码混淆（6位 vs 长码） | 历史净值查询失败 | 缓存中建立映射，用户只需使用 6 位码 |
