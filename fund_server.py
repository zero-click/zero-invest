# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP
from fund_tool import query_fund_details, search_funds, update_fund_database

app = FastMCP("FundInfo", port=8000)

app.add_tool(query_fund_details)
app.add_tool(search_funds)
app.add_tool(update_fund_database)

if __name__ == "__main__":
    app.run(transport="streamable-http")
