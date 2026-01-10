#!/usr/bin/env python3
"""
Binance MCP Server - 币安加密货币数据服务器
模块化版本 v1.1.0

支持功能：
- 实时价格查询
- 历史K线数据
- 技术指标分析（RSI、MACD、布林带）
- 合约分析（资金费率、期现价差）
- Alpha空投/竞赛追踪
"""

from .config import *
from .utils import *
from .indicators import *
from .api import *
from .analysis import *
from .alpha_realtime import *
from .alpha_config import *
from .alpha import *
from .server import handle_mcp_request, main

__version__ = "1.1.0"
__all__ = [
    # Config
    "SPOT_BASE_URLS", "FUTURES_BASE_URLS", "HEADERS", "KLINE_INTERVALS",
    
    # Utils
    "format_number", "timestamp_to_datetime", "safe_float", "calculate_time_remaining",
    
    # Indicators
    "calculate_sma", "calculate_ema", "calculate_rsi", "calculate_macd",
    "calculate_bollinger_bands", "calculate_support_resistance",
    "analyze_trend_pattern", "predict_price_probability",
    
    # API
    "make_spot_request", "make_futures_request",
    "get_spot_price", "get_ticker_24h", "get_multiple_tickers",
    "get_klines", "get_futures_price", "get_funding_rate",
    "analyze_spot_vs_futures", "search_symbols", "get_top_gainers_losers",
    
    # Analysis
    "comprehensive_analysis", "analyze_market_factors", "analyze_kline_patterns",
    
    # Alpha Realtime
    "fetch_realtime_alpha_airdrops", "fetch_alpha_token_price_from_alpha123",
    "get_realtime_alpha_airdrops",
    
    # Alpha Config
    "auto_detect_alpha_competitions", "get_alpha_airdrops_config",
    
    # Alpha
    "get_alpha_tokens_list", "analyze_alpha_token",
    "get_active_alpha_competitions", "add_alpha_competition",
    
    # Server
    "handle_mcp_request", "main"
]
