#!/usr/bin/env python3
"""
Binance MCP Server - 币安加密货币数据服务器
支持实时价格、历史数据、K线分析、技术指标、合约分析、Alpha代币分析等
"""

import json
import sys
import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import math

# 币安API基础URL（主站 + 备用站点）
# 如果主站访问受限，可以尝试使用备用站点
SPOT_BASE_URLS = [
    "https://api.binance.com/api/v3",      # 主站
    "https://api1.binance.com/api/v3",     # 备用1
    "https://api2.binance.com/api/v3",     # 备用2
    "https://api3.binance.com/api/v3",     # 备用3
    "https://api4.binance.com/api/v3",     # 备用4
]

FUTURES_BASE_URLS = [
    "https://fapi.binance.com/fapi/v1",
    "https://fapi1.binance.com/fapi/v1",
]

SPOT_BASE_URL = SPOT_BASE_URLS[0]
FUTURES_BASE_URL = FUTURES_BASE_URLS[0]
COIN_FUTURES_BASE_URL = "https://dapi.binance.com/dapi/v1"

# 请求头，模拟浏览器访问
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# K线时间周期映射
KLINE_INTERVALS = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
    "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
}

# ==================== 辅助函数 ====================

def format_number(num: float, decimals: int = 2) -> str:
    """格式化数字显示"""
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.{decimals}f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.{decimals}f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.{decimals}f}K"
    return f"{num:.{decimals}f}"

def timestamp_to_datetime(ts: int) -> str:
    """时间戳转日期时间字符串"""
    return datetime.fromtimestamp(ts / 1000).strftime("%Y-%m-%d %H:%M:%S")

def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

# ==================== 技术指标计算 ====================

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

# ==================== 币安API调用函数 ====================

def make_spot_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """发起现货API请求，自动尝试备用域名"""
    last_error = None
    
    for base_url in SPOT_BASE_URLS:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            
            # 检查地区限制
            if response.status_code == 451:
                continue  # 尝试下一个域名
            
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.HTTPError as e:
            if response.status_code == 451:
                last_error = "API访问受地区限制，请使用VPN或代理"
                continue
            last_error = f"HTTP错误: {response.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            continue
    
    return {"success": False, "error": last_error or "所有API端点均不可用，请检查网络或使用代理"}

def make_futures_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """发起合约API请求，自动尝试备用域名"""
    last_error = None
    
    for base_url in FUTURES_BASE_URLS:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)
            
            if response.status_code == 451:
                continue
            
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.HTTPError as e:
            if response.status_code == 451:
                last_error = "API访问受地区限制，请使用VPN或代理"
                continue
            last_error = f"HTTP错误: {response.status_code}"
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            continue
    
    return {"success": False, "error": last_error or "所有API端点均不可用"}

def get_spot_price(symbol: str) -> Dict[str, Any]:
    """获取现货价格"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_spot_request("/ticker/price", {"symbol": symbol})
    
    if not result["success"]:
        return {"error": result["error"], "symbol": symbol}
    
    data = result["data"]
    return {
        "symbol": data["symbol"],
        "price": safe_float(data["price"]),
        "price_formatted": f"${safe_float(data['price']):,.4f}"
    }

def get_ticker_24h(symbol: str) -> Dict[str, Any]:
    """获取24小时行情数据"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_spot_request("/ticker/24hr", {"symbol": symbol})
    
    if not result["success"]:
        return {"error": result["error"], "symbol": symbol}
    
    data = result["data"]
    price_change_pct = safe_float(data.get("priceChangePercent", 0))
    
    return {
        "symbol": data["symbol"],
        "price": safe_float(data["lastPrice"]),
        "price_formatted": f"${safe_float(data['lastPrice']):,.4f}",
        "price_change": safe_float(data["priceChange"]),
        "price_change_percent": price_change_pct,
        "price_change_display": f"{price_change_pct:+.2f}%",
        "high_24h": safe_float(data["highPrice"]),
        "low_24h": safe_float(data["lowPrice"]),
        "volume_24h": safe_float(data["volume"]),
        "volume_24h_formatted": format_number(safe_float(data["volume"])),
        "quote_volume_24h": safe_float(data["quoteVolume"]),
        "quote_volume_formatted": f"${format_number(safe_float(data['quoteVolume']))}",
        "open_price": safe_float(data["openPrice"]),
        "weighted_avg_price": safe_float(data["weightedAvgPrice"]),
        "trade_count": int(data.get("count", 0)),
        "trend_emoji": "🟢" if price_change_pct > 0 else ("🔴" if price_change_pct < 0 else "⚪")
    }

def get_multiple_tickers(symbols: List[str]) -> Dict[str, Any]:
    """获取多个交易对的24小时行情"""
    results = {}
    for symbol in symbols:
        ticker = get_ticker_24h(symbol)
        results[symbol.upper()] = ticker
    return results

def get_klines(symbol: str, interval: str = "1h", limit: int = 100) -> Dict[str, Any]:
    """获取K线数据"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    if interval not in KLINE_INTERVALS:
        return {"error": f"不支持的时间周期: {interval}，支持的周期: {list(KLINE_INTERVALS.keys())}"}
    
    result = make_spot_request("/klines", {
        "symbol": symbol,
        "interval": interval,
        "limit": min(limit, 1000)
    })
    
    if not result["success"]:
        return {"error": result["error"], "symbol": symbol}
    
    data = result["data"]
    klines = []
    for k in data:
        klines.append({
            "open_time": timestamp_to_datetime(k[0]),
            "open": safe_float(k[1]),
            "high": safe_float(k[2]),
            "low": safe_float(k[3]),
            "close": safe_float(k[4]),
            "volume": safe_float(k[5]),
            "close_time": timestamp_to_datetime(k[6]),
            "quote_volume": safe_float(k[7]),
            "trades": int(k[8])
        })
    
    return {
        "symbol": symbol,
        "interval": interval,
        "count": len(klines),
        "klines": klines
    }

def get_futures_price(symbol: str) -> Dict[str, Any]:
    """获取合约价格"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_futures_request("/ticker/price", {"symbol": symbol})
    
    if not result["success"]:
        return {"error": result["error"], "symbol": symbol}
    
    data = result["data"]
    return {
        "symbol": data["symbol"],
        "price": safe_float(data["price"]),
        "price_formatted": f"${safe_float(data['price']):,.4f}",
        "time": timestamp_to_datetime(data["time"])
    }

def get_funding_rate(symbol: str) -> Dict[str, Any]:
    """获取资金费率"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_futures_request("/fundingRate", {"symbol": symbol, "limit": 10})
    
    if not result["success"]:
        return {"error": result["error"], "symbol": symbol}
    
    data = result["data"]
    
    if not data:
        return {"error": f"无资金费率数据: {symbol}"}
    
    latest = data[0]
    funding_rate = safe_float(latest["fundingRate"]) * 100
    
    # 计算年化费率 (每8小时一次，一天3次，一年365天)
    annual_rate = funding_rate * 3 * 365
    
    return {
        "symbol": symbol,
        "funding_rate": funding_rate,
        "funding_rate_display": f"{funding_rate:+.4f}%",
        "annual_rate": f"{annual_rate:+.2f}%",
        "funding_time": timestamp_to_datetime(latest["fundingTime"]),
        "signal": "多头付费" if funding_rate > 0 else ("空头付费" if funding_rate < 0 else "中性"),
        "history": [{"rate": f"{safe_float(d['fundingRate']) * 100:+.4f}%", 
                    "time": timestamp_to_datetime(d['fundingTime'])} for d in data[:5]]
    }

def analyze_spot_vs_futures(symbol: str) -> Dict[str, Any]:
    """分析现货与合约价差"""
    spot = get_spot_price(symbol)
    futures = get_futures_price(symbol)
    funding = get_funding_rate(symbol)
    
    if "error" in spot or "error" in futures:
        return {"error": "获取价格数据失败"}
    
    spot_price = spot["price"]
    futures_price = futures["price"]
    premium = ((futures_price - spot_price) / spot_price) * 100
    
    return {
        "symbol": symbol.upper(),
        "spot_price": f"${spot_price:,.4f}",
        "futures_price": f"${futures_price:,.4f}",
        "premium": f"{premium:+.4f}%",
        "premium_type": "期货溢价" if premium > 0 else ("期货折价" if premium < 0 else "平价"),
        "funding_rate": funding.get("funding_rate_display", "N/A"),
        "annual_funding": funding.get("annual_rate", "N/A"),
        "analysis": {
            "market_sentiment": "偏多" if premium > 0.1 else ("偏空" if premium < -0.1 else "中性"),
            "arbitrage_opportunity": abs(premium) > 0.5,
            "suggestion": "期现套利可行" if abs(premium) > 0.5 else "价差正常"
        }
    }

# ==================== 综合分析函数 ====================

def comprehensive_analysis(symbol: str) -> Dict[str, Any]:
    """综合技术分析"""
    # 获取K线数据
    klines_data = get_klines(symbol, "1h", 200)
    
    if "error" in klines_data:
        return klines_data
    
    klines = klines_data["klines"]
    
    # 提取价格数据
    closes = [k["close"] for k in klines]
    highs = [k["high"] for k in klines]
    lows = [k["low"] for k in klines]
    
    # 获取实时行情
    ticker = get_ticker_24h(symbol)
    if "error" in ticker:
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
        
        "trend_analysis": trend,
        "prediction": prediction,
        
        "technical_indicators": {
            "rsi": {
                "value": rsi,
                "signal": "超卖" if rsi < 30 else ("超买" if rsi > 70 else "中性"),
                "description": f"RSI={rsi}，{'建议关注反弹' if rsi < 30 else ('注意回调风险' if rsi > 70 else '处于正常区间')}"
            },
            "macd": {
                "macd_line": macd["macd"],
                "signal_line": macd["signal"],
                "histogram": macd["histogram"],
                "signal": "多头" if macd["histogram"] > 0 else "空头",
                "description": f"MACD柱状图{'为正，多头动能' if macd['histogram'] > 0 else '为负，空头动能'}"
            },
            "bollinger_bands": {
                "upper": f"${bb['upper']:,.4f}",
                "middle": f"${bb['middle']:,.4f}",
                "lower": f"${bb['lower']:,.4f}",
                "bandwidth": f"{bb['bandwidth']:.2f}%",
                "position": "上轨附近" if closes[-1] > bb["upper"] * 0.98 else (
                    "下轨附近" if closes[-1] < bb["lower"] * 1.02 else "中轨区域"
                )
            },
            "moving_averages": {
                "ma7": f"${ma7:,.4f}",
                "ma20": f"${ma20:,.4f}",
                "ma50": f"${ma50:,.4f}",
                "price_vs_ma7": f"{(closes[-1] / ma7 - 1) * 100:+.2f}%",
                "price_vs_ma20": f"{(closes[-1] / ma20 - 1) * 100:+.2f}%"
            }
        },
        
        "support_resistance": {
            "resistance_levels": [f"${r:,.4f}" for r in sr["resistance"][:3]],
            "support_levels": [f"${s:,.4f}" for s in sr["support"][:3]]
        },
        
        "summary": generate_analysis_summary(trend, prediction, rsi, macd)
    }

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

def search_symbols(keyword: str) -> Dict[str, Any]:
    """搜索交易对"""
    result = make_spot_request("/exchangeInfo", {})
    
    if not result["success"]:
        return {"error": result["error"]}
    
    data = result["data"]
    keyword = keyword.upper()
    matches = []
    
    for s in data["symbols"]:
        if s["status"] == "TRADING" and s["quoteAsset"] == "USDT":
            if keyword in s["baseAsset"] or keyword in s["symbol"]:
                matches.append({
                    "symbol": s["symbol"],
                    "base_asset": s["baseAsset"],
                    "quote_asset": s["quoteAsset"]
                })
    
    return {
        "keyword": keyword,
        "count": len(matches),
        "symbols": matches[:20]
    }

def get_top_gainers_losers(limit: int = 10) -> Dict[str, Any]:
    """获取涨跌幅榜"""
    result = make_spot_request("/ticker/24hr", {})
    
    if not result["success"]:
        return {"error": result["error"]}
    
    data = result["data"]
    
    # 过滤USDT交易对
    usdt_pairs = [d for d in data if d["symbol"].endswith("USDT") and safe_float(d["quoteVolume"]) > 1000000]
    
    # 按涨跌幅排序
    sorted_by_change = sorted(usdt_pairs, key=lambda x: safe_float(x["priceChangePercent"]), reverse=True)
    
    gainers = []
    for d in sorted_by_change[:limit]:
        gainers.append({
            "symbol": d["symbol"],
            "price": f"${safe_float(d['lastPrice']):,.4f}",
            "change": f"{safe_float(d['priceChangePercent']):+.2f}%",
            "volume": f"${format_number(safe_float(d['quoteVolume']))}"
        })
    
    losers = []
    for d in sorted_by_change[-limit:]:
        losers.append({
            "symbol": d["symbol"],
            "price": f"${safe_float(d['lastPrice']):,.4f}",
            "change": f"{safe_float(d['priceChangePercent']):+.2f}%",
            "volume": f"${format_number(safe_float(d['quoteVolume']))}"
        })
    
    losers.reverse()
    
    return {
        "top_gainers": gainers,
        "top_losers": losers,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# ==================== Alpha代币分析 ====================

import os
import re

# CoinGecko API（备用数据源，无地区限制）
COINGECKO_API = "https://api.coingecko.com/api/v3"

# Alpha123 API（第三方实时数据源）- 提供币安Alpha空投实时数据
ALPHA123_API = "https://alpha123.uk/api"
ALPHA123_HEADERS = {
    "accept": "*/*",
    "accept-language": "zh-CN,zh;q=0.9",
    "referer": "https://alpha123.uk/",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36"
}

def fetch_realtime_alpha_airdrops() -> Dict[str, Any]:
    """
    从Alpha123获取实时空投数据
    这是一个第三方聚合API，提供币安Alpha空投的实时信息
    """
    url = f"{ALPHA123_API}/data?t={int(datetime.now().timestamp() * 1000)}&fresh=1"
    
    try:
        response = requests.get(url, headers=ALPHA123_HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        airdrops = data.get("airdrops", [])
        
        # 处理Phase 2的时间偏移（加18小时）
        for item in airdrops:
            if item.get("phase") == 2 and item.get("date") and item.get("time"):
                try:
                    date_time_str = f"{item['date']} {item['time']}"
                    parsed = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M")
                    parsed = parsed + timedelta(hours=18)
                    item["date"] = parsed.strftime("%Y-%m-%d")
                    item["time"] = parsed.strftime("%H:%M")
                except:
                    pass
        
        return {
            "success": True,
            "airdrops": airdrops,
            "source": "alpha123.uk",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "airdrops": []
        }

def fetch_alpha_token_price_from_alpha123(token: str) -> Dict[str, Any]:
    """从Alpha123获取代币价格"""
    url = f"{ALPHA123_API}/price/{token}?t={int(datetime.now().timestamp() * 1000)}&fresh=1"
    
    try:
        response = requests.get(url, headers=ALPHA123_HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            return {
                "success": True,
                "price": data.get("price", 0),
                "source": "alpha123.uk"
            }
        return {"success": False, "price": 0}
    except Exception as e:
        return {"success": False, "error": str(e), "price": 0}

def get_realtime_alpha_airdrops() -> Dict[str, Any]:
    """
    获取实时Alpha空投列表（包含价格和价值计算）
    """
    # 获取空投数据
    result = fetch_realtime_alpha_airdrops()
    
    if not result.get("success"):
        return {
            "error": result.get("error", "获取空投数据失败"),
            "fallback": "请尝试手动访问 https://alpha123.uk 查看"
        }
    
    airdrops = result.get("airdrops", [])
    
    # 分类整理
    upcoming = []  # 即将开始
    ongoing = []   # 进行中
    ended = []     # 已结束
    
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    
    for item in airdrops:
        token = item.get("token", "")
        name = item.get("name", "")
        date = item.get("date", "")
        time = item.get("time", "")
        points = item.get("points", "")
        amount = item.get("amount", "")
        phase = item.get("phase", 1)
        status = item.get("status", "")
        airdrop_type = item.get("type", "")
        completed = item.get("completed", False)
        
        # 获取价格
        price_data = fetch_alpha_token_price_from_alpha123(token)
        price = price_data.get("price", 0) if price_data.get("success") else 0
        
        # 计算价值
        try:
            amount_num = int(amount) if amount else 0
        except:
            amount_num = 0
        
        total_value = price * amount_num if price and amount_num else 0
        
        airdrop_info = {
            "token": token,
            "name": name,
            "date": date,
            "time": time,
            "datetime": f"{date} {time}",
            "points_required": points,
            "amount": amount,
            "phase": phase,
            "type": airdrop_type,
            "current_price": f"${price:.6f}" if price else "获取中...",
            "total_value": f"${total_value:.2f}" if total_value else "待计算",
            "status": "已完成" if completed else status
        }
        
        # 分类
        if completed:
            ended.append(airdrop_info)
        elif date < today:
            ended.append(airdrop_info)
        elif date == today:
            # 检查时间
            try:
                airdrop_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                if airdrop_time <= now:
                    ongoing.append(airdrop_info)
                else:
                    upcoming.append(airdrop_info)
            except:
                ongoing.append(airdrop_info)
        else:
            upcoming.append(airdrop_info)
    
    # 按时间排序
    upcoming.sort(key=lambda x: x["datetime"])
    ongoing.sort(key=lambda x: x["datetime"])
    ended.sort(key=lambda x: x["datetime"], reverse=True)
    
    return {
        "query_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "data_source": "alpha123.uk (实时)",
        
        "summary": {
            "upcoming_count": len(upcoming),
            "ongoing_count": len(ongoing),
            "ended_count": len(ended)
        },
        
        "upcoming_airdrops": upcoming[:10],  # 即将开始的前10个
        "ongoing_airdrops": ongoing[:10],    # 进行中的前10个
        "recently_ended": ended[:10],         # 最近结束的前10个
        
        "note": "数据来自第三方聚合，仅供参考，以币安官方为准"
    }

# 配置文件路径（与脚本同目录）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALPHA_CONFIG_FILE = os.path.join(SCRIPT_DIR, "alpha_competitions.json")

# Alpha代币ID映射（用于CoinGecko查询）
ALPHA_TOKEN_COINGECKO_IDS = {
    "TIMI": "metaarena",
    "H": None,  # 新币可能还没收录
    "BLUAI": None,
    "OOOO": None,
    "MAT": None,
    "ARB": "arbitrum",
}

# 默认Alpha竞赛配置（当外部配置文件不可用时使用）
DEFAULT_ALPHA_COMPETITIONS = {
    "H": {
        "name": "H Alpha 交易竞赛",
        "token_name": "H",
        "start_time": "2026-01-09 21:00:00",
        "end_time": "2026-01-16 21:00:00",
        "timezone": "UTC+8",
        "total_reward": None,
        "winner_count": None,
        "per_user_reward": None,
        "status": "进行中",
        "note": "第一期H代币交易竞赛"
    },
    "TIMI": {
        "name": "2nd TIMI Alpha 交易竞赛",
        "token_name": "MetaArena (TIMI)",
        "start_time": "2026-01-05 21:00:00",
        "end_time": "2026-01-12 21:00:00",
        "timezone": "UTC+8",
        "total_reward": 7178800,
        "winner_count": 5240,
        "per_user_reward": 1370,
        "status": "进行中",
        "note": "第二阶段TIMI交易竞赛"
    },
}

# 默认Alpha空投配置
DEFAULT_ALPHA_AIRDROPS = {
    "BLUAI": {"name": "Bluwhale", "launch_date": "2025-10-21", "min_points": 220, "airdrop_amount": 1600, "status": "已结束"},
    "OOOO": {"name": "oooo Protocol", "launch_date": "2025-12-30", "min_points": 200, "airdrop_amount": 1000, "status": "已结束"},
}

def load_alpha_config_from_file() -> Dict[str, Any]:
    """从外部JSON文件加载Alpha竞赛配置"""
    try:
        if os.path.exists(ALPHA_CONFIG_FILE):
            with open(ALPHA_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        pass
    return None

def save_alpha_config_to_file(config: Dict[str, Any]) -> bool:
    """保存Alpha竞赛配置到外部JSON文件"""
    try:
        with open(ALPHA_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        return False

def get_alpha_competitions_config() -> Dict[str, Any]:
    """获取Alpha竞赛配置（优先从文件加载）"""
    file_config = load_alpha_config_from_file()
    
    if file_config and "active_competitions" in file_config:
        # 转换文件格式为内部格式
        competitions = {}
        for comp in file_config.get("active_competitions", []):
            symbol = comp.get("symbol", "").upper()
            if symbol:
                competitions[symbol] = {
                    "name": comp.get("name", f"{symbol} Alpha 竞赛"),
                    "token_name": comp.get("token_name", symbol),
                    "start_time": comp.get("start_time", ""),
                    "end_time": comp.get("end_time", ""),
                    "timezone": comp.get("timezone", "UTC+8"),
                    "total_reward": comp.get("total_reward"),
                    "winner_count": comp.get("winner_count"),
                    "per_user_reward": comp.get("per_user_reward"),
                    "status": comp.get("status", "进行中"),
                    "note": comp.get("note", "")
                }
        
        # 添加已结束的竞赛
        for comp in file_config.get("ended_competitions", []):
            symbol = comp.get("symbol", "").upper()
            if symbol and symbol not in competitions:
                competitions[symbol] = {
                    "name": comp.get("name", f"{symbol} Alpha 竞赛"),
                    "token_name": comp.get("token_name", symbol),
                    "start_time": comp.get("start_time", ""),
                    "end_time": comp.get("end_time", ""),
                    "timezone": comp.get("timezone", "UTC+8"),
                    "total_reward": comp.get("total_reward"),
                    "winner_count": comp.get("winner_count"),
                    "per_user_reward": comp.get("per_user_reward"),
                    "status": "已结束",
                    "note": comp.get("note", "")
                }
        
        return competitions
    
    return DEFAULT_ALPHA_COMPETITIONS

def fetch_alpha_news_from_web() -> List[Dict[str, Any]]:
    """从第三方新闻网站获取最新Alpha竞赛信息"""
    news_sources = [
        {
            "name": "ChainCatcher",
            "url": "https://www.chaincatcher.com/api/article/list",
            "keyword": "币安 Alpha"
        },
        {
            "name": "Odaily",
            "url": "https://www.odaily.news/api/pp/api/search",
            "keyword": "Binance Alpha"
        }
    ]
    
    found_competitions = []
    
    # 尝试搜索新闻
    for source in news_sources:
        try:
            # 这里可以实现具体的新闻抓取逻辑
            # 由于各网站API可能有限制，这里只做框架
            pass
        except Exception:
            continue
    
    return found_competitions

def auto_detect_alpha_competitions() -> Dict[str, Any]:
    """
    自动检测Alpha竞赛信息
    1. 首先检查外部配置文件
    2. 然后尝试从新闻网站获取
    3. 最后使用默认配置
    """
    # 从配置文件加载
    config = get_alpha_competitions_config()
    
    # 检查是否有过期的竞赛需要更新状态
    now = datetime.now()
    updated = False
    
    for symbol, comp in config.items():
        if comp.get("status") == "进行中":
            try:
                end_time = datetime.strptime(comp["end_time"], "%Y-%m-%d %H:%M:%S")
                if end_time < now:
                    comp["status"] = "已结束"
                    updated = True
            except:
                pass
    
    return config

def add_alpha_competition(symbol: str, name: str, start_time: str, end_time: str,
                          total_reward: int = None, winner_count: int = None,
                          per_user_reward: int = None, note: str = "") -> Dict[str, Any]:
    """添加新的Alpha竞赛到配置"""
    symbol = symbol.upper()
    
    # 加载现有配置
    file_config = load_alpha_config_from_file() or {
        "last_updated": "",
        "active_competitions": [],
        "ended_competitions": [],
        "alpha_airdrops": [],
        "coingecko_id_mapping": {}
    }
    
    # 创建新竞赛
    new_competition = {
        "symbol": symbol,
        "name": name,
        "token_name": symbol,
        "start_time": start_time,
        "end_time": end_time,
        "timezone": "UTC+8",
        "total_reward": total_reward,
        "winner_count": winner_count,
        "per_user_reward": per_user_reward,
        "status": "进行中",
        "note": note
    }
    
    # 检查是否已存在
    existing = False
    for i, comp in enumerate(file_config.get("active_competitions", [])):
        if comp.get("symbol", "").upper() == symbol:
            file_config["active_competitions"][i] = new_competition
            existing = True
            break
    
    if not existing:
        if "active_competitions" not in file_config:
            file_config["active_competitions"] = []
        file_config["active_competitions"].append(new_competition)
    
    # 更新时间戳
    file_config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 保存到文件
    if save_alpha_config_to_file(file_config):
        return {
            "success": True,
            "message": f"已{'更新' if existing else '添加'}竞赛: {name}",
            "competition": new_competition
        }
    else:
        return {
            "success": False,
            "message": "保存配置文件失败"
        }

# 使用动态加载的配置
ALPHA_COMPETITIONS = auto_detect_alpha_competitions()

# Alpha空投配置（从文件或默认值）
def get_alpha_airdrops_config() -> Dict[str, Any]:
    """获取Alpha空投配置"""
    file_config = load_alpha_config_from_file()
    
    if file_config and "alpha_airdrops" in file_config:
        airdrops = {}
        for airdrop in file_config.get("alpha_airdrops", []):
            symbol = airdrop.get("symbol", "").upper()
            if symbol:
                airdrops[symbol] = {
                    "name": airdrop.get("name", symbol),
                    "launch_date": airdrop.get("launch_date", ""),
                    "min_points": airdrop.get("min_points", 0),
                    "airdrop_amount": airdrop.get("airdrop_amount", 0),
                    "status": airdrop.get("status", "已结束")
                }
        return airdrops if airdrops else DEFAULT_ALPHA_AIRDROPS
    
    return DEFAULT_ALPHA_AIRDROPS

ALPHA_AIRDROPS = get_alpha_airdrops_config()

def get_token_price_from_coingecko(coin_id: str) -> Dict[str, Any]:
    """从CoinGecko获取代币价格（备用数据源）"""
    if not coin_id:
        return {"error": "未配置CoinGecko ID"}
    
    url = f"{COINGECKO_API}/simple/price"
    params = {
        "ids": coin_id,
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if coin_id in data:
            return {
                "price": data[coin_id].get("usd", 0),
                "change_24h": data[coin_id].get("usd_24h_change", 0),
                "source": "CoinGecko"
            }
        return {"error": "未找到价格数据"}
    except Exception as e:
        return {"error": str(e)}

def get_alpha_token_price(symbol: str) -> Dict[str, Any]:
    """获取Alpha代币价格（优先币安，备用CoinGecko）"""
    symbol = symbol.upper()
    
    # 尝试从币安获取
    ticker = get_ticker_24h(symbol)
    if "error" not in ticker:
        return {
            "price": ticker["price"],
            "change_24h": ticker["price_change_percent"],
            "volume_24h": ticker.get("quote_volume_24h", 0),
            "source": "Binance"
        }
    
    # 备用：从CoinGecko获取
    coingecko_id = ALPHA_TOKEN_COINGECKO_IDS.get(symbol)
    if coingecko_id:
        cg_data = get_token_price_from_coingecko(coingecko_id)
        if "error" not in cg_data:
            return cg_data
    
    return {"error": f"无法获取{symbol}价格", "source": None}

def calculate_time_remaining(end_time_str: str) -> str:
    """计算剩余时间"""
    try:
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        
        if end_time < now:
            return "已结束"
        
        delta = end_time - now
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            return f"{days}天{hours}小时"
        elif hours > 0:
            minutes = (delta.seconds % 3600) // 60
            return f"{hours}小时{minutes}分钟"
        else:
            minutes = delta.seconds // 60
            return f"{minutes}分钟"
    except:
        return "未知"

def get_alpha_tokens_list() -> Dict[str, Any]:
    """获取Alpha代币列表（空投类）"""
    tokens_info = []
    
    for symbol, info in ALPHA_AIRDROPS.items():
        # 尝试获取当前价格
        price_data = get_alpha_token_price(symbol)
        
        if "error" not in price_data:
            price = price_data["price"]
            total_value = price * info["airdrop_amount"]
            
            tokens_info.append({
                "symbol": symbol,
                "name": info["name"],
                "launch_date": info["launch_date"],
                "min_points_required": info["min_points"],
                "airdrop_amount": info["airdrop_amount"],
                "current_price": f"${price:,.6f}",
                "airdrop_value": f"${total_value:,.2f}",
                "change_24h": f"{price_data.get('change_24h', 0):+.2f}%",
                "data_source": price_data.get("source", "Unknown"),
                "status": info["status"]
            })
        else:
            tokens_info.append({
                "symbol": symbol,
                "name": info["name"],
                "launch_date": info["launch_date"],
                "min_points_required": info["min_points"],
                "airdrop_amount": info["airdrop_amount"],
                "current_price": "N/A（未上线或已更名）",
                "airdrop_value": "N/A",
                "status": info["status"]
            })
    
    return {
        "alpha_airdrops": tokens_info,
        "total_count": len(tokens_info),
        "note": "Alpha空投信息需要手动更新，建议关注币安官方公告"
    }

def analyze_alpha_token(symbol: str) -> Dict[str, Any]:
    """分析Alpha代币"""
    symbol = symbol.upper()
    
    # 获取价格数据（优先币安，备用CoinGecko）
    price_data = get_alpha_token_price(symbol)
    
    # 尝试获取完整行情
    ticker = get_ticker_24h(symbol)
    has_full_ticker = "error" not in ticker
    
    # 如果两个数据源都失败
    if "error" in price_data and not has_full_ticker:
        # 尝试CoinGecko详细数据
        coingecko_id = ALPHA_TOKEN_COINGECKO_IDS.get(symbol)
        if coingecko_id:
            try:
                url = f"{COINGECKO_API}/coins/{coingecko_id}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    cg_data = response.json()
                    market_data = cg_data.get("market_data", {})
                    price = market_data.get("current_price", {}).get("usd", 0)
                    
                    # 检查是否有竞赛信息
                    comp_info = ALPHA_COMPETITIONS.get(symbol, {})
                    airdrop_info = ALPHA_AIRDROPS.get(symbol, {})
                    
                    per_user_reward = comp_info.get("per_user_reward") or airdrop_info.get("airdrop_amount") or 0
                    reward_value = price * per_user_reward if per_user_reward else 0
                    
                    return {
                        "symbol": symbol,
                        "data_source": "CoinGecko",
                        "market_data": {
                            "price": f"${price:,.6f}",
                            "change_24h": f"{market_data.get('price_change_percentage_24h', 0):+.2f}%",
                            "market_cap": f"${market_data.get('market_cap', {}).get('usd', 0):,.0f}",
                            "volume_24h": f"${market_data.get('total_volume', {}).get('usd', 0):,.0f}",
                            "high_24h": f"${market_data.get('high_24h', {}).get('usd', 0):,.6f}",
                            "low_24h": f"${market_data.get('low_24h', {}).get('usd', 0):,.6f}",
                            "ath": f"${market_data.get('ath', {}).get('usd', 0):,.6f}",
                            "atl": f"${market_data.get('atl', {}).get('usd', 0):,.6f}"
                        },
                        "competition_info": comp_info if comp_info else None,
                        "per_user_reward": per_user_reward if per_user_reward else "N/A",
                        "reward_value": f"${reward_value:,.2f}" if reward_value else "N/A",
                        "note": "数据来自CoinGecko，技术分析需要币安API支持"
                    }
            except:
                pass
        
        return {"error": f"无法获取{symbol}数据，可能未上线或已更名"}
    
    # 有完整行情数据，进行技术分析
    if has_full_ticker:
        analysis = comprehensive_analysis(symbol)
        has_analysis = "error" not in analysis
    else:
        has_analysis = False
        analysis = {}
    
    # 检查竞赛信息
    comp_info = ALPHA_COMPETITIONS.get(symbol, {})
    airdrop_info = ALPHA_AIRDROPS.get(symbol, {})
    
    price = ticker["price"] if has_full_ticker else price_data.get("price", 0)
    per_user_reward = comp_info.get("per_user_reward") or airdrop_info.get("airdrop_amount") or 0
    total_reward = comp_info.get("total_reward") or 0
    
    result = {
        "symbol": symbol,
        "data_source": price_data.get("source", "Binance"),
        
        # 市场数据
        "market_data": {
            "price": f"${price:,.6f}",
            "change_24h": ticker["price_change_display"] if has_full_ticker else f"{price_data.get('change_24h', 0):+.2f}%",
            "volume_24h": ticker["quote_volume_formatted"] if has_full_ticker else "N/A",
            "high_24h": f"${ticker['high_24h']:,.6f}" if has_full_ticker else "N/A",
            "low_24h": f"${ticker['low_24h']:,.6f}" if has_full_ticker else "N/A"
        },
        
        # 💰 价值计算
        "value_analysis": {
            "per_user_reward": f"{per_user_reward:,}" if per_user_reward else "N/A",
            "per_user_value": f"${price * per_user_reward:,.2f}" if per_user_reward and price else "N/A",
            "total_reward": f"{total_reward:,}" if total_reward else "N/A",
            "total_value": f"${price * total_reward:,.2f}" if total_reward and price else "N/A"
        },
        
        # 竞赛信息
        "competition_info": {
            "name": comp_info.get("name", "N/A"),
            "end_time": comp_info.get("end_time", "N/A"),
            "time_remaining": calculate_time_remaining(comp_info["end_time"]) if comp_info.get("end_time") else "N/A",
            "status": comp_info.get("status", "未知")
        } if comp_info else None
    }
    
    # 添加技术分析（如果有）
    if has_analysis:
        result["technical_analysis"] = analysis.get("technical_indicators", {})
        result["trend"] = analysis.get("trend_analysis", {})
        result["prediction"] = analysis.get("prediction", {})
        result["summary"] = analysis.get("summary", "")
    
    return result

def get_active_alpha_competitions() -> Dict[str, Any]:
    """获取进行中的Alpha竞赛，包含实时价格和总价值计算"""
    
    active_competitions = []
    ended_competitions = []
    
    for symbol, comp in ALPHA_COMPETITIONS.items():
        # 获取代币价格
        price_data = get_alpha_token_price(symbol.replace("_ALPHA", ""))
        
        price = price_data.get("price", 0) if "error" not in price_data else 0
        change_24h = price_data.get("change_24h", 0) if "error" not in price_data else 0
        data_source = price_data.get("source", "N/A")
        
        # 计算价值
        total_reward = comp.get("total_reward") or 0
        per_user_reward = comp.get("per_user_reward") or 0
        
        # 活动总价值 = 总奖励 × 当前价格
        total_value = total_reward * price if total_reward and price else 0
        # 每人可得价值 = 每人奖励 × 当前价格
        per_user_value = per_user_reward * price if per_user_reward and price else 0
        
        # 计算剩余时间
        time_remaining = calculate_time_remaining(comp["end_time"])
        
        competition_info = {
            "symbol": symbol.replace("_ALPHA", ""),
            "name": comp["name"],
            "token_name": comp["token_name"],
            
            # 时间信息
            "start_time": comp["start_time"],
            "end_time": comp["end_time"],
            "timezone": comp["timezone"],
            "time_remaining": time_remaining,
            
            # 奖励信息
            "total_reward": f"{total_reward:,}" if total_reward else "待公布",
            "winner_count": f"{comp.get('winner_count', 0):,}" if comp.get("winner_count") else "待公布",
            "per_user_reward": f"{per_user_reward:,}" if per_user_reward else "待公布",
            
            # 💰 价值计算（核心功能）
            "current_price": f"${price:,.6f}" if price else "获取中...",
            "price_change_24h": f"{change_24h:+.2f}%" if change_24h else "N/A",
            "total_value": f"${total_value:,.2f}" if total_value else "待计算",
            "per_user_value": f"${per_user_value:,.2f}" if per_user_value else "待计算",
            
            # 其他信息
            "data_source": data_source,
            "status": comp["status"],
            "note": comp.get("note", "")
        }
        
        if comp["status"] == "进行中":
            active_competitions.append(competition_info)
        else:
            ended_competitions.append(competition_info)
    
    # 按结束时间排序（最快结束的在前）
    active_competitions.sort(key=lambda x: x["end_time"])
    
    return {
        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active_count": len(active_competitions),
        
        "active_competitions": active_competitions,
        
        "recently_ended": ended_competitions[:3],  # 只显示最近3个已结束的
        
        "value_calculation_note": "活动总价值 = 总奖励数量 × 当前价格 | 每人可得价值 = 每人奖励 × 当前价格",
        
        "update_reminder": "⚠️ 竞赛信息需手动更新，请编辑 binance_mcp.py 中的 ALPHA_COMPETITIONS 配置"
    }

# ==================== 影响因素分析 ====================

def analyze_market_factors(symbol: str) -> Dict[str, Any]:
    """分析市场影响因素"""
    ticker = get_ticker_24h(symbol)
    
    if "error" in ticker:
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

# ==================== K线形态分析 ====================

def analyze_kline_patterns(symbol: str, interval: str = "4h") -> Dict[str, Any]:
    """分析K线形态"""
    klines_data = get_klines(symbol, interval, 100)
    
    if "error" in klines_data:
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
        "analysis_summary": f"当前处于{overall_pattern}，" + (
            f"近期发现{len(patterns)}个形态信号" if patterns else "暂无明显形态信号"
        )
    }

# ==================== MCP协议处理 ====================

def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any] | None:
    """处理MCP请求"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    if request_id is None:
        return None

    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }

    try:
        if method == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "binance-mcp",
                    "version": "1.0.0"
                }
            }
        
        elif method == "tools/list":
            response["result"] = {
                "tools": [
                    # 价格查询
                    {
                        "name": "get_spot_price",
                        "description": "获取币安现货实时价格",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号，如 BTC, ETH, BNB（自动添加USDT后缀）"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "get_ticker_24h",
                        "description": "获取24小时行情数据，包含价格、涨跌幅、成交量等",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号，如 BTC, ETH"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "get_multiple_tickers",
                        "description": "批量获取多个交易对的24小时行情",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbols": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "交易对符号数组，如 ['BTC', 'ETH', 'BNB']"
                                }
                            },
                            "required": ["symbols"]
                        }
                    },
                    # K线数据
                    {
                        "name": "get_klines",
                        "description": "获取K线数据，支持多种时间周期",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号"
                                },
                                "interval": {
                                    "type": "string",
                                    "description": "时间周期: 1m,3m,5m,15m,30m,1h,2h,4h,6h,8h,12h,1d,3d,1w,1M",
                                    "default": "1h"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "K线数量，最大1000",
                                    "default": 100
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    # 技术分析
                    {
                        "name": "comprehensive_analysis",
                        "description": "综合技术分析：包含趋势判断、涨跌概率预测、RSI、MACD、布林带、支撑阻力位等",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "analyze_kline_patterns",
                        "description": "K线形态分析：识别十字星、锤子线、吞没形态等",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号"
                                },
                                "interval": {
                                    "type": "string",
                                    "description": "时间周期，默认4h",
                                    "default": "4h"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "analyze_market_factors",
                        "description": "分析市场影响因素：与BTC/ETH对比、相对强弱、成交量分析",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    # 合约分析
                    {
                        "name": "get_futures_price",
                        "description": "获取合约价格（USDT永续合约）",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "get_funding_rate",
                        "description": "获取合约资金费率和年化收益",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "analyze_spot_vs_futures",
                        "description": "分析现货与合约价差，判断套利机会",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "交易对符号"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    # Alpha分析
                    {
                        "name": "get_realtime_alpha_airdrops",
                        "description": "【实时】获取币安Alpha空投列表，包含即将开始、进行中、已结束的空投，自动计算价格和价值",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_alpha_tokens_list",
                        "description": "获取币安Alpha代币列表（本地配置）",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "analyze_alpha_token",
                        "description": "分析Alpha代币：价格、涨跌、技术指标、空投价值",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "Alpha代币符号"
                                }
                            },
                            "required": ["symbol"]
                        }
                    },
                    {
                        "name": "get_active_alpha_competitions",
                        "description": "获取进行中的Alpha竞赛信息，包含实时价格、活动总价值、每人可得价值",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "add_alpha_competition",
                        "description": "添加新的Alpha竞赛到配置（当发现新竞赛时使用）",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "symbol": {
                                    "type": "string",
                                    "description": "代币符号，如 TIMI, H"
                                },
                                "name": {
                                    "type": "string",
                                    "description": "竞赛名称"
                                },
                                "start_time": {
                                    "type": "string",
                                    "description": "开始时间，格式: 2026-01-09 21:00:00"
                                },
                                "end_time": {
                                    "type": "string",
                                    "description": "结束时间，格式: 2026-01-16 21:00:00"
                                },
                                "total_reward": {
                                    "type": "integer",
                                    "description": "总奖励数量（可选）"
                                },
                                "winner_count": {
                                    "type": "integer",
                                    "description": "获奖人数（可选）"
                                },
                                "per_user_reward": {
                                    "type": "integer",
                                    "description": "每人可得奖励（可选）"
                                },
                                "note": {
                                    "type": "string",
                                    "description": "备注说明（可选）"
                                }
                            },
                            "required": ["symbol", "name", "start_time", "end_time"]
                        }
                    },
                    # 市场数据
                    {
                        "name": "search_symbols",
                        "description": "搜索交易对",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "keyword": {
                                    "type": "string",
                                    "description": "搜索关键词"
                                }
                            },
                            "required": ["keyword"]
                        }
                    },
                    {
                        "name": "get_top_gainers_losers",
                        "description": "获取涨跌幅排行榜",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "limit": {
                                    "type": "integer",
                                    "description": "返回数量，默认10",
                                    "default": 10
                                }
                            }
                        }
                    }
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            # 价格查询
            if tool_name == "get_spot_price":
                result = get_spot_price(arguments.get("symbol", ""))
            elif tool_name == "get_ticker_24h":
                result = get_ticker_24h(arguments.get("symbol", ""))
            elif tool_name == "get_multiple_tickers":
                result = get_multiple_tickers(arguments.get("symbols", []))
            
            # K线数据
            elif tool_name == "get_klines":
                result = get_klines(
                    arguments.get("symbol", ""),
                    arguments.get("interval", "1h"),
                    arguments.get("limit", 100)
                )
            
            # 技术分析
            elif tool_name == "comprehensive_analysis":
                result = comprehensive_analysis(arguments.get("symbol", ""))
            elif tool_name == "analyze_kline_patterns":
                result = analyze_kline_patterns(
                    arguments.get("symbol", ""),
                    arguments.get("interval", "4h")
                )
            elif tool_name == "analyze_market_factors":
                result = analyze_market_factors(arguments.get("symbol", ""))
            
            # 合约分析
            elif tool_name == "get_futures_price":
                result = get_futures_price(arguments.get("symbol", ""))
            elif tool_name == "get_funding_rate":
                result = get_funding_rate(arguments.get("symbol", ""))
            elif tool_name == "analyze_spot_vs_futures":
                result = analyze_spot_vs_futures(arguments.get("symbol", ""))
            
            # Alpha分析
            elif tool_name == "get_realtime_alpha_airdrops":
                result = get_realtime_alpha_airdrops()
            elif tool_name == "get_alpha_tokens_list":
                result = get_alpha_tokens_list()
            elif tool_name == "analyze_alpha_token":
                result = analyze_alpha_token(arguments.get("symbol", ""))
            elif tool_name == "get_active_alpha_competitions":
                # 重新加载配置以获取最新数据
                global ALPHA_COMPETITIONS
                ALPHA_COMPETITIONS = auto_detect_alpha_competitions()
                result = get_active_alpha_competitions()
            elif tool_name == "add_alpha_competition":
                result = add_alpha_competition(
                    symbol=arguments.get("symbol", ""),
                    name=arguments.get("name", ""),
                    start_time=arguments.get("start_time", ""),
                    end_time=arguments.get("end_time", ""),
                    total_reward=arguments.get("total_reward"),
                    winner_count=arguments.get("winner_count"),
                    per_user_reward=arguments.get("per_user_reward"),
                    note=arguments.get("note", "")
                )
                # 添加后重新加载配置
                if result.get("success"):
                    ALPHA_COMPETITIONS = auto_detect_alpha_competitions()
            
            # 市场数据
            elif tool_name == "search_symbols":
                result = search_symbols(arguments.get("keyword", ""))
            elif tool_name == "get_top_gainers_losers":
                result = get_top_gainers_losers(arguments.get("limit", 10))
            
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            response["result"] = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2, ensure_ascii=False)
                    }
                ]
            }
        
        else:
            response["error"] = {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
    
    except Exception as e:
        response["error"] = {
            "code": -32603,
            "message": f"Internal error: {str(e)}"
        }

    return response

def main():
    """MCP服务器主循环"""
    for line in sys.stdin:
        try:
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            response = handle_mcp_request(request)
            if response is not None:
                print(json.dumps(response, ensure_ascii=False), flush=True)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    main()

