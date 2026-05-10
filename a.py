import json

with open("index_database.json") as f:
    db = json.load(f)

KEYWORDS = [
    "银行","证券","保险",
    "煤炭","钢铁","有色","油气",
    "电力","新能源",
    "医药","医疗",
    "食品","饮料","白酒","家电","零售",
    "半导体","电子","软件","通信","互联网",
    "汽车","机械","电气",
    "地产","建筑",
    "传媒","军工","环保","交通"
]

selected = {}

for item in db.get("industry", []):
    name = item.get("name", "")
    for kw in KEYWORDS:
        if kw in name and kw not in selected:
            selected[kw] = item

INDUSTRY_WATCHLIST = {
    item["code"]: (item["name"], kw)
    for kw, item in selected.items()
}

print(f"选出 {len(INDUSTRY_WATCHLIST)} 个行业指数")
print(INDUSTRY_WATCHLIST)
