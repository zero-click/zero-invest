# -*- coding: utf-8 -*-
from mcp.server.fastmcp import FastMCP
from fund_tool import query_fund_details, search_funds, update_fund_database
from index_valuation import (
    get_index_pe,
    get_csindex_valuation,
    get_index_valuation_batch,
    get_portfolio_index_valuation,
    compare_fund_with_index,
)

app = FastMCP("FundInfo", port=8000)

# Original fund tools
app.add_tool(query_fund_details)
app.add_tool(search_funds)
app.add_tool(update_fund_database)

# New index valuation tools
app.add_tool(get_index_pe)
app.add_tool(get_csindex_valuation)
app.add_tool(get_index_valuation_batch)
app.add_tool(get_portfolio_index_valuation)
app.add_tool(compare_fund_with_index)

if __name__ == "__main__":
    app.run(transport="streamable-http")
