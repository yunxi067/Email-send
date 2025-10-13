#!/bin/bash

# ========================================
# 邮件系统Docker部署脚本
# GitHub: https://github.com/yunxi067/Email-send.git
# ========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "     📧 邮件系统部署脚本"
echo "=========================================="

# 检查是否需要从GitHub克隆
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${YELLOW}未检测到项目文件，从GitHub克隆...${NC}"
    git clone https://github.com/yunxi067/Email-send.git .
fi

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}docker-compose未安装，尝试安装...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 停止旧容器
echo -e "${YELLOW}停止旧容器...${NC}"
docker-compose down 2>/dev/null || true

# 清理旧镜像
echo -e "${YELLOW}清理旧镜像...${NC}"
docker rmi email-backend email-frontend 2>/dev/null || true

# 构建并启动
echo -e "${GREEN}构建并启动服务...${NC}"
docker-compose up -d --build

# 等待服务启动
sleep 10

# 检查服务状态
echo -e "\n${GREEN}检查服务状态...${NC}"
docker-compose ps

# 测试API
echo -e "\n${GREEN}测试API...${NC}"
curl -s http://localhost:5000/api/health | python3 -m json.tool || echo "API测试失败"

echo -e "\n${GREEN}=========================================="
echo -e "✅ 部署完成！"
echo -e "=========================================="
echo -e "前端访问: http://$(curl -s ifconfig.me 2>/dev/null || echo localhost):3000"
echo -e "API地址: http://$(curl -s ifconfig.me 2>/dev/null || echo localhost):5000"
echo -e "\n查看日志: docker-compose logs -f"
echo -e "停止服务: docker-compose down${NC}"