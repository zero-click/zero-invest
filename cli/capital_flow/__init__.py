# -*- coding: utf-8 -*-
"""沪深港通资金流分析命令组"""

import typer

cf_app = typer.Typer(help="沪深港通资金流分析", no_args_is_help=True)

# 导入所有命令模块以注册 @cf_app.command()
import cli.capital_flow.summary    # noqa: F401
import cli.capital_flow.history    # noqa: F401
import cli.capital_flow.sector_rank  # noqa: F401
