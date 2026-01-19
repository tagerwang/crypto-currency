# 快速部署指南

## 前提条件
- ✅ 服务器已创建（Ubuntu 22.04）
- ✅ 获得服务器 IP 地址
- ✅ 获得 root 密码

## 三步部署

### 步骤 1：上传文件到服务器

在本地 Kiro 终端执行：

```bash
# 替换 YOUR_SERVER_IP 为你的实际 IP
scp -r ./* root@YOUR_SERVER_IP:/root/mcp-crypto-api/
```

输入密码后等待上传完成。

### 步骤 2：连接到服务器

```bash
ssh root@YOUR_SERVER_IP
```

### 步骤 3：执行部署脚本

在服务器上执行：

```bash
cd /root/mcp-crypto-api
chmod +x quick_deploy.sh
./quick_deploy.sh
```

等待 3-5 分钟，部署完成！

## 验证部署

```bash
# 在服务器上测试
curl http://localhost/health

# 在本地测试（替换为你的 IP）
curl http://YOUR_SERVER_IP/health
```

## 测试 API

```bash
# 获取 BTC 价格
curl http://YOUR_SERVER_IP/binance/spot/price?symbol=BTC

# 查看所有 API
curl http://YOUR_SERVER_IP/
```

## 常用命令

```bash
# 查看服务状态
sudo supervisorctl status mcp-crypto-api

# 查看日志
sudo tail -f /var/log/mcp-crypto-api.out.log

# 重启服务
sudo supervisorctl restart mcp-crypto-api
```

## 遇到问题？

1. 检查服务状态：`sudo supervisorctl status`
2. 查看错误日志：`sudo tail -100 /var/log/mcp-crypto-api.err.log`
3. 手动测试：`cd /root/mcp-crypto-api && source venv/bin/activate && python mcp_http_server.py`
