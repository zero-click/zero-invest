# -*- coding: utf-8 -*-
"""个股相关查询命令组"""

import typer

stock_app = typer.Typer(help="个股相关查询", no_args_is_help=True)

# 导入所有命令模块以注册 @stock_app.command()
from . import search        # noqa: F401
from . import query         # noqa: F401
from . import hist          # noqa: F401
from . import valuation     # noqa: F401
from . import scenario_a    # noqa: F401
from . import scenario_b    # noqa: F401
from . import scenario_c    # noqa: F401
from . import classify      # noqa: F401
from . import checklist     # noqa: F401
from . import drawdown      # noqa: F401
from . import check_logic   # noqa: F401
from . import exit_eval     # noqa: F401
from . import update        # noqa: F401
from . import cache         # noqa: F401
