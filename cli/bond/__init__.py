# -*- coding: utf-8 -*-
"""基金相关查询命令组"""

import typer

bond_app = typer.Typer(help="基金相关查询", no_args_is_help=True)

# 导入所有命令模块以注册 @bond_app.command()
import cli.bond.search        # noqa: F401
import cli.bond.query         # noqa: F401
import cli.bond.ranking       # noqa: F401
import cli.bond.rating        # noqa: F401
import cli.bond.manager       # noqa: F401
import cli.bond.holdings      # noqa: F401
import cli.bond.allocation    # noqa: F401
import cli.bond.fee           # noqa: F401
import cli.bond.liquidity     # noqa: F401
import cli.bond.performance   # noqa: F401
import cli.bond.risk          # noqa: F401
import cli.bond.top_holdings  # noqa: F401
import cli.bond.portfolio     # noqa: F401
import cli.bond.update        # noqa: F401
