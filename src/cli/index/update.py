# -*- coding: utf-8 -*-
"""更新指数数据库命令"""

import typer

from . import index_app


@index_app.command("update")
def update():
    """更新指数数据库"""
    from fund_tools import update_index_cache, INDEX_DB_FILE

    print("正在更新指数数据库...")
    result = update_index_cache()
    if result and isinstance(result, dict):
        total = result.get('total', 0)
        print(f"✅ 指数数据库更新成功！共 {total} 个指数，已保存到 {INDEX_DB_FILE}")
    else:
        print("❌ 指数数据库更新失败")
