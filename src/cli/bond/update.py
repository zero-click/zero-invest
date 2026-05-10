# -*- coding: utf-8 -*-
"""更新基金数据库命令"""

import os

import typer

from . import bond_app


@bond_app.command("update")
def update():
    """更新基金数据库"""
    from fund_tools import get_fund_list, FUND_DB_FILE

    print("正在更新基金数据库...")
    get_fund_list.cache_clear()
    if os.path.exists(FUND_DB_FILE):
        os.remove(FUND_DB_FILE)
    result = get_fund_list()
    if not result.empty:
        print(f"✅ 基金数据库更新成功！共 {len(result)} 只基金，已保存到 {FUND_DB_FILE}")
    else:
        print("❌ 基金数据库更新失败")
