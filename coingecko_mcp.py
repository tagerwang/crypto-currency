#!/usr/bin/env python3
"""
CoinGecko MCP Server - 无需API密钥的加密货币数据服务器
支持查询所有主流币种，包括BNB、ZKP等
"""

import json
import sys
import requests
from typing import Any, Dict

# CoinGecko API基础URL（免费，无需API密钥）
BASE_URL = "https://api.coingecko.com/api/v3"

def get_market_chart(coin_id: str, days: int = 7) -> Dict[str, Any]:
    """
    获取币种历史价格数据
    """
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def calculate_trend_probability(coin_id: str) -> Dict[str, Any]:
    """
    计算涨跌概率分析
    基于近7天数据计算趋势
    """
    chart_data = get_market_chart(coin_id, 7)
    
    if "error" in chart_data:
        return {"error": chart_data["error"]}
    
    prices = chart_data.get("prices", [])
    if len(prices) < 10:
        return {"error": "数据不足"}
    
    # 提取价格序列
    price_values = [p[1] for p in prices]
    
    # 计算每日涨跌
    daily_changes = []
    # 每天约有24个数据点（每小时一个）
    points_per_day = len(price_values) // 7
    for i in range(1, 7):
        start_idx = (i - 1) * points_per_day
        end_idx = i * points_per_day
        if end_idx < len(price_values):
            day_start = price_values[start_idx]
            day_end = price_values[end_idx]
            change = (day_end - day_start) / day_start * 100
            daily_changes.append(change)
    
    # 统计涨跌天数
    up_days = sum(1 for c in daily_changes if c > 0)
    down_days = sum(1 for c in daily_changes if c < 0)
    total_days = len(daily_changes)
    
    # 计算动量指标
    current_price = price_values[-1]
    ma_3d = sum(price_values[-points_per_day*3:]) / (points_per_day * 3) if len(price_values) >= points_per_day * 3 else current_price
    ma_7d = sum(price_values) / len(price_values)
    
    # 价格位置（相对于7日均线）
    price_vs_ma7 = (current_price - ma_7d) / ma_7d * 100
    
    # 计算波动率
    returns = [(price_values[i] - price_values[i-1]) / price_values[i-1] for i in range(1, len(price_values))]
    volatility = (sum(r**2 for r in returns) / len(returns)) ** 0.5 * 100
    
    # 综合判断涨跌概率
    # 基于：历史涨跌比例 + 均线位置 + 动量
    base_prob = (up_days / total_days) * 100 if total_days > 0 else 50
    
    # 均线加成：价格在均线上方加分，下方减分
    ma_factor = min(max(price_vs_ma7 * 2, -15), 15)
    
    # 短期动量：3日均线 vs 7日均线
    momentum = (ma_3d - ma_7d) / ma_7d * 100
    momentum_factor = min(max(momentum * 3, -10), 10)
    
    # 最终概率
    up_probability = min(max(base_prob + ma_factor + momentum_factor, 15), 85)
    down_probability = 100 - up_probability
    
    # 趋势判断
    if up_probability >= 60:
        trend = "📈 偏多"
        trend_desc = "短期看涨"
    elif up_probability <= 40:
        trend = "📉 偏空"
        trend_desc = "短期看跌"
    else:
        trend = "➡️ 震荡"
        trend_desc = "方向不明"
    
    return {
        "trend": trend,
        "trend_description": trend_desc,
        "up_probability": round(up_probability, 1),
        "down_probability": round(down_probability, 1),
        "7d_up_days": up_days,
        "7d_down_days": down_days,
        "price_vs_ma7": f"{price_vs_ma7:+.2f}%",
        "volatility_7d": f"{volatility:.2f}%",
        "analysis": f"近7日{up_days}涨{down_days}跌，当前价格{'高于' if price_vs_ma7 > 0 else '低于'}7日均线{abs(price_vs_ma7):.1f}%"
    }

def get_price(coin_ids: str) -> Dict[str, Any]:
    """
    获取币种价格（含涨跌概率分析）
    coin_ids: 逗号分隔的币种ID，如 "bitcoin,ethereum,binancecoin"
    """
    url = f"{BASE_URL}/simple/price"
    params = {
        'ids': coin_ids,
        'vs_currencies': 'usd',
        'include_24hr_change': 'true',
        'include_24hr_vol': 'true',
        'include_market_cap': 'true',
        'include_last_updated_at': 'true'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        price_data = response.json()
        
        # 为每个币种添加涨跌概率分析
        for coin_id in coin_ids.split(','):
            coin_id = coin_id.strip()
            if coin_id in price_data:
                trend_analysis = calculate_trend_probability(coin_id)
                price_data[coin_id]["trend_analysis"] = trend_analysis
        
        return price_data
    except Exception as e:
        return {"error": str(e)}

def get_coin_data(coin_id: str) -> Dict[str, Any]:
    """
    获取币种详细信息
    coin_id: 币种ID，如 "bitcoin"
    """
    url = f"{BASE_URL}/coins/{coin_id}"
    params = {
        'localization': 'false',
        'tickers': 'false',
        'community_data': 'false',
        'developer_data': 'false'
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 提取关键信息
        return {
            "id": data.get("id"),
            "symbol": data.get("symbol"),
            "name": data.get("name"),
            "current_price": data.get("market_data", {}).get("current_price", {}).get("usd"),
            "market_cap": data.get("market_data", {}).get("market_cap", {}).get("usd"),
            "total_volume": data.get("market_data", {}).get("total_volume", {}).get("usd"),
            "price_change_24h": data.get("market_data", {}).get("price_change_24h"),
            "price_change_percentage_24h": data.get("market_data", {}).get("price_change_percentage_24h"),
            "high_24h": data.get("market_data", {}).get("high_24h", {}).get("usd"),
            "low_24h": data.get("market_data", {}).get("low_24h", {}).get("usd"),
            "ath": data.get("market_data", {}).get("ath", {}).get("usd"),
            "ath_date": data.get("market_data", {}).get("ath_date", {}).get("usd"),
            "atl": data.get("market_data", {}).get("atl", {}).get("usd"),
            "atl_date": data.get("market_data", {}).get("atl_date", {}).get("usd")
        }
    except Exception as e:
        return {"error": str(e)}

def search_coins(query: str) -> Dict[str, Any]:
    """
    搜索币种
    query: 搜索关键词，如 "zkp"
    """
    url = f"{BASE_URL}/search"
    params = {'query': query}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

def get_trending() -> Dict[str, Any]:
    """获取热门币种"""
    url = f"{BASE_URL}/search/trending"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# MCP协议处理
def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any] | None:
    """处理MCP请求 - 返回符合JSON-RPC 2.0规范的响应"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # 处理通知（没有id的请求不需要响应）
    if request_id is None:
        # notifications/initialized 等通知不需要响应
        return None

    # 构建基础响应
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
                    "name": "coingecko-mcp",
                    "version": "1.0.0"
                }
            }
        
        elif method == "tools/list":
            response["result"] = {
                "tools": [
                    {
                        "name": "get_price",
                        "description": "获取加密货币价格（支持BTC、ETH、BNB、ZKP等所有币种）",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "coin_ids": {
                                    "type": "string",
                                    "description": "币种ID，多个用逗号分隔。常用ID: bitcoin, ethereum, binancecoin, zkpass等"
                                }
                            },
                            "required": ["coin_ids"]
                        }
                    },
                    {
                        "name": "get_coin_data",
                        "description": "获取币种详细信息",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "coin_id": {
                                    "type": "string",
                                    "description": "币种ID，如 bitcoin"
                                }
                            },
                            "required": ["coin_id"]
                        }
                    },
                    {
                        "name": "search_coins",
                        "description": "搜索币种",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "搜索关键词"
                                }
                            },
                            "required": ["query"]
                        }
                    },
                    {
                        "name": "get_trending",
                        "description": "获取当前热门币种",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "get_price":
                result = get_price(arguments.get("coin_ids", ""))
            elif tool_name == "get_coin_data":
                result = get_coin_data(arguments.get("coin_id", ""))
            elif tool_name == "search_coins":
                result = search_coins(arguments.get("query", ""))
            elif tool_name == "get_trending":
                result = get_trending()
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            response["result"] = {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
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
            # 通知不需要响应
            if response is not None:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            # 忽略无效JSON
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
