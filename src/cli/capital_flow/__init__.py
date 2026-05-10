# -*- coding: utf-8 -*-
"""沪深港通资金流分析命令组"""

import typer

cf_app = typer.Typer(help="沪深港通资金流分析", no_args_is_help=True)

# 导入所有命令模块以注册 @cf_app.command()
from . import summary    # noqa: F401
from . import history    # noqa: F401
