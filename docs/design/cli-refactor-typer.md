# 重构设计：CLI argparse → Typer 模块化

## 变更范围

纯内部重构，外部行为完全不变。所有 CLI 命令、参数、输出格式保持一致。

## 选型决定

**Typer >=0.15.0**（基于 Gate 0 研究）
- 类型注解驱动，样板代码最少
- Rich 集成提供美观 help
- `add_typer()` 原生多文件支持
- 底层 Click，可随时降级

## 目标文件结构

```
cli/                          # 新包（替代原 cli.py 单文件）
├── __init__.py               # 空
├── main.py                   # 根 Typer app，组装子 app，print_banner()
├── helpers.py                # 共享工具函数：_fmt_amount(), get_current_year()
├── bond/                     # bond 子命令组（13 个命令）
│   ├── __init__.py           # bond_app = typer.Typer(...)
│   ├── search.py
│   ├── query.py
│   ├── ranking.py
│   ├── rating.py
│   ├── manager.py
│   ├── holdings.py
│   ├── allocation.py
│   ├── fee.py
│   ├── liquidity.py
│   ├── performance.py
│   ├── risk.py
│   ├── top_holdings.py
│   ├── portfolio.py
│   └── update.py
├── index/                    # index 子命令组（9 个命令）
│   ├── __init__.py           # index_app = typer.Typer(...)
│   ├── search.py
│   ├── query.py
│   ├── valuation.py
│   ├── batch.py
│   ├── risk.py
│   ├── listfund.py
│   ├── heatmap.py
│   └── update.py
└── capital_flow/             # capital-flow 子命令组（3 个命令）
    ├── __init__.py           # cf_app = typer.Typer(...)
    ├── summary.py
    ├── history.py
    └── sector_rank.py
```

## 每个命令文件的统一模式

```python
# cli/bond/search.py
import typer
from . import bond_app
from ...helpers import print_banner

@bond_app.command()
def search(
    keyword: str = typer.Argument(help="搜索关键词（基金代码/名称/拼音）"),
    all_results: bool = typer.Option(False, "--all", "-a", help="显示所有结果"),
):
    """搜索基金"""
    print_banner()
    print(f"🔍 搜索基金: {keyword}")
    print()

    # 延迟导入：避免加载 akshare/pandas 增加启动时间
    from fund_tools import search_funds

    result = search_funds(keyword)
    # ... 打印逻辑 ...
```

## 关键设计决策

### 1. 延迟导入（Lazy Import）

akshare + pandas 导入耗时 ~2-3 秒。所有 fund_tools 函数在**命令函数内部**导入，不在模块顶层导入。

原 cli.py 在文件顶部一次性导入所有函数，每次运行 CLI 都要等。重构后只有真正执行某个命令时才加载对应模块。

### 2. 打印函数随命令走

原 cli.py 的 17 个 `print_*` 函数散落在一个文件里。重构后每个命令文件自带打印逻辑（如果逻辑复杂），或直接内联在命令函数中。

共享打印工具（如 `_fmt_amount`、`print_banner`）放在 `cli/helpers.py`。

### 3. 入口点

```python
# cli/main.py
import typer

app = typer.Typer(
    name="ttjj-fund",
    help="中国基金和指数信息查询工具 v2.3",
    no_args_is_help=True,
)

def _register_apps():
    from .bond import bond_app
    from .index import index_app
    from .capital_flow import cf_app

    app.add_typer(bond_app, name="bond", help="基金相关查询")
    app.add_typer(index_app, name="index", help="指数相关查询")
    app.add_typer(cf_app, name="capital-flow", help="沪深港通资金流分析")

_register_apps()

if __name__ == "__main__":
    app()
```

### 4. 保持原有调用方式

顶层 `cli.py` 改为入口代理：
```python
#!/usr/bin/env python3
from cli.main import app
app()
```

或 `pyproject.toml` console_scripts 指向 `cli.main:app`。

## 新增依赖

```
typer>=0.15.0
```

Typer 会自动带入 `click` 和 `rich`。

## 迁移策略

1. 安装 typer，确认 import 可用
2. 创建 `cli/` 包骨架
3. 逐组迁移：bond → index → capital-flow
4. 每组迁移后验证 `python cli.py <group> --help` 输出一致
5. 删除旧 `cli.py`（或改为代理入口）
6. 全量测试

## 风险

| 风险 | 缓解 |
|------|------|
| 参数默认值 / choices 行为差异 | 逐命令对比 `--help` 输出 |
| 输出格式微变（Typer Rich 影响） | 使用 `rich_markup_mode=None` 或纯 print |
| 非交易日 API 报错（capital-flow） | 保留原有容错逻辑不变 |
