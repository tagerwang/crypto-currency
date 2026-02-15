#!/usr/bin/env python3
"""
MCP服务器 - JSON-RPC 2.0协议处理
"""

import json
import sys
from typing import Dict, Any

from .api import (
    get_spot_price, get_ticker_24h, get_multiple_tickers,
    get_klines, get_futures_price, get_futures_ticker_24h, get_futures_klines,
    get_futures_multiple_tickers, get_funding_rate, get_realtime_funding_rate,
    get_extreme_funding_rates, get_mark_price, get_open_interest,
    get_open_interest_hist, get_top_long_short_ratio,
    get_top_long_short_position_ratio, get_global_long_short_ratio,
    get_taker_buy_sell_ratio, analyze_spot_vs_futures,
    search_symbols, search_futures_symbols, get_top_gainers_losers,
    get_futures_top_gainers_losers
)
from .analysis import (
    comprehensive_analysis, analyze_market_factors, analyze_kline_patterns,
    comprehensive_analysis_futures, analyze_futures_kline_patterns,
    analyze_futures_market_factors
)
from .alpha import (
    get_alpha_tokens_list, analyze_alpha_token,
    get_active_alpha_competitions, add_alpha_competition
)
from .alpha_realtime import get_realtime_alpha_airdrops
from .alpha_config import auto_detect_alpha_competitions

# MCP工具定义
MCP_TOOLS = [
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
        "description": "综合技术分析（基于1小时K线）：包含趋势判断、涨跌概率预测、RSI、MACD、布林带、支撑阻力位等。⚠️ 所有指标均基于1小时周期，适用于短期交易决策",
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
        "description": "K线形态分析（默认4小时K线）：识别十字星、锤子线、上吊线、吞没形态等经典K线形态。⚠️ 默认使用4小时K线，可通过interval参数调整周期",
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
        "description": "获取历史结算资金费率（最新已结算费率 + 历史记录）- 返回historical_settled_rate字段",
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
        "name": "get_realtime_funding_rate",
        "description": "【推荐】获取实时资金费率（当前实时生效费率 + 预测费率）- 返回current_realtime_rate（当前实时费率）和predicted_next_rate（预测费率）字段，用于交易决策",
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
        "name": "get_extreme_funding_rates",
        "description": "【实时】获取极端资金费率的合约列表，筛选出负费率和正费率极端的合约",
        "inputSchema": {
            "type": "object",
            "properties": {
                "threshold": {
                    "type": "number",
                    "description": "费率阈值（百分比），默认0.1表示筛选费率>0.1%或<-0.1%的合约",
                    "default": 0.1
                },
                "limit": {
                    "type": "integer",
                    "description": "每类返回的最大数量，默认20",
                    "default": 20
                }
            }
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
    {
        "name": "get_futures_ticker_24h",
        "description": "获取合约24小时行情数据（直接使用合约数据，非现货fallback）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "交易对符号"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_futures_klines",
        "description": "获取合约K线数据",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "交易对符号"},
                "interval": {"type": "string", "description": "时间周期，默认1h", "default": "1h"},
                "limit": {"type": "integer", "description": "K线数量，最大1000", "default": 100}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_futures_multiple_tickers",
        "description": "批量获取多个合约的24小时行情",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "交易对符号数组"
                }
            },
            "required": ["symbols"]
        }
    },
    {
        "name": "search_futures_symbols",
        "description": "搜索合约交易对",
        "inputSchema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词"}
            },
            "required": ["keyword"]
        }
    },
    {
        "name": "get_futures_top_gainers_losers",
        "description": "获取合约涨跌幅排行榜",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "返回数量，默认10", "default": 10}
            }
        }
    },
    {
        "name": "get_open_interest",
        "description": "获取合约当前持仓量",
        "inputSchema": {
            "type": "object",
            "properties": {"symbol": {"type": "string", "description": "交易对符号"}},
            "required": ["symbol"]
        }
    },
    {
        "name": "get_open_interest_hist",
        "description": "获取合约持仓量历史",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "交易对符号"},
                "period": {"type": "string", "description": "周期: 5m,15m,30m,1h,2h,4h,6h,12h,1d", "default": "1h"},
                "limit": {"type": "integer", "description": "数量，默认30", "default": 30}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_top_long_short_ratio",
        "description": "获取大户账户多空比（top 20%用户）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "period": {"type": "string", "default": "1h"},
                "limit": {"type": "integer", "default": 30}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_top_long_short_position_ratio",
        "description": "获取大户持仓多空比",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "period": {"type": "string", "default": "1h"},
                "limit": {"type": "integer", "default": 30}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_global_long_short_ratio",
        "description": "获取全市场多空比",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "period": {"type": "string", "default": "1h"},
                "limit": {"type": "integer", "default": 30}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_taker_buy_sell_ratio",
        "description": "获取主动买卖比（taker long/short ratio）",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "period": {"type": "string", "default": "1h"},
                "limit": {"type": "integer", "default": 30}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "get_mark_price",
        "description": "获取合约标记价格、指数价格、资金费率及下次结算时间",
        "inputSchema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"]
        }
    },
    {
        "name": "comprehensive_analysis_futures",
        "description": "合约版综合技术分析（基于1小时K线）：RSI、MACD、布林带、支撑阻力等",
        "inputSchema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"]
        }
    },
    {
        "name": "analyze_futures_kline_patterns",
        "description": "合约K线形态分析（默认4小时）：十字星、锤子线、吞没形态等",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string"},
                "interval": {"type": "string", "default": "4h"}
            },
            "required": ["symbol"]
        }
    },
    {
        "name": "analyze_futures_market_factors",
        "description": "合约市场因素分析：与BTC/ETH对比、相对强弱",
        "inputSchema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
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
                    "version": "1.1.0"
                }
            }
        
        elif method == "tools/list":
            response["result"] = {"tools": MCP_TOOLS}

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
            elif tool_name == "get_realtime_funding_rate":
                result = get_realtime_funding_rate(arguments.get("symbol", ""))
            elif tool_name == "get_extreme_funding_rates":
                result = get_extreme_funding_rates(
                    arguments.get("threshold", 0.1),
                    arguments.get("limit", 20)
                )
            elif tool_name == "analyze_spot_vs_futures":
                result = analyze_spot_vs_futures(arguments.get("symbol", ""))
            elif tool_name == "get_futures_ticker_24h":
                result = get_futures_ticker_24h(arguments.get("symbol", ""))
            elif tool_name == "get_futures_klines":
                result = get_futures_klines(
                    arguments.get("symbol", ""),
                    arguments.get("interval", "1h"),
                    arguments.get("limit", 100)
                )
            elif tool_name == "get_futures_multiple_tickers":
                result = get_futures_multiple_tickers(arguments.get("symbols", []))
            elif tool_name == "search_futures_symbols":
                result = search_futures_symbols(arguments.get("keyword", ""))
            elif tool_name == "get_futures_top_gainers_losers":
                result = get_futures_top_gainers_losers(arguments.get("limit", 10))
            elif tool_name == "get_open_interest":
                result = get_open_interest(arguments.get("symbol", ""))
            elif tool_name == "get_open_interest_hist":
                result = get_open_interest_hist(
                    arguments.get("symbol", ""),
                    arguments.get("period", "1h"),
                    arguments.get("limit", 30)
                )
            elif tool_name == "get_top_long_short_ratio":
                result = get_top_long_short_ratio(
                    arguments.get("symbol", ""),
                    arguments.get("period", "1h"),
                    arguments.get("limit", 30)
                )
            elif tool_name == "get_top_long_short_position_ratio":
                result = get_top_long_short_position_ratio(
                    arguments.get("symbol", ""),
                    arguments.get("period", "1h"),
                    arguments.get("limit", 30)
                )
            elif tool_name == "get_global_long_short_ratio":
                result = get_global_long_short_ratio(
                    arguments.get("symbol", ""),
                    arguments.get("period", "1h"),
                    arguments.get("limit", 30)
                )
            elif tool_name == "get_taker_buy_sell_ratio":
                result = get_taker_buy_sell_ratio(
                    arguments.get("symbol", ""),
                    arguments.get("period", "1h"),
                    arguments.get("limit", 30)
                )
            elif tool_name == "get_mark_price":
                result = get_mark_price(arguments.get("symbol", ""))
            elif tool_name == "comprehensive_analysis_futures":
                result = comprehensive_analysis_futures(arguments.get("symbol", ""))
            elif tool_name == "analyze_futures_kline_patterns":
                result = analyze_futures_kline_patterns(
                    arguments.get("symbol", ""),
                    arguments.get("interval", "4h")
                )
            elif tool_name == "analyze_futures_market_factors":
                result = analyze_futures_market_factors(arguments.get("symbol", ""))
            
            # Alpha分析
            elif tool_name == "get_realtime_alpha_airdrops":
                result = get_realtime_alpha_airdrops()
            elif tool_name == "get_alpha_tokens_list":
                result = get_alpha_tokens_list()
            elif tool_name == "analyze_alpha_token":
                result = analyze_alpha_token(arguments.get("symbol", ""))
            elif tool_name == "get_active_alpha_competitions":
                # 重新加载配置
                from . import alpha
                alpha.ALPHA_COMPETITIONS = auto_detect_alpha_competitions()
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

