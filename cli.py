#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI 入口 — 调用 Typer 模块化 CLI"""

import sys
import os

# 项目根目录和 src 目录都需要在 Python 路径中
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)

from cli.main import app

app()
