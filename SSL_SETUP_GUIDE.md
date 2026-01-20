# SSL 配置完整指南

> 包含 DuckDNS 配置、SSL 证书对比、脚本学习等所有 SSL 相关内容

---

## 📋 目录

1. [DuckDNS 配置](#duckdns-配置)
2. [SSL 证书对比](#ssl-证书对比)
3. [配置脚本学习](#配置脚本学习)
4. [SSH 隧道方案](#ssh-隧道方案)

---

## DuckDNS 配置

> **域名**: `tager.duckdns.org`  
> **服务器 IP**: `45.32.114.70`

### 📊 当前状态

✅ **DuckDNS 已配置**  
⏳ **DNS 正在传播中**（本地已生效，全球 DNS 需要 5-30 分钟）

### 🔍 检查 DNS 状态

```bash
./check_dns.sh
```

或手动检查：

```bash
dig +short tager.duckdns.org
# 应该返回: 45.32.114.70
```

### 🚀 DNS 生效后的配置步骤

#### 方式 A：一键配置（推荐）

```bash
scp setup_ssl_for_duckdns.sh root@45.32.114.70:/opt/mcp-crypto-api/
ssh root@45.32.114.70 "cd /opt/mcp-crypto-api && chmod +x setup_ssl_for_duckdns.sh && sudo ./setup_ssl_for_duckdns.sh"
```

#### 方式 B：分步配置

```bash
# 1. 上传脚本
scp setup_ssl_for_duckdns.sh root@45.32.114.70:/opt/mcp-crypto-api/

# 2. SSH 到服务器
ssh root@45.32.114.70

# 3. 运行配置脚本
cd /opt/mcp-crypto-api
chmod +x setup_ssl_for_duckdns.sh
sudo ./setup_ssl_for_duckdns.sh
```

### ✅ 配置完成后

#### 1. 测试 HTTPS

```bash
curl https://tager.duckdns.org/health
```

#### 2. 停止 SSH 隧道

```bash
pkill -f "ssh.*8443:localhost:443"
```

#### 3. 配置 Kiro

```json
{
  "mcpServers": {
    "binance-remote": {
      "type": "http",
      "url": "https://tager.duckdns.org/mcp",
      "description": "Binance API - DuckDNS"
    },
    "coingecko-remote": {
      "type": "http",
      "url": "https://tager.duckdns.org/mcp-coingecko",
      "description": "CoinGecko API - DuckDNS"
    }
  }
}
```

---

## SSL 证书对比

### 🔐 证书类型对比

#### 自签名证书（之前）

```
颁发者：你自己的服务器
验证：❌ 无第三方验证
信任：❌ 浏览器/客户端不信任
用途：仅用于测试和开发
```

**特点**：
- ❌ 浏览器显示"不安全"警告
- ❌ Kiro 拒绝连接
- ✅ 免费、立即生成

#### Let's Encrypt 证书（现在）

```
颁发者：Let's Encrypt（受信任的 CA）
验证：✅ 通过 HTTP-01 或 DNS-01 验证
信任：✅ 所有主流浏览器和客户端信任
用途：生产环境
```

**特点**：
- ✅ 浏览器显示 🔒 安全
- ✅ Kiro 完全支持
- ✅ 免费、自动续期

### 📊 详细对比表

| 特性 | 自签名证书 | Let's Encrypt |
|------|-----------|---------------|
| **颁发者** | 自己 | Let's Encrypt CA |
| **验证方式** | 无 | HTTP-01 / DNS-01 |
| **浏览器信任** | ❌ 不信任 | ✅ 信任 |
| **Kiro 支持** | ❌ 不支持 | ✅ 支持 |
| **有效期** | 自定义 | 90天 |
| **续期** | 手动 | 自动 |
| **费用** | 免费 | 免费 |
| **适用场景** | 测试/开发 | 生产环境 |

### 🔍 为什么之前不行？

**Kiro 的安全策略**：

```javascript
// ✅ 支持的配置
{
  "url": "https://domain.com/mcp"  // 有效证书
}

// ❌ 不支持的配置
{
  "url": "https://45.32.114.70/mcp",  // 自签名证书
  "allowInsecure": true  // Kiro 不支持此选项
}
```

### 🛠️ 如何获得有效证书

#### HTTP-01 验证（我们使用的）

```
1. Certbot 在服务器上创建验证文件
2. Let's Encrypt 访问验证文件
3. 验证成功 → 颁发证书
```

#### 配置过程

```bash
# 运行 Certbot
certbot --nginx -d tager.duckdns.org \
    --non-interactive \
    --agree-tos \
    --email certbot@tager.duckdns.org
```

**Certbot 做了什么**：
1. ✅ 检查 DNS 解析
2. ✅ 创建验证文件
3. ✅ Let's Encrypt 验证
4. ✅ 下载证书
5. ✅ 自动修改 Nginx 配置
6. ✅ 配置自动续期

---

## 配置脚本学习

### 脚本功能

`setup_ssl_for_duckdns.sh` 是一个通用的域名 SSL 配置脚本。

### 核心代码解析

#### 1. 脚本头部和错误处理

```bash
#!/bin/bash
set -e
set -u
set -o pipefail
```

**学习要点**：
- `set -e` - 遇到错误立即退出
- `set -u` - 使用未定义变量时报错
- `set -o pipefail` - 管道命令中任何一个失败都返回失败

#### 2. 颜色输出函数

```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}
```

**ANSI 颜色代码表**：

| 颜色 | 代码 | 用途 |
|------|------|------|
| 红色 | `\033[0;31m` | 错误信息 |
| 绿色 | `\033[0;32m` | 成功信息 |
| 黄色 | `\033[1;33m` | 警告信息 |
| 重置 | `\033[0m` | 恢复默认颜色 |

#### 3. DNS 检查

```bash
SERVER_IP=$(curl -s ifconfig.me || echo "")
DNS_IP=$(dig +short "$DOMAIN" | tail -n1 || echo "")

if [ "$DNS_IP" != "$SERVER_IP" ]; then
    print_warning "IP 不匹配"
fi
```

**为什么重要**：Let's Encrypt 需要通过 HTTP-01 验证，DNS 必须正确解析。

#### 4. Certbot 证书获取

```bash
certbot --nginx \
    -d "$DOMAIN" \
    --non-interactive \
    --agree-tos \
    --email "$EMAIL" \
    --redirect \
    --hsts \
    --staple-ocsp
```

**参数详解**：

| 参数 | 说明 |
|------|------|
| `--nginx` | 使用 Nginx 插件，自动配置 |
| `-d $DOMAIN` | 指定域名 |
| `--non-interactive` | 非交互模式 |
| `--agree-tos` | 同意服务条款 |
| `--redirect` | 自动设置 HTTP → HTTPS 重定向 |
| `--hsts` | 启用 HSTS（强制 HTTPS） |
| `--staple-ocsp` | 启用 OCSP Stapling |

#### 5. 自动续期配置

```bash
systemctl enable certbot.timer
systemctl start certbot.timer
certbot renew --dry-run
```

**续期机制**：
- 每天运行两次
- 检查证书是否在 30 天内过期
- 自动续期并重启 Nginx

---

## SSH 隧道方案

> 适用场景：DNS 生效前的临时方案，或作为长期稳定方案

### 工作原理

```
你的电脑 (macOS)
    ↓ HTTPS 请求到 localhost:8443
本地端口 8443
    ↓ SSH 加密隧道
远程服务器端口 443
    ↓ Nginx + unified_server.py
MCP 服务
```

### 快速开始

#### 1. 启动 SSH 隧道

```bash
ssh -f -N -L 8443:localhost:443 root@45.32.114.70
```

**参数说明**：
- `-f`：后台运行
- `-N`：不执行远程命令
- `-L 8443:localhost:443`：端口转发

#### 2. 验证隧道

```bash
# 检查隧道进程
ps aux | grep "ssh.*8443"

# 测试连接
curl -k https://localhost:8443/health
```

#### 3. 配置 Kiro

```json
{
  "mcpServers": {
    "binance-remote": {
      "type": "http",
      "url": "https://localhost:8443/mcp",
      "description": "Binance API - 通过SSH隧道"
    },
    "coingecko-remote": {
      "type": "http",
      "url": "https://localhost:8443/mcp-coingecko",
      "description": "CoinGecko API - 通过SSH隧道"
    }
  }
}
```

### 自动化配置

#### macOS - 开机自动启动

```bash
cat > ~/Library/LaunchAgents/com.mcp.tunnel.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.mcp.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/ssh</string>
        <string>-N</string>
        <string>-L</string>
        <string>8443:localhost:443</string>
        <string>root@45.32.114.70</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.mcp.tunnel.plist
```

### 故障排查

#### 问题 1：端口已被占用

```bash
# 查找占用进程
lsof -i :8443

# 杀死进程
kill -9 <PID>
```

#### 问题 2：SSH 连接断开

**配置 SSH 保活**：

```bash
# 编辑 ~/.ssh/config
Host 45.32.114.70
    ServerAliveInterval 60
    ServerAliveCountMax 3
    TCPKeepAlive yes
```

#### 问题 3：需要输入密码

**配置 SSH 密钥认证**：

```bash
# 生成密钥
ssh-keygen -t rsa -b 4096

# 复制公钥到服务器
ssh-copy-id root@45.32.114.70
```

### 优缺点分析

#### 优点

| 优点 | 说明 |
|------|------|
| ✅ **简单可靠** | 5分钟配置完成 |
| ✅ **加密传输** | SSH 协议加密 |
| ✅ **Kiro 完全支持** | 使用 localhost |
| ✅ **免费** | 无需域名或证书 |

#### 缺点

| 缺点 | 说明 | 解决方案 |
|------|------|----------|
| ⚠️ **需要保持连接** | SSH 断开后失效 | 自动重连脚本 |
| ⚠️ **单设备使用** | 每个设备单独配置 | 每台设备启动隧道 |
| ⚠️ **手动启动** | 重启后需重新启动 | 配置开机自动启动 |

### 管理命令

```bash
# 启动隧道
ssh -f -N -L 8443:localhost:443 root@45.32.114.70

# 检查状态
ps aux | grep "ssh.*8443"

# 停止隧道
pkill -f "ssh.*8443:localhost:443"

# 重启隧道
pkill -f "ssh.*8443:localhost:443" && sleep 2 && ssh -f -N -L 8443:localhost:443 root@45.32.114.70
```

---

## 🎯 总结

### 推荐方案

1. **生产环境**：使用 DuckDNS + Let's Encrypt
   - 免费域名和证书
   - 自动续期
   - 跨设备使用

2. **临时/测试**：使用 SSH 隧道
   - 快速配置
   - 无需域名
   - 适合个人使用

### 快速决策

- **有域名** → 使用 Let's Encrypt
- **无域名** → 使用 DuckDNS + Let's Encrypt
- **临时使用** → 使用 SSH 隧道
- **不想配置** → 使用 SSH 隧道

---

**文档整合完成！** 🎉
