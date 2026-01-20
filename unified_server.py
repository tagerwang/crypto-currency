#!/usr/bin/env python3
"""
统一服务器 - 同时支持REST API和MCP协议
- REST API: http://server/binance/spot/price?symbol=BTC
- MCP协议: http://server/mcp (POST JSON-RPC 2.0)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)

# 导入MCP服务器处理函数
from binance_mcp.server import handle_mcp_request

# 导入业务逻辑
from binance_mcp.api import (
    get_spot_price, get_ticker_24h, get_klines,
    get_futures_price, get_funding_rate, get_realtime_funding_rate,
    get_extreme_funding_rates, analyze_spot_vs_futures,
    search_symbols, get_top_gainers_losers
)
from binance_mcp.analysis import (
    comprehensive_analysis, analyze_kline_patterns, analyze_market_factors
)
from binance_mcp.alpha import (
    get_alpha_tokens_list, analyze_alpha_token, get_active_alpha_competitions
)
from binance_mcp.alpha_realtime import get_realtime_alpha_airdrops
from coingecko_mcp import get_price, get_coin_data, search_coins, get_trending

# ============ MCP 协议端点 ============
@app.route('/mcp', methods=['POST'])
def mcp_endpoint():
    """MCP协议端点 - Binance工具"""
    try:
        mcp_request = request.get_json()
        response = handle_mcp_request(mcp_request)
        if response:
            return jsonify(response)
        return '', 204
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": str(e)}
        }), 500

@app.route('/mcp-coingecko', methods=['POST'])
def mcp_coingecko_endpoint():
    """MCP协议端点 - CoinGecko工具"""
    try:
        from coingecko_mcp import handle_mcp_request as handle_coingecko_request
        mcp_request = request.get_json()
        response = handle_coingecko_request(mcp_request)
        if response:
            return jsonify(response)
        return '', 204
    except Exception as e:
        return jsonify({
            "jsonrpc": "2.0",
            "id": None,
            "error": {"code": -32603, "message": str(e)}
        }), 500

# ============ 健康检查 ============
@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "Unified Crypto API Server",
        "protocols": ["REST", "MCP"],
        "mcp_endpoint": "/mcp"
    })

# ============ REST API - Binance ============
@app.route('/binance/spot/price', methods=['GET'])
def binance_spot_price():
    symbol = request.args.get('symbol', 'BTC')
    result = get_spot_price(symbol)
    return jsonify(result)

@app.route('/binance/ticker/24h', methods=['GET'])
def binance_ticker_24h():
    symbol = request.args.get('symbol', 'BTC')
    result = get_ticker_24h(symbol)
    return jsonify(result)

@app.route('/binance/klines', methods=['GET'])
def binance_klines():
    symbol = request.args.get('symbol', 'BTC')
    interval = request.args.get('interval', '1h')
    limit = int(request.args.get('limit', 100))
    result = get_klines(symbol, interval, limit)
    return jsonify(result)

@app.route('/binance/analysis/comprehensive', methods=['GET'])
def binance_comprehensive_analysis():
    symbol = request.args.get('symbol', 'BTC')
    result = comprehensive_analysis(symbol)
    return jsonify(result)

@app.route('/binance/analysis/kline-patterns', methods=['GET'])
def binance_kline_patterns():
    symbol = request.args.get('symbol', 'BTC')
    interval = request.args.get('interval', '4h')
    result = analyze_kline_patterns(symbol, interval)
    return jsonify(result)

@app.route('/binance/futures/price', methods=['GET'])
def binance_futures_price():
    symbol = request.args.get('symbol', 'BTC')
    result = get_futures_price(symbol)
    return jsonify(result)

@app.route('/binance/funding-rate', methods=['GET'])
def binance_funding_rate():
    symbol = request.args.get('symbol', 'BTC')
    result = get_funding_rate(symbol)
    return jsonify(result)

@app.route('/binance/funding-rate/realtime', methods=['GET'])
def binance_realtime_funding_rate():
    symbol = request.args.get('symbol', 'BTC')
    result = get_realtime_funding_rate(symbol)
    return jsonify(result)

@app.route('/binance/funding-rate/extreme', methods=['GET'])
def binance_extreme_funding_rates():
    threshold = float(request.args.get('threshold', 0.1))
    limit = int(request.args.get('limit', 20))
    result = get_extreme_funding_rates(threshold, limit)
    return jsonify(result)

@app.route('/binance/analysis/spot-vs-futures', methods=['GET'])
def binance_spot_vs_futures():
    symbol = request.args.get('symbol', 'BTC')
    result = analyze_spot_vs_futures(symbol)
    return jsonify(result)

@app.route('/binance/alpha/airdrops', methods=['GET'])
def binance_alpha_airdrops():
    result = get_realtime_alpha_airdrops()
    return jsonify(result)

@app.route('/binance/alpha/tokens', methods=['GET'])
def binance_alpha_tokens():
    result = get_alpha_tokens_list()
    return jsonify(result)

@app.route('/binance/alpha/analyze', methods=['GET'])
def binance_analyze_alpha():
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "symbol parameter required"}), 400
    result = analyze_alpha_token(symbol)
    return jsonify(result)

@app.route('/binance/alpha/competitions', methods=['GET'])
def binance_alpha_competitions():
    result = get_active_alpha_competitions()
    return jsonify(result)

@app.route('/binance/search', methods=['GET'])
def binance_search():
    keyword = request.args.get('keyword', '')
    result = search_symbols(keyword)
    return jsonify(result)

@app.route('/binance/top-movers', methods=['GET'])
def binance_top_movers():
    limit = int(request.args.get('limit', 10))
    result = get_top_gainers_losers(limit)
    return jsonify(result)

@app.route('/binance/analysis/market-factors', methods=['GET'])
def binance_market_factors():
    symbol = request.args.get('symbol', 'BTC')
    result = analyze_market_factors(symbol)
    return jsonify(result)

# ============ REST API - CoinGecko ============
@app.route('/coingecko/price', methods=['GET'])
def coingecko_price():
    coin_ids = request.args.get('coin_ids', 'bitcoin')
    result = get_price(coin_ids)
    return jsonify(result)

@app.route('/coingecko/coin', methods=['GET'])
def coingecko_coin():
    coin_id = request.args.get('coin_id', 'bitcoin')
    result = get_coin_data(coin_id)
    return jsonify(result)

@app.route('/coingecko/search', methods=['GET'])
def coingecko_search():
    query = request.args.get('query', '')
    result = search_coins(query)
    return jsonify(result)

@app.route('/coingecko/trending', methods=['GET'])
def coingecko_trending():
    result = get_trending()
    return jsonify(result)

# ============ API 文档 ============
@app.route('/', methods=['GET'])
def api_docs():
    """API 文档"""
    return jsonify({
        "service": "Unified Crypto API Server",
        "version": "2.0.0",
        "protocols": {
            "REST": "HTTP GET/POST",
            "MCP": {
                "binance": "JSON-RPC 2.0 at POST /mcp",
                "coingecko": "JSON-RPC 2.0 at POST /mcp-coingecko"
            }
        },
        "rest_endpoints": {
            "health": "GET /health",
            "binance": {
                "spot_price": "GET /binance/spot/price?symbol=BTC",
                "ticker_24h": "GET /binance/ticker/24h?symbol=BTC",
                "klines": "GET /binance/klines?symbol=BTC&interval=1h&limit=100",
                "comprehensive_analysis": "GET /binance/analysis/comprehensive?symbol=BTC",
                "kline_patterns": "GET /binance/analysis/kline-patterns?symbol=BTC&interval=4h",
                "futures_price": "GET /binance/futures/price?symbol=BTC",
                "funding_rate": "GET /binance/funding-rate?symbol=BTC",
                "realtime_funding_rate": "GET /binance/funding-rate/realtime?symbol=BTC",
                "extreme_funding_rates": "GET /binance/funding-rate/extreme?threshold=0.1&limit=20",
                "spot_vs_futures": "GET /binance/analysis/spot-vs-futures?symbol=BTC",
                "alpha_airdrops": "GET /binance/alpha/airdrops",
                "alpha_tokens": "GET /binance/alpha/tokens",
                "analyze_alpha": "GET /binance/alpha/analyze?symbol=TIMI",
                "alpha_competitions": "GET /binance/alpha/competitions",
                "search": "GET /binance/search?keyword=BTC",
                "top_movers": "GET /binance/top-movers?limit=10",
                "market_factors": "GET /binance/analysis/market-factors?symbol=BTC"
            },
            "coingecko": {
                "price": "GET /coingecko/price?coin_ids=bitcoin,ethereum",
                "coin_data": "GET /coingecko/coin?coin_id=bitcoin",
                "search": "GET /coingecko/search?query=bitcoin",
                "trending": "GET /coingecko/trending"
            }
        },
        "mcp_usage": {
            "binance_endpoint": "POST /mcp",
            "coingecko_endpoint": "POST /mcp-coingecko",
            "example": {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "get_spot_price",
                    "arguments": {"symbol": "BTC"}
                }
            }
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
