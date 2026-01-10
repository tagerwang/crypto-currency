# CoinGecko MCP Server 开发文档

> 一个从零开始的 MCP (Model Context Protocol) 服务器实现指南

---

## 📖 目录

1. [什么是 MCP？](#什么是-mcp)
2. [项目概述](#项目概述)
3. [核心架构](#核心架构)
4. [代码详解](#代码详解)
5. [MCP 协议规范](#mcp-协议规范)
6. [如何使用](#如何使用)
7. [扩展开发](#扩展开发)
8. [官方文档链接](#官方文档链接)

---

## 什么是 MCP？

**MCP (Model Context Protocol)** 是 Anthropic 推出的一个开放协议，用于标准化大语言模型（LLM）与外部数据源、工具的交互方式。

### 核心概念

| 概念 | 说明 |
|------|------|
| **Host（宿主）** | 运行 LLM 的应用程序（如 Claude Desktop、Cursor） |
| **Client（客户端）** | 宿主内部的 MCP 客户端，管理与服务器的连接 |
| **Server（服务器）** | 提供数据和工具的外部程序 |
| **Tools（工具）** | 服务器暴露给 LLM 的可调用函数 |

### 通信协议

MCP 基于 **JSON-RPC 2.0** 协议进行通信，支持两种传输方式：
- **stdio**：通过标准输入/输出通信（本项目采用）
- **HTTP/SSE**：通过 HTTP 和 Server-Sent Events 通信

---

## 项目概述

本项目是一个**纯原生实现**的 MCP 服务器，不依赖任何 MCP 框架库，直接实现 JSON-RPC 2.0 协议。

### 特点

- ✅ **无需 API 密钥**：使用 CoinGecko 免费公共 API
- ✅ **零框架依赖**：仅需 `requests` 库
- ✅ **完整协议实现**：支持 initialize、tools/list、tools/call
- ✅ **涨跌概率分析**：基于7天数据的趋势预测

### 提供的工具

| 工具名称 | 功能 | 参数 |
|---------|------|------|
| `get_price` | 获取币种价格（含涨跌概率） | `coin_ids`: 币种ID，逗号分隔 |
| `get_coin_data` | 获取币种详细信息 | `coin_id`: 单个币种ID |
| `search_coins` | 搜索币种 | `query`: 搜索关键词 |
| `get_trending` | 获取热门币种 | 无参数 |

---

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Host (Cursor/Claude)                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    MCP Client                        │   │
│  └──────────────────────┬──────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │ stdio (JSON-RPC 2.0)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  coingecko_mcp.py                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              handle_mcp_request()                    │   │
│  │                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐   │   │
│  │  │ initialize  │  │ tools/list  │  │ tools/call │   │   │
│  │  └─────────────┘  └─────────────┘  └────────────┘   │   │
│  └──────────────────────┬───────────────────────────────┘   │
│                         ▼                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Business Logic Layer                    │   │
│  │                                                      │   │
│  │  get_price()  get_coin_data()  search_coins()       │   │
│  │  get_trending()  calculate_trend_probability()      │   │
│  └──────────────────────┬───────────────────────────────┘   │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTP
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   CoinGecko Public API                      │
│              https://api.coingecko.com/api/v3               │
└─────────────────────────────────────────────────────────────┘
```

---

## 代码详解

### 1. 文件结构

```python
#!/usr/bin/env python3
"""
CoinGecko MCP Server - 无需API密钥的加密货币数据服务器
"""

import json
import sys
import requests
from typing import Any, Dict

# CoinGecko API基础URL
BASE_URL = "https://api.coingecko.com/api/v3"
```

**关键点**：
- `#!/usr/bin/env python3`：Shebang 行，允许直接执行脚本
- `sys`：用于 stdin/stdout 通信
- `json`：处理 JSON-RPC 消息

### 2. 业务逻辑层

#### 2.1 获取历史价格数据

```python
def get_market_chart(coin_id: str, days: int = 7) -> Dict[str, Any]:
    """获取币种历史价格数据"""
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {
        'vs_currency': 'usd',
        'days': days
    }
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
```

#### 2.2 涨跌概率计算（核心算法）

```python
def calculate_trend_probability(coin_id: str) -> Dict[str, Any]:
    """
    计算涨跌概率分析
    基于近7天数据计算趋势
    """
```

**算法逻辑**：
1. 获取7天历史价格数据
2. 计算每日涨跌情况
3. 计算均线指标（MA3、MA7）
4. 计算波动率
5. 综合判断概率

**概率计算公式**：
```
up_probability = base_prob + ma_factor + momentum_factor

其中：
- base_prob = 历史涨天数 / 总天数 × 100
- ma_factor = 价格相对均线位置 × 2（限制在 ±15）
- momentum_factor = 短期动量 × 3（限制在 ±10）
```

#### 2.3 获取价格

```python
def get_price(coin_ids: str) -> Dict[str, Any]:
    """获取币种价格（含涨跌概率分析）"""
    url = f"{BASE_URL}/simple/price"
    params = {
        'ids': coin_ids,
        'vs_currencies': 'usd',
        'include_24hr_change': 'true',
        'include_24hr_vol': 'true',
        'include_market_cap': 'true',
        'include_last_updated_at': 'true'
    }
    # ... 实现
```

**特色**：每次查询价格时自动附加涨跌概率分析。

### 3. MCP 协议实现层

#### 3.1 请求处理入口

```python
def handle_mcp_request(request: Dict[str, Any]) -> Dict[str, Any] | None:
    """处理MCP请求 - 返回符合JSON-RPC 2.0规范的响应"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")

    # 通知不需要响应
    if request_id is None:
        return None

    # 构建基础响应
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
```

**JSON-RPC 2.0 要点**：
- 每个请求必须有 `method` 字段
- 有 `id` 的是请求，需要响应
- 无 `id` 的是通知，不需要响应

#### 3.2 处理 `initialize` 方法

```python
if method == "initialize":
    response["result"] = {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "coingecko-mcp",
            "version": "1.0.0"
        }
    }
```

**说明**：
- `protocolVersion`：MCP 协议版本
- `capabilities`：服务器能力声明（这里声明支持 tools）
- `serverInfo`：服务器元信息

#### 3.3 处理 `tools/list` 方法

```python
elif method == "tools/list":
    response["result"] = {
        "tools": [
            {
                "name": "get_price",
                "description": "获取加密货币价格...",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "coin_ids": {
                            "type": "string",
                            "description": "币种ID，多个用逗号分隔"
                        }
                    },
                    "required": ["coin_ids"]
                }
            },
            # ... 其他工具
        ]
    }
```

**工具定义结构**：
- `name`：工具名称（唯一标识）
- `description`：工具描述（LLM 用于理解功能）
- `inputSchema`：JSON Schema 格式的参数定义

#### 3.4 处理 `tools/call` 方法

```python
elif method == "tools/call":
    tool_name = params.get("name")
    arguments = params.get("arguments", {})

    if tool_name == "get_price":
        result = get_price(arguments.get("coin_ids", ""))
    # ... 其他工具

    response["result"] = {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, indent=2)
            }
        ]
    }
```

**返回格式**：
- `content`：内容数组
- 支持类型：`text`、`image`、`resource`

### 4. 主循环

```python
def main():
    """MCP服务器主循环"""
    for line in sys.stdin:
        try:
            line = line.strip()
            if not line:
                continue
            request = json.loads(line)
            response = handle_mcp_request(request)
            if response is not None:
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response), flush=True)
```

**关键点**：
- 从 `stdin` 逐行读取 JSON
- 处理后写入 `stdout`
- `flush=True` 确保立即输出
- 错误处理返回标准 JSON-RPC 错误格式

---

## MCP 协议规范

### JSON-RPC 2.0 消息格式

#### 请求格式

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "get_price",
        "arguments": {
            "coin_ids": "bitcoin,ethereum"
        }
    }
}
```

#### 响应格式（成功）

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
        "content": [
            {
                "type": "text",
                "text": "..."
            }
        ]
    }
}
```

#### 响应格式（错误）

```json
{
    "jsonrpc": "2.0",
    "id": 1,
    "error": {
        "code": -32601,
        "message": "Method not found"
    }
}
```

### MCP 标准方法

| 方法 | 说明 |
|------|------|
| `initialize` | 初始化连接，交换能力信息 |
| `initialized` | 通知（无响应），表示初始化完成 |
| `tools/list` | 列出可用工具 |
| `tools/call` | 调用工具 |
| `resources/list` | 列出可用资源 |
| `resources/read` | 读取资源 |
| `prompts/list` | 列出可用提示模板 |
| `prompts/get` | 获取提示模板 |

### 标准错误码

| 错误码 | 含义 |
|--------|------|
| -32700 | Parse error（JSON 解析失败） |
| -32600 | Invalid Request（无效请求） |
| -32601 | Method not found（方法不存在） |
| -32602 | Invalid params（参数错误） |
| -32603 | Internal error（内部错误） |

---

## 如何使用

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置 Cursor

在 Cursor 设置中添加 MCP 服务器配置：

**macOS**: `~/Library/Application Support/Cursor/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json`

```json
{
    "mcpServers": {
        "coingecko": {
            "command": "python3",
            "args": ["/absolute/path/to/coingecko_mcp.py"],
            "env": {}
        }
    }
}
```

### 3. 重启 Cursor

配置完成后重启 Cursor，即可在对话中使用加密货币查询功能。

### 4. 使用示例

在 Cursor 中询问：
- "查询比特币和以太坊的当前价格"
- "搜索 ZKP 相关的币种"
- "获取当前热门币种"

---

## 扩展开发

### 添加新工具

1. **实现业务函数**：

```python
def get_historical_data(coin_id: str, days: int) -> Dict[str, Any]:
    """获取历史数据"""
    # 实现逻辑
    pass
```

2. **在 `tools/list` 中注册**：

```python
{
    "name": "get_historical_data",
    "description": "获取历史价格数据",
    "inputSchema": {
        "type": "object",
        "properties": {
            "coin_id": {"type": "string", "description": "币种ID"},
            "days": {"type": "integer", "description": "天数"}
        },
        "required": ["coin_id"]
    }
}
```

3. **在 `tools/call` 中添加处理**：

```python
elif tool_name == "get_historical_data":
    result = get_historical_data(
        arguments.get("coin_id", ""),
        arguments.get("days", 7)
    )
```

### 添加资源支持

如果需要支持 `resources` 能力：

```python
# 在 initialize 响应中声明
"capabilities": {
    "tools": {},
    "resources": {}
}

# 实现 resources/list
elif method == "resources/list":
    response["result"] = {
        "resources": [
            {
                "uri": "crypto://market-overview",
                "name": "Market Overview",
                "description": "加密货币市场概览",
                "mimeType": "application/json"
            }
        ]
    }

# 实现 resources/read
elif method == "resources/read":
    uri = params.get("uri")
    # 返回资源内容
```

---

## 官方文档链接

### MCP 官方资源

| 资源 | 链接 |
|------|------|
| **MCP 官方网站** | https://modelcontextprotocol.io |
| **MCP 规范文档** | https://modelcontextprotocol.io/specification |
| **GitHub 仓库** | https://github.com/modelcontextprotocol |
| **Python SDK** | https://github.com/modelcontextprotocol/python-sdk |
| **TypeScript SDK** | https://github.com/modelcontextprotocol/typescript-sdk |
| **MCP 中文文档** | https://mcp.transdocs.org |

### CoinGecko API 文档

| 资源 | 链接 |
|------|------|
| **API 文档** | https://docs.coingecko.com/v3.0.1/reference/introduction |
| **免费 API 端点** | https://api.coingecko.com/api/v3 |

### 推荐阅读

1. **MCP 快速入门**：https://modelcontextprotocol.io/quickstart
2. **服务器开发指南**：https://modelcontextprotocol.io/docs/concepts/servers
3. **JSON-RPC 2.0 规范**：https://www.jsonrpc.org/specification

---

## 总结

这个项目展示了如何从零开始实现一个 MCP 服务器，核心要点：

1. **通信机制**：基于 stdio 的 JSON-RPC 2.0
2. **协议流程**：`initialize` → `tools/list` → `tools/call`
3. **工具定义**：使用 JSON Schema 描述参数
4. **错误处理**：遵循 JSON-RPC 错误规范

通过这种原生实现方式，你可以完全掌控 MCP 协议的每个细节，也可以轻松扩展到其他 API 或数据源。

---

*文档生成时间：2026年1月9日*

