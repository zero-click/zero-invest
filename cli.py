#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI 入口 — 调用 Typer 模块化 CLI (src/cli/)"""

import sys
import os

# 只加 src/ 到 sys.path，避免根目录 cli.py 与 src/cli/ 包冲突
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_project_root, 'src'))

from cli.main import app  # noqa: E402

app()
