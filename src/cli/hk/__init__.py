# -*- coding: utf-8 -*-
"""香港市场命令组"""

import typer

hk_app = typer.Typer(help="香港市场基金和指数数据查询", no_args_is_help=True)

# 导入所有命令模块以注册 @hk_app.command()
from . import fund_ranking      # noqa: F401
from . import fund_search       # noqa: F401
from . import fund_history      # noqa: F401
from . import index_spot        # noqa: F401
from . import index_daily       # noqa: F401
