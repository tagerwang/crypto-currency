#!/usr/bin/env python3
"""
配置文件 - API地址、常量定义
"""

# 币安API基础URL（主站 + 备用站点）
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

# Alpha代币ID映射（用于CoinGecko查询）
ALPHA_TOKEN_COINGECKO_IDS = {
    "TIMI": "metaarena",
    "H": None,
    "BLUAI": None,
    "OOOO": None,
    "MAT": None,
    "ARB": "arbitrum",
}

# 默认Alpha竞赛配置
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


