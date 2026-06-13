# -*- coding: utf-8 -*-
"""根 Typer 应用：组装所有子命令组"""

import typer

app = typer.Typer(
    name="ttjj-fund",
    help="中国基金和指数信息查询工具 v2.3",
    no_args_is_help=True,
)


def _register():
    from .bond import bond_app
    from .index import index_app
    from .capital_flow import cf_app
    from .stock import stock_app

    app.add_typer(bond_app, name="bond")
    app.add_typer(index_app, name="index")
    app.add_typer(cf_app, name="capital-flow")
    app.add_typer(stock_app, name="stock")


_register()


if __name__ == "__main__":
    app()
