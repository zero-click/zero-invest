# -*- coding: utf-8 -*-
"""基金相关查询命令组"""

import typer

bond_app = typer.Typer(help="基金相关查询", no_args_is_help=True)

# 导入所有命令模块以注册 @bond_app.command()
from . import search        # noqa: F401
from . import query         # noqa: F401
from . import ranking       # noqa: F401
from . import rating        # noqa: F401
from . import manager       # noqa: F401
from . import holdings      # noqa: F401
from . import allocation    # noqa: F401
from . import fee           # noqa: F401
from . import liquidity     # noqa: F401
from . import performance   # noqa: F401
from . import risk          # noqa: F401
from . import top_holdings  # noqa: F401
from . import portfolio     # noqa: F401
from . import recent        # noqa: F401
from . import update        # noqa: F401
