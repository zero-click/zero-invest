# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import fund_tool
import os

app = FastAPI(
    title="基金信息查询 MCP 服务",
    description="一个通过 Web API 提供基金数据查询的服务。",
    version="1.0.0",
)

# 获取当前文件所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MANIFEST_PATH = os.path.join(BASE_DIR, "mcp_manifest.json")

@app.get("/.well-known/mcp_manifest.json", summary="获取 MCP 清单文件")
async def get_manifest():
    """
    提供给大模型用以发现和理解此服务能力的清单文件。
    """
    if not os.path.exists(MANIFEST_PATH):
        raise HTTPException(status_code=404, detail="清单文件 'mcp_manifest.json' 未找到。")
    return FileResponse(MANIFEST_PATH)

@app.get("/fund/{code}", summary="查询基金详细信息")
async def get_fund_details(code: str):
    """
    根据给定的6位基金代码，查询基金的详细信息。
    """
    print(f"接收到查询请求: /fund/{code}")
    data = fund_tool.query_fund_details(code)
    if data.get("status") == "error":
        raise HTTPException(status_code=404, detail=data.get("message"))
    return data

@app.get("/search/{keyword}", summary="搜索基金")
async def search_for_funds(keyword: str):
    """
    根据给定的关键词（代码、名称、拼音）搜索相关基金列表。
    """
    print(f"接收到搜索请求: /search/{keyword}")
    data = fund_tool.search_funds(keyword)
    if isinstance(data, dict) and data.get("status") == "error":
        raise HTTPException(status_code=400, detail=data.get("message"))
    if not data:
        return {"message": f"未找到与 '{keyword}' 相关的基金。"}
    return data

@app.post("/update", summary="更新本地基金数据库")
async def update_database():
    """
    从上游数据源下载最新的基金列表，并更新本地数据库。
    这是一个耗时操作。
    """
    print("接收到数据库更新请求: /update")
    result = fund_tool.update_fund_database()
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("message"))
    return {"message": f"基金数据库更新成功! 共找到 {result.get('count')} 只基金。", "path": result.get('path')}

@app.get("/", summary="服务根节点")
async def read_root():
    return {"message": "欢迎使用基金信息查询 MCP 服务。这是一个为大模型设计的插件服务。请访问 /.well-known/mcp_manifest.json 获取服务清单。"}

if __name__ == "__main__":
    import uvicorn
    print("服务已启动，请访问 http://127.0.0.1:8000")
    print("API 文档请访问 http://127.0.0.1:8000/docs")
    print("MCP 清单请访问 http://127.0.0.1:8000/.well-known/mcp_manifest.json")
    uvicorn.run(app, host="127.0.0.1", port=8000)
