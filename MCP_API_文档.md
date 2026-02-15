# MCP 加密货币数据服务 API 文档

版本: 2.0.0  
更新时间: 2026-02-14

---

## 目录

- [服务概览](#服务概览)
- [接入方式](#接入方式)
- [Binance MCP 服务](#binance-mcp-服务)
  - [现货市场](#现货市场)
  - [合约市场](#合约市场)
  - [Alpha 市场](#alpha-市场)
  - [技术分析](#技术分析)
- [CoinGecko MCP 服务](#coingecko-mcp-服务)
- [响应格式](#响应格式)
- [错误处理](#错误处理)

---

## 服务概览

| 服务 | 类型 | 工具数 | 说明 |
|------|------|--------|------|
| Binance MCP | 现货 + 合约 + Alpha | 34 | 币安交易所数据，含价格、K线、技术分析、资金费率等 |
| CoinGecko MCP | 行情聚合 | 4 | 市值、价格、趋势、搜索（含市值数据） |

---

## 接入方式

### 1. MCP JSON-RPC 2.0 协议（完整能力）

**入口**：`POST http://localhost:8080/mcp`

**请求格式**：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "工具名",
    "arguments": { "参数": "值" }
  }
}
```

**响应格式**：

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"数据JSON字符串\"}"
      }
    ]
  }
}
```

### 2. REST API（部分工具）

**入口**：`http://localhost:8080/binance/*` 或 `/coingecko/*`

直接 GET 请求，Query String 传参，返回 JSON。

> 注意：`get_multiple_tickers` 和 `add_alpha_competition` 仅支持 MCP 协议，没有 REST 接口。

---

## Binance MCP 服务

总计 **34 个工具**，分为现货、合约、Alpha、技术分析四大类。

---

## 现货市场

### get_spot_price

获取现货实时价格（现货优先，不存在时尝试 Alpha）。

**MCP 调用**：

```json
{
  "method": "tools/call",
  "params": {
    "name": "get_spot_price",
    "arguments": { "symbol": "BTC" }
  }
}
```

**REST API**：

```
GET /binance/spot/price?symbol=BTC
```

**响应示例**：

```json
{
  "symbol": "BTCUSDT",
  "market": "现货",
  "price": 97500.5,
  "price_formatted": "$97,500.5000"
}
```

---

### get_ticker_24h

获取 24 小时行情（现货优先 → Alpha → 合约）。

**参数**：`symbol`（必填）

**MCP**：

```json
{
  "name": "get_ticker_24h",
  "arguments": { "symbol": "ETH" }
}
```

**REST**：

```
GET /binance/ticker/24h?symbol=ETH
```

**响应字段**：

- `price`、`price_formatted` - 当前价
- `price_change_percent`、`price_change_display` - 涨跌幅
- `quote_volume_24h`、`quote_volume_formatted` - 24h 成交额
- `high_24h`、`low_24h` - 24h 高低
- `market` - "现货" / "合约" / "Alpha"

---

### get_multiple_tickers

批量获取多个交易对的 24h 行情。

**参数**：`symbols`（数组，必填）

**MCP**：

```json
{
  "name": "get_multiple_tickers",
  "arguments": { "symbols": ["BTC", "ETH", "BNB"] }
}
```

**REST**：❌ 无

---

### get_klines

获取现货 K 线数据（现货优先 → Alpha → 合约）。

**参数**：
- `symbol`（必填）
- `interval`（默认 1h）：`1m`, `3m`, `5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `8h`, `12h`, `1d`, `3d`, `1w`, `1M`
- `limit`（默认 100，最大 1000）

**MCP**：

```json
{
  "name": "get_klines",
  "arguments": {
    "symbol": "BTC",
    "interval": "5m",
    "limit": 200
  }
}
```

**REST**：

```
GET /binance/klines?symbol=BTC&interval=15m&limit=100
```

**响应字段**：

- `klines` 数组：`open_time`、`open`、`high`、`low`、`close`、`volume`、`close_time`、`quote_volume`、`trades`
- `interval`、`count`、`market`

---

### search_symbols

搜索现货交易对（现货 + Alpha）。

**参数**：`keyword`（必填）

**MCP/REST**：

```
GET /binance/search?keyword=BTC
```

**响应**：

```json
{
  "keyword": "BTC",
  "count": 5,
  "spot_count": 3,
  "alpha_count": 2,
  "symbols": [
    { "symbol": "BTCUSDT", "base_asset": "BTC", "market": "现货" },
    ...
  ]
}
```

---

### get_top_gainers_losers

获取现货涨跌幅排行榜。

**参数**：`limit`（默认 10）

**MCP/REST**：

```
GET /binance/top-movers?limit=20
```

**响应**：

```json
{
  "top_gainers": [
    { "symbol": "XXXUSDT", "price": "$1.23", "change": "+45.32%", "volume": "$10.5M" }
  ],
  "top_losers": [...],
  "market": "现货"
}
```

---

## 合约市场

### get_futures_price

获取合约价格（USDT 永续）。

**参数**：`symbol`（必填）

**MCP/REST**：

```
GET /binance/futures/price?symbol=BTC
```

---

### get_futures_ticker_24h

获取合约 24h 行情（直接使用合约数据，非 fallback）。

**参数**：`symbol`（必填）

**MCP**：

```json
{
  "name": "get_futures_ticker_24h",
  "arguments": { "symbol": "BTC" }
}
```

**REST**：❌ 无

**响应**：与 `get_ticker_24h` 类似，`market` 字段为 "合约"。

---

### get_futures_klines

获取合约 K 线数据。

**参数**：`symbol`、`interval`（默认 1h）、`limit`（默认 100）

**MCP**：

```json
{
  "name": "get_futures_klines",
  "arguments": {
    "symbol": "ETH",
    "interval": "5m",
    "limit": 200
  }
}
```

**REST**：❌ 无

---

### get_futures_multiple_tickers

批量获取合约 24h 行情。

**参数**：`symbols`（数组，必填）

**MCP**：

```json
{
  "name": "get_futures_multiple_tickers",
  "arguments": { "symbols": ["BTC", "ETH", "SOL"] }
}
```

**REST**：❌ 无

---

### search_futures_symbols

搜索合约交易对（仅永续合约）。

**参数**：`keyword`（必填）

**MCP**：

```json
{
  "name": "search_futures_symbols",
  "arguments": { "keyword": "BTC" }
}
```

**REST**：❌ 无

---

### get_futures_top_gainers_losers

获取合约涨跌幅排行榜。

**参数**：`limit`（默认 10）

**MCP**：

```json
{
  "name": "get_futures_top_gainers_losers",
  "arguments": { "limit": 20 }
}
```

**REST**：❌ 无

---

### get_funding_rate

获取历史结算资金费率（最新已结算费率 + 历史记录）。

**参数**：`symbol`（必填）

**MCP/REST**：

```
GET /binance/funding-rate?symbol=BTC
```

**响应字段**：
- `historical_settled_rate` - 上期已结算费率
- `annual_rate` - 年化费率
- `next_funding_time` - 下次结算时间
- `countdown` - 倒计时
- `history` - 历史记录（最近 5 期）

---

### get_realtime_funding_rate

获取实时资金费率（当前实时生效费率 + 预测费率）。

**参数**：`symbol`（必填）

**MCP/REST**：

```
GET /binance/funding-rate/realtime?symbol=BTC
```

**响应字段**：
- `current_realtime_rate` - 当前实时费率
- `predicted_next_rate` - 预测下期费率
- `annual_rate` - 年化费率

---

### get_extreme_funding_rates

获取极端资金费率的合约列表（负费率 + 正费率）。

**参数**：
- `threshold`（默认 0.1）- 费率阈值（百分比）
- `limit`（默认 20）

**MCP/REST**：

```
GET /binance/funding-rate/extreme?threshold=0.1&limit=20
```

**响应**：

```json
{
  "extreme_negative": {
    "description": "极端负费率（空头付费，做多有利）",
    "count": 15,
    "contracts": [...]
  },
  "extreme_positive": {
    "description": "极端正费率（多头付费，做空有利）",
    "count": 12,
    "contracts": [...]
  }
}
```

---

### get_mark_price

获取合约标记价格、指数价格、资金费率及下次结算时间。

**参数**：`symbol`（必填）

**MCP**：

```json
{
  "name": "get_mark_price",
  "arguments": { "symbol": "BTC" }
}
```

**REST**：❌ 无

**响应字段**：
- `mark_price`、`index_price` - 标记价、指数价
- `last_funding_rate` - 资金费率
- `next_funding_time` - 下次结算时间
- `countdown_to_settlement` - 倒计时

---

### get_open_interest

获取合约当前持仓量。

**参数**：`symbol`（必填）

**MCP**：

```json
{
  "name": "get_open_interest",
  "arguments": { "symbol": "BTC" }
}
```

**REST**：❌ 无

**响应**：

```json
{
  "symbol": "BTCUSDT",
  "market": "合约",
  "open_interest": 123456.78,
  "open_interest_formatted": "123.5K",
  "timestamp": "2026-02-14 12:00:00"
}
```

---

### get_open_interest_hist

获取合约持仓量历史。

**参数**：
- `symbol`（必填）
- `period`（默认 1h）：`5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `12h`, `1d`
- `limit`（默认 30，最大 500）

**MCP**：

```json
{
  "name": "get_open_interest_hist",
  "arguments": {
    "symbol": "ETH",
    "period": "1h",
    "limit": 50
  }
}
```

**REST**：❌ 无

**响应**：

```json
{
  "symbol": "ETHUSDT",
  "period": "1h",
  "count": 50,
  "history": [
    {
      "timestamp": "2026-02-14 12:00:00",
      "open_interest": 234567.89,
      "open_interest_value": 500000000.0
    }
  ]
}
```

---

### get_top_long_short_ratio

获取大户账户多空比（top 20% 用户）。

**参数**：
- `symbol`（必填）
- `period`（默认 1h）：`5m`, `15m`, `30m`, `1h`, `2h`, `4h`, `6h`, `12h`, `1d`
- `limit`（默认 30，最大 500）

**MCP**：

```json
{
  "name": "get_top_long_short_ratio",
  "arguments": {
    "symbol": "BTC",
    "period": "15m",
    "limit": 30
  }
}
```

**REST**：❌ 无

**响应**：

```json
{
  "symbol": "BTCUSDT",
  "period": "15m",
  "description": "大户账户多空比（持仓量前20%用户）",
  "latest_ratio": 1.25,
  "count": 30,
  "history": [
    {
      "timestamp": "2026-02-14 12:00:00",
      "long_short_ratio": 1.25,
      "long_account": "55.56%",
      "short_account": "44.44%"
    }
  ]
}
```

---

### get_top_long_short_position_ratio

获取大户持仓多空比。

**参数**：同上

**MCP**：

```json
{
  "name": "get_top_long_short_position_ratio",
  "arguments": { "symbol": "ETH", "period": "1h" }
}
```

**REST**：❌ 无

---

### get_global_long_short_ratio

获取全市场多空比。

**参数**：同上

**MCP**：

```json
{
  "name": "get_global_long_short_ratio",
  "arguments": { "symbol": "BTC", "period": "1h" }
}
```

**REST**：❌ 无

---

### get_taker_buy_sell_ratio

获取主动买卖比（taker long/short ratio）。

**参数**：同上

**MCP**：

```json
{
  "name": "get_taker_buy_sell_ratio",
  "arguments": { "symbol": "BTC", "period": "5m" }
}
```

**REST**：❌ 无

**响应**：

```json
{
  "symbol": "BTCUSDT",
  "period": "5m",
  "description": "主动买卖比（taker主动成交）",
  "latest_ratio": 1.15,
  "history": [
    {
      "timestamp": "2026-02-14 12:00:00",
      "buy_sell_ratio": 1.15,
      "buy_vol": 1234.56,
      "sell_vol": 1073.10
    }
  ]
}
```

---

### analyze_spot_vs_futures

分析现货与合约价差，判断套利机会。

**参数**：`symbol`（必填）

**MCP/REST**：

```
GET /binance/analysis/spot-vs-futures?symbol=BTC
```

**响应**：

```json
{
  "symbol": "BTC",
  "spot_price": "$97,500.00",
  "futures_price": "$97,550.00",
  "premium": "+0.0513%",
  "funding_rate": "+0.0100%",
  "analysis": {
    "market_sentiment": "偏多",
    "arbitrage_opportunity": false
  }
}
```

---

## 技术分析

### comprehensive_analysis

综合技术分析（现货，基于 1 小时 K 线）。

**参数**：`symbol`（必填）

**MCP/REST**：

```
GET /binance/analysis/comprehensive?symbol=BTC
```

**响应字段**：
- `trend_analysis` - 趋势判断
- `prediction` - 涨跌概率预测
- `technical_indicators` - RSI、MACD、布林带
- `support_resistance` - 支撑阻力位
- `summary` - 分析总结

---

### comprehensive_analysis_futures

合约版综合技术分析（基于 1 小时 K 线）。

**参数**：`symbol`（必填）

**MCP**：

```json
{
  "name": "comprehensive_analysis_futures",
  "arguments": { "symbol": "ETH" }
}
```

**REST**：❌ 无

**响应**：与 `comprehensive_analysis` 类似，`market` 字段为 "合约"。

---

### analyze_kline_patterns

K 线形态分析（现货，默认 4 小时）。

**参数**：
- `symbol`（必填）
- `interval`（默认 4h）

**MCP/REST**：

```
GET /binance/analysis/kline-patterns?symbol=BTC&interval=15m
```

**响应**：

```json
{
  "symbol": "BTCUSDT",
  "interval": "15m",
  "overall_pattern": "上升趋势",
  "recent_patterns": [
    { "pattern": "锤子线", "time": "2026-02-14 11:45:00", "type": "bullish" }
  ],
  "pattern_count": 3
}
```

---

### analyze_futures_kline_patterns

合约 K 线形态分析（默认 4 小时）。

**参数**：同上

**MCP**：

```json
{
  "name": "analyze_futures_kline_patterns",
  "arguments": { "symbol": "BTC", "interval": "5m" }
}
```

**REST**：❌ 无

---

### analyze_market_factors

分析市场影响因素（现货）：与 BTC/ETH 对比、相对强弱、成交量分析。

**参数**：`symbol`（必填）

**MCP/REST**：

```
GET /binance/analysis/market-factors?symbol=SOL
```

**响应**：

```json
{
  "symbol": "SOLUSDT",
  "market_comparison": {
    "btc_change_24h": "+2.50%",
    "vs_btc": "+5.30%",
    "relative_strength": "强于大盘"
  },
  "factors": ["📈 BTC大涨带动市场情绪", "💪 相对BTC强势 (+5.3%)"]
}
```

---

### analyze_futures_market_factors

合约市场因素分析。

**参数**：`symbol`（必填）

**MCP**：

```json
{
  "name": "analyze_futures_market_factors",
  "arguments": { "symbol": "SOL" }
}
```

**REST**：❌ 无

---

## Alpha 市场

### get_realtime_alpha_airdrops

获取币安 Alpha 空投列表（实时，含价格和价值）。

**参数**：无

**MCP/REST**：

```
GET /binance/alpha/airdrops
```

**响应**：

```json
{
  "upcoming": [...],
  "ongoing": [...],
  "ended": [...]
}
```

---

### get_alpha_tokens_list

获取 Alpha 代币列表（本地配置）。

**参数**：无

**MCP/REST**：

```
GET /binance/alpha/tokens
```

---

### analyze_alpha_token

分析 Alpha 代币：价格、涨跌、技术指标、空投价值。

**参数**：`symbol`（必填）

**MCP/REST**：

```
GET /binance/alpha/analyze?symbol=TIMI
```

**响应**：

```json
{
  "symbol": "TIMI",
  "data_source": "Binance",
  "market_data": {
    "price": "$0.123456",
    "change_24h": "+12.34%",
    "volume_24h": "$1.5M",
    "market_cap": "$50M"
  },
  "value_analysis": {...},
  "technical_analysis": {...}
}
```

---

### get_active_alpha_competitions

获取进行中的 Alpha 竞赛信息（含实时价格、总价值、单人价值）。

**参数**：无

**MCP/REST**：

```
GET /binance/alpha/competitions
```

---

### add_alpha_competition

添加新的 Alpha 竞赛到配置。

**参数**：
- `symbol`（必填）
- `name`（必填）
- `start_time`（必填）：格式 "2026-01-09 21:00:00"
- `end_time`（必填）
- `total_reward`（可选）
- `winner_count`（可选）
- `per_user_reward`（可选）
- `note`（可选）

**MCP**：

```json
{
  "name": "add_alpha_competition",
  "arguments": {
    "symbol": "NEWTOKEN",
    "name": "New Alpha 竞赛",
    "start_time": "2026-02-20 21:00:00",
    "end_time": "2026-02-27 21:00:00",
    "total_reward": 1000000,
    "winner_count": 1000,
    "per_user_reward": 1000
  }
}
```

**REST**：❌ 无

---

## CoinGecko MCP 服务

MCP 入口：`POST http://localhost:8080/mcp-coingecko`

### get_price

获取加密货币价格（支持批量，含 24h 涨跌）。

**参数**：`coin_ids`（必填，逗号分隔）

**MCP/REST**：

```
GET /coingecko/price?coin_ids=bitcoin,ethereum
```

**响应**：

```json
{
  "bitcoin": {
    "usd": 97500.5,
    "usd_24h_change": 2.34
  },
  "ethereum": {...}
}
```

---

### get_coin_data

获取币种详细信息（含市值、供应量、历史最高等）。

**参数**：`coin_id`（必填）

**MCP/REST**：

```
GET /coingecko/coin?coin_id=bitcoin
```

**响应字段**：
- `current_price` - 当前价
- `market_cap` - **市值**
- `total_volume` - 24h 成交量
- `price_change_24h`、`price_change_percentage_24h`
- `high_24h`、`low_24h`、`ath`、`atl`

---

### search_coins

搜索币种。

**参数**：`query`（必填）

**MCP/REST**：

```
GET /coingecko/search?query=bitcoin
```

---

### get_trending

获取当前热门币种。

**参数**：无

**MCP/REST**：

```
GET /coingecko/trending
```

---

## 响应格式

### MCP 成功响应

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"实际数据JSON\"}"
      }
    ]
  }
}
```

### MCP 错误响应

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32603,
    "message": "错误描述"
  }
}
```

### REST 响应

直接返回 JSON，无 MCP 包装：

```json
{
  "symbol": "BTCUSDT",
  "price": 97500.5,
  ...
}
```

---

## 错误处理

### 网络错误

```json
{
  "error": "网络连接失败，请检查网络或代理设置",
  "network_error": true,
  "stop_execution": true,
  "user_action_required": "⚠️ 检测到网络问题，请先确保VPN/代理正常连接后再重试"
}
```

### 交易对不存在

```json
{
  "error": "HTTP错误: 400",
  "symbol": "XXXUSDT"
}
```

---

## 快速查询表

| 需求 | Binance 工具 | CoinGecko 工具 |
|------|-------------|----------------|
| 价格 | get_spot_price、get_ticker_24h | get_price |
| 成交量 | get_ticker_24h（quote_volume_24h） | get_coin_data（total_volume） |
| **市值** | ❌ 无 | ✅ get_coin_data（market_cap） |
| K 线 | get_klines、get_futures_klines | ❌ 无 |
| 技术分析 | comprehensive_analysis 等 | ❌ 无 |
| 资金费率 | get_realtime_funding_rate | ❌ 无 |
| 持仓量 | get_open_interest | ❌ 无 |
| 多空比 | get_top_long_short_ratio | ❌ 无 |
| 涨跌榜 | get_top_gainers_losers | ❌ 无 |
| 热门币 | ❌ 无 | ✅ get_trending |

---

## 使用建议

1. **币安数据更准确、实时性强**，优先使用 Binance MCP
2. **市值查询必须用 CoinGecko**（币安无市值数据）
3. **短线交易**：用 `get_klines` 或 `get_futures_klines` + `interval="5m"` / `"15m"`
4. **合约特有数据**：资金费率、持仓量、多空比等仅合约有
5. **批量查询**：用 `get_multiple_tickers` 或 `get_futures_multiple_tickers`（仅 MCP）

---

## 启动服务

```bash
# 安装依赖
pip install -r requirements.txt

# 启动统一服务器（REST + MCP）
python unified_server.py

# 或仅 REST
python mcp_http_server.py
```

默认端口：**8080**

---

## 附录：所有工具列表

### Binance MCP（34 个工具）

**现货（9）**：get_spot_price, get_ticker_24h, get_multiple_tickers, get_klines, search_symbols, get_top_gainers_losers, comprehensive_analysis, analyze_kline_patterns, analyze_market_factors

**合约（17）**：get_futures_price, get_futures_ticker_24h, get_futures_klines, get_futures_multiple_tickers, search_futures_symbols, get_futures_top_gainers_losers, get_funding_rate, get_realtime_funding_rate, get_extreme_funding_rates, get_mark_price, get_open_interest, get_open_interest_hist, get_top_long_short_ratio, get_top_long_short_position_ratio, get_global_long_short_ratio, get_taker_buy_sell_ratio, analyze_spot_vs_futures, comprehensive_analysis_futures, analyze_futures_kline_patterns, analyze_futures_market_factors

**Alpha（5）**：get_realtime_alpha_airdrops, get_alpha_tokens_list, analyze_alpha_token, get_active_alpha_competitions, add_alpha_competition

**技术分析（3）**：已计入上述分类

### CoinGecko MCP（4 个工具）

get_price, get_coin_data, search_coins, get_trending

---

文档完成。如有疑问请参考项目代码或联系维护者。
