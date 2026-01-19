# MCP Crypto API 服务器部署指南

## 一、服务器准备

### 1. 购买 Vultr 服务器
- 位置：**Singapore**
- 操作系统：**Ubuntu 22.04 LTS** (无图形界面)
- 配置：至少 1 vCPU, 2GB RAM
- 获取服务器 IP 地址

### 2. 连接到服务器
```bash
# 在本地终端执行
ssh root@YOUR_SERVER_IP
```

## 二、上传项目文件

### 方法 1：使用 SCP（推荐）
```bash
# 在本地项目目录执行
scp -r ./* root@YOUR_SERVER_IP:/root/mcp-crypto-api/
```

### 方法 2：使用 Git
```bash
# 在服务器上执行
cd /root
git clone <your-repo-url> mcp-crypto-api
```

### 方法 3：使用 SFTP 工具
- 使用 FileZilla、WinSCP 等工具
- 连接到服务器
- 上传所有项目文件到 `/root/mcp-crypto-api/`

## 三、执行部署

### 1. 连接到服务器
```bash
ssh root@YOUR_SERVER_IP
```

### 2. 进入项目目录
```bash
cd /root/mcp-crypto-api
```

### 3. 给部署脚本执行权限
```bash
chmod +x deploy.sh
```

### 4. 运行部署脚本
```bash
./deploy.sh
```

部署脚本会自动完成：
- ✅ 安装 Python、Nginx、Supervisor
- ✅ 创建虚拟环境
- ✅ 安装依赖包
- ✅ 配置进程管理
- ✅ 配置反向代理
- ✅ 启动服务

## 四、验证部署

### 1. 检查服务状态
```bash
sudo supervisorctl status mcp-crypto-api
```
应该显示 `RUNNING`

### 2. 测试 API
```bash
# 在服务器上测试
curl http://localhost/health

# 在本地测试（替换为你的服务器 IP）
curl http://YOUR_SERVER_IP/health
```

### 3. 测试具体功能
```bash
# 获取 BTC 价格
curl http://YOUR_SERVER_IP/binance/spot/price?symbol=BTC

# 获取综合分析
curl http://YOUR_SERVER_IP/binance/analysis/comprehensive?symbol=BTC

# 获取热门币种
curl http://YOUR_SERVER_IP/coingecko/trending
```

## 五、常用管理命令

### 服务管理
```bash
# 查看服务状态
sudo supervisorctl status mcp-crypto-api

# 重启服务
sudo supervisorctl restart mcp-crypto-api

# 停止服务
sudo supervisorctl stop mcp-crypto-api

# 启动服务
sudo supervisorctl start mcp-crypto-api
```

### 查看日志
```bash
# 查看实时日志
sudo tail -f /var/log/mcp-crypto-api.out.log

# 查看错误日志
sudo tail -f /var/log/mcp-crypto-api.err.log

# 查看 Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 更新代码
```bash
# 1. 上传新代码到服务器
# 2. 重启服务
sudo supervisorctl restart mcp-crypto-api
```

## 六、安全加固（可选但推荐）

### 1. 配置 HTTPS（使用 Let's Encrypt）
```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书（替换为你的域名）
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 2. 添加 API 密钥认证
修改 `mcp_http_server.py`，添加：
```python
from functools import wraps

API_KEY = "YOUR_SECRET_API_KEY"  # 替换为你的密钥

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({"error": "Invalid API key"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 在需要保护的路由上添加装饰器
@app.route('/binance/spot/price', methods=['GET'])
@require_api_key
def binance_spot_price():
    # ...
```

### 3. 限制访问 IP（可选）
在 Nginx 配置中添加：
```nginx
# 只允许特定 IP 访问
allow YOUR_IP_ADDRESS;
deny all;
```

## 七、API 使用示例

### Python 客户端
```python
import requests

BASE_URL = "http://YOUR_SERVER_IP"

# 获取 BTC 价格
response = requests.get(f"{BASE_URL}/binance/spot/price?symbol=BTC")
print(response.json())

# 获取综合分析
response = requests.get(f"{BASE_URL}/binance/analysis/comprehensive?symbol=ETH")
print(response.json())
```

### JavaScript 客户端
```javascript
const BASE_URL = "http://YOUR_SERVER_IP";

// 获取 BTC 价格
fetch(`${BASE_URL}/binance/spot/price?symbol=BTC`)
  .then(res => res.json())
  .then(data => console.log(data));
```

### cURL
```bash
# 获取 BTC 价格
curl "http://YOUR_SERVER_IP/binance/spot/price?symbol=BTC"

# 获取资金费率
curl "http://YOUR_SERVER_IP/binance/funding-rate/realtime?symbol=BTC"
```

## 八、故障排查

### 服务无法启动
```bash
# 查看错误日志
sudo tail -100 /var/log/mcp-crypto-api.err.log

# 手动测试
cd /opt/mcp-crypto-api
source venv/bin/activate
python mcp_http_server.py
```

### 无法访问 API
```bash
# 检查防火墙
sudo ufw status

# 检查 Nginx
sudo nginx -t
sudo systemctl status nginx

# 检查端口监听
sudo netstat -tlnp | grep 8080
sudo netstat -tlnp | grep 80
```

### Python 依赖问题
```bash
cd /opt/mcp-crypto-api
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

## 九、性能优化

### 1. 使用 Gunicorn（生产环境推荐）
```bash
# 安装 Gunicorn
pip install gunicorn

# 修改 Supervisor 配置
command=$PROJECT_DIR/venv/bin/gunicorn -w 4 -b 127.0.0.1:8080 mcp_http_server:app
```

### 2. 添加缓存
安装 Redis 并使用 Flask-Caching

### 3. 监控
使用 Prometheus + Grafana 监控 API 性能

## 十、API 端点列表

访问 `http://YOUR_SERVER_IP/` 查看完整 API 文档

主要端点：
- `GET /health` - 健康检查
- `GET /binance/spot/price?symbol=BTC` - 现货价格
- `GET /binance/analysis/comprehensive?symbol=BTC` - 综合分析
- `GET /binance/funding-rate/realtime?symbol=BTC` - 实时资金费率
- `GET /coingecko/trending` - 热门币种

---

## 需要帮助？

如果遇到问题：
1. 查看日志文件
2. 检查服务状态
3. 验证网络连接
4. 确认 API 端点正确
