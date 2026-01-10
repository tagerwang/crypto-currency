# 🪙 Crypto MCP Servers

> 加密货币数据 MCP 服务器集合，支持 Cursor、Claude Desktop 等 AI 工具

---

## 📦 包含的服务器

### 1. CoinGecko MCP (`coingecko_mcp.py`)

获取加密货币市场数据，支持所有主流币种。

**功能特性**：
- 🔍 获取实时价格（BTC、ETH、BNB 等）
- 📊 7日涨跌概率分析
- 🔥 热门币种查询
- 🔎 币种搜索

### 2. Binance MCP (`binance_mcp/`) ⭐ 模块化重构

币安交易所全功能数据分析服务器（已模块化拆分）。

**功能特性**：

| 类别 | 功能 | 工具名称 |
|------|------|----------|
| **价格查询** | 现货实时价格 | `get_spot_price` |
| | 24小时行情 | `get_ticker_24h` |
| | 批量价格查询 | `get_multiple_tickers` |
| **K线分析** | 获取K线数据 | `get_klines` |
| | K线形态识别 | `analyze_kline_patterns` |
| **技术分析** | 综合分析（RSI/MACD/布林带） | `comprehensive_analysis` |
| | 影响因素分析 | `analyze_market_factors` |
| **合约分析** | 合约价格 | `get_futures_price` |
| | 资金费率 | `get_funding_rate` |
| | 现货合约价差 | `analyze_spot_vs_futures` |
| **Alpha分析** | Alpha代币列表 | `get_alpha_tokens_list` |
| | Alpha代币分析 | `analyze_alpha_token` |
| | 进行中的竞赛 | `get_active_alpha_competitions` |
| **市场数据** | 搜索交易对 | `search_symbols` |
| | 涨跌幅排行 | `get_top_gainers_losers` |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置 Cursor

打开 Cursor 设置，找到 MCP Servers 配置，添加：

```json
{
  "mcpServers": {
    "binance": {
      "command": "python3",
      "args": ["-m", "binance_mcp"],
      "cwd": "/你的路径/crypto",
      "env": {}
    },
    "coingecko": {
      "command": "python3", 
      "args": ["/你的路径/crypto/coingecko_mcp.py"],
      "env": {}
    }
  }
}
```

或者使用旧的单文件方式（兼容）：

```json
{
  "mcpServers": {
    "binance": {
      "command": "python3",
      "args": ["/你的路径/crypto/binance_mcp.py"],
      "env": {}
    }
  }
}
```

### 3. 重启 Cursor

配置完成后重启 Cursor 即可使用。

---

## 📖 使用示例

### 基础查询

```
"帮我查询 BTC 和 ETH 的当前价格"
"查看 SOL 的24小时涨跌幅"
"BNB 今天表现怎么样？"
```

### 技术分析

```
"帮我分析一下 BTC 的技术面"
"ETH 的 RSI 和 MACD 指标怎么样？"
"分析 SOL 的K线形态"
"BNB 的支撑位和阻力位在哪里？"
```

### 趋势预测

```
"BTC 接下来是涨还是跌？"
"分析一下 ETH 的涨跌概率"
"SOL 的未来趋势如何？"
```

### 合约分析

```
"查看 BTC 的资金费率"
"ETH 现货和合约价差多少？"
"有没有期现套利机会？"
```

### Alpha 竞赛分析

```
"帮我查询进行中的 Alpha 竞赛"
"查看 Alpha 代币列表"
"分析 BLUAI 这个 Alpha 代币"
```

### 市场概览

```
"今天币安涨幅最大的币是什么？"
"哪些币跌得最多？"
"搜索一下和 AI 相关的币"
```

---

## 🔧 技术指标说明

### RSI (相对强弱指数)

| 数值范围 | 含义 | 建议 |
|---------|------|------|
| < 30 | 超卖 | 可能反弹，关注买入机会 |
| 30-70 | 正常 | 趋势延续 |
| > 70 | 超买 | 可能回调，注意风险 |

### MACD

| 信号 | 含义 |
|------|------|
| MACD > 信号线 | 多头动能 |
| MACD < 信号线 | 空头动能 |
| 柱状图由负转正 | 金叉，买入信号 |
| 柱状图由正转负 | 死叉，卖出信号 |

### 布林带

| 位置 | 含义 |
|------|------|
| 触及上轨 | 短期可能回调 |
| 触及下轨 | 短期可能反弹 |
| 带宽收窄 | 即将突破 |

---

## 📂 文件结构

```
crypto/
├── binance_mcp/                 # 币安 MCP 服务器（模块化）
│   ├── __init__.py             # 模块入口，导出所有功能
│   ├── __main__.py             # 支持 python -m binance_mcp 运行
│   ├── config.py               # 配置：API地址、常量 (~92行)
│   ├── utils.py                # 工具：格式化、转换函数 (~57行)
│   ├── indicators.py           # 技术指标：RSI、MACD、布林带 (~289行)
│   ├── api.py                  # API调用：现货、合约、K线 (~320行)
│   ├── analysis.py             # 分析：综合分析、K线形态 (~291行)
│   ├── alpha_realtime.py       # Alpha实时数据获取 (~159行)
│   ├── alpha_config.py         # Alpha配置管理 (~173行)
│   ├── alpha.py                # Alpha分析入口 (~283行)
│   └── server.py               # MCP服务器主循环 (~450行)
│
├── binance_mcp.py              # [兼容] 旧版单文件（已弃用）
├── coingecko_mcp.py            # CoinGecko MCP 服务器
├── alpha_competitions.json     # Alpha 竞赛配置（手动更新）
├── MCP_DEVELOPMENT_GUIDE.md    # MCP 开发指南
└── readme.md                   # 本文档
```

---

## 🔄 更新 Alpha 竞赛数据

由于币安没有公开的 Alpha 竞赛 API，需要手动更新：

1. 访问 [币安 Alpha 活动页面](https://www.binance.com/zh-CN/activity/alpha)
2. 编辑 `alpha_competitions.json` 添加新活动
3. 在 `binance_mcp.py` 中更新 `ALPHA_TOKENS` 字典

示例格式：

```python
ALPHA_TOKENS = {
    "NEW_TOKEN": {
        "name": "New Token Name",
        "launch_date": "2026-01-15",
        "min_points": 200,
        "airdrop_amount": 1000,
        "status": "进行中"
    }
}
```

---

## ⚠️ 免责声明

- 本工具仅供学习和参考，不构成任何投资建议
- 加密货币市场风险极高，请谨慎投资
- 技术分析仅供参考，市场可能出现与预测相反的走势
- 请自行承担投资决策带来的风险

---

## 📝 更新日志

### v1.1.0 (2026-01-10)

- 🔧 **模块化重构**：将 `binance_mcp.py` (2000+行) 拆分为独立模块
  - `config.py` - 配置常量
  - `utils.py` - 工具函数
  - `indicators.py` - 技术指标计算
  - `api.py` - 币安API调用
  - `analysis.py` - 综合分析功能
  - `alpha_realtime.py` - 实时Alpha数据
  - `alpha_config.py` - 配置管理
  - `alpha.py` - Alpha分析入口
  - `server.py` - MCP服务器
- 📦 支持 `python -m binance_mcp` 方式运行
- 🔄 保留旧版单文件以保持向后兼容

### v1.0.0 (2026-01-10)

- ✅ 新增币安 MCP 服务器
- ✅ 支持现货价格查询
- ✅ 支持24小时行情数据
- ✅ 支持K线数据获取
- ✅ 支持技术指标计算（RSI、MACD、布林带）
- ✅ 支持趋势分析和涨跌预测
- ✅ 支持K线形态识别
- ✅ 支持合约价格和资金费率查询
- ✅ 支持现货合约价差分析
- ✅ 支持 Alpha 代币分析
- ✅ 支持涨跌幅排行榜
- ✅ 支持交易对搜索

---

## 🔗 相关链接

- [MCP 官方文档](https://modelcontextprotocol.io)
- [币安 API 文档](https://binance-docs.github.io/apidocs/)
- [CoinGecko API 文档](https://docs.coingecko.com/)

---

*Made with ❤️ for crypto enthusiasts*
