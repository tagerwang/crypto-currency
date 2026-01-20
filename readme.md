# 🪙 加密货币 MCP 服务器

> 为 Kiro/Claude 提供币安和 CoinGecko API 的 MCP (Model Context Protocol) 服务器

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ 特性

- � **统一服务器架构** - 同时支持 REST API 和 MCP 协议
- 📊 **币安 API** - 现货/合约价格、资金费率、技术分析、Alpha 代币
- 🪙 **CoinGecko API** - 价格查询、热门币种、币种搜索
- 🔒 **HTTPS 支持** - Let's Encrypt 自动证书
- 🌐 **免费域名** - DuckDNS 集成
- 🔧 **易于部署** - 一键部署脚本

---

## � 包含的服务

### 1. Binance MCP

币安交易所全功能数据分析服务器（模块化架构）

**核心功能**：

| 类别 | 功能 |
|------|------|
| **价格查询** | 现货/合约价格、24小时行情、批量查询 |
| **K线分析** | K线数据、形态识别（十字星、锤子线等） |
| **技术分析** | RSI、MACD、布林带、支撑阻力位 |
| **合约分析** | 资金费率、现货合约价差、套利机会 |
| **Alpha代币** | 实时空投、竞赛追踪、价值分析 |
| **市场数据** | 交易对搜索、涨跌幅排行 |

### 2. CoinGecko MCP

获取加密货币市场数据，支持所有主流币种

**核心功能**：
- 实时价格查询（BTC、ETH、BNB 等）
- 7日涨跌概率分析
- 热门币种查询
- 币种搜索

---

## 🚀 快速开始

### 方式 1：远程服务器（推荐）

```bash
# 1. 部署到服务器
scp -r ./* root@YOUR_SERVER:/opt/mcp-crypto-api/
ssh root@YOUR_SERVER "cd /opt/mcp-crypto-api && ./quick_deploy.sh"

# 2. 配置 Kiro
cat > ~/.kiro/settings/mcp.json << 'EOF'
{
  "mcpServers": {
    "binance-remote": {
      "type": "http",
      "url": "https://your-domain.duckdns.org/mcp"
    },
    "coingecko-remote": {
      "type": "http",
      "url": "https://your-domain.duckdns.org/mcp-coingecko"
    }
  }
}
EOF

# 3. 重启 Kiro 并测试
```

### 方式 2：本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务器
python3 unified_server.py

# 3. 配置 Kiro（本地）
{
  "binance-local": {
    "command": "python3",
    "args": ["-m", "binance_mcp"],
    "cwd": "/path/to/project"
  }
}
```

---

## � 文档

| 文档 | 说明 |
|------|------|
| `DEPLOYMENT_GUIDE.md` | 部署指南（快速开始） |
| `SSL_SETUP_GUIDE.md` | SSL 完整配置（DuckDNS、证书、隧道） |
| `LOCAL_WORKFLOW.md` | 本地开发工作流 |
| `完整部署文档.md` | 详细部署文档（架构、原理） |
| `MCP_DEVELOPMENT_GUIDE.md` | MCP 开发指南 |
| `QUICK_START.md` | 三步快速部署 |
| `CHANGELOG.md` | 更新日志 |

---

## 🛠️ 项目结构

```
.
├── binance_mcp/              # 币安 MCP 模块（模块化包）
│   ├── __init__.py
│   ├── api.py               # API 调用
│   ├── analysis.py          # 技术分析
│   ├── alpha.py             # Alpha 代币
│   └── server.py            # MCP 服务器
├── coingecko_mcp.py         # CoinGecko MCP 服务
├── unified_server.py        # 统一服务器（REST + MCP）
├── mcp_http_server.py       # HTTP 服务器（旧版）
├── setup_ssl_for_duckdns.sh # SSL 配置脚本
├── check_dns.sh             # DNS 检查工具
├── start_tunnel.sh          # SSH 隧道启动
├── quick_deploy.sh          # 快速部署脚本
└── requirements.txt         # Python 依赖
```

---

## 🔧 配置示例

### 远程 MCP（HTTPS）

```json
{
  "mcpServers": {
    "binance-remote": {
      "type": "http",
      "url": "https://tager.duckdns.org/mcp",
      "description": "Binance API"
    }
  }
}
```

### SSH 隧道

```bash
# 启动隧道
ssh -f -N -L 8443:localhost:443 root@YOUR_SERVER

# 配置
{
  "url": "https://localhost:8443/mcp"
}
```

---

## 📊 使用示例

在 Kiro 中询问：

```
你：BNB现价多少？
Kiro：BNB 当前价格为 $692.50

你：分析 BTC 的技术指标
Kiro：[调用 comprehensive_analysis 工具]
      BTC 技术分析：
      - RSI: 65.2（中性偏多）
      - MACD: 金叉信号
      - 布林带: 价格接近上轨
      ...

你：有哪些 Alpha 空投正在进行？
Kiro：[调用 get_realtime_alpha_airdrops 工具]
      当前进行中的空投：
      1. TIMI - 总价值 $12,500
      2. H - 总价值 $8,900
      ...
```

---

## 🔄 更新部署

```bash
# 方式 1：使用部署脚本
./deploy_simple.sh

# 方式 2：手动部署
rsync -avz ./* root@YOUR_SERVER:/opt/mcp-crypto-api/
ssh root@YOUR_SERVER "supervisorctl restart mcp-crypto-api"

# 方式 3：使用 Git
git push
ssh root@YOUR_SERVER "cd /opt/mcp-crypto-api && git pull && supervisorctl restart mcp-crypto-api"
```

---

## 🐛 故障排查

```bash
# 查看服务状态
ssh root@YOUR_SERVER
sudo systemctl status mcp-crypto-api

# 查看日志
sudo journalctl -u mcp-crypto-api -n 50

# 重启服务
sudo systemctl restart mcp-crypto-api

# 测试 API
curl https://your-domain.duckdns.org/health
```

---

## 📝 许可证

MIT License

---

## � 致谢

- [Anthropic](https://www.anthropic.com/) - MCP 协议
- [Binance](https://www.binance.com/) - 币安 API
- [CoinGecko](https://www.coingecko.com/) - CoinGecko API
- [DuckDNS](https://www.duckdns.org/) - 免费域名服务
- [Let's Encrypt](https://letsencrypt.org/) - 免费 SSL 证书

---

**快速链接**：
- 📖 [部署指南](DEPLOYMENT_GUIDE.md)
- 🔒 [SSL 配置](SSL_SETUP_GUIDE.md)
- 💻 [本地开发](LOCAL_WORKFLOW.md)
- 📚 [完整文档](完整部署文档.md)
