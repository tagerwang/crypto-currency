#!/usr/bin/env python3
"""
技术指标计算 - SMA、EMA、RSI、MACD、布林带等
"""

import math
from typing import Dict, List, Any


def calculate_sma(prices: List[float], period: int) -> List[float]:
    """计算简单移动平均线"""
    if len(prices) < period:
        return []
    sma = []
    for i in range(len(prices) - period + 1):
        sma.append(sum(prices[i:i + period]) / period)
    return sma


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """计算指数移动平均线"""
    if len(prices) < period:
        return []
    
    multiplier = 2 / (period + 1)
    ema = [sum(prices[:period]) / period]  # 第一个EMA用SMA
    
    for price in prices[period:]:
        ema.append((price - ema[-1]) * multiplier + ema[-1])
    
    return ema


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """计算相对强弱指标RSI"""
    if len(prices) < period + 1:
        return 50.0
    
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        if change >= 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    
    if len(gains) < period:
        return 50.0
    
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return round(rsi, 2)


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
    """计算MACD指标"""
    if len(prices) < slow + signal:
        return {"macd": 0, "signal": 0, "histogram": 0}
    
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    # 对齐长度
    diff = len(ema_fast) - len(ema_slow)
    if diff > 0:
        ema_fast = ema_fast[diff:]
    
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    
    if len(macd_line) < signal:
        return {"macd": 0, "signal": 0, "histogram": 0}
    
    signal_line = calculate_ema(macd_line, signal)
    
    current_macd = macd_line[-1] if macd_line else 0
    current_signal = signal_line[-1] if signal_line else 0
    histogram = current_macd - current_signal
    
    return {
        "macd": round(current_macd, 6),
        "signal": round(current_signal, 6),
        "histogram": round(histogram, 6)
    }


def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Dict[str, float]:
    """计算布林带"""
    if len(prices) < period:
        return {"upper": 0, "middle": 0, "lower": 0, "bandwidth": 0}
    
    recent_prices = prices[-period:]
    middle = sum(recent_prices) / period
    
    variance = sum((p - middle) ** 2 for p in recent_prices) / period
    std = math.sqrt(variance)
    
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    bandwidth = ((upper - lower) / middle) * 100 if middle > 0 else 0
    
    return {
        "upper": round(upper, 6),
        "middle": round(middle, 6),
        "lower": round(lower, 6),
        "bandwidth": round(bandwidth, 2)
    }


def calculate_support_resistance(highs: List[float], lows: List[float], closes: List[float]) -> Dict[str, List[float]]:
    """计算支撑位和阻力位"""
    if len(closes) < 20:
        return {"support": [], "resistance": []}
    
    # 使用最近的高低点
    recent_highs = highs[-50:] if len(highs) >= 50 else highs
    recent_lows = lows[-50:] if len(lows) >= 50 else lows
    
    # 找出局部高点作为阻力位
    resistances = []
    for i in range(2, len(recent_highs) - 2):
        if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i-2] and \
           recent_highs[i] > recent_highs[i+1] and recent_highs[i] > recent_highs[i+2]:
            resistances.append(recent_highs[i])
    
    # 找出局部低点作为支撑位
    supports = []
    for i in range(2, len(recent_lows) - 2):
        if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i-2] and \
           recent_lows[i] < recent_lows[i+1] and recent_lows[i] < recent_lows[i+2]:
            supports.append(recent_lows[i])
    
    # 去重并排序
    resistances = sorted(list(set([round(r, 4) for r in resistances])), reverse=True)[:5]
    supports = sorted(list(set([round(s, 4) for s in supports])), reverse=True)[:5]
    
    return {
        "resistance": resistances,
        "support": supports
    }


def analyze_trend_pattern(closes: List[float]) -> Dict[str, Any]:
    """分析趋势形态"""
    if len(closes) < 20:
        return {"trend": "未知", "strength": 0, "description": "数据不足"}
    
    # 计算多个时间段的涨跌
    changes = {
        "1d": (closes[-1] - closes[-2]) / closes[-2] * 100 if len(closes) >= 2 else 0,
        "7d": (closes[-1] - closes[-7]) / closes[-7] * 100 if len(closes) >= 7 else 0,
        "14d": (closes[-1] - closes[-14]) / closes[-14] * 100 if len(closes) >= 14 else 0,
    }
    
    # 计算均线
    ma7 = sum(closes[-7:]) / 7 if len(closes) >= 7 else closes[-1]
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else closes[-1]
    ma50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else ma20
    
    current_price = closes[-1]
    
    # 判断趋势
    trend_score = 0
    
    # 价格与均线关系
    if current_price > ma7:
        trend_score += 1
    else:
        trend_score -= 1
    
    if current_price > ma20:
        trend_score += 1
    else:
        trend_score -= 1
    
    if ma7 > ma20:
        trend_score += 1
    else:
        trend_score -= 1
    
    # 短期涨跌
    if changes["7d"] > 5:
        trend_score += 2
    elif changes["7d"] > 0:
        trend_score += 1
    elif changes["7d"] < -5:
        trend_score -= 2
    else:
        trend_score -= 1
    
    # 判断趋势方向
    if trend_score >= 3:
        trend = "📈 强势上涨"
        description = "多头趋势明显，建议关注回调买入机会"
    elif trend_score >= 1:
        trend = "↗️ 温和上涨"
        description = "偏多震荡，可能继续上行"
    elif trend_score <= -3:
        trend = "📉 强势下跌"
        description = "空头趋势明显，建议谨慎观望"
    elif trend_score <= -1:
        trend = "↘️ 温和下跌"
        description = "偏空震荡，可能继续下行"
    else:
        trend = "➡️ 横盘震荡"
        description = "方向不明，等待突破"
    
    return {
        "trend": trend,
        "trend_score": trend_score,
        "strength": abs(trend_score) / 5 * 100,
        "description": description,
        "price_vs_ma7": f"{(current_price / ma7 - 1) * 100:+.2f}%",
        "price_vs_ma20": f"{(current_price / ma20 - 1) * 100:+.2f}%",
        "changes": {k: f"{v:+.2f}%" for k, v in changes.items()}
    }


def predict_price_probability(closes: List[float], rsi: float, macd: Dict, bb: Dict) -> Dict[str, Any]:
    """预测涨跌概率"""
    if len(closes) < 14:
        return {"up_probability": 50, "down_probability": 50, "confidence": "低"}
    
    score = 50  # 基础分数
    
    # RSI 分析
    if rsi < 30:
        score += 15  # 超卖，可能反弹
    elif rsi > 70:
        score -= 15  # 超买，可能回调
    elif rsi > 50:
        score += 5
    else:
        score -= 5
    
    # MACD 分析
    if macd["histogram"] > 0:
        score += 10
        if macd["macd"] > macd["signal"]:
            score += 5
    else:
        score -= 10
        if macd["macd"] < macd["signal"]:
            score -= 5
    
    # 布林带分析
    current_price = closes[-1]
    if current_price < bb["lower"]:
        score += 10  # 触及下轨，可能反弹
    elif current_price > bb["upper"]:
        score -= 10  # 触及上轨，可能回调
    
    # 短期动量
    momentum = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
    score += min(max(momentum * 2, -10), 10)
    
    # 限制在合理范围
    up_probability = min(max(score, 15), 85)
    
    # 判断置信度
    if 40 <= up_probability <= 60:
        confidence = "低"
    elif 30 <= up_probability <= 70:
        confidence = "中"
    else:
        confidence = "高"
    
    return {
        "up_probability": round(up_probability, 1),
        "down_probability": round(100 - up_probability, 1),
        "confidence": confidence,
        "factors": {
            "rsi_signal": "超卖反弹" if rsi < 30 else ("超买回调" if rsi > 70 else "中性"),
            "macd_signal": "多头" if macd["histogram"] > 0 else "空头",
            "bb_signal": "触底" if current_price < bb["lower"] else ("触顶" if current_price > bb["upper"] else "中性"),
            "momentum": f"{momentum:+.2f}%"
        }
    }


