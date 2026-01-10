#!/usr/bin/env python3
"""
实时Alpha空投数据 - 从第三方API获取
"""

import requests
from typing import Dict, Any
from datetime import datetime, timedelta

from .config import ALPHA123_API, ALPHA123_HEADERS


def fetch_realtime_alpha_airdrops() -> Dict[str, Any]:
    """从Alpha123获取实时空投数据"""
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
    """获取实时Alpha空投列表（包含价格和价值计算）"""
    result = fetch_realtime_alpha_airdrops()
    
    if not result.get("success"):
        return {
            "error": result.get("error", "获取空投数据失败"),
            "fallback": "请尝试手动访问 https://alpha123.uk 查看"
        }
    
    airdrops = result.get("airdrops", [])
    
    upcoming = []
    ongoing = []
    ended = []
    
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
        
        price_data = fetch_alpha_token_price_from_alpha123(token)
        price = price_data.get("price", 0) if price_data.get("success") else 0
        
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
        
        if completed:
            ended.append(airdrop_info)
        elif date < today:
            ended.append(airdrop_info)
        elif date == today:
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
        "upcoming_airdrops": upcoming[:10],
        "ongoing_airdrops": ongoing[:10],
        "recently_ended": ended[:10],
        "note": "数据来自第三方聚合，仅供参考，以币安官方为准"
    }


