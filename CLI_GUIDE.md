# 命令行使用指南

## 概述

`fund_tool_akshare.py` 是一个功能完整的命令行工具，支持10个子命令，涵盖基金搜索、详情查询、专业分析等功能。

---

## 快速开始

```bash
# 基本用法
python fund_tool_akshare.py <命令> [参数]

# 查看帮助
python fund_tool_akshare.py --help

# 查看特定命令的帮助
python fund_tool_akshare.py <命令> --help
```

---

## 命令列表

### 1. search - 搜索基金

按代码、名称或拼音搜索基金。

```bash
python fund_tool_akshare.py search "华夏"

# 显示所有结果（不限制50条）
python fund_tool_akshare.py search "混合" --all
```

**输出示例**：
```
  查找到 152 只基金 (显示前 10 只):

  序号   基金代码       基金名称                   基金类型
  --------------------------------------------------------------
  1      000001        华夏成长混合               混合型-灵活
  2      000011        华夏大盘精选混合A          混合型-灵活
  ...
```

---

### 2. query - 查询基金详情

获取基金的完整详细信息。

```bash
python fund_tool_akshare.py query 000001
```

**输出包含**：
- 基本信息（代码、名称、类型、成立日期、规模）
- 基金经理
- 费率信息
- 业绩表现
- 风险指标
- 十大重仓股

---

### 3. ranking - 查看排行榜

查看各类型基金的业绩排行榜。

```bash
# 查看全部基金TOP10
python fund_tool_akshare.py ranking

# 查看股票型基金TOP20
python fund_tool_akshare.py ranking --type 股票型 --top 20

# 查看混合型基金TOP15
python fund_tool_akshare.py ranking -t 混合型 -n 15
```

**支持的类型**：全部、股票型、混合型、债券型、指数型、QDII、FOF

---

### 4. rating - 查询基金评级

获取第三方机构评级。

```bash
python fund_tool_akshare.py rating 000001
```

**评级机构**：上海证券、招商证券、济安金信、晨星评级

---

### 5. manager - 基金经理详情 ⭐ 新增

查询基金经理的深度信息。

```bash
python fund_tool_akshare.py manager 000001
```

**输出包含**：
- 基金经理数量
- 每位经理的姓名、所属公司
- 累计从业时间
- 现任基金资产总规模
- 现任基金最佳回报
- 管理的其他基金

**示例输出**：
```
  基金经理数量: 2

  👤 经理 1: 刘睿聪
  ------------------------------------------------------------
    所属公司: 华夏基金
    累计从业时间: 1119天
    管理规模: 31.76亿元
    最佳回报: 44.60%
    现任基金: 华夏成长混合 (000001)
```

---

### 6. holdings - 持仓动态分析 ⭐ 新增

分析基金的持仓变化和集中度。

```bash
# 分析最近4个季度（默认）
python fund_tool_akshare.py holdings 000001

# 分析最近2个季度
python fund_tool_akshare.py holdings 000001 --periods 2
python fund_tool_akshare.py holdings 000001 -p 2
```

**输出包含**：
- 前10大持仓占比和集中度评估
- 最新前10大持仓列表
- 按季度显示的持仓变化趋势

**示例输出**：
```
  📊 持仓集中度
  ------------------------------------------------------------
    前10大持仓占比: 26.05%
    集中度评估: 低

  💼 最新前10大持仓
  ------------------------------------------------------------
   1. 航天电器         3.46%
   2. 中航高科         3.24%
  ...
```

---

### 7. allocation - 资产配置结构 ⭐ 新增

查看基金的资产配置和行业分布。

```bash
# 查看2024年配置（默认）
python fund_tool_akshare.py allocation 000001

# 查看指定年份配置
python fund_tool_akshare.py allocation 000001 --year 2023
python fund_tool_akshare.py allocation 000001 -y 2023
```

**输出包含**：
- 投资风格（成长/价值/平衡）
- 行业配置分布（前5大）
- 股票持仓样本
- 债券持仓样本

---

### 8. fee - 费用明细 ⭐ 新增

查询基金的所有费用信息。

```bash
python fund_tool_akshare.py fee 000001
```

**输出包含**：
- 管理费率
- 托管费率
- 申购费率（如有）
- 赎回费率（分档）

**示例输出**：
```
  💰 运作费用
  ------------------------------------------------------------
    管理费率: 1.20%（每年）
    托管费率: 0.20%（每年）

  📤 赎回费率
  ------------------------------------------------------------
    小于7天                 1.50%
    大于等于7天               0.50%
```

---

### 9. liquidity - 流动性信息 ⭐ 新增

查询基金的申赎规则和流动性。

```bash
python fund_tool_akshare.py liquidity 000001
```

**输出包含**：
- 申赎状态（开放/暂停）
- 交易场所
- 申赎时间
- 最低申购金额
- 申购确认时间
- 赎回到账时间

---

### 10. update - 更新数据库

更新本地的基金数据缓存。

```bash
python fund_tool_akshare.py update
```

---

## 使用技巧

### 组合查询

```bash
# 1. 搜索基金
python fund_tool_akshare.py search "华夏"

# 2. 查看详情
python fund_tool_akshare.py query 000001

# 3. 查看基金经理
python fund_tool_akshare.py manager 000001

# 4. 分析持仓
python fund_tool_akshare.py holdings 000001

# 5. 查看费用
python fund_tool_akshare.py fee 000001

# 6. 查看流动性
python fund_tool_akshare.py liquidity 000001
```

### 输出重定向

```bash
# 保存到文件
python fund_tool_akshare.py query 000001 > fund_000001.txt

# 同时输出和保存
python fund_tool_akshare.py query 000001 | tee fund_000001.txt
```

### 批量处理

```bash
# 使用脚本批量查询
for code in 000001 000002 110022; do
    echo "查询 $code"
    python fund_tool_akshare.py query $code
done
```

---

## 常见问题

### Q: 如何获取特定基金的完整分析报告？

```bash
# 使用多个命令组合
python fund_tool_akshare.py query 000001
python fund_tool_akshare.py manager 000001
python fund_tool_akshare.py holdings 000001
python fund_tool_akshare.py allocation 000001
python fund_tool_akshare.py fee 000001
python fund_tool_akshare.py liquidity 000001
```

或者使用演示脚本：
```bash
python demo_new_features.py 000001
```

### Q: 基金代码格式要求？

必须是6位数字，如：000001、110022、163406

### Q: 数据更新频率？

- 基金列表：需要手动 `update` 更新
- 基金详情：实时查询
- 持仓数据：按季度更新
- 净值数据：每个交易日更新

---

## 更多帮助

```bash
# 查看完整帮助
python fund_tool_akshare.py --help

# 查看项目README
cat README.md

# 查看新功能文档
cat NEW_FEATURES.md
```

---

**版本**: v2.1
**更新日期**: 2026-01-20
