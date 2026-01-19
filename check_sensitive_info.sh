#!/bin/bash
echo "🔍 检查项目中的敏感信息..."
echo ""

# 检查配置文件中的占位符
echo "检查配置文件是否使用了占位符..."
config_files=("deploy_simple.sh" "server_manager.sh" "mcp_config_remote.json")

found_issues=0

for file in "${config_files[@]}"; do
    if [ -f "$file" ]; then
        if ! grep -q "YOUR_SERVER_IP" "$file"; then
            echo "⚠️  $file 可能包含真实服务器信息（未找到占位符）"
            found_issues=1
        else
            echo "✅ $file 使用了占位符"
        fi
    fi
done

echo ""
echo "================================"
if [ $found_issues -eq 0 ]; then
    echo "✅ 配置文件已正确使用占位符"
    echo "================================"
    exit 0
else
    echo "⚠️  发现潜在的敏感信息"
    echo "================================"
    exit 1
fi
