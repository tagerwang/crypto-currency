#!/bin/bash
# 检查 DNS 是否生效

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

EXPECTED_IP="$SERVER_IP"

echo "=========================================="
echo "  检查 DNS 状态"
echo "=========================================="
echo ""
echo "域名: $DOMAIN"
echo "期望 IP: $EXPECTED_IP"
echo ""

# 使用多个 DNS 服务器检查
echo "📡 检查 DNS 解析..."
echo ""

# Google DNS
echo "1. Google DNS (8.8.8.8):"
GOOGLE_IP=$(dig @8.8.8.8 +short $DOMAIN | tail -n1)
echo "   解析结果: $GOOGLE_IP"
if [ "$GOOGLE_IP" = "$EXPECTED_IP" ]; then
    echo "   状态: ✅ 正确"
else
    echo "   状态: ❌ 未生效"
fi
echo ""

# Cloudflare DNS
echo "2. Cloudflare DNS (1.1.1.1):"
CF_IP=$(dig @1.1.1.1 +short $DOMAIN | tail -n1)
echo "   解析结果: $CF_IP"
if [ "$CF_IP" = "$EXPECTED_IP" ]; then
    echo "   状态: ✅ 正确"
else
    echo "   状态: ❌ 未生效"
fi
echo ""

# 本地 DNS
echo "3. 本地 DNS:"
LOCAL_IP=$(dig +short $DOMAIN | tail -n1)
echo "   解析结果: $LOCAL_IP"
if [ "$LOCAL_IP" = "$EXPECTED_IP" ]; then
    echo "   状态: ✅ 正确"
else
    echo "   状态: ❌ 未生效"
fi
echo ""

# 总结
echo "=========================================="
if [ "$GOOGLE_IP" = "$EXPECTED_IP" ] && [ "$CF_IP" = "$EXPECTED_IP" ] && [ "$LOCAL_IP" = "$EXPECTED_IP" ]; then
    echo "  ✅ DNS 已完全生效！"
    echo "=========================================="
    echo ""
    echo "可以运行以下命令配置 SSL："
    echo "  scp setup_ssl_for_duckdns.sh root@$SERVER_IP:/opt/mcp-crypto-api/"
    echo "  ssh root@$SERVER_IP"
    echo "  cd /opt/mcp-crypto-api"
    echo "  sudo ./setup_ssl_for_duckdns.sh"
elif [ "$GOOGLE_IP" = "$EXPECTED_IP" ] || [ "$CF_IP" = "$EXPECTED_IP" ]; then
    echo "  ⏳ DNS 正在生效中..."
    echo "=========================================="
    echo ""
    echo "部分 DNS 服务器已更新，请等待全部生效"
    echo "预计时间: 1-6 小时"
else
    echo "  ❌ DNS 尚未生效"
    echo "=========================================="
    echo ""
    echo "请等待 6-12 小时后重试"
    echo "或者检查 Vultr 控制面板的 DNS 配置"
fi
echo ""
