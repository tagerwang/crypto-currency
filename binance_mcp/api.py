#!/usr/bin/env python3
"""
币安API调用 - 现货、合约、K线等接口
"""

import requests
from typing import Dict, List, Any
from datetime import datetime

from .config import SPOT_BASE_URLS, FUTURES_BASE_URLS, HEADERS, KLINE_INTERVALS
from .utils import format_number, timestamp_to_datetime, safe_float


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
    """获取资金费率（历史结算费率）"""
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


def get_realtime_funding_rate(symbol: str) -> Dict[str, Any]:
    """获取实时预测资金费率（下一期即将结算的费率）"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    # 获取 premiumIndex 数据
    result = make_futures_request("/premiumIndex", {"symbol": symbol})
    
    if not result["success"]:
        return {"error": result["error"], "symbol": symbol}
    
    data = result["data"]
    
    mark_price = safe_float(data.get("markPrice", 0))
    index_price = safe_float(data.get("indexPrice", 0))
    last_funding_rate = safe_float(data.get("lastFundingRate", 0)) * 100
    next_funding_time = data.get("nextFundingTime", 0)
    interest_rate = safe_float(data.get("interestRate", 0.0001)) * 100  # 默认0.01%
    
    # 计算溢价指数 Premium = (Mark Price - Index Price) / Index Price
    if index_price > 0:
        premium = ((mark_price - index_price) / index_price) * 100
    else:
        premium = 0
    
    # 计算预测费率
    # 预测费率 = Premium + clamp(Interest - Premium, -0.05%, 0.05%)
    # 然后 clamp 到 [-0.75%, 0.75%]
    diff = interest_rate - premium
    clamped_diff = max(-0.05, min(0.05, diff))
    predicted_rate = premium + clamped_diff
    predicted_rate = max(-0.75, min(0.75, predicted_rate))
    
    # 计算倒计时
    now_ts = datetime.now().timestamp() * 1000
    countdown_ms = next_funding_time - now_ts
    if countdown_ms > 0:
        countdown_seconds = int(countdown_ms / 1000)
        hours = countdown_seconds // 3600
        minutes = (countdown_seconds % 3600) // 60
        seconds = countdown_seconds % 60
        countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        countdown_str = "结算中..."
    
    # 年化收益计算（假设每8小时结算一次）
    annual_rate = predicted_rate * 3 * 365
    
    return {
        "symbol": symbol,
        "mark_price": mark_price,
        "mark_price_display": f"${mark_price:,.4f}",
        "index_price": index_price,
        "index_price_display": f"${index_price:,.4f}",
        "premium": premium,
        "premium_display": f"{premium:+.4f}%",
        "predicted_funding_rate": predicted_rate,
        "predicted_rate_display": f"{predicted_rate:+.5f}%",
        "last_funding_rate": last_funding_rate,
        "last_rate_display": f"{last_funding_rate:+.4f}%",
        "annual_rate": f"{annual_rate:+.2f}%",
        "next_funding_time": timestamp_to_datetime(next_funding_time) if next_funding_time else "N/A",
        "countdown": countdown_str,
        "signal": "多头付费" if predicted_rate > 0 else ("空头付费" if predicted_rate < 0 else "中性"),
        "rate_level": "极端负费率" if predicted_rate < -0.5 else (
            "高负费率" if predicted_rate < -0.1 else (
            "正常负费率" if predicted_rate < 0 else (
            "正常正费率" if predicted_rate < 0.1 else (
            "高正费率" if predicted_rate < 0.5 else "极端正费率"))))
    }


def get_extreme_funding_rates(threshold: float = 0.1, limit: int = 20) -> Dict[str, Any]:
    """获取极端资金费率的合约列表"""
    # 获取所有合约信息
    result = make_futures_request("/premiumIndex", {})
    
    if not result["success"]:
        return {"error": result["error"]}
    
    data = result["data"]
    
    extreme_negative = []  # 负费率（空头付费）
    extreme_positive = []  # 正费率（多头付费）
    
    for item in data:
        symbol = item.get("symbol", "")
        if not symbol.endswith("USDT"):
            continue
            
        mark_price = safe_float(item.get("markPrice", 0))
        index_price = safe_float(item.get("indexPrice", 0))
        last_funding_rate = safe_float(item.get("lastFundingRate", 0)) * 100
        next_funding_time = item.get("nextFundingTime", 0)
        interest_rate = safe_float(item.get("interestRate", 0.0001)) * 100
        
        # 计算预测费率
        if index_price > 0:
            premium = ((mark_price - index_price) / index_price) * 100
        else:
            premium = 0
        
        diff = interest_rate - premium
        clamped_diff = max(-0.05, min(0.05, diff))
        predicted_rate = premium + clamped_diff
        predicted_rate = max(-0.75, min(0.75, predicted_rate))
        
        # 计算倒计时
        now_ts = datetime.now().timestamp() * 1000
        countdown_ms = next_funding_time - now_ts
        if countdown_ms > 0:
            countdown_seconds = int(countdown_ms / 1000)
            hours = countdown_seconds // 3600
            minutes = (countdown_seconds % 3600) // 60
            countdown_str = f"{hours:02d}:{minutes:02d}"
        else:
            countdown_str = "结算中"
        
        entry = {
            "symbol": symbol,
            "predicted_rate": predicted_rate,
            "predicted_rate_display": f"{predicted_rate:+.5f}%",
            "last_rate": f"{last_funding_rate:+.4f}%",
            "mark_price": f"${mark_price:,.4f}",
            "premium": f"{premium:+.4f}%",
            "countdown": countdown_str,
            "annual_rate": f"{predicted_rate * 3 * 365:+.2f}%"
        }
        
        if predicted_rate < -threshold:
            extreme_negative.append(entry)
        elif predicted_rate > threshold:
            extreme_positive.append(entry)
    
    # 排序
    extreme_negative.sort(key=lambda x: x["predicted_rate"])
    extreme_positive.sort(key=lambda x: x["predicted_rate"], reverse=True)
    
    return {
        "threshold": f"{threshold}%",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "extreme_negative": {
            "description": "极端负费率（空头付费，做多有利）",
            "count": len(extreme_negative),
            "contracts": extreme_negative[:limit]
        },
        "extreme_positive": {
            "description": "极端正费率（多头付费，做空有利）", 
            "count": len(extreme_positive),
            "contracts": extreme_positive[:limit]
        }
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


