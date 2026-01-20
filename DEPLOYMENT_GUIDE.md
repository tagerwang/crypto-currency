# 部署指南

> 快速部署 MCP 加密货币服务

---

## 🚀 快速开始

### 当前配置

- **域名**：`tager.duckdns.org`
- **服务器**：`45.32.114.70`
- **SSL 证书**：Let's Encrypt（自动续期）

### 三步部署

```bash
# 1. 上传文件
scp -r ./* root@45.32.114.70:/opt/mcp-crypto-api/

# 2. SSH 到服务器
ssh root@45.32.114.70

# 3. 运行部署脚本
cd /opt/mcp-crypto-api
chmod +x quick_deploy.sh
./quick_deploy.sh
```

### Kiro 配置

编辑 `~/.kiro/settings/mcp.json`：

```json
{
  "mcpServers": {
    "binance-remote": {
      "type": "http",
      "url": "https://tager.duckdns.org/mcp",
      "description": "Binance API"
    },
    "coingecko-remote": {
      "type": "http",
      "url": "https://tager.duckdns.org/mcp-coingecko",
      "description": "CoinGecko API"
    }
  }
}
```

---

## 🌐 配置方案

### 方案 1：DuckDNS + SSL（推荐）

**优点**：免费域名、自动 SSL、跨设备使用

```bash
# 1. 检查 DNS
./check_dns.sh

# 2. 配置 SSL
scp setup_ssl_for_duckdns.sh root@45.32.114.70:/tmp/
ssh root@45.32.114.70 "cd /tmp && sudo ./setup_ssl_for_duckdns.sh"

# 3. 测试
curl https://tager.duckdns.org/health
```

**详细文档**：参见 `SSL_SETUP_GUIDE.md`

### 方案 2：SSH 隧道（临时）

**优点**：快速配置、无需域名

```bash
# 1. 启动隧道
ssh -f -N -L 8443:localhost:443 root@45.32.114.70

# 2. 配置 Kiro
{
  "url": "https://localhost:8443/mcp"
}

# 3. 测试
curl -k https://localhost:8443/health
```

**详细文档**：参见 `SSL_SETUP_GUIDE.md` 的 SSH 隧道章节

---

## 🔧 故障排查

### 服务未运行

```bash
ssh root@45.32.114.70
sudo systemctl status mcp-crypto-api
sudo systemctl restart mcp-crypto-api
```

### DNS 未解析

```bash
dig +short tager.duckdns.org
# 等待 5-30 分钟或使用 SSH 隧道
```

### 证书问题

```bash
ssh root@45.32.114.70
sudo certbot certificates
sudo certbot renew
```

---

## 📝 常用命令

```bash
# 查看服务状态
sudo systemctl status mcp-crypto-api

# 查看日志
sudo journalctl -u mcp-crypto-api -n 50

# 重启服务
sudo systemctl restart mcp-crypto-api

# 测试 API
curl https://tager.duckdns.org/health
```

---

## 📚 相关文档

- `SSL_SETUP_GUIDE.md` - SSL 完整配置（DuckDNS、证书、隧道）
- `LOCAL_WORKFLOW.md` - 本地开发工作流
- `完整部署文档.md` - 详细部署文档
- `MCP_DEVELOPMENT_GUIDE.md` - MCP 开发指南
- `QUICK_START.md` - 快速开始指南
