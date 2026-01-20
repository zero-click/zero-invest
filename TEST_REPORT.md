# 单元测试说明

## 📊 测试概况

本测试套件使用 **pytest** 框架，包含 18 个测试用例，覆盖基金信息查询的所有核心功能。

### 测试统计

- **总测试数**: 18 个
- **通过率**: 100% ✅
- **代码覆盖率**: 70%
- **执行时间**: ~0.5 秒

### 测试类别

| 测试类 | 测试数 | 描述 |
|--------|--------|------|
| `TestFundList` | 3 | 基金列表获取（含缓存测试） |
| `TestSearchFunds` | 5 | 基金搜索（代码/名称/拼音） |
| `TestGetFundDetails` | 2 | 基金详情查询 |
| `TestGetFundRankings` | 2 | 基金排行榜 |
| `TestGetFundRating` | 3 | 基金评级查询 |
| `TestCalculateRiskMetrics` | 2 | 风险指标计算 |
| `TestIntegration` | 1 | 集成测试 |

## 🚀 运行测试

### 基础运行

```bash
# 运行所有测试
.venv/bin/pytest test_fund_tool.py

# 详细输出
.venv/bin/pytest test_fund_tool.py -v

# 显示简短traceback
.venv/bin/pytest test_fund_tool.py -v --tb=short
```

### 高级运行

```bash
# 运行特定测试类
.venv/bin/pytest test_fund_tool.py::TestSearchFunds -v

# 运行特定测试方法
.venv/bin/pytest test_fund_tool.py::TestSearchFunds::test_search_funds_by_name -v

# 运行集成测试
.venv/bin/pytest test_fund_tool.py -m integration

# 并行运行（需要 pytest-xdist）
.venv/bin/pytest test_fund_tool.py -n auto
```

### 覆盖率报告

```bash
# 终端输出（显示未覆盖的行号）
.venv/bin/pytest test_fund_tool.py --cov=fund_tool_akshare --cov-report=term-missing

# HTML 报告
.venv/bin/pytest test_fund_tool.py --cov=fund_tool_akshare --cov-report=html

# 在浏览器中打开报告
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## 📝 测试用例说明

### 1. TestFundList (基金列表测试)

- `test_get_fund_list_success` ✅ - 测试成功获取基金列表
- `test_get_fund_list_cached` ✅ - 测试缓存功能（LRU缓存）
- `test_get_fund_list_error` ✅ - 测试网络错误处理

### 2. TestSearchFunds (基金搜索测试)

- `test_search_funds_by_code` ✅ - 按基金代码搜索
- `test_search_funds_by_name` ✅ - 按基金名称搜索
- `test_search_funds_by_pinyin` ✅ - 按拼音缩写搜索
- `test_search_funds_not_found` ✅ - 搜索不到结果
- `test_search_funds_empty_database` ✅ - 数据库为空

### 3. TestGetFundDetails (基金详情测试)

- `test_query_fund_details_invalid_code_format` ✅ - 无效代码格式验证
- `test_query_fund_details_success` ✅ - 成功查询详情

### 4. TestGetFundRankings (排行榜测试)

- `test_get_fund_rankings_success` ✅ - 成功获取排行榜
- `test_get_fund_rankings_error` ✅ - 网络错误处理

### 5. TestGetFundRating (基金评级测试)

- `test_get_fund_rating_success` ✅ - 成功获取评级
- `test_get_fund_rating_not_found` ✅ - 基金未找到
- `test_get_fund_rating_error` ✅ - 网络错误处理

### 6. TestCalculateRiskMetrics (风险指标测试)

- `test_calculate_risk_metrics_from_data_valid` ✅ - 有效数据计算
- `test_calculate_risk_metrics_from_data_empty` ✅ - 空数据处理

### 7. TestIntegration (集成测试)

- `test_full_workflow_search_and_details` ✅ - 完整工作流测试

## 🔧 Mock 策略

使用 `unittest.mock` 进行 Mock，避免真实的网络请求：

```python
@patch('fund_tool_akshare.ak.fund_name_em')
def test_get_fund_list_success(self, mock_fund_name_em):
    # Mock 返回数据
    mock_data = pd.DataFrame({...})
    mock_fund_name_em.return_value = mock_data

    # 执行测试
    result = fund_tool.get_fund_list()

    # 验证
    assert not result.empty
```

## 📊 覆盖率分析

当前覆盖率：**70%**

### 已覆盖的代码

- ✅ 基金列表获取 (`get_fund_list`)
- ✅ 基金搜索逻辑 (`search_funds`)
- ✅ 基金详情查询主流程 (`query_fund_details`)
- ✅ 风险指标计算 (`calculate_risk_metrics_from_data`)
- ✅ 排行榜查询 (`get_fund_rankings`)
- ✅ 评级查询 (`get_fund_rating`)

### 未覆盖的代码

主要是一些异常处理分支和特定条件：

```python
# fund_tool_akshare.py:61-63 (未覆盖)
keyword_lower = keyword.lower()
results = [f for f in fund_database if ...]
```

## 🎯 持续集成

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run tests
      run: pytest test_fund_tool.py --cov=fund_tool_akshare --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## 🐛 调试测试

### 运行单个测试并打印输出

```bash
.venv/bin/pytest test_fund_tool.py::TestSearchFunds::test_search_funds_by_name -v -s
```

### 在第一个失败时停止

```bash
.venv/bin/pytest test_fund_tool.py -x
```

### 进入调试模式（pdb）

```bash
.venv/bin/pytest test_fund_tool.py --pdb
```

## 📚 最佳实践

1. **隔离性** - 每个测试独立运行，互不影响
2. **Mock外部依赖** - 使用 mock 避免真实网络请求
3. **测试命名** - 清晰描述测试目的
4. **覆盖边界情况** - 测试成功和失败场景
5. **使用夹具** - 复用测试数据（已定义 `fund_data_sample` 等夹具）

## 🔄 持续改进

### 提高覆盖率的建议

1. 添加更多边界测试
2. 测试异常处理路径
3. 添加性能测试
4. 添加端到端测试（需要真实网络）

### 下一步

- [ ] 添加性能测试（基准测试）
- [ ] 添加参数化测试（使用 `@pytest.mark.parametrize`）
- [ ] 添加对 fund_mcp_server.py 的测试
- [ ] 集成到 CI/CD 流程

## 📞 问题反馈

如果测试失败或有疑问，请查看：
- 测试日志：`pytest -v -s`
- 覆盖率报告：`htmlcov/index.html`
- 代码文档：`README_MCP.md`
