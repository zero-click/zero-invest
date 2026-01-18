# 基金信息 MCP 服务器

这是一个提供中国公募基金实时数据的 Web 服务。本项目作为大语言模型（LLM）的可调用插件（Model-Callable Plugin, MCP），允许 LLM 通过结构化的 API 查询基金信息。同时，它也保留了原有的命令行接口（CLI）功能。

## 功能特性

-   **MCP 兼容**: 暴露 `mcp_manifest.json` 和 OpenAPI 规范，支持 LLM 的发现和集成。
-   **REST API**: 提供简洁的 API 端点，用于查询和搜索基金信息。
-   **实时数据**: 直接从数据源获取最新的基金详情，包括单位净值（NAV）、业绩表现和十大重仓股。
-   **本地数据库**: 缓存所有可用基金的列表，以实现快速搜索。
-   **命令行接口**: 可作为命令行工具直接进行本地查询。

## 项目结构

```
.
├── .gitignore          # Git 忽略文件
├── .venv/              # Python 虚拟环境
├── fund_database.json  # 基金列表的本地缓存
├── fund_server.py      # FastAPI Web 服务器 (MCP)
├── fund_tool.py        # 核心逻辑和命令行工具
├── mcp_manifest.json   # MCP 清单文件
└── requirements.txt    # Python 依赖
```

## API 端点

服务器提供以下 API 端点：

| 方法   | 路径                           | 描述                                     |
| ------ | ------------------------------ | ---------------------------------------- |
| `GET`  | `/`                            | 服务欢迎消息。                             |
| `GET`  | `/.well-known/mcp_manifest.json` | 提供 MCP 清单文件，用于 LLM 的发现。     |
| `GET`  | `/docs`                        | 交互式 API 文档（Swagger UI）。          |
| `GET`  | `/fund/{code}`                 | 获取指定基金的详细信息。                 |
| `GET`  | `/search/{keyword}`            | 根据代码、名称或拼音搜索基金。           |
| `POST` | `/update`                      | 触发本地基金数据库的更新。               |


## 安装

1.  **克隆仓库（如果适用）**
    ```bash
    # git clone <repository_url>
    # cd <repository_directory>
    ```

2.  **设置环境**
    本项目使用 Python 虚拟环境。如果尚未创建，请先创建：
    ```bash
    python3 -m venv .venv
    ```

3.  **激活虚拟环境**
    -   macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    -   Windows:
        ```bash
        .venv\Scripts\activate
        ```

4.  **安装依赖**
    安装 `requirements.txt` 中列出的所有依赖包：
    ```bash
    pip install -r requirements.txt
    ```

## 使用方法

### 作为 MCP 服务器

运行 Web 服务器：
```bash
python3 fund_server.py
```
服务器将在 `http://127.0.0.1:8000` 端口可用。

-   要交互式测试 API，请在浏览器中打开 `http://127.0.0.1:8000/docs`。
-   要查看 MCP 清单，请访问 `http://127.0.0.1:8000/.well-known/mcp_manifest.json`。
-   **查询示例**: `curl http://127.0.0.1:8000/fund/022364`

### 作为命令行工具

原始的 CLI 功能保留在 `fund_tool.py` 中。您可以直接使用它进行本地查询。

1.  **更新本地数据库（首次使用或需要更新时运行）**
    ```bash
    python3 fund_tool.py update
    ```

2.  **搜索基金**
    ```bash
    python3 fund_tool.py search "科技"
    ```

3.  **查询基金详情**
    ```bash
    python3 fund_tool.py query 022364
    ```