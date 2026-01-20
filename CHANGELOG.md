# 更新日志

## v2.0.0 (2026-01-19) - 统一服务器

### 🚀 重大更新

- **统一服务器架构**：创建 `unified_server.py` 同时支持 REST API 和 MCP 协议
  - REST API：保持向后兼容，所有现有端点继续工作
  - MCP 协议：新增 `/mcp` 和 `/mcp-coingecko` 端点
  - Kiro 可直接连接远程服务器，无需本地桥接

### 🔧 模块化重构

- **移除旧文件**：删除 `binance_mcp.py`（已被 `binance_mcp/` 模块完全替代）
- **模块化包**：`binance_mcp/` 包含：
  - `api.py` - API 调用
  - `analysis.py` - 技术分析
  - `alpha.py` - Alpha 代币
  - `alpha_realtime.py` - 实时空投
  - `alpha_config.py` - Alpha 配置
  - `server.py` - MCP 服务器
  - `config.py` - 配置常量
  - `utils.py` - 工具函数
  - `indicators.py` - 技术指标

### 📝 文档更新

- 更新所有文档，移除对 `binance_mcp.py` 的引用
- 新增 `UNIFIED_DEPLOYMENT.md` - 统一部署指南
- 新增 `DEPLOY_STEPS.md` - 简化部署步骤
- 更新 `readme.md` - 反映新的项目结构
- 更新 `完整部署文档.md` - 使用新的服务器架构

### 🎯 配置更新

- **MCP 配置**：更新为使用远程 MCP 端点
  ```json
  {
    "binance-remote": {
      "type": "http",
      "url": "http://45.32.114.70/mcp"
    },
    "coingecko-remote": {
      "type": "http",
      "url": "http://45.32.114.70/mcp-coingecko"
    }
  }
  ```

### 🔄 迁移指南

从旧版本迁移：

1. **服务器端**：
   ```bash
   # 更新 supervisor 配置
   sudo sed -i 's/mcp_http_server.py/unified_server.py/g' \
     /etc/supervisor/conf.d/mcp-crypto-api.conf
   
   # 重启服务
   sudo supervisorctl restart mcp-crypto-api
   ```

2. **客户端**：
   - 更新 `~/.kiro/settings/mcp.json` 使用新的 MCP 端点
   - 重启 Kiro

### ⚠️ 破坏性变更

- 移除 `binance_mcp.py` 文件
- 如果有代码直接导入 `binance_mcp.py`，需要改为导入 `binance_mcp` 模块

---

## v1.1.0 (2026-01-10) - 模块化重构

### 🔧 模块化

- 将单文件拆分为 `binance_mcp/` 模块化包
- 提高代码可维护性和可扩展性

### ✨ 新功能

- Alpha 代币实时空投追踪
- 自动检测 Alpha 竞赛
- 改进的技术指标计算

---

## v1.0.0 (2026-01-09) - 初始版本

### 🎉 首次发布

- Binance API 集成
- CoinGecko API 集成
- REST API 服务器
- MCP 协议支持（stdio）
- 技术分析工具
- 资金费率查询
- Alpha 代币分析
