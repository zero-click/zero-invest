
import os, re, json, requests

for k in ['http_proxy','https_proxy','HTTP_PROXY','HTTPS_PROXY']:
    os.environ.pop(k, None)

# === 1. 腾讯估值计算 ===
print("=== 腾讯估值分析 ===")
# 已知: 股价465.8 HKD, EPS 18.91 HKD
price = 465.8
eps = 18.91
pe_ttm = price / eps
print(f"  股价: {price} HKD")
print(f"  EPS(TTM): {eps} HKD")
print(f"  PE(TTM): {pe_ttm:.1f}x")
print(f"  PB: 3.33x")

# 2024/2025年Non-IFRS净利润参考
# 2024 Non-IFRS净利 ~2200亿人民币
# 2025Q1 继续增长
# 总股本约94.5亿股
shares = 94.5  # 亿股
market_cap_rmb = price * shares * 0.92  # 港币转人民币约0.92
print(f"\n  总市值(估): ~{market_cap_rmb:.0f}亿人民币")

# Non-IFRS PE (更准确)
# 2024 Non-IFRS净利润 ~2200亿RMB -> EPS ~23.3 RMB ~25.4 HKD
non_ifrs_eps_hkd = 25.4  # 估算
non_ifrs_pe = price / non_ifrs_eps_hkd
print(f"  Non-IFRS EPS(估): ~{non_ifrs_eps_hkd} HKD")
print(f"  Non-IFRS PE: ~{non_ifrs_pe:.1f}x")

# 历史PE参考
print(f"\n  腾讯PE历史参考:")
print(f"    2021高点(750HKD): ~35x Non-IFRS PE")
print(f"    2022低点(200HKD): ~10x Non-IFRS PE")
print(f"    近5年均值: ~20x Non-IFRS PE")
print(f"    当前: ~{non_ifrs_pe:.1f}x -> {'偏低' if non_ifrs_pe < 18 else ('合理' if non_ifrs_pe < 22 else '偏高')}")

# === 2. 腾讯业务分析 ===
print("\n=== 腾讯业务板块 ===")
print("  1. 游戏(约30%): 王者荣耀/和平精英/PUBG全球, 海外游戏增速>国内")
print("  2. 社交(约20%): 微信13亿MAU, 视频号广告快速增长")
print("  3. 金融科技(约25%): 支付+理财, 稳健增长")
print("  4. 云与企业服务(约15%): 企业微信+腾讯云+AI")
print("  5. 投资(约10%): 持有大量上市公司股权")

# === 3. 近期催化剂/风险 ===
print("\n=== 近期催化剂 ===")
print("  🟢 AI大模型: 混元大模型商业化, 元宝APP")
print("  🟢 游戏出海: 海外收入占比持续提升")
print("  🟢 视频号: 广告+电商货币化率提升")
print("  🟢 回购: 2024/2025大规模回购(1000亿港元级)")

print("\n=== 近期风险 ===")
print("  🔴 关税/中美博弈: 科技股首当其冲")
print("  🔴 60日跌近20%: 技术面偏弱, 短期卖压")
print("  🔴 恒指26100: 港股整体波动大")
print("  🔴 游戏监管: 政策不确定性")

# === 4. 恒指估值参考 ===
print("\n=== 港股市场环境 ===")
print("  恒生指数: 26104")
print("  恒指PE: ~10-11x (历史偏低)")
print("  AH溢价指数: ~135 (A股比H股贵35%)")
print("  港股整体估值: 历史低位区间, 长期配置价值较高")

# === 5. "梭哈"风险评估 ===
print("\n=== '梭哈'风险评估 ===")
print("  ❌ 单票集中度: 100%仓位一只股票 = 高风险")
print("  ❌ 最大回撤: 腾讯历史最大回撤超70%(2021-2022)")
print("  ❌ 波动性: 港股单日波动5%+常见")
print("  ❌ 流动性风险: 紧急用钱时可能被迫低位卖出")

print("\n=== 如果465 HKD买入, 不同情景 ===")
print("  乐观(涨到600): +28.8%, AI+游戏双驱动")
print("  中性(涨到530): +13.7%, 回到均值PE")
print("  悲观(跌到380): -18.5%, 中美恶化/盈利下修")
print("  极端(跌到300): -35.6%, 类似2022情况")
