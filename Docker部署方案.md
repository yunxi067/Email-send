# 🐳 Docker一键部署方案

> 最简单的部署方式，适合快速上线

## 📦 为什么选择Docker？

- ✅ **一键部署** - 无需配置复杂环境
- ✅ **环境隔离** - 不影响服务器其他应用
- ✅ **易于迁移** - 随时可以迁移到其他服务器
- ✅ **版本管理** - 方便回滚和更新

## 🚀 快速开始（5分钟部署）

### 第1步：准备Docker环境

```bash
# Ubuntu/Debian安装Docker
curl -fsSL https://get.docker.com | sh

# CentOS安装Docker
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker

# 安装docker-compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 第2步：创建Docker配置文件

在项目根目录创建以下文件：

#### `Dockerfile.backend`
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# 复制应用文件
COPY backend/ .

# 创建必要的目录
RUN mkdir -p uploads attachments templates

# 暴露端口
EXPOSE 5000

# 启动命令
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

#### `Dockerfile.frontend`
```dockerfile
FROM node:16-alpine as builder

WORKDIR /app

# 复制package文件
COPY frontend/package*.json ./

# 安装依赖
RUN npm ci

# 复制源代码
COPY frontend/ .

# 构建
RUN npm run build

# 生产环境镜像
FROM nginx:alpine

# 复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

#### `docker-compose.yml`
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: email-sender-backend
    restart: always
    volumes:
      - ./data/uploads:/app/uploads
      - ./data/attachments:/app/attachments
      - ./data/templates:/app/templates
    environment:
      - FLASK_ENV=production
    networks:
      - email-network

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    container_name: email-sender-frontend
    restart: always
    ports:
      - "80:80"
    depends_on:
      - backend
    networks:
      - email-network

networks:
  email-network:
    driver: bridge

volumes:
  uploads:
  attachments:
  templates:
```

#### `nginx.conf`
```nginx
server {
    listen 80;
    server_name localhost;
    
    # 前端文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API代理
    location /api {
        proxy_pass http://backend:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 文件上传限制
        client_max_body_size 50M;
    }
}
```

### 第3步：一键启动

```bash
# 在项目根目录执行
docker-compose up -d

# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 第4步：访问服务

浏览器访问：`http://服务器IP`

## 🔧 进阶配置

### 1. 使用外部端口

如果80端口被占用，修改 `docker-compose.yml`:

```yaml
frontend:
  ports:
    - "8080:80"  # 改为8080端口
```

### 2. 配置HTTPS

使用Nginx反向代理 + Let's Encrypt:

```yaml
# docker-compose.yml 添加
services:
  nginx-proxy:
    image: jwilder/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - ./certs:/etc/nginx/certs
      - ./vhost.d:/etc/nginx/vhost.d
      - ./html:/usr/share/nginx/html
    networks:
      - email-network

  letsencrypt:
    image: jrcs/letsencrypt-nginx-proxy-companion
    container_name: letsencrypt
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./certs:/etc/nginx/certs
      - ./vhost.d:/etc/nginx/vhost.d
      - ./html:/usr/share/nginx/html
    environment:
      - NGINX_PROXY_CONTAINER=nginx-proxy
    networks:
      - email-network

  frontend:
    environment:
      - VIRTUAL_HOST=your-domain.com
      - LETSENCRYPT_HOST=your-domain.com
      - LETSENCRYPT_EMAIL=your-email@example.com
```

### 3. 数据持久化

数据默认保存在Docker卷中，也可以映射到主机目录：

```yaml
volumes:
  - /opt/email-sender/uploads:/app/uploads
  - /opt/email-sender/attachments:/app/attachments
  - /opt/email-sender/templates:/app/templates
```

## 📝 运维管理

### 常用命令

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看日志
docker-compose logs -f backend  # 后端日志
docker-compose logs -f frontend # 前端日志

# 进入容器
docker exec -it email-sender-backend bash

# 更新镜像
docker-compose pull
docker-compose up -d --build

# 清理未使用的镜像
docker system prune -a
```

### 备份与恢复

```bash
# 备份数据
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 恢复数据
tar -xzf backup-20240101.tar.gz

# 导出镜像（用于迁移）
docker save -o email-sender.tar email-sender-backend email-sender-frontend

# 导入镜像
docker load -i email-sender.tar
```

### 监控服务

```bash
# 创建健康检查脚本
cat > check-health.sh << 'EOF'
#!/bin/bash
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo "服务正常运行"
else
    echo "服务异常，正在重启..."
    docker-compose restart
fi
EOF

chmod +x check-health.sh

# 添加到crontab（每5分钟检查一次）
crontab -e
# 添加以下行
*/5 * * * * /path/to/check-health.sh
```

## 🔒 安全配置

### 1. 限制访问IP（可选）

修改 `nginx.conf`:

```nginx
location / {
    # 只允许特定IP
    allow 192.168.1.0/24;
    allow 10.0.0.0/8;
    deny all;
    
    root /usr/share/nginx/html;
    try_files $uri $uri/ /index.html;
}
```

### 2. 添加基础认证（可选）

```bash
# 安装htpasswd工具
apt-get install apache2-utils

# 创建密码文件
htpasswd -c .htpasswd user1

# 挂载到nginx容器
# 修改docker-compose.yml
volumes:
  - ./.htpasswd:/etc/nginx/.htpasswd
```

## 💡 优化建议

### 1. 使用Docker Swarm（集群部署）

```bash
# 初始化Swarm
docker swarm init

# 部署服务栈
docker stack deploy -c docker-compose.yml email-sender

# 扩展服务
docker service scale email-sender_backend=3
```

### 2. 使用外部数据库（可选）

如果数据量大，可以使用外部数据库存储：

```yaml
services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: emailsender
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secure-password
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

## 🎯 一键部署脚本

创建 `deploy-docker.sh`:

```bash
#!/bin/bash

echo "开始Docker部署..."

# 1. 安装Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    curl -fsSL https://get.docker.com | sh
fi

# 2. 安装docker-compose（如果未安装）
if ! command -v docker-compose &> /dev/null; then
    echo "安装docker-compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 3. 创建数据目录
mkdir -p data/{uploads,attachments,templates}

# 4. 构建并启动
docker-compose up -d --build

# 5. 等待服务启动
sleep 10

# 6. 检查服务状态
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo "✅ 部署成功！"
    echo "访问地址: http://$(curl -s ifconfig.me)"
else
    echo "❌ 部署失败，请检查日志"
    docker-compose logs
fi
```

## ✅ 部署完成检查

- [ ] Docker和docker-compose已安装
- [ ] 容器正常运行（`docker ps`）
- [ ] 可以访问前端页面
- [ ] API健康检查通过
- [ ] 数据目录已创建
- [ ] 日志无错误

## 🆘 故障排查

### 问题1：容器启动失败
```bash
# 查看详细错误
docker-compose logs
```

### 问题2：无法访问
```bash
# 检查端口
netstat -tlnp | grep 80

# 检查防火墙
iptables -L
```

### 问题3：API连接失败
```bash
# 检查网络
docker network ls
docker network inspect email-sender_email-network
```

## 📈 性能优化

1. **增加worker数量**：修改gunicorn的 `-w` 参数
2. **使用Redis缓存**：添加Redis服务
3. **配置资源限制**：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

使用Docker部署是最简单快捷的方式，特别适合小规模团队使用！🚀
