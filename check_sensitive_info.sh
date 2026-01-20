#!/bin/bash
# 检查敏感信息脚本 - 确保没有硬编码的 IP 和域名

echo "=========================================="
echo "  检查敏感信息"
echo "=========================================="
echo ""

# 定义要检查的敏感信息模式
PATTERNS=(
    "45\.32\.114\.70"
    "tager\.duckdns\.org"
)

FOUND=0

echo "🔍 扫描文件中的敏感信息..."
echo ""

for pattern in "${PATTERNS[@]}"; do
    echo "检查模式: $pattern"
    
    # 排除特定文件和目录
    results=$(grep -r "$pattern" . \
        --exclude-dir=".git" \
        --exclude-dir="__pycache__" \
        --exclude-dir=".kiro" \
        --exclude-dir="venv" \
        --exclude="*.log" \
        --exclude="check_sensitive_info.sh" \
        --exclude=".env" \
        --exclude=".env.example" \
        2>/dev/null || true)
    
    if [ -n "$results" ]; then
        echo "❌ 发现敏感信息:"
        echo "$results"
        echo ""
        FOUND=1
    else
        echo "✅ 未发现"
        echo ""
    fi
done

echo "=========================================="
if [ $FOUND -eq 0 ]; then
    echo "  ✅ 检查通过！未发现敏感信息"
else
    echo "  ⚠️  发现敏感信息，请检查上述文件"
    echo ""
    echo "提示："
    echo "1. 将敏感信息移至 .env 文件"
    echo "2. 在脚本中使用环境变量"
    echo "3. 确保 .env 已添加到 .gitignore"
fi
echo "=========================================="
echo ""

exit $FOUND
