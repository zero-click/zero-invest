# 快速使用指南

## 🚦 快速启动

### 1. 激活虚拟环境
```bash
source .venv/bin/activate
```

### 2. 命令行测试

#### 测试基金搜索
```bash
.venv/bin/python3 -c "
import fund_tool_akshare as fund
result = fund.search_funds('华夏')
print(f'找到 {result[\"count\"]} 只基金')
for f in result['data'][:5]:
    print(f\"  {f['基金代码']} - {f['基金简称']}\")
"
```

#### 测试基金详情
```bash
.venv/bin/python3 -c "
import fund_tool_akshare as fund
details = fund.query_fund_details('000001')
print(f\"基金: {details['name']}\")
print(f\"经理: {', '.join([m['姓名'] for m in details['managers']])}\")
print(f\"重仓股: {', '.join(details['top_holdings'][:3])}\")
"
```

#### 测试排行榜
```bash
.venv/bin/python3 -c "
import fund_tool_akshare as fund
result = fund.get_fund_rankings('股票型')
print(f'股票型基金共 {result[\"count\"]} 只')
for i, f in enumerate(result['data'][:5], 1):
    print(f\"{i}. {f['基金简称']} - 近1年:{f.get('近1年', 'N/A')}\")
"
```

#### 测试基金评级
```bash
.venv/bin/python3 -c "
import fund_tool_akshare as fund
result = fund.get_fund_rating('000001')
rating = result['ratings']
print(f\"基金: {rating['简称']}\")
print(f\"晨星评级: {rating.get('晨星评级', 'N/A')}⭐\")
print(f\"招商证券: {rating.get('招商证券', 'N/A')}⭐\")
"
```

### 3. 启动 MCP 服务

#### HTTP 模式（推荐用于测试）
```bash
.venv/bin/python3 fund_mcp_server.py
```

然后在浏览器打开: http://localhost:8000/mcp

#### 使用 MCP Inspector
```bash
npx -y @modelcontextprotocol/inspector
```

连接到: http://localhost:8000/mcp

### 4. 配置 Claude Desktop

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fund-info": {
      "command": "/Users/woosleyxu/code/ttjj-fund/.venv/bin/python",
      "args": ["/Users/woosleyxu/code/ttjj-fund/fund_mcp_server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

重启 Claude Desktop 即可使用。

## 📝 常用命令

### 直接运行测试脚本
```bash
.venv/bin/python3 fund_tool_akshare.py
```

### 启动 FastAPI 服务（旧版）
```bash
.venv/bin/python3 fund_server_akshare.py
```

### 查看日志
```bash
tail -f fund_service.log
```

## 🎯 示例对话（Claude Desktop）

**用户**: 帮我搜索"科技"相关的基金

**Claude**: 我来帮你搜索科技相关的基金...
[调用 search_funds 工具]

**用户**: 查询000001基金的详细信息

**Claude**: 我来查询000001基金的详细信息...
[调用 get_fund_details 工具]

**用户**: 显示股票型基金排行榜前5名

**Claude**: 我来获取股票型基金的排行榜...
[调用 get_fund_rankings 工具]

## 🔧 故障排除

### SSL 证书问题
雪球网数据可能出现SSL证书错误，这是网络环境问题，不影响核心功能。

### 依赖安装失败
```bash
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

### 虚拟环境未激活
```bash
source .venv/bin/activate
```

## 📚 更多信息

查看完整文档: [README_MCP.md](README_MCP.md)
