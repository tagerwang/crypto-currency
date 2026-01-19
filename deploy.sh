#!/bin/bash
# MCP 服务器部署脚本

echo "=== MCP Crypto API 部署脚本 ==="

# 1. 更新系统
echo "1. 更新系统..."
sudo apt update && sudo apt upgrade -y

# 2. 安装 Python 和必要工具
echo "2. 安装 Python 和工具..."
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git

# 3. 创建项目目录
echo "3. 创建项目目录..."
PROJECT_DIR="/opt/mcp-crypto-api"
sudo mkdir -p $PROJECT_DIR
sudo chown $USER:$USER $PROJECT_DIR

# 4. 克隆或复制项目文件
echo "4. 复制项目文件..."
# 如果使用 git
# git clone <your-repo-url> $PROJECT_DIR
# 或者手动上传文件到服务器

# 5. 创建虚拟环境
echo "5. 创建 Python 虚拟环境..."
cd $PROJECT_DIR
python3 -m venv venv
source venv/bin/activate

# 6. 安装依赖
echo "6. 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 7. 配置 Supervisor（进程管理）
echo "7. 配置 Supervisor..."
sudo tee /etc/supervisor/conf.d/mcp-crypto-api.conf > /dev/null <<EOF
[program:mcp-crypto-api]
directory=$PROJECT_DIR
command=$PROJECT_DIR/venv/bin/python mcp_http_server.py
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/mcp-crypto-api.err.log
stdout_logfile=/var/log/mcp-crypto-api.out.log
environment=PORT=8080
EOF

# 8. 配置 Nginx（反向代理）
echo "8. 配置 Nginx..."
sudo tee /etc/nginx/sites-available/mcp-crypto-api > /dev/null <<EOF
server {
    listen 80;
    server_name _;  # 替换为你的域名或 IP

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/mcp-crypto-api /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 9. 配置防火墙
echo "9. 配置防火墙..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS（如果需要）
sudo ufw --force enable

# 10. 启动服务
echo "10. 启动服务..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start mcp-crypto-api
sudo nginx -t && sudo systemctl restart nginx

echo ""
echo "=== 部署完成！==="
echo "服务状态检查："
sudo supervisorctl status mcp-crypto-api
echo ""
echo "访问测试："
echo "curl http://localhost/health"
echo "curl http://YOUR_SERVER_IP/health"
echo ""
echo "查看日志："
echo "sudo tail -f /var/log/mcp-crypto-api.out.log"
echo "sudo tail -f /var/log/mcp-crypto-api.err.log"
