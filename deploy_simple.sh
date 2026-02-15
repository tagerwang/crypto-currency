#!/bin/bash
# 简单部署脚本 - 直接执行部署

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ 错误: .env 文件不存在"
    echo "请复制 .env.example 为 .env 并填入真实值"
    exit 1
fi

# 检查必需的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ] || [ -z "$PROJECT_DIR" ]; then
    echo "❌ 错误: 缺少必需的环境变量"
    echo "请在 .env 文件中设置 SERVER_IP, SERVER_USER 和 PROJECT_DIR"
    exit 1
fi
# PROJECT_DIR 为服务器上的项目路径，quick_deploy.sh 会在此目录启动服务，请与 .env 中一致（如 /opt/mcp-crypto-api）

echo "=== 开始部署到服务器 $SERVER_IP ==="
echo ""

# 1. 上传文件
echo "📦 步骤 1/3: 上传文件..."
rsync -avz --progress \
    --exclude '__pycache__' \
    --exclude '*.pyc' \
    --exclude '.git' \
    --exclude 'venv' \
    --exclude '.DS_Store' \
    --exclude '.kiro' \
    --exclude 'test_*.py' \
    ./* $SERVER_USER@$SERVER_IP:$PROJECT_DIR/

if [ $? -eq 0 ]; then
    echo "✅ 文件上传成功"
else
    echo "❌ 文件上传失败"
    exit 1
fi

echo ""

# 2. 执行部署脚本
echo "🚀 步骤 2/3: 在服务器上执行部署..."
ssh $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && chmod +x quick_deploy.sh && ./quick_deploy.sh"

if [ $? -eq 0 ]; then
    echo "✅ 部署成功"
else
    echo "❌ 部署失败，请检查日志"
    exit 1
fi

echo ""

# 3. 测试 API
echo "🧪 步骤 3/3: 测试 API..."
sleep 3

echo "测试健康检查..."
curl -s http://$SERVER_IP/health | python3 -m json.tool

echo ""
echo "测试 BTC 价格..."
curl -s "http://$SERVER_IP/binance/spot/price?symbol=BTC" | python3 -m json.tool

echo ""
echo "==================================="
echo "✅ 部署完成！"
echo "==================================="
echo ""
echo "API 地址："
echo "  http://$SERVER_IP/"
echo "  http://$SERVER_IP/health"
echo "  http://$SERVER_IP/binance/spot/price?symbol=BTC"
echo ""
echo "管理命令："
echo "  查看日志: ssh root@$SERVER_IP 'tail -f /var/log/mcp-crypto-api.out.log'"
echo "  查看状态: ssh root@$SERVER_IP 'supervisorctl status'"
echo "  重启服务: ssh root@$SERVER_IP 'supervisorctl restart mcp-crypto-api'"
echo ""
