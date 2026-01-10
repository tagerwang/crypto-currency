#!/usr/bin/env python3
"""测试资金费率字段"""

from binance_mcp.api import get_realtime_funding_rate, get_funding_rate

# 测试实时费率
print("=" * 60)
print("测试 get_realtime_funding_rate (实时费率)")
print("=" * 60)
result = get_realtime_funding_rate("ID")
print(f"Symbol: {result.get('symbol')}")
print(f"\n当前实时费率字段:")
print(f"  current_realtime_rate: {result.get('current_realtime_rate')}")
print(f"  current_realtime_rate_display: {result.get('current_realtime_rate_display')}")
print(f"  current_annual_rate: {result.get('current_annual_rate')}")
print(f"  current_signal: {result.get('current_signal')}")
print(f"\n预测费率字段:")
print(f"  predicted_next_rate: {result.get('predicted_next_rate')}")
print(f"  predicted_next_rate_display: {result.get('predicted_next_rate_display')}")
print(f"  predicted_annual_rate: {result.get('predicted_annual_rate')}")
print(f"  predicted_signal: {result.get('predicted_signal')}")
print(f"\n历史结算费率字段（兼容性）:")
print(f"  historical_settled_rate: {result.get('historical_settled_rate')}")
print(f"  historical_settled_rate_display: {result.get('historical_settled_rate_display')}")
print(f"\n说明: {result.get('note')}")

print("\n" + "=" * 60)
print("测试 get_funding_rate (历史结算费率)")
print("=" * 60)
result2 = get_funding_rate("ID")
print(f"Symbol: {result2.get('symbol')}")
print(f"  historical_settled_rate: {result2.get('historical_settled_rate')}")
print(f"  historical_settled_rate_display: {result2.get('historical_settled_rate_display')}")
print(f"  annual_rate: {result2.get('annual_rate')}")
print(f"\n说明: {result2.get('note')}")
