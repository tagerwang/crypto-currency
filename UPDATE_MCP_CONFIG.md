# 更新 MCP 配置为远程服务器

## 方式 1：手动更新（推荐）

1. 在 Kiro 中打开命令面板（Cmd+Shift+P）
2. 搜索 "MCP" 或 "Open MCP Settings"
3. 找到 `binance` 和 `coingecko` 配置
4. 替换为以下配置：

```json
{
  "mcpServers": {
    "binance-remote": {
      "type": "http",
      "url": "http://YOUR_SERVER_IP",
      "description": "Binance API - 远程服务器",
      "autoApprove": [
        "get_extreme_funding_rates",
        "comprehensive_analysis",
        "get_klines",
        "analyze_kline_patterns",
        "get_ticker_24h",
        "get_realtime_funding_rate",
        "search_symbols",
        "get_futures_price",
        "get_funding_rate",
        "analyze_spot_vs_futures",
        "get_alpha_tokens_list",
        "analyze_market_factors",
        "get_top_gainers_losers",
        "get_spot_price"
      ]
    },
    "coingecko-remote": {
      "type": "http",
      "url": "http://YOUR_SERVER_IP",
      "description": "CoinGecko API - 远程服务器",
      "autoApprove": [
        "get_trending",
        "search_coins",
        "get_coin_data",
        "get_price"
      ]
    },
    "crypto-com": {
      "type": "http",
      "url": "https://mcp.crypto.com/market-data/mcp"
    }
  }
}
```

## 方式 2：使用命令行

在 Kiro 终端执行：

```bash
# 备份原配置
cp ~/.kiro/settings/mcp.json ~/.kiro/settings/mcp.json.backup

# 复制新配置
cp mcp_config_remote.json ~/.kiro/settings/mcp.json
```

## 方式 3：保留本地和远程两个版本

如果你想同时保留本地和远程版本，可以这样配置：

```json
{
  "mcpServers": {
    "binance-remote": {
      "type": "http",
      "url": "http://YOUR_SERVER_IP",
      "description": "Binance API - 远程服务器（推荐）"
    },
    "binance-local": {
      "command": "/opt/homebrew/bin/python3",
      "args": ["-m", "binance_mcp"],
      "cwd": "/Users/wangtao/exercise/crypto-currency-main",
      "env": {
        "PYTHONPATH": "/Users/wangtao/exercise/crypto-currency-main"
      },
      "disabled": true,
      "description": "Binance API - 本地版本（已禁用）"
    },
    "coingecko-remote": {
      "type": "http",
      "url": "http://YOUR_SERVER_IP",
      "description": "CoinGecko API - 远程服务器（推荐）"
    },
    "coingecko-local": {
      "command": "python3",
      "args": ["/Users/wangtao/exercise/crypto-currency-main/coingecko_mcp.py"],
      "disabled": true,
      "description": "CoinGecko API - 本地版本（已禁用）"
    }
  }
}
```

这样你可以：
- 默认使用远程服务器（快速、稳定）
- 需要时启用本地版本（调试、开发）

## 配置说明

### HTTP MCP 服务器配置

```json
{
  "type": "http",
  "url": "http://YOUR_SERVER_IP"
}
```

- `type`: 设置为 "http" 表示通过 HTTP 协议访问
- `url`: 你的服务器地址

### 优势

使用远程服务器的优势：
- ✅ 不占用本地资源
- ✅ 响应速度快（服务器在新加坡，靠近交易所）
- ✅ 24/7 可用
- ✅ 多设备共享
- ✅ 统一管理和更新

## 验证配置

配置完成后：

1. 重启 Kiro 或重新加载 MCP 服务器
2. 在 Kiro 中测试：

```bash
# 测试 Binance API
curl http://YOUR_SERVER_IP/binance/spot/price?symbol=BTC

# 测试 CoinGecko API
curl http://YOUR_SERVER_IP/coingecko/trending
```

## 故障排查

如果 MCP 无法连接：

1. 检查服务器是否运行：
   ```bash
   curl http://YOUR_SERVER_IP/health
   ```

2. 检查 MCP 配置语法：
   - 确保 JSON 格式正确
   - 确保 URL 没有多余的斜杠

3. 查看 Kiro MCP 日志：
   - 在 Kiro 中打开输出面板
   - 选择 "MCP" 频道

## 切换回本地版本

如果需要切换回本地版本：

1. 将 `binance-remote` 的 `disabled` 设为 `true`
2. 将 `binance-local` 的 `disabled` 设为 `false`
3. 重新加载 MCP 服务器
