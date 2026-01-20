#!/bin/bash
# 为 DuckDNS 域名配置 SSL 证书

set -e

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ 错误: .env 文件不存在"
    echo "请复制 .env.example 为 .env 并填入真实值"
    exit 1
fi

# 检查必需的环境变量
if [ -z "$DOMAIN" ] || [ -z "$SERVER_IP" ]; then
    echo "❌ 错误: 缺少必需的环境变量"
    echo "请在 .env 文件中设置 DOMAIN 和 SERVER_IP"
    exit 1
fi

echo "=========================================="
echo "  配置 SSL 证书"
echo "  域名: $DOMAIN"
echo "=========================================="
echo ""

# 检查 DNS 是否生效
echo "🔍 步骤 1/5: 检查 DNS..."
DNS_IP=$(dig +short $DOMAIN | tail -n1)

if [ "$DNS_IP" != "$SERVER_IP" ]; then
    echo "❌ DNS 尚未生效或配置错误"
    echo "   当前解析: $DNS_IP"
    echo "   期望解析: $SERVER_IP"
    echo ""
    echo "请在 DuckDNS 控制面板确认 IP 设置正确"
    echo "检查命令: dig +short $DOMAIN"
    exit 1
fi

echo "✅ DNS 已生效: $DNS_IP"
echo ""

# 安装 certbot（如果未安装）
echo "📦 步骤 2/5: 检查 certbot..."
if ! command -v certbot &> /dev/null; then
    echo "正在安装 certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
else
    echo "✅ certbot 已安装"
fi
echo ""

# 获取 SSL 证书
echo "🔐 步骤 3/5: 获取 SSL 证书..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email certbot@$DOMAIN

if [ $? -ne 0 ]; then
    echo "❌ 证书获取失败"
    echo ""
    echo "可能的原因："
    echo "1. DNS 未完全生效，请等待几分钟后重试"
    echo "2. 防火墙阻止了 80/443 端口"
    echo "3. Nginx 配置有误"
    echo ""
    echo "故障排查："
    echo "  sudo ufw allow 80/tcp"
    echo "  sudo ufw allow 443/tcp"
    echo "  sudo nginx -t"
    echo "  sudo systemctl restart nginx"
    exit 1
fi

echo ""
echo "🔄 步骤 4/5: 配置自动续期..."
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo "✅ 步骤 5/5: 测试证书..."
certbot certificates

echo ""
echo "=========================================="
echo "  ✅ 配置完成！"
echo "=========================================="
echo ""
echo "🌍 访问地址："
echo "   https://$DOMAIN/"
echo "   https://$DOMAIN/mcp"
echo "   https://$DOMAIN/mcp-coingecko"
echo ""
echo "🧪 测试命令："
echo "   curl https://$DOMAIN/health"
echo ""
echo "🔧 Kiro 配置："
echo '   {
     "mcpServers": {
       "binance-remote": {
         "type": "http",
         "url": "https://'$DOMAIN'/mcp",
         "description": "Binance API - DuckDNS",
         "autoApprove": ["get_spot_price", "get_ticker_24h"]
       },
       "coingecko-remote": {
         "type": "http",
         "url": "https://'$DOMAIN'/mcp-coingecko",
         "description": "CoinGecko API - DuckDNS",
         "autoApprove": ["get_price", "get_trending"]
       }
     }
   }'
echo ""
echo "📝 证书信息："
echo "   有效期: 90 天"
echo "   自动续期: 已启用"
echo "   下次续期检查: $(systemctl list-timers | grep certbot | awk '{print $1, $2, $3}')"
echo ""
