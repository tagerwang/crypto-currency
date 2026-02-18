#!/usr/bin/env python3
"""
币安API调用 - 现货、合约、K线等接口
"""

import requests
from typing import Dict, List, Any
from datetime import datetime

from .config import SPOT_BASE_URLS, FUTURES_BASE_URLS, FUTURES_DATA_BASE_URLS, HEADERS, KLINE_INTERVALS, ALPHA_BASE_URL
from .utils import format_number, timestamp_to_datetime, safe_float
from .request_pool import fetch_spot_with_dedup, fetch_futures_with_dedup, fetch_futures_data_with_dedup


# Alpha代币符号缓存
_alpha_symbols_cache = None
_alpha_symbols_cache_time = None
_alpha_token_list_cache = None
_alpha_token_list_cache_time = None


def _do_spot_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """实际发起现货API请求（供 request_pool 合并/缓存后调用）"""
    last_error = None
    is_network_error = False

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
                is_network_error = True
                continue
            last_error = f"HTTP错误: {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            last_error = "网络连接失败，请检查网络或代理设置"
            is_network_error = True
            continue
        except requests.exceptions.Timeout as e:
            last_error = "请求超时，请检查网络连接"
            is_network_error = True
            continue
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            is_network_error = True
            continue
    
    error_msg = last_error or "所有API端点均不可用，请检查网络或使用代理"
    return {
        "success": False, 
        "error": error_msg,
        "network_error": True,
        "stop_execution": True,
        "user_action_required": "⚠️ 检测到网络问题，请先确保VPN/代理正常连接后再重试。当前无法获取准确数据。"
    }


def make_spot_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """发起现货API请求，自动尝试备用域名；经请求合并与缓存，多用户同机访问时减少对币安API调用"""
    return fetch_spot_with_dedup(endpoint, params, lambda: _do_spot_request(endpoint, params))


def _do_futures_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """实际发起合约API请求（供 request_pool 合并/缓存后调用）"""
    last_error = None
    is_network_error = False

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
                is_network_error = True
                continue
            last_error = f"HTTP错误: {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            last_error = "网络连接失败，请检查网络或代理设置"
            is_network_error = True
            continue
        except requests.exceptions.Timeout as e:
            last_error = "请求超时，请检查网络连接"
            is_network_error = True
            continue
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            is_network_error = True
            continue

    error_msg = last_error or "所有API端点均不可用"
    return {
        "success": False,
        "error": error_msg,
        "network_error": True,
        "stop_execution": True,
        "user_action_required": "⚠️ 检测到网络问题，请先确保VPN/代理正常连接后再重试。当前无法获取准确数据。"
    }


def make_futures_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """发起合约API请求，自动尝试备用域名；经请求合并与缓存，多用户同机访问时减少对币安API调用"""
    return fetch_futures_with_dedup(endpoint, params, lambda: _do_futures_request(endpoint, params))


def _do_futures_data_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """实际发起合约数据API请求（供 request_pool 合并/缓存后调用）"""
    last_error = None
    is_network_error = False

    for base_url in FUTURES_DATA_BASE_URLS:
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=10)

            if response.status_code == 451:
                continue
            response.raise_for_status()
            return {"success": True, "data": response.json()}
        except requests.exceptions.HTTPError as e:
            if response.status_code == 451:
                last_error = "API访问受地区限制，请使用VPN或代理"
                is_network_error = True
                continue
            last_error = f"HTTP错误: {response.status_code}"
        except requests.exceptions.ConnectionError as e:
            last_error = "网络连接失败，请检查网络或代理设置"
            is_network_error = True
            continue
        except requests.exceptions.Timeout as e:
            last_error = "请求超时，请检查网络连接"
            is_network_error = True
            continue
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            is_network_error = True
            continue

    error_msg = last_error or "所有API端点均不可用"
    return {
        "success": False,
        "error": error_msg,
        "network_error": True,
        "stop_execution": True,
        "user_action_required": "⚠️ 检测到网络问题，请先确保VPN/代理正常连接后再重试。当前无法获取准确数据。"
    }


def make_futures_data_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """发起合约数据API请求（/futures/data/* 持仓量、多空比等）；经请求合并与缓存，多用户同机访问时减少对币安API调用"""
    return fetch_futures_data_with_dedup(endpoint, params, lambda: _do_futures_data_request(endpoint, params))


def _futures_trading_symbol_set(exchange_info_data: Dict) -> set:
    """从合约 exchangeInfo 的 data 中提取 status=TRADING、USDT/USDC 永续合约的 symbol 集合（与 APP 可交易列表一致）"""
    symbols = exchange_info_data.get("symbols", [])
    return {
        s["symbol"]
        for s in symbols
        if s.get("status") == "TRADING"
        and s.get("quoteAsset") in ("USDT", "USDC")
        and s.get("contractType", "PERPETUAL") == "PERPETUAL"
    }


def make_alpha_request(endpoint: str, params: Dict = None) -> Dict[str, Any]:
    """发起Alpha API请求"""
    url = f"{ALPHA_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success") or data.get("code") == "000000":
            return {"success": True, "data": data.get("data", data)}
        return {"success": False, "error": data.get("message", "Alpha API返回错误")}
    except requests.exceptions.HTTPError as e:
        return {"success": False, "error": f"HTTP错误: {response.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def get_alpha_token_list() -> Dict[str, Any]:
    """获取Alpha代币列表（包含代币名称映射）"""
    global _alpha_token_list_cache, _alpha_token_list_cache_time
    
    # 缓存5分钟
    now = datetime.now()
    if _alpha_token_list_cache and _alpha_token_list_cache_time:
        cache_age = (now - _alpha_token_list_cache_time).total_seconds()
        if cache_age < 300:
            return _alpha_token_list_cache
    
    url = "https://www.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/cex/alpha/all/token/list"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") == "000000":
            result = {"success": True, "data": data.get("data", [])}
            _alpha_token_list_cache = result
            _alpha_token_list_cache_time = now
            return result
        return {"success": False, "error": data.get("message", "获取代币列表失败")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_alpha_exchange_info() -> Dict[str, Any]:
    """获取Alpha交易所信息（包含所有Alpha代币列表）"""
    global _alpha_symbols_cache, _alpha_symbols_cache_time
    
    # 缓存5分钟
    now = datetime.now()
    if _alpha_symbols_cache and _alpha_symbols_cache_time:
        cache_age = (now - _alpha_symbols_cache_time).total_seconds()
        if cache_age < 300:
            return _alpha_symbols_cache
    
    result = make_alpha_request("/get-exchange-info")
    
    if result["success"]:
        _alpha_symbols_cache = result
        _alpha_symbols_cache_time = now
    
    return result


def is_alpha_token(symbol: str) -> bool:
    """检查是否为Alpha代币"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    exchange_info = get_alpha_exchange_info()
    if not exchange_info.get("success"):
        return False
    
    data = exchange_info.get("data", {})
    symbols = data.get("symbols", [])
    
    for s in symbols:
        # Alpha代币格式可能是 ALPHA_XXX 或直接是代币名
        if s.get("symbol") == symbol or s.get("baseAsset", "").upper() == symbol.replace("USDT", ""):
            return True
        # 检查baseAsset是否包含代币名（如 ALPHA_105 对应某个代币）
        base_asset = s.get("baseAsset", "")
        if symbol.replace("USDT", "") in base_asset.upper():
            return True
    
    return False


def get_alpha_ticker(symbol: str) -> Dict[str, Any]:
    """获取Alpha代币24小时行情"""
    symbol = symbol.upper()
    if symbol.endswith("USDT"):
        symbol = symbol[:-4]  # 去掉USDT后缀
    
    # 从代币列表获取信息
    token_list = get_alpha_token_list()
    if not token_list.get("success"):
        return {"error": "无法获取Alpha代币列表", "symbol": symbol}
    
    tokens = token_list.get("data", [])
    
    # 查找匹配的代币
    token_info = None
    for t in tokens:
        if t.get("symbol", "").upper() == symbol or t.get("name", "").upper() == symbol:
            token_info = t
            break
    
    if not token_info:
        return {"error": f"未找到Alpha代币: {symbol}", "symbol": symbol}
    
    # 从token_info中提取行情数据
    price = safe_float(token_info.get("price", 0))
    price_change_pct = safe_float(token_info.get("percentChange24h", 0))
    volume_24h = safe_float(token_info.get("volume24h", 0))
    high_24h = safe_float(token_info.get("priceHigh24h", 0))
    low_24h = safe_float(token_info.get("priceLow24h", 0))
    market_cap = safe_float(token_info.get("marketCap", 0))
    
    return {
        "symbol": f"{token_info.get('symbol')}USDT",
        "alpha_id": token_info.get("alphaId"),
        "name": token_info.get("name"),
        "market": "Alpha",
        "price": price,
        "price_formatted": f"${price:,.6f}",
        "price_change_percent": price_change_pct,
        "price_change_display": f"{price_change_pct:+.2f}%",
        "high_24h": high_24h,
        "low_24h": low_24h,
        "volume_24h": volume_24h,
        "quote_volume_24h": volume_24h,
        "quote_volume_formatted": f"${format_number(volume_24h)}",
        "market_cap": market_cap,
        "market_cap_formatted": f"${format_number(market_cap)}",
        "chain": token_info.get("chainName", ""),
        "holders": token_info.get("holders", 0),
        "trend_emoji": "🟢" if price_change_pct > 0 else ("🔴" if price_change_pct < 0 else "⚪"),
        "note": "数据来自币安Alpha市场"
    }


def get_spot_price(symbol: str, try_alpha: bool = True) -> Dict[str, Any]:
    """获取现货价格（现货优先，找不到时尝试Alpha市场）"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_spot_request("/ticker/price", {"symbol": symbol})
    
    if not result["success"]:
        # 如果是HTTP 400错误（交易对不存在），尝试Alpha市场
        if try_alpha and "400" in str(result.get("error", "")):
            alpha_result = get_alpha_ticker(symbol)
            if "error" not in alpha_result:
                return {
                    "symbol": symbol,
                    "market": "Alpha",
                    "price": alpha_result.get("price", 0),
                    "price_formatted": alpha_result.get("price_formatted", "N/A"),
                    "note": "数据来自币安Alpha市场"
                }
        
        error_response = {"error": result["error"], "symbol": symbol}
        # 传递网络错误标记
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
    data = result["data"]
    return {
        "symbol": data["symbol"],
        "market": "现货",
        "price": safe_float(data["price"]),
        "price_formatted": f"${safe_float(data['price']):,.4f}"
    }


def get_ticker_24h(symbol: str, try_alpha: bool = True, try_futures: bool = True) -> Dict[str, Any]:
    """获取24小时行情数据（现货优先，找不到时尝试Alpha市场，再尝试合约市场）"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_spot_request("/ticker/24hr", {"symbol": symbol})
    
    if not result["success"]:
        # 如果是HTTP 400错误（交易对不存在），依次尝试Alpha市场和合约市场
        if "400" in str(result.get("error", "")):
            # 先尝试Alpha市场
            if try_alpha:
                alpha_result = get_alpha_ticker(symbol)
                if "error" not in alpha_result:
                    return alpha_result
            
            # Alpha失败或未启用，尝试合约市场
            if try_futures:
                futures_result = get_futures_ticker_24h(symbol)
                if "error" not in futures_result:
                    return futures_result
        
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
    data = result["data"]
    price_change_pct = safe_float(data.get("priceChangePercent", 0))
    
    return {
        "symbol": data["symbol"],
        "market": "现货",
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


def get_klines(symbol: str, interval: str = "1h", limit: int = 100, try_alpha: bool = True, try_futures: bool = True) -> Dict[str, Any]:
    """获取K线数据（现货优先，找不到时尝试Alpha市场，再尝试合约市场）"""
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
        # 如果是HTTP 400错误（交易对不存在），依次尝试Alpha市场和合约市场
        if "400" in str(result.get("error", "")):
            # 先尝试Alpha市场
            if try_alpha:
                alpha_result = get_alpha_klines(symbol, interval, limit)
                if "error" not in alpha_result:
                    return alpha_result
            
            # Alpha失败或未启用，尝试合约市场
            if try_futures:
                futures_result = get_futures_klines(symbol, interval, limit)
                if "error" not in futures_result:
                    return futures_result
        
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
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
        "market": "现货",
        "interval": interval,
        "count": len(klines),
        "klines": klines
    }


def get_alpha_klines(symbol: str, interval: str = "1h", limit: int = 100) -> Dict[str, Any]:
    """获取Alpha代币K线数据"""
    symbol = symbol.upper()
    if symbol.endswith("USDT"):
        symbol = symbol[:-4]  # 去掉USDT后缀
    
    # 从代币列表获取alpha_id
    token_list = get_alpha_token_list()
    if not token_list.get("success"):
        return {"error": "无法获取Alpha代币列表", "symbol": symbol}
    
    tokens = token_list.get("data", [])
    
    # 查找匹配的代币
    alpha_id = None
    token_symbol = None
    for t in tokens:
        if t.get("symbol", "").upper() == symbol or t.get("name", "").upper() == symbol:
            alpha_id = t.get("alphaId")
            token_symbol = t.get("symbol")
            break
    
    if not alpha_id:
        return {"error": f"未找到Alpha代币: {symbol}", "symbol": symbol}
    
    # 构建Alpha K线请求
    alpha_symbol = f"{alpha_id}USDT"
    url = f"{ALPHA_BASE_URL}/klines"
    
    try:
        response = requests.get(url, params={
            "symbol": alpha_symbol,
            "interval": interval,
            "limit": min(limit, 1000)
        }, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if data.get("code") != "000000":
            return {"error": data.get("message", "获取K线失败"), "symbol": symbol}
        
        klines_data = data.get("data", [])
        klines = []
        for k in klines_data:
            # Alpha API返回的时间戳是字符串格式
            open_time = k[0]
            if isinstance(open_time, str):
                open_time = int(open_time)
            close_time = k[6] if len(k) > 6 else 0
            if isinstance(close_time, str):
                close_time = int(close_time)
            
            klines.append({
                "open_time": timestamp_to_datetime(open_time),
                "open": safe_float(k[1]),
                "high": safe_float(k[2]),
                "low": safe_float(k[3]),
                "close": safe_float(k[4]),
                "volume": safe_float(k[5]),
                "close_time": timestamp_to_datetime(close_time) if close_time else "",
                "quote_volume": safe_float(k[7]) if len(k) > 7 else 0,
                "trades": int(k[8]) if len(k) > 8 else 0
            })
        
        return {
            "symbol": f"{token_symbol}USDT",
            "alpha_id": alpha_id,
            "market": "Alpha",
            "interval": interval,
            "count": len(klines),
            "klines": klines,
            "note": "数据来自币安Alpha市场"
        }
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def get_futures_price(symbol: str) -> Dict[str, Any]:
    """获取合约价格"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_futures_request("/ticker/price", {"symbol": symbol})
    
    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
    data = result["data"]
    return {
        "symbol": data["symbol"],
        "price": safe_float(data["price"]),
        "price_formatted": f"${safe_float(data['price']):,.4f}",
        "time": timestamp_to_datetime(data["time"])
    }


def get_futures_ticker_24h(symbol: str) -> Dict[str, Any]:
    """获取合约24小时行情数据"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    result = make_futures_request("/ticker/24hr", {"symbol": symbol})
    
    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
    data = result["data"]
    price_change_pct = safe_float(data.get("priceChangePercent", 0))
    
    return {
        "symbol": data["symbol"],
        "market": "合约",
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


def get_futures_klines(symbol: str, interval: str = "1h", limit: int = 100) -> Dict[str, Any]:
    """获取合约K线数据"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    if interval not in KLINE_INTERVALS:
        return {"error": f"不支持的时间周期: {interval}，支持的周期: {list(KLINE_INTERVALS.keys())}"}
    
    result = make_futures_request("/klines", {
        "symbol": symbol,
        "interval": interval,
        "limit": min(limit, 1000)
    })
    
    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
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
        "market": "合约",
        "interval": interval,
        "count": len(klines),
        "klines": klines
    }


def get_futures_multiple_tickers(symbols: List[str]) -> Dict[str, Any]:
    """批量获取多个合约的24小时行情"""
    results = {}
    for symbol in symbols:
        ticker = get_futures_ticker_24h(symbol)
        results[symbol.upper()] = ticker
    return results


def get_funding_rate(symbol: str) -> Dict[str, Any]:
    """获取历史结算资金费率（最新已结算费率 + 历史记录）"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    # 先获取实时数据（包含最新已结算费率）
    premium_result = make_futures_request("/premiumIndex", {"symbol": symbol})
    
    if not premium_result["success"]:
        error_response = {"error": premium_result["error"], "symbol": symbol}
        if premium_result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = premium_result.get("user_action_required", "")
        return error_response
    
    premium_data = premium_result["data"]
    last_funding_rate = safe_float(premium_data.get("lastFundingRate", 0)) * 100
    next_funding_time = premium_data.get("nextFundingTime", 0)
    
    # 获取历史费率记录
    history_result = make_futures_request("/fundingRate", {"symbol": symbol, "limit": 10})
    history_data = []
    if history_result["success"] and history_result["data"]:
        history_data = [{"rate": f"{safe_float(d['fundingRate']) * 100:+.4f}%", 
                        "time": timestamp_to_datetime(d['fundingTime'])} for d in history_result["data"][:5]]
    
    # 计算年化费率 (每8小时一次，一天3次，一年365天)
    annual_rate = last_funding_rate * 3 * 365
    
    # 计算下次结算倒计时
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
    
    return {
        "symbol": symbol,
        "historical_settled_rate": last_funding_rate,
        "historical_settled_rate_display": f"{last_funding_rate:+.4f}%",
        "annual_rate": f"{annual_rate:+.2f}%",
        "next_funding_time": timestamp_to_datetime(next_funding_time) if next_funding_time else "N/A",
        "countdown": countdown_str,
        "signal": "多头付费" if last_funding_rate > 0 else ("空头付费" if last_funding_rate < 0 else "中性"),
        "rate_level": "极端负费率" if last_funding_rate < -0.5 else (
            "高负费率" if last_funding_rate < -0.1 else (
                "正常负费率" if last_funding_rate < 0 else (
                    "正常正费率" if last_funding_rate < 0.1 else (
                        "高正费率" if last_funding_rate < 0.5 else "极端正费率"
                    )
                )
            )
        ),
        "history": history_data,
        "note": "historical_settled_rate是上一期已结算的费率（历史数据）"
    }


def get_realtime_funding_rate(symbol: str) -> Dict[str, Any]:
    """获取实时资金费率（当前实时费率 + 预测费率）
    
    返回字段说明：
    - current_realtime_rate: 当前实时生效的资金费率（上一期已结算，现在正在生效）
    - predicted_next_rate: 下一期预测资金费率（即将在下次结算时生效）
    - historical_settled_rate: 历史结算费率（与current_realtime_rate相同，保留兼容性）
    """
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    # 获取 premiumIndex 数据
    result = make_futures_request("/premiumIndex", {"symbol": symbol})
    
    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
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
    
    # 年化收益计算
    annual_rate_current = last_funding_rate * 3 * 365
    annual_rate_predicted = predicted_rate * 3 * 365
    
    return {
        "symbol": symbol,
        "mark_price": mark_price,
        "mark_price_display": f"${mark_price:,.4f}",
        "index_price": index_price,
        "index_price_display": f"${index_price:,.4f}",
        "premium": premium,
        "premium_display": f"{premium:+.4f}%",
        
        # 当前实时费率（正在生效的费率）
        "current_realtime_rate": last_funding_rate,
        "current_realtime_rate_display": f"{last_funding_rate:+.4f}%",
        "current_annual_rate": f"{annual_rate_current:+.2f}%",
        "current_signal": "多头付费" if last_funding_rate > 0 else ("空头付费" if last_funding_rate < 0 else "中性"),
        
        # 预测费率（下次将要结算的费率）
        "predicted_next_rate": predicted_rate,
        "predicted_next_rate_display": f"{predicted_rate:+.5f}%",
        "predicted_annual_rate": f"{annual_rate_predicted:+.2f}%",
        "predicted_signal": "多头付费" if predicted_rate > 0 else ("空头付费" if predicted_rate < 0 else "中性"),
        
        # 历史结算费率（与current_realtime_rate相同，保留兼容性）
        "historical_settled_rate": last_funding_rate,
        "historical_settled_rate_display": f"{last_funding_rate:+.4f}%",
        
        # 结算时间
        "next_funding_time": timestamp_to_datetime(next_funding_time) if next_funding_time else "N/A",
        "countdown": countdown_str,
        
        # 费率等级（基于当前实时费率）
        "rate_level": "极端负费率" if last_funding_rate < -0.5 else (
            "高负费率" if last_funding_rate < -0.1 else (
            "正常负费率" if last_funding_rate < 0 else (
            "正常正费率" if last_funding_rate < 0.1 else (
            "高正费率" if last_funding_rate < 0.5 else "极端正费率")))),
        
        "note": "⚠️ 重要说明：current_realtime_rate是当前实时生效的费率（用于交易决策），predicted_next_rate是下次预测费率（参考用）"
    }


def get_extreme_funding_rates(threshold: float = 0.1, limit: int = 20) -> Dict[str, Any]:
    """获取极端资金费率的合约列表（仅 status=TRADING 的 USDT/USDC 永续合约，与 APP 一致）"""
    info_result = make_futures_request("/exchangeInfo", {})
    if not info_result["success"]:
        error_response = {"error": info_result["error"]}
        if info_result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = info_result.get("user_action_required", "")
        return error_response

    trading_symbols = _futures_trading_symbol_set(info_result["data"])

    result = make_futures_request("/premiumIndex", {})
    if not result["success"]:
        error_response = {"error": result["error"]}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]

    extreme_negative = []  # 负费率（空头付费）
    extreme_positive = []  # 正费率（多头付费）

    for item in data:
        symbol = item.get("symbol", "")
        if symbol not in trading_symbols:
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


def get_mark_price(symbol: str) -> Dict[str, Any]:
    """获取合约标记价格、指数价格、资金费率及下次结算时间"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    result = make_futures_request("/premiumIndex", {"symbol": symbol})

    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    mark_price = safe_float(data.get("markPrice", 0))
    index_price = safe_float(data.get("indexPrice", 0))
    last_funding_rate = safe_float(data.get("lastFundingRate", 0)) * 100
    next_funding_time = data.get("nextFundingTime", 0)
    estimated_settle = data.get("estimatedSettlePrice", 0)

    now_ts = datetime.now().timestamp() * 1000
    countdown_ms = next_funding_time - now_ts
    if countdown_ms > 0:
        countdown_seconds = int(countdown_ms / 1000)
        hours = countdown_seconds // 3600
        minutes = (countdown_seconds % 3600) // 60
        countdown_str = f"{hours:02d}:{minutes:02d}"
    else:
        countdown_str = "结算中"

    # 原始费率（小数，如 0.0001）供调用方做数值比较
    last_funding_rate_decimal = safe_float(data.get("lastFundingRate", 0))

    return {
        "symbol": symbol,
        "market": "合约",
        "mark_price": mark_price,
        "mark_price_formatted": f"${mark_price:,.4f}",
        "index_price": index_price,
        "index_price_formatted": f"${index_price:,.4f}",
        "last_funding_rate": f"{last_funding_rate:+.4f}%",
        "last_funding_rate_decimal": last_funding_rate_decimal,
        "next_funding_time": timestamp_to_datetime(next_funding_time) if next_funding_time else "N/A",
        "countdown_to_settlement": countdown_str,
        "estimated_settle_price": f"${safe_float(estimated_settle):,.4f}" if estimated_settle else "N/A",
    }


def get_open_interest(symbol: str) -> Dict[str, Any]:
    """获取合约当前持仓量"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    result = make_futures_request("/openInterest", {"symbol": symbol})

    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    open_interest = safe_float(data.get("openInterest", 0))
    timestamp = data.get("time", 0)

    return {
        "symbol": symbol,
        "market": "合约",
        "open_interest": open_interest,
        "open_interest_formatted": format_number(open_interest),
        "timestamp": timestamp_to_datetime(timestamp) if timestamp else "N/A",
    }


def get_open_interest_hist(symbol: str, period: str = "1h", limit: int = 30) -> Dict[str, Any]:
    """获取合约持仓量历史"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    valid_periods = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]
    if period not in valid_periods:
        return {"error": f"不支持的周期: {period}，支持: {valid_periods}"}

    result = make_futures_data_request("openInterestHist", {
        "symbol": symbol,
        "period": period,
        "limit": min(limit, 500),
    })

    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    history = [
        {
            "timestamp": timestamp_to_datetime(d["timestamp"]) if d.get("timestamp") else "N/A",
            "open_interest": safe_float(d.get("sumOpenInterest", 0)),
            "open_interest_value": safe_float(d.get("sumOpenInterestValue", 0)),
        }
        for d in data
    ]

    return {
        "symbol": symbol,
        "market": "合约",
        "period": period,
        "count": len(history),
        "history": history,
    }


def get_top_long_short_ratio(symbol: str, period: str = "1h", limit: int = 30) -> Dict[str, Any]:
    """获取大户账户多空比（top 20% 用户）"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    valid_periods = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]
    if period not in valid_periods:
        return {"error": f"不支持的周期: {period}，支持: {valid_periods}"}

    result = make_futures_data_request("topLongShortAccountRatio", {
        "symbol": symbol,
        "period": period,
        "limit": min(limit, 500),
    })

    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    history = [
        {
            "timestamp": timestamp_to_datetime(d["timestamp"]) if d.get("timestamp") else "N/A",
            "long_short_ratio": safe_float(d.get("longShortRatio", 0)),
            "long_account": f"{safe_float(d.get('longAccount', 0)) * 100:.2f}%",
            "short_account": f"{safe_float(d.get('shortAccount', 0)) * 100:.2f}%",
        }
        for d in data
    ]

    latest = history[0] if history else {}
    return {
        "symbol": symbol,
        "market": "合约",
        "period": period,
        "description": "大户账户多空比（持仓量前20%用户）",
        "latest_ratio": latest.get("long_short_ratio", 0),
        "count": len(history),
        "history": history,
    }


def get_top_long_short_position_ratio(symbol: str, period: str = "1h", limit: int = 30) -> Dict[str, Any]:
    """获取大户持仓多空比"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    valid_periods = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]
    if period not in valid_periods:
        return {"error": f"不支持的周期: {period}，支持: {valid_periods}"}

    result = make_futures_data_request("topLongShortPositionRatio", {
        "symbol": symbol,
        "period": period,
        "limit": min(limit, 500),
    })

    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    history = [
        {
            "timestamp": timestamp_to_datetime(d["timestamp"]) if d.get("timestamp") else "N/A",
            "long_short_ratio": safe_float(d.get("longShortRatio", 0)),
            "long_position": f"{safe_float(d.get('longPosition', 0)) * 100:.2f}%",
            "short_position": f"{safe_float(d.get('shortPosition', 0)) * 100:.2f}%",
        }
        for d in data
    ]

    latest = history[0] if history else {}
    return {
        "symbol": symbol,
        "market": "合约",
        "period": period,
        "description": "大户持仓多空比",
        "latest_ratio": latest.get("long_short_ratio", 0),
        "count": len(history),
        "history": history,
    }


def get_global_long_short_ratio(symbol: str, period: str = "1h", limit: int = 30) -> Dict[str, Any]:
    """获取全市场多空比"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    valid_periods = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]
    if period not in valid_periods:
        return {"error": f"不支持的周期: {period}，支持: {valid_periods}"}

    result = make_futures_data_request("globalLongShortAccountRatio", {
        "symbol": symbol,
        "period": period,
        "limit": min(limit, 500),
    })

    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    history = [
        {
            "timestamp": timestamp_to_datetime(d["timestamp"]) if d.get("timestamp") else "N/A",
            "long_short_ratio": safe_float(d.get("longShortRatio", 0)),
            "long_account": f"{safe_float(d.get('longAccount', 0)) * 100:.2f}%",
            "short_account": f"{safe_float(d.get('shortAccount', 0)) * 100:.2f}%",
        }
        for d in data
    ]

    latest = history[0] if history else {}
    return {
        "symbol": symbol,
        "market": "合约",
        "period": period,
        "description": "全市场账户多空比",
        "latest_ratio": latest.get("long_short_ratio", 0),
        "count": len(history),
        "history": history,
    }


def get_taker_buy_sell_ratio(symbol: str, period: str = "1h", limit: int = 30) -> Dict[str, Any]:
    """获取主动买卖比（taker long/short ratio）"""
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"

    valid_periods = ["5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d"]
    if period not in valid_periods:
        return {"error": f"不支持的周期: {period}，支持: {valid_periods}"}

    result = make_futures_data_request("takerlongshortRatio", {
        "symbol": symbol,
        "period": period,
        "limit": min(limit, 500),
    })

    if not result["success"]:
        error_response = {"error": result["error"], "symbol": symbol}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    history = [
        {
            "timestamp": timestamp_to_datetime(d["timestamp"]) if d.get("timestamp") else "N/A",
            "buy_sell_ratio": safe_float(d.get("buySellRatio", 0)),
            "buy_vol": safe_float(d.get("buyVol", 0)),
            "sell_vol": safe_float(d.get("sellVol", 0)),
        }
        for d in data
    ]

    latest = history[0] if history else {}
    return {
        "symbol": symbol,
        "market": "合约",
        "period": period,
        "description": "主动买卖比（taker主动成交）",
        "latest_ratio": latest.get("buy_sell_ratio", 0),
        "count": len(history),
        "history": history,
    }


def analyze_spot_vs_futures(symbol: str) -> Dict[str, Any]:
    """分析现货与合约价差"""
    spot = get_spot_price(symbol)
    futures = get_futures_price(symbol)
    funding = get_realtime_funding_rate(symbol)  # 使用实时预测费率
    
    # 检查是否有网络错误
    if "error" in spot:
        if spot.get("network_error"):
            return spot
    if "error" in futures:
        if futures.get("network_error"):
            return futures
    
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
        "funding_rate": funding.get("predicted_rate_display", "N/A"),  # 使用预测费率
        "annual_funding": funding.get("annual_rate", "N/A"),
        "analysis": {
            "market_sentiment": "偏多" if premium > 0.1 else ("偏空" if premium < -0.1 else "中性"),
            "arbitrage_opportunity": abs(premium) > 0.5,
            "suggestion": "期现套利可行" if abs(premium) > 0.5 else "价差正常"
        }
    }


def search_symbols(keyword: str) -> Dict[str, Any]:
    """搜索交易对（现货 + Alpha代币）"""
    keyword = keyword.upper()
    spot_matches = []
    alpha_matches = []
    
    # 1. 搜索现货市场
    result = make_spot_request("/exchangeInfo", {})
    
    if result["success"]:
        data = result["data"]
        for s in data["symbols"]:
            if s["status"] == "TRADING" and s["quoteAsset"] == "USDT":
                if keyword in s["baseAsset"] or keyword in s["symbol"]:
                    spot_matches.append({
                        "symbol": s["symbol"],
                        "base_asset": s["baseAsset"],
                        "quote_asset": s["quoteAsset"],
                        "market": "现货"
                    })
    
    # 2. 如果现货没找到，搜索Alpha代币
    if len(spot_matches) == 0:
        alpha_matches = search_alpha_tokens(keyword)
    
    # 合并结果
    all_matches = spot_matches[:20] + alpha_matches[:10]
    
    return {
        "keyword": keyword,
        "count": len(all_matches),
        "spot_count": len(spot_matches),
        "alpha_count": len(alpha_matches),
        "symbols": all_matches,
        "note": "现货未找到时自动搜索Alpha代币" if alpha_matches else None
    }


def search_futures_symbols(keyword: str) -> Dict[str, Any]:
    """搜索合约交易对"""
    keyword = keyword.upper()
    result = make_futures_request("/exchangeInfo", {})

    if not result["success"]:
        error_response = {"error": result["error"], "keyword": keyword}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    matches = []
    for s in data.get("symbols", []):
        if s.get("status") == "TRADING" and s.get("quoteAsset") in ("USDT", "USDC") and s.get("contractType", "PERPETUAL") == "PERPETUAL":
            if keyword in s.get("baseAsset", "") or keyword in s.get("symbol", ""):
                matches.append({
                    "symbol": s["symbol"],
                    "base_asset": s["baseAsset"],
                    "quote_asset": s["quoteAsset"],
                    "market": "合约",
                })

    return {
        "keyword": keyword,
        "count": len(matches),
        "symbols": matches[:30],
    }


def search_alpha_tokens(keyword: str) -> List[Dict[str, Any]]:
    """搜索Alpha代币（从币安Alpha代币列表API）"""
    keyword = keyword.upper()
    matches = []
    
    # 从币安Alpha代币列表API获取
    try:
        token_list = get_alpha_token_list()
        if token_list.get("success"):
            tokens = token_list.get("data", [])
            for t in tokens:
                symbol = t.get("symbol", "").upper()
                name = t.get("name", "").upper()
                if keyword in symbol or keyword in name:
                    matches.append({
                        "symbol": f"{t.get('symbol')}USDT",
                        "base_asset": t.get("symbol"),
                        "quote_asset": "USDT",
                        "market": "Alpha",
                        "name": t.get("name"),
                        "alpha_id": t.get("alphaId"),
                        "chain": t.get("chainName"),
                        "price": f"${safe_float(t.get('price', 0)):,.6f}",
                        "change_24h": f"{safe_float(t.get('percentChange24h', 0)):+.2f}%",
                        "note": "币安Alpha代币"
                    })
    except Exception as e:
        pass
    
    return matches


def get_top_gainers_losers(limit: int = 10) -> Dict[str, Any]:
    """获取涨跌幅榜"""
    result = make_spot_request("/ticker/24hr", {})
    
    if not result["success"]:
        error_response = {"error": result["error"]}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response
    
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
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market": "现货",
    }


def get_futures_top_gainers_losers(limit: int = 10) -> Dict[str, Any]:
    """获取合约涨跌幅榜（仅包含 exchangeInfo 中 status=TRADING 的 USDT/USDC 永续合约，与 APP 合约市场一致）"""
    info_result = make_futures_request("/exchangeInfo", {})
    if not info_result["success"]:
        error_response = {"error": info_result["error"]}
        if info_result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = info_result.get("user_action_required", "")
        return error_response

    trading_symbols = _futures_trading_symbol_set(info_result["data"])

    result = make_futures_request("/ticker/24hr", {})
    if not result["success"]:
        error_response = {"error": result["error"]}
        if result.get("network_error"):
            error_response["network_error"] = True
            error_response["stop_execution"] = True
            error_response["user_action_required"] = result.get("user_action_required", "")
        return error_response

    data = result["data"]
    usdt_pairs = [
        d
        for d in data
        if d["symbol"] in trading_symbols
        and safe_float(d.get("quoteVolume", 0)) > 1000000
    ]
    sorted_by_change = sorted(usdt_pairs, key=lambda x: safe_float(x.get("priceChangePercent", 0)), reverse=True)

    gainers = []
    for d in sorted_by_change[:limit]:
        gainers.append({
            "symbol": d["symbol"],
            "price": f"${safe_float(d.get('lastPrice', 0)):,.4f}",
            "change": f"{safe_float(d.get('priceChangePercent', 0)):+.2f}%",
            "volume": f"${format_number(safe_float(d.get('quoteVolume', 0)))}",
        })

    losers = []
    for d in sorted_by_change[-limit:]:
        losers.append({
            "symbol": d["symbol"],
            "price": f"${safe_float(d.get('lastPrice', 0)):,.4f}",
            "change": f"{safe_float(d.get('priceChangePercent', 0)):+.2f}%",
            "volume": f"${format_number(safe_float(d.get('quoteVolume', 0)))}",
        })
    losers.reverse()

    return {
        "top_gainers": gainers,
        "top_losers": losers,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market": "合约",
    }


