# -*- coding: utf-8 -*-
"""指数相关查询命令组"""

import typer

index_app = typer.Typer(help="指数相关查询", no_args_is_help=True)

# 导入所有命令模块以注册 @index_app.command()
import cli.index.search      # noqa: F401
import cli.index.query       # noqa: F401
import cli.index.valuation   # noqa: F401
import cli.index.batch       # noqa: F401
import cli.index.risk        # noqa: F401
import cli.index.listfund    # noqa: F401
import cli.index.heatmap     # noqa: F401
import cli.index.update      # noqa: F401
