#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI 入口 — 调用 Typer 模块化 CLI (src/cli/)"""

import socket
import sys
import os

# 国内金融数据站直连，不走 proxy（墙内 CDN 对墙外 IP 开 TCP 后掐断）
# no_proxy 对 setdefault 已设的 proxy 不起作用，需要显式覆盖
existing = os.environ.get('no_proxy', '')
_extra = 'eastmoney.com,em.qt,datacenter-web.eastmoney.com'
os.environ['no_proxy'] = (existing + ',' + _extra) if existing else _extra

# 强制 IPv4：部分机器 IPv6 回程路由不通，requests 默认优先走 IPv6 会超时
# 必须在 akshare/requests 导入前设置
import requests.packages.urllib3.util.connection as _conn
_conn.allowed_gai_family = lambda: socket.AF_INET

# 只加 src/ 到 sys.path，避免根目录 cli.py 与 src/cli/ 包冲突
_project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_project_root, 'src'))

from cli.main import app  # noqa: E402

app()
