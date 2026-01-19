#!/bin/bash
# 服务器管理脚本 - 在本地 Kiro 终端中使用

# 配置你的服务器信息
SERVER_IP="YOUR_SERVER_IP"  # 替换为你的服务器IP
SERVER_USER="root"
PROJECT_DIR="/opt/mcp-crypto-api"

# 颜色输出
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== MCP 服务器管理工具 ===${NC}"
echo ""

# 显示菜单
show_menu() {
    echo "请选择操作："
    echo "1) 部署/更新代码到服务器"
    echo "2) 查看服务状态"
    echo "3) 重启服务"
    echo "4) 查看实时日志"
    echo "5) 测试 API"
    echo "6) SSH 连接到服务器"
    echo "7) 查看服务器资源使用"
    echo "0) 退出"
    echo ""
    read -p "输入选项 [0-7]: " choice
}

# 1. 部署代码
deploy_code() {
    echo -e "${GREEN}正在部署代码到服务器...${NC}"
    
    # 排除不需要的文件
    rsync -avz --progress \
        --exclude '__pycache__' \
        --exclude '*.pyc' \
        --exclude '.git' \
        --exclude 'venv' \
        --exclude '.DS_Store' \
        ./* $SERVER_USER@$SERVER_IP:$PROJECT_DIR/
    
    echo -e "${GREEN}代码已上传，正在重启服务...${NC}"
    ssh $SERVER_USER@$SERVER_IP "cd $PROJECT_DIR && supervisorctl restart mcp-crypto-api"
    
    echo -e "${GREEN}✅ 部署完成！${NC}"
}

# 2. 查看服务状态
check_status() {
    echo -e "${BLUE}服务状态：${NC}"
    ssh $SERVER_USER@$SERVER_IP "supervisorctl status mcp-crypto-api"
}

# 3. 重启服务
restart_service() {
    echo -e "${GREEN}正在重启服务...${NC}"
    ssh $SERVER_USER@$SERVER_IP "supervisorctl restart mcp-crypto-api"
    echo -e "${GREEN}✅ 服务已重启${NC}"
}

# 4. 查看日志
view_logs() {
    echo -e "${BLUE}实时日志（按 Ctrl+C 退出）：${NC}"
    ssh $SERVER_USER@$SERVER_IP "tail -f /var/log/mcp-crypto-api.out.log"
}

# 5. 测试 API
test_api() {
    echo -e "${BLUE}测试 API...${NC}"
    echo ""
    
    echo "1. 健康检查："
    curl -s http://$SERVER_IP/health | python3 -m json.tool
    echo ""
    
    echo "2. BTC 价格："
    curl -s "http://$SERVER_IP/binance/spot/price?symbol=BTC" | python3 -m json.tool
    echo ""
    
    echo "3. 热门币种："
    curl -s http://$SERVER_IP/coingecko/trending | python3 -m json.tool | head -20
}

# 6. SSH 连接
ssh_connect() {
    echo -e "${BLUE}连接到服务器...${NC}"
    ssh $SERVER_USER@$SERVER_IP
}

# 7. 查看资源使用
check_resources() {
    echo -e "${BLUE}服务器资源使用：${NC}"
    ssh $SERVER_USER@$SERVER_IP "echo '=== CPU 和内存 ===' && top -bn1 | head -5 && echo '' && echo '=== 磁盘使用 ===' && df -h | grep -E '^/dev/' && echo '' && echo '=== 网络连接 ===' && netstat -an | grep :80 | wc -l && echo '个活跃连接'"
}

# 主循环
while true; do
    show_menu
    
    case $choice in
        1) deploy_code ;;
        2) check_status ;;
        3) restart_service ;;
        4) view_logs ;;
        5) test_api ;;
        6) ssh_connect ;;
        7) check_resources ;;
        0) echo "再见！"; exit 0 ;;
        *) echo -e "${RED}无效选项${NC}" ;;
    esac
    
    echo ""
    read -p "按 Enter 继续..."
    clear
done
