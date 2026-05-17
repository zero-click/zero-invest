# -*- coding: utf-8 -*-
"""指数相关查询命令组"""

import typer

index_app = typer.Typer(help="指数相关查询", no_args_is_help=True)

# 导入所有命令模块以注册 @index_app.command()
from . import search      # noqa: F401
from . import query       # noqa: F401
from . import valuation   # noqa: F401
from . import batch       # noqa: F401
from . import risk        # noqa: F401
from . import listfund    # noqa: F401
from . import heatmap     # noqa: F401
from . import daily       # noqa: F401
from . import recent      # noqa: F401
from . import update      # noqa: F401
