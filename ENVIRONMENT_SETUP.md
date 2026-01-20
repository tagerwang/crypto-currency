# 环境变量配置指南

> 统一管理项目配置，提高安全性和灵活性

---

## 📋 目录

1. [快速开始](#快速开始)
2. [环境变量说明](#环境变量说明)
3. [使用脚本](#使用脚本)
4. [安全特性](#安全特性)
5. [故障排查](#故障排查)

---

## 🚀 快速开始

### 30秒配置

```bash
# 1. 复制模板
cp .env.example .env

# 2. 编辑文件
nano .env

# 3. 填入真实值
SERVER_IP=45.32.114.70
DOMAIN=tager.duckdns.org
SERVER_USER=root
PROJECT_DIR=/opt/mcp-crypto-api

# 4. 完成！
```

### 验证配置

```bash
# 测试环境变量
./check_dns.sh

# 检查敏感信息
./check_sensitive_info.sh
```

---

## 📝 环境变量说明

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `SERVER_IP` | ✅ | 服务器 IP 地址 | `45.32.114.70` |
| `DOMAIN` | ✅ | DuckDNS 域名 | `tager.duckdns.org` |
| `SERVER_USER` | ✅ | SSH 用户名 | `root` |
| `PROJECT_DIR` | ✅ | 项目目录 | `/opt/mcp-crypto-api` |
| `API_KEY` | ❌ | API 认证密钥（可选） | `your_secret_key` |

---

## 🔧 使用脚本

以下脚本会自动加载 `.env` 文件：

```bash
./check_dns.sh              # 检查 DNS 解析
./setup_ssl_for_duckdns.sh  # 配置 SSL 证书
./start_tunnel.sh           # 启动 SSH 隧道
./deploy_simple.sh          # 部署到服务器
./server_manager.sh         # 服务器管理
```

### 脚本自动验证

每个脚本运行前会：
1. 检查 `.env` 文件是否存在
2. 验证必需的环境变量
3. 显示友好的错误信息

**错误示例**：
```bash
❌ 错误: .env 文件不存在
请复制 .env.example 为 .env 并填入真实值
```

---

## 🔒 安全特性

### Git 安全

`.env` 文件已在 `.gitignore` 中：

```gitignore
# 本地配置
.env
```

✅ 敏感信息不会被提交到版本控制

### 敏感信息检查

运行检查脚本：

```bash
./check_sensitive_info.sh
```

**输出示例**：
```
==========================================
  检查敏感信息
==========================================

🔍 扫描文件中的敏感信息...

检查模式: 45\.32\.114\.70
✅ 未发现

检查模式: tager\.duckdns\.org
✅ 未发现

==========================================
  ✅ 检查通过！未发现敏感信息
==========================================
```

### 迁移完成

所有硬编码的 IP 和域名已迁移到环境变量：

**之前（硬编码）**：
```bash
DOMAIN="tager.duckdns.org"
SERVER_IP="45.32.114.70"
```

**之后（环境变量）**：
```bash
# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "❌ 错误: .env 文件不存在"
    exit 1
fi

# 使用环境变量
echo "域名: $DOMAIN"
echo "服务器: $SERVER_IP"
```

---

## 🐛 故障排查

### 问题 1：.env 文件不存在

**错误信息**：
```bash
❌ 错误: .env 文件不存在
```

**解决方法**：
```bash
cp .env.example .env
nano .env  # 填入真实值
```

### 问题 2：缺少环境变量

**错误信息**：
```bash
❌ 错误: 缺少必需的环境变量
请在 .env 文件中设置 SERVER_IP, SERVER_USER 和 PROJECT_DIR
```

**解决方法**：
打开 `.env` 文件，确保所有必需的变量都已设置且没有空值。

### 问题 3：权限问题

**错误信息**：
```bash
Permission denied
```

**解决方法**：
```bash
chmod +x *.sh  # 给所有脚本添加执行权限
```

### 问题 4：环境变量未生效

**测试方法**：
```bash
# 手动加载环境变量
source .env

# 检查变量值
echo $SERVER_IP
echo $DOMAIN
```

---

## 📚 最佳实践

### 本地开发

1. 每个开发者维护自己的 `.env` 文件
2. 不要共享 `.env` 文件
3. 使用 `.env.example` 作为模板

### 生产环境

1. 使用安全的方式管理环境变量（如密钥管理服务）
2. 定期轮换敏感信息
3. 实施访问控制

### 团队协作

1. 更新 `.env.example` 时通知团队
2. 在文档中说明新增的环境变量
3. 定期运行 `check_sensitive_info.sh`

---

## 🔄 在服务器上使用

如果需要在服务器上也使用环境变量：

```bash
# 1. 上传 .env 文件到服务器
scp .env $SERVER_USER@$SERVER_IP:$PROJECT_DIR/

# 2. 在服务器脚本中加载
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi
```

---

## 📖 文档中的示例

以下文档文件中包含示例 IP 和域名（用于说明目的）：
- `SSL_SETUP_GUIDE.md`
- `DEPLOYMENT_GUIDE.md`
- `readme.md`
- `CHANGELOG.md`

这些是文档示例，不影响实际部署的安全性。

---

## ✅ 配置检查清单

- [ ] 已创建 `.env` 文件
- [ ] 已填入所有必需的环境变量
- [ ] `.env` 在 `.gitignore` 中
- [ ] 运行 `check_sensitive_info.sh` 通过
- [ ] 测试脚本正常工作

---

## 🎯 优势

1. **安全性** - 敏感信息不会被提交到 Git
2. **灵活性** - 不同环境可以使用不同的配置
3. **可维护性** - 集中管理配置，易于更新
4. **团队协作** - 每个成员维护自己的 `.env` 文件

---

## ⚠️ 重要提醒

- **永远不要**将 `.env` 文件提交到 Git
- **永远不要**在公开场合分享 `.env` 内容
- 定期更新敏感信息（如 API 密钥）
- 定期运行 `check_sensitive_info.sh` 检查代码安全性

---

## 📚 相关文档

- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - 部署指南
- [SSL_SETUP_GUIDE.md](SSL_SETUP_GUIDE.md) - SSL 配置
- [GIT_COMMIT_GUIDE.md](GIT_COMMIT_GUIDE.md) - Git 提交规范

---

**配置完成！** 🎉 现在可以安全地使用所有脚本了。
