for i in {1..6}; do
  echo "--- 第 $i 次请求 ---"
  
  START=$(date +%s%3N)
  RESPONSE=$(curl -s -X POST http://localhost:8080/mcp \
    -H "Content-Type: application/json" \
    -d '{
      "jsonrpc": "2.0",
      "id": '$i',
      "method": "tools/call",
      "params": {
        "name": "get_open_interest",
        "arguments": { "symbol": "BTC" }
      }
    }')
  END=$(date +%s%3N)
  
  ELAPSED=$((END - START))
  echo "响应时间: ${ELAPSED}ms"
  echo "$RESPONSE" | jq -r '.result.content[0].text' | grep -E "open_interest|timestamp"
  echo ""
  
  [ $i -lt 6 ] && sleep 1
done