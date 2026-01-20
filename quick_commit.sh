#!/bin/bash
# 快速提交脚本

echo "=========================================="
echo "  Git 快速提交"
echo "=========================================="
echo ""

# 显示状态
echo "📊 当前状态："
git status --short
echo ""

# 确认
echo "是否提交所有更改？(y/n)"
read -r CONFIRM

if [[ ! "${CONFIRM,,}" =~ ^(y|yes)$ ]]; then
    echo "已取消"
    exit 0
fi

# 添加所有文件
echo ""
echo "📦 添加文件..."
git add .

# 提交
echo ""
echo "💾 提交..."
git commit -m "feat: 完成 DuckDNS + SSL 部署配置

主要变更：
- 配置 DuckDNS 域名 (domian.org)
- 获取 Let's Encrypt SSL 证书
- 添加 SSH 隧道备选方案
- 重构为统一服务器架构
- 整理和精简项目文档（35→21个文件）

核心文件：
- DEPLOYMENT_GUIDE.md - 综合部署指南
- DUCKDNS_SETUP.md - DuckDNS 详细配置
- 当前使用方案_SSH隧道.md - SSH 隧道指南
- SSL_CERTIFICATE_COMPARISON.md - SSL 证书对比
- unified_server.py - 统一服务器
- setup_ssl_for_duckdns.sh - SSL 配置脚本

删除文件：
- binance_mcp.py - 已重构为模块化包
- 15个临时文档和脚本"

# 推送
echo ""
echo "🚀 推送到远程..."
git push

echo ""
echo "✅ 完成！"
