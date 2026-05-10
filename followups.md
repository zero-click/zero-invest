# TODO（指数估值工具 follow-up）

## P0（核心必须改）

- [ ] 用 `category`（broad / industry / dividend）做数据源路由（不要只靠 code）
- [ ] 估值判断统一改为 **PE 分位数**（不要用绝对PE）
- [ ] 区分“行情数据”和“估值数据”（csindex 不同接口）

## P1（数据质量）

- [ ] 加入 `cninfo`（证监会行业PE）补齐行业估值缺失
- [ ] 分位计算窗口优化（3年 / 5年，而不是只用 publish_date）
- [ ] 优化数据源顺序，减少无效 fallback 请求

## P2（稳定性）

- [ ] 增加请求限速（避免被数据源限流，不做裸并发）
- [ ] 增加缓存（减少重复请求）
- [ ] 日志分级（DEBUG 默认关闭）

## P3（可选优化）

- [ ] 增加 `publisher` 字段（中证 / 上交所 / 深交所）
- [ ] 封装统一接口：`get_index_valuation(code)`
- [ ] 预留：自建PE计算（成分股汇总）
