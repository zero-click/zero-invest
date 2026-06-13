# zero-invest

中国公募基金、指数与个股信息查询 CLI 工具，基于 `akshare` 数据源。提供基金研究、指数估值查询、个股场景分析等功能。

## 主要功能

### 基金分析

- 基金搜索：按代码、名称、拼音搜索公募基金
- 基金详情：基本信息、规模、基金经理、成立日期、类型
- 业绩表现：近 1 周/1 月/3 月/6 月/1 年/3 年/今年/成立以来收益
- 风险指标：标准差、夏普比率、最大回撤等
- 持仓分析：十大重仓股、持仓集中度、季度持仓变化
- 费用信息：管理费、托管费、申购费、赎回费

### 指数管理

- 多源指数数据库：聚合中证指数、东方财富、Sina、akshare 指数信息表
- 指数查询：基本信息、当前点位、涨跌幅、历史收益
- 指数估值：PE-TTM、PB、股息率、历史分位、估值温度
- 指数风险：波动率、最大回撤、回撤修复周期、夏普比率
- 估值热力图：宽基和行业估值表，支持按 PE/PB/股息率排序

### 个股分析

- 股票搜索：按代码或名称搜索 A 股
- 实时行情：当前价、涨跌幅、市值、PE、PB
- 历史K线：历史价格走势、区间统计、回撤分析
- 估值概览：PE/PB/PS/EV 等估值指标
- 场景分析：三种估值场景（稳定成长型、高速成长型、强周期型）
- 准入检查：基于用户指定类型的准入流水表

## 安装

```bash
# 克隆仓库
git clone https://github.com/zero-click/zero-invest.git
cd zero-invest

# 安装依赖
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## CLI 使用

### 基金命令

```bash
# 搜索基金
python cli.py bond search "华夏"

# 查询基金
python cli.py bond query 000001
python cli.py bond query 000001 --detail

# 专项查询
python cli.py bond performance 000001
python cli.py bond risk 000001
python cli.py bond top-holdings 000001
python cli.py bond fee 000001
```

### 指数命令

```bash
# 更新指数数据库
python cli.py index update

# 搜索指数
python cli.py index search "红利"

# 查询指数
python cli.py index query 000300        # 基本信息
python cli.py index query 000300 -d     # 完整信息（含估值和风险）

# 估值热力图
python cli.py index heatmap --sort-by pb --limit 20
```

### 个股命令

```bash
# 搜索股票
python cli.py stock search "平安"

# 查询股票
python cli.py stock query 600519
python cli.py stock valuation 600519    # 估值概览
python cli.py stock hist 600519         # 历史K线

# 场景分析
python cli.py stock scenario-a 600519  # 稳定成长型（Forward PE / PEG）
python cli.py stock scenario-b 600519  # 高速成长型（PS + FCF反算）
python cli.py stock scenario-c 600519  # 强周期型（DOI / EV/EBITDA / PB）

# 准入检查
python cli.py stock checklist 600519 --type a  # a=稳定成长型, b=高速成长型, c=强周期型
```

### 帮助

```bash
python cli.py --help
python cli.py bond --help
python cli.py stock --help
```

## 数据来源

- 基金：东方财富、天天基金等 akshare 数据源
- 指数：中证指数、东方财富、Sina、akshare
- 个股：东方财富实时行情、历史K线、财务指标

数据依赖第三方公开接口，可能存在延迟、缺失或临时不可用。

## 注意事项

- 本项目仅用于学习和研究，不构成投资建议
- 估值判断函数（如 PEG 估值）仅供参考，请结合实际情况自行判断
- 数据以官方披露为准，CLI 数据可能存在滞后或错误

## License

MIT License
