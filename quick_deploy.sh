#!/bin/bash
# 快速部署脚本 - 适合新手

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  MCP Crypto API 一键部署"
echo "=========================================="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "❌ 请使用 root 用户运行此脚本"
    echo "   使用命令: sudo ./quick_deploy.sh"
    exit 1
fi

# 获取当前目录
CURRENT_DIR=$(pwd)
PROJECT_DIR="/opt/mcp-crypto-api"

echo "📦 步骤 1/8: 更新系统..."
apt update -qq

echo "🐍 步骤 2/8: 安装 Python 和工具..."
apt install -y python3 python3-pip python3-venv nginx supervisor > /dev/null 2>&1

echo "📁 步骤 3/8: 准备项目目录..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

echo "🔧 步骤 4/8: 创建虚拟环境..."
python3 -m venv venv

echo "📚 步骤 5/8: 安装依赖..."
$PROJECT_DIR/venv/bin/pip install --quiet --upgrade pip
$PROJECT_DIR/venv/bin/pip install --quiet -r requirements.txt

echo "⚙️  步骤 6/8: 配置进程管理..."
cat > /etc/supervisor/conf.d/mcp-crypto-api.conf <<EOF
[program:mcp-crypto-api]
directory=$PROJECT_DIR
command=$PROJECT_DIR/venv/bin/python unified_server.py
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-crypto-api.err.log
stdout_logfile=/var/log/mcp-crypto-api.out.log
environment=PORT=8080
EOF

echo "🌐 步骤 7/8: 配置 Nginx..."
cat > /etc/nginx/sites-available/mcp-crypto-api <<EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

ln -sf /etc/nginx/sites-available/mcp-crypto-api /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo "🔥 步骤 8/8: 配置防火墙..."
ufw --force enable > /dev/null 2>&1
ufw allow 22/tcp > /dev/null 2>&1
ufw allow 80/tcp > /dev/null 2>&1
ufw allow 443/tcp > /dev/null 2>&1

echo "🚀 启动服务..."
supervisorctl reread > /dev/null 2>&1
supervisorctl update > /dev/null 2>&1
supervisorctl start mcp-crypto-api > /dev/null 2>&1
nginx -t > /dev/null 2>&1 && systemctl restart nginx

# 等待服务启动
sleep 3

echo ""
echo "=========================================="
echo "  ✅ 部署完成！"
echo "=========================================="
echo ""

# 获取服务器 IP
SERVER_IP=$(curl -s ifconfig.me)

echo "📊 服务状态："
supervisorctl status mcp-crypto-api

echo ""
echo "🌍 访问地址："
echo "   http://$SERVER_IP/"
echo "   http://$SERVER_IP/health"
echo ""

echo "🧪 测试命令："
echo "   curl http://$SERVER_IP/health"
echo "   curl http://$SERVER_IP/binance/spot/price?symbol=BTC"
echo ""

echo "📝 查看日志："
echo "   sudo tail -f /var/log/mcp-crypto-api.out.log"
echo ""

echo "🔧 管理命令："
echo "   sudo supervisorctl status mcp-crypto-api    # 查看状态"
echo "   sudo supervisorctl restart mcp-crypto-api   # 重启服务"
echo ""

# 自动测试
echo "🧪 自动测试 API..."
sleep 2
if curl -s http://localhost/health | grep -q "ok"; then
    echo "   ✅ API 运行正常！"
else
    echo "   ⚠️  API 可能未正常启动，请检查日志"
fi

echo ""
echo "=========================================="
