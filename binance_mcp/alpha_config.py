#!/usr/bin/env python3
"""
Alpha竞赛配置管理 - 文件读写、配置加载
"""

import os
import json
from typing import Dict, Any
from datetime import datetime

from .config import DEFAULT_ALPHA_COMPETITIONS, DEFAULT_ALPHA_AIRDROPS

# 配置文件路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ALPHA_CONFIG_FILE = os.path.join(os.path.dirname(SCRIPT_DIR), "alpha_competitions.json")


def load_alpha_config_from_file() -> Dict[str, Any]:
    """从外部JSON文件加载Alpha竞赛配置"""
    try:
        if os.path.exists(ALPHA_CONFIG_FILE):
            with open(ALPHA_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def save_alpha_config_to_file(config: Dict[str, Any]) -> bool:
    """保存Alpha竞赛配置到外部JSON文件"""
    try:
        with open(ALPHA_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_alpha_competitions_config() -> Dict[str, Any]:
    """获取Alpha竞赛配置（优先从文件加载）"""
    file_config = load_alpha_config_from_file()
    
    if file_config and "active_competitions" in file_config:
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


def auto_detect_alpha_competitions() -> Dict[str, Any]:
    """自动检测Alpha竞赛信息"""
    config = get_alpha_competitions_config()
    now = datetime.now()
    
    for symbol, comp in config.items():
        if comp.get("status") == "进行中":
            try:
                end_time = datetime.strptime(comp["end_time"], "%Y-%m-%d %H:%M:%S")
                if end_time < now:
                    comp["status"] = "已结束"
            except:
                pass
    
    return config


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


def add_alpha_competition(symbol: str, name: str, start_time: str, end_time: str,
                          total_reward: int = None, winner_count: int = None,
                          per_user_reward: int = None, note: str = "") -> Dict[str, Any]:
    """添加新的Alpha竞赛到配置"""
    symbol = symbol.upper()
    
    file_config = load_alpha_config_from_file() or {
        "last_updated": "",
        "active_competitions": [],
        "ended_competitions": [],
        "alpha_airdrops": [],
        "coingecko_id_mapping": {}
    }
    
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
    
    file_config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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


