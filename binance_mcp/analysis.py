#!/usr/bin/env python3
"""
综合分析功能 - 技术分析、市场因素、K线形态
"""

from typing import Dict, Any
from datetime import datetime

from .utils import format_number
from .indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_support_resistance, analyze_trend_pattern, predict_price_probability
)
from .api import get_ticker_24h, get_klines


def generate_analysis_summary(trend: Dict, prediction: Dict, rsi: float, macd: Dict) -> str:
    """生成分析总结"""
    parts = []
    
    # 趋势判断
    parts.append(f"趋势：{trend['trend']}")
    
    # 涨跌概率
    if prediction["up_probability"] >= 60:
        parts.append(f"看涨概率 {prediction['up_probability']}%（{prediction['confidence']}置信度）")
    elif prediction["up_probability"] <= 40:
        parts.append(f"看跌概率 {prediction['down_probability']}%（{prediction['confidence']}置信度）")
    else:
        parts.append("方向不明，建议观望")
    
    # RSI 提示
    if rsi < 30:
        parts.append("⚠️ RSI超卖，可能迎来反弹")
    elif rsi > 70:
        parts.append("⚠️ RSI超买，注意回调风险")
    
    # MACD 提示
    if macd["histogram"] > 0 and macd["macd"] > macd["signal"]:
        parts.append("MACD金叉，多头动能增强")
    elif macd["histogram"] < 0 and macd["macd"] < macd["signal"]:
        parts.append("MACD死叉，空头动能增强")
    
    return " | ".join(parts)


def comprehensive_analysis(symbol: str) -> Dict[str, Any]:
    """
    综合技术分析（基于1小时K线）
    
    ⚠️ 重要说明：
    - 本分析使用1小时K线数据（最近200根）
    - RSI、MACD、布林带等指标均基于1小时周期
    - 趋势判断、支撑阻力位等也是小时级别的分析
    - 适用于短期交易决策（1-24小时）
    - 如需日线或其他周期分析，请单独调用get_klines获取对应周期数据
    """
    # 获取1小时K线数据（最近200根，约8天数据）
    klines_data = get_klines(symbol, "1h", 200)
    
    if "error" in klines_data:
        # 如果是网络错误，直接传递所有错误标记
        if klines_data.get("network_error"):
            return klines_data
        return klines_data
    
    klines = klines_data["klines"]
    
    # 提取价格数据
    closes = [k["close"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    
    # 获取实时行情
    ticker = get_ticker_24h(symbol)
    if "error" in ticker:
        # 如果是网络错误，直接传递所有错误标记
        if ticker.get("network_error"):
            return ticker
        return ticker
    
    # 计算技术指标
    rsi = calculate_rsi(closes)
    macd = calculate_macd(closes)
    bb = calculate_bollinger_bands(closes)
    sr = calculate_support_resistance(highs, lows, closes)
    trend = analyze_trend_pattern(closes)
    prediction = predict_price_probability(closes, rsi, macd, bb)
    
    # 计算均线
    ma7 = sum(closes[-7:]) / 7 if len(closes) >= 7 else closes[-1]
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
    ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else closes[-1]
    
    return {
        "symbol": ticker["symbol"],
        "current_price": ticker["price_formatted"],
        "change_24h": ticker["price_change_display"],
        "volume_24h": ticker["quote_volume_formatted"],
        "trend_emoji": ticker["trend_emoji"],
        "analysis_timeframe": "1小时K线",
        "analysis_note": "⚠️ 本分析基于1小时K线，所有技术指标（RSI/MACD/布林带）均为小时级别，适用于短期交易决策",
        
        "trend_analysis": trend,
        "prediction": prediction,
        
        "technical_indicators": {
            "rsi": {
                "value": rsi,
                "signal": "超卖" if rsi < 30 else ("超买" if rsi > 70 else "中性"),
                "description": f"RSI={rsi}（1小时K线），{'建议关注反弹' if rsi < 30 else ('注意回调风险' if rsi > 70 else '处于正常区间')}"
            },
            "macd": {
                "macd_line": macd["macd"],
                "signal_line": macd["signal"],
                "histogram": macd["histogram"],
                "signal": "多头" if macd["histogram"] > 0 else "空头",
                "description": f"MACD柱状图{'为正，多头动能' if macd['histogram'] > 0 else '为负，空头动能'}（1小时K线）"
            },
            "bollinger_bands": {
                "upper": f"${bb['upper']:,.4f}",
                "middle": f"${bb['middle']:,.4f}",
                "lower": f"${bb['lower']:,.4f}",
                "bandwidth": f"{bb['bandwidth']:.2f}%",
                "position": "上轨附近" if closes[-1] > bb["upper"] * 0.98 else (
                    "下轨附近" if closes[-1] < bb["lower"] * 1.02 else "中轨区域"
                ),
                "note": "基于1小时K线"
            },
            "moving_averages": {
                "ma7": f"${ma7:,.4f}",
                "ma20": f"${ma20:,.4f}",
                "ma50": f"${ma50:,.4f}",
                "price_vs_ma7": f"{(closes[-1] / ma7 - 1) * 100:+.2f}%",
                "price_vs_ma20": f"{(closes[-1] / ma20 - 1) * 100:+.2f}%",
                "note": "均线基于1小时K线计算"
            }
        },
        
        "support_resistance": {
            "resistance_levels": [f"${r:,.4f}" for r in sr["resistance"][:3]],
            "support_levels": [f"${s:,.4f}" for s in sr["support"][:3]],
            "note": "基于1小时K线的高低点计算"
        },
        
        "summary": generate_analysis_summary(trend, prediction, rsi, macd) + "（1小时K线分析）"
    }


def analyze_market_factors(symbol: str) -> Dict[str, Any]:
    """分析市场影响因素"""
    ticker = get_ticker_24h(symbol)
    
    if "error" in ticker:
        # 如果是网络错误，直接传递所有错误标记
        if ticker.get("network_error"):
            return ticker
        return ticker
    
    # 获取BTC和ETH作为市场参考
    btc_ticker = get_ticker_24h("BTC")
    eth_ticker = get_ticker_24h("ETH")
    
    # 计算与大盘相关性
    symbol_change = ticker["price_change_percent"]
    btc_change = btc_ticker.get("price_change_percent", 0) if "error" not in btc_ticker else 0
    eth_change = eth_ticker.get("price_change_percent", 0) if "error" not in eth_ticker else 0
    
    # 判断相对强弱
    vs_btc = symbol_change - btc_change
    vs_eth = symbol_change - eth_change
    
    factors = []
    
    # 大盘影响
    if btc_change > 2:
        factors.append("📈 BTC大涨带动市场情绪")
    elif btc_change < -2:
        factors.append("📉 BTC下跌拖累市场")
    
    # 相对强度
    if vs_btc > 5:
        factors.append(f"💪 相对BTC强势 (+{vs_btc:.1f}%)")
    elif vs_btc < -5:
        factors.append(f"😔 相对BTC弱势 ({vs_btc:.1f}%)")
    
    # 成交量分析
    volume = ticker["quote_volume_24h"]
    if volume > 100000000:  # 1亿美元以上
        factors.append("🔥 交易活跃，资金流入明显")
    elif volume < 1000000:  # 100万美元以下
        factors.append("💤 交易清淡，流动性较差")
    
    return {
        "symbol": ticker["symbol"],
        "price": ticker["price_formatted"],
        "change_24h": ticker["price_change_display"],
        "market_comparison": {
            "btc_change_24h": f"{btc_change:+.2f}%",
            "eth_change_24h": f"{eth_change:+.2f}%",
            "vs_btc": f"{vs_btc:+.2f}%",
            "vs_eth": f"{vs_eth:+.2f}%",
            "relative_strength": "强于大盘" if vs_btc > 0 else "弱于大盘"
        },
        "factors": factors if factors else ["市场平稳，无特殊因素"],
        "suggestions": [
            "关注BTC走势，大盘方向影响整体市场",
            "注意成交量变化，量价配合更健康",
            "留意项目基本面消息和公告"
        ]
    }


def analyze_kline_patterns(symbol: str, interval: str = "4h") -> Dict[str, Any]:
    """
    分析K线形态（默认4小时K线）
    
    识别常见K线形态：十字星、锤子线、上吊线、吞没形态等
    
    参数：
    - symbol: 交易对符号
    - interval: K线周期，默认"4h"（4小时），可选：1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M
    
    ⚠️ 注意：分析结果的时间周期取决于interval参数，默认为4小时级别
    """
    klines_data = get_klines(symbol, interval, 100)
    
    if "error" in klines_data:
        # 如果是网络错误，直接传递所有错误标记
        if klines_data.get("network_error"):
            return klines_data
        return klines_data
    
    klines = klines_data["klines"]
    
    if len(klines) < 10:
        return {"error": "数据不足，无法分析"}
    
    patterns = []
    
    # 分析最近几根K线
    recent = klines[-10:]
    
    for i in range(2, len(recent)):
        k = recent[i]
        prev = recent[i - 1]
        prev2 = recent[i - 2]
        
        body = k["close"] - k["open"]
        upper_shadow = k["high"] - max(k["open"], k["close"])
        lower_shadow = min(k["open"], k["close"]) - k["low"]
        body_size = abs(body)
        
        # 十字星
        if body_size < (k["high"] - k["low"]) * 0.1:
            patterns.append({
                "pattern": "十字星",
                "time": k["open_time"],
                "significance": "趋势可能反转",
                "type": "reversal"
            })
        
        # 锤子线（下影线长，上影线短）
        if lower_shadow > body_size * 2 and upper_shadow < body_size * 0.5:
            patterns.append({
                "pattern": "锤子线",
                "time": k["open_time"],
                "significance": "底部反转信号",
                "type": "bullish"
            })
        
        # 上吊线（上影线长，下影线短）
        if upper_shadow > body_size * 2 and lower_shadow < body_size * 0.5:
            patterns.append({
                "pattern": "上吊线",
                "time": k["open_time"],
                "significance": "顶部反转信号",
                "type": "bearish"
            })
        
        # 吞没形态
        prev_body = prev["close"] - prev["open"]
        if body > 0 and prev_body < 0 and body > abs(prev_body) * 1.5:
            patterns.append({
                "pattern": "看涨吞没",
                "time": k["open_time"],
                "significance": "强烈看涨信号",
                "type": "bullish"
            })
        elif body < 0 and prev_body > 0 and abs(body) > prev_body * 1.5:
            patterns.append({
                "pattern": "看跌吞没",
                "time": k["open_time"],
                "significance": "强烈看跌信号",
                "type": "bearish"
            })
    
    # 提取最近的价格数据
    closes = [k["close"] for k in klines]
    
    # 计算整体形态
    ma20 = sum(closes[-20:]) / 20
    ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
    
    overall_pattern = "上升趋势" if closes[-1] > ma20 > ma50 else (
        "下降趋势" if closes[-1] < ma20 < ma50 else "震荡整理"
    )
    
    return {
        "symbol": klines_data["symbol"],
        "interval": interval,
        "interval_note": f"⚠️ 本分析基于{interval}周期K线，形态信号的时间级别与此周期对应",
        "overall_pattern": overall_pattern,
        "recent_patterns": patterns[-5:] if patterns else [],
        "pattern_count": len(patterns),
        "latest_kline": {
            "time": klines[-1]["open_time"],
            "open": f"${klines[-1]['open']:,.4f}",
            "high": f"${klines[-1]['high']:,.4f}",
            "low": f"${klines[-1]['low']:,.4f}",
            "close": f"${klines[-1]['close']:,.4f}",
            "volume": format_number(klines[-1]["volume"])
        },
        "analysis_summary": f"当前处于{overall_pattern}（基于{interval}K线），" + (
            f"近期发现{len(patterns)}个形态信号" if patterns else "暂无明显形态信号"
        )
    }


