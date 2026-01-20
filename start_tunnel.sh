#!/bin/bash
# 本地端口转发脚本 - 让 Kiro 通过 localhost 访问远程服务器

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ 错误: .env 文件不存在"
    echo "请复制 .env.example 为 .env 并填入真实值"
    exit 1
fi

# 检查必需的环境变量
if [ -z "$SERVER_IP" ] || [ -z "$SERVER_USER" ]; then
    echo "❌ 错误: 缺少必需的环境变量"
    echo "请在 .env 文件中设置 SERVER_IP 和 SERVER_USER"
    exit 1
fi

echo "🚇 启动 SSH 隧道..."
echo "   本地端口: 8080"
echo "   远程服务器: $SERVER_IP:80"
echo ""
echo "⚠️  保持此终端窗口打开！"
echo "   按 Ctrl+C 停止隧道"
echo ""

# 创建 SSH 隧道
# -L 8080:localhost:80 - 将本地 8080 端口转发到远程服务器的 80 端口
# -N - 不执行远程命令
# -f - 后台运行（可选，如果想前台运行就去掉 -f）
ssh -L 8080:localhost:80 -N $SERVER_USER@$SERVER_IP
