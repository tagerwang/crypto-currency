#!/usr/bin/env python3
"""
Alpha空投/竞赛分析 - 统一入口
"""

import requests
from typing import Dict, Any
from datetime import datetime

from .config import COINGECKO_API, ALPHA_TOKEN_COINGECKO_IDS
from .utils import calculate_time_remaining
from .api import get_ticker_24h
from .analysis import comprehensive_analysis
from .alpha_realtime import get_realtime_alpha_airdrops
from .alpha_config import (
    auto_detect_alpha_competitions, get_alpha_airdrops_config,
    add_alpha_competition as _add_alpha_competition
)

# 初始化配置
ALPHA_COMPETITIONS = auto_detect_alpha_competitions()
ALPHA_AIRDROPS = get_alpha_airdrops_config()


def get_token_price_from_coingecko(coin_id: str) -> Dict[str, Any]:
    """从CoinGecko获取代币价格"""
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
    
    ticker = get_ticker_24h(symbol)
    if "error" not in ticker:
        return {
            "price": ticker["price"],
            "change_24h": ticker["price_change_percent"],
            "volume_24h": ticker.get("quote_volume_24h", 0),
            "source": "Binance"
        }
    
    coingecko_id = ALPHA_TOKEN_COINGECKO_IDS.get(symbol)
    if coingecko_id:
        cg_data = get_token_price_from_coingecko(coingecko_id)
        if "error" not in cg_data:
            return cg_data
    
    return {"error": f"无法获取{symbol}价格", "source": None}


def get_alpha_tokens_list() -> Dict[str, Any]:
    """获取Alpha代币列表（空投类）"""
    tokens_info = []
    
    for symbol, info in ALPHA_AIRDROPS.items():
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
    
    price_data = get_alpha_token_price(symbol)
    ticker = get_ticker_24h(symbol)
    has_full_ticker = "error" not in ticker
    
    if "error" in price_data and not has_full_ticker:
        coingecko_id = ALPHA_TOKEN_COINGECKO_IDS.get(symbol)
        if coingecko_id:
            try:
                url = f"{COINGECKO_API}/coins/{coingecko_id}"
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    cg_data = response.json()
                    market_data = cg_data.get("market_data", {})
                    price = market_data.get("current_price", {}).get("usd", 0)
                    
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
    
    if has_full_ticker:
        analysis = comprehensive_analysis(symbol)
        has_analysis = "error" not in analysis
    else:
        has_analysis = False
        analysis = {}
    
    comp_info = ALPHA_COMPETITIONS.get(symbol, {})
    airdrop_info = ALPHA_AIRDROPS.get(symbol, {})
    
    price = ticker["price"] if has_full_ticker else price_data.get("price", 0)
    per_user_reward = comp_info.get("per_user_reward") or airdrop_info.get("airdrop_amount") or 0
    total_reward = comp_info.get("total_reward") or 0
    
    result = {
        "symbol": symbol,
        "data_source": price_data.get("source", "Binance"),
        "market_data": {
            "price": f"${price:,.6f}",
            "change_24h": ticker["price_change_display"] if has_full_ticker else f"{price_data.get('change_24h', 0):+.2f}%",
            "volume_24h": ticker["quote_volume_formatted"] if has_full_ticker else "N/A",
            "high_24h": f"${ticker['high_24h']:,.6f}" if has_full_ticker else "N/A",
            "low_24h": f"${ticker['low_24h']:,.6f}" if has_full_ticker else "N/A"
        },
        "value_analysis": {
            "per_user_reward": f"{per_user_reward:,}" if per_user_reward else "N/A",
            "per_user_value": f"${price * per_user_reward:,.2f}" if per_user_reward and price else "N/A",
            "total_reward": f"{total_reward:,}" if total_reward else "N/A",
            "total_value": f"${price * total_reward:,.2f}" if total_reward and price else "N/A"
        },
        "competition_info": {
            "name": comp_info.get("name", "N/A"),
            "end_time": comp_info.get("end_time", "N/A"),
            "time_remaining": calculate_time_remaining(comp_info["end_time"]) if comp_info.get("end_time") else "N/A",
            "status": comp_info.get("status", "未知")
        } if comp_info else None
    }
    
    if has_analysis:
        result["technical_analysis"] = analysis.get("technical_indicators", {})
        result["trend"] = analysis.get("trend_analysis", {})
        result["prediction"] = analysis.get("prediction", {})
        result["summary"] = analysis.get("summary", "")
    
    return result


def get_active_alpha_competitions() -> Dict[str, Any]:
    """获取进行中的Alpha竞赛"""
    active_competitions = []
    ended_competitions = []
    
    for symbol, comp in ALPHA_COMPETITIONS.items():
        price_data = get_alpha_token_price(symbol.replace("_ALPHA", ""))
        
        price = price_data.get("price", 0) if "error" not in price_data else 0
        change_24h = price_data.get("change_24h", 0) if "error" not in price_data else 0
        data_source = price_data.get("source", "N/A")
        
        total_reward = comp.get("total_reward") or 0
        per_user_reward = comp.get("per_user_reward") or 0
        
        total_value = total_reward * price if total_reward and price else 0
        per_user_value = per_user_reward * price if per_user_reward and price else 0
        
        time_remaining = calculate_time_remaining(comp["end_time"])
        
        competition_info = {
            "symbol": symbol.replace("_ALPHA", ""),
            "name": comp["name"],
            "token_name": comp["token_name"],
            "start_time": comp["start_time"],
            "end_time": comp["end_time"],
            "timezone": comp["timezone"],
            "time_remaining": time_remaining,
            "total_reward": f"{total_reward:,}" if total_reward else "待公布",
            "winner_count": f"{comp.get('winner_count', 0):,}" if comp.get("winner_count") else "待公布",
            "per_user_reward": f"{per_user_reward:,}" if per_user_reward else "待公布",
            "current_price": f"${price:,.6f}" if price else "获取中...",
            "price_change_24h": f"{change_24h:+.2f}%" if change_24h else "N/A",
            "total_value": f"${total_value:,.2f}" if total_value else "待计算",
            "per_user_value": f"${per_user_value:,.2f}" if per_user_value else "待计算",
            "data_source": data_source,
            "status": comp["status"],
            "note": comp.get("note", "")
        }
        
        if comp["status"] == "进行中":
            active_competitions.append(competition_info)
        else:
            ended_competitions.append(competition_info)
    
    active_competitions.sort(key=lambda x: x["end_time"])
    
    return {
        "query_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "active_count": len(active_competitions),
        "active_competitions": active_competitions,
        "recently_ended": ended_competitions[:3],
        "value_calculation_note": "活动总价值 = 总奖励数量 × 当前价格 | 每人可得价值 = 每人奖励 × 当前价格",
        "update_reminder": "⚠️ 竞赛信息需手动更新，请使用 add_alpha_competition 工具"
    }


def add_alpha_competition(symbol: str, name: str, start_time: str, end_time: str,
                          total_reward: int = None, winner_count: int = None,
                          per_user_reward: int = None, note: str = "") -> Dict[str, Any]:
    """添加新的Alpha竞赛到配置"""
    global ALPHA_COMPETITIONS
    
    result = _add_alpha_competition(
        symbol, name, start_time, end_time,
        total_reward, winner_count, per_user_reward, note
    )
    
    if result.get("success"):
        ALPHA_COMPETITIONS = auto_detect_alpha_competitions()
    
    return result
