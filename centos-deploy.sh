#!/bin/bash

# =========================================
# 📧 邮件系统 CentOS 7 一键部署脚本
# GitHub: https://github.com/yunxi067/Email-send
# 作者: yunxi067
# =========================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}    📧 邮件自动发送系统 - CentOS 7 部署        ${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查root权限
if [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}错误: 请使用root用户运行此脚本${NC}"
   echo "使用命令: sudo $0"
   exit 1
fi

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

echo -e "${GREEN}[1/8] 检查环境...${NC}"

# 检查Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Docker未安装，正在安装...${NC}"
    yum install -y yum-utils
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    yum install -y docker-ce docker-ce-cli containerd.io
    systemctl start docker
    systemctl enable docker
    echo -e "${GREEN}Docker安装成功${NC}"
else
    echo -e "${GREEN}Docker已安装${NC}"
fi

# 检查docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}docker-compose未安装，正在安装...${NC}"
    curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}docker-compose安装成功${NC}"
else
    echo -e "${GREEN}docker-compose已安装${NC}"
fi

# 检查Git
if ! command -v git &> /dev/null; then
    echo -e "${YELLOW}Git未安装，正在安装...${NC}"
    yum install -y git
    echo -e "${GREEN}Git安装成功${NC}"
else
    echo -e "${GREEN}Git已安装${NC}"
fi

echo -e "${GREEN}[2/8] 准备项目目录...${NC}"

PROJECT_DIR="/opt/email-sender"

# 如果目录存在，备份旧数据
if [ -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}发现旧版本，正在备份...${NC}"
    
    # 备份附件和模板
    if [ -d "$PROJECT_DIR/data" ]; then
        cp -r "$PROJECT_DIR/data" "/tmp/email-data-backup-$(date +%Y%m%d%H%M%S)"
        echo -e "${GREEN}数据已备份${NC}"
    fi
    
    # 停止旧容器
    cd $PROJECT_DIR
    docker-compose down 2>/dev/null || true
    
    # 删除旧目录
    cd /
    rm -rf $PROJECT_DIR
fi

echo -e "${GREEN}[3/8] 克隆项目代码...${NC}"

mkdir -p $PROJECT_DIR
cd $PROJECT_DIR
git clone https://github.com/yunxi067/Email-send.git .

# 如果克隆失败，尝试使用镜像
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}GitHub访问失败，尝试使用镜像...${NC}"
    git clone https://gitee.com/mirrors/Email-send.git . 2>/dev/null || \
    git clone https://hub.fastgit.xyz/yunxi067/Email-send.git . 2>/dev/null || \
    (echo -e "${RED}代码下载失败，请检查网络连接${NC}" && exit 1)
fi

echo -e "${GREEN}[4/8] 创建数据目录...${NC}"

# 创建必要的目录
mkdir -p data/uploads data/attachments data/templates

# 恢复备份数据（如果有）
if [ -d "/tmp/email-data-backup-"* ]; then
    BACKUP_DIR=$(ls -d /tmp/email-data-backup-* | tail -1)
    echo -e "${YELLOW}恢复备份数据...${NC}"
    cp -r $BACKUP_DIR/* data/ 2>/dev/null || true
    echo -e "${GREEN}数据恢复成功${NC}"
fi

echo -e "${GREEN}[5/8] 配置防火墙...${NC}"

# 检查firewalld
if systemctl is-active --quiet firewalld; then
    firewall-cmd --permanent --add-port=3000/tcp
    firewall-cmd --permanent --add-port=5000/tcp
    firewall-cmd --reload
    echo -e "${GREEN}防火墙端口 3000, 5000 已开放${NC}"
else
    echo -e "${YELLOW}防火墙未运行，跳过配置${NC}"
fi

# 检查iptables
if command -v iptables &> /dev/null; then
    iptables -A INPUT -p tcp --dport 3000 -j ACCEPT 2>/dev/null || true
    iptables -A INPUT -p tcp --dport 5000 -j ACCEPT 2>/dev/null || true
    service iptables save 2>/dev/null || true
fi

echo -e "${GREEN}[6/8] 构建Docker镜像...${NC}"

# 停止可能存在的旧容器
docker stop email-backend email-frontend 2>/dev/null || true
docker rm email-backend email-frontend 2>/dev/null || true

# 构建并启动服务
docker-compose up -d --build

echo -e "${GREEN}[7/8] 等待服务启动...${NC}"

# 等待服务启动
for i in {1..30}; do
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}后端服务启动成功${NC}"
        break
    fi
    echo -n "."
    sleep 2
done

echo ""

# 检查服务状态
docker-compose ps

echo -e "${GREEN}[8/8] 创建Excel模板...${NC}"

# 下载Excel模板
curl -s http://localhost:5000/api/download-template -o data/templates/邮件发送模板.xlsx 2>/dev/null || true

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}       ✅ 部署成功！                           ${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${BLUE}📌 访问地址：${NC}"
echo -e "  🌐 前端界面: ${YELLOW}http://${SERVER_IP}:3000${NC}"
echo -e "  🔌 后端API:  ${YELLOW}http://${SERVER_IP}:5000/api/health${NC}"
echo ""
echo -e "${BLUE}📧 139邮箱配置：${NC}"
echo -e "  SMTP服务器: smtp.139.com"
echo -e "  SMTP端口:   465 (SSL)"
echo -e "  POP3服务器: pop.139.com"
echo -e "  POP3端口:   995 (SSL)"
echo -e "  IMAP服务器: imap.139.com"
echo -e "  IMAP端口:   993 (SSL)"
echo -e "  ${RED}注意: 使用16位授权码，非登录密码${NC}"
echo ""
echo -e "${BLUE}📊 系统功能：${NC}"
echo -e "  ✅ 自动跳过无附件收件人"
echo -e "  ✅ 支持Excel批量导入"
echo -e "  ✅ 个性化附件发送"
echo -e "  ✅ 多收件人支持（顿号分隔）"
echo ""
echo -e "${BLUE}📝 常用命令：${NC}"
echo -e "  查看日志:   ${YELLOW}docker-compose logs -f${NC}"
echo -e "  停止服务:   ${YELLOW}docker-compose down${NC}"
echo -e "  重启服务:   ${YELLOW}docker-compose restart${NC}"
echo -e "  查看状态:   ${YELLOW}docker-compose ps${NC}"
echo ""
echo -e "${BLUE}📎 附件管理：${NC}"
echo -e "  上传附件:   ${YELLOW}docker cp 文件路径 email-backend:/app/attachments/${NC}"
echo -e "  查看附件:   ${YELLOW}docker exec email-backend ls -la /app/attachments/${NC}"
echo ""
echo -e "${GREEN}部署路径: ${PROJECT_DIR}${NC}"
echo -e "${GREEN}GitHub:  https://github.com/yunxi067/Email-send${NC}"
echo ""

# 创建快捷命令
cat > /usr/local/bin/email-system << 'EOF'
#!/bin/bash
cd /opt/email-sender
case "$1" in
    start)
        docker-compose up -d
        echo "邮件系统已启动"
        ;;
    stop)
        docker-compose down
        echo "邮件系统已停止"
        ;;
    restart)
        docker-compose restart
        echo "邮件系统已重启"
        ;;
    logs)
        docker-compose logs -f
        ;;
    status)
        docker-compose ps
        ;;
    *)
        echo "用法: email-system {start|stop|restart|logs|status}"
        exit 1
esac
EOF

chmod +x /usr/local/bin/email-system

echo -e "${GREEN}提示: 可以使用 ${YELLOW}email-system${GREEN} 命令管理服务${NC}"
echo -e "  ${YELLOW}email-system start${NC}   - 启动服务"
echo -e "  ${YELLOW}email-system stop${NC}    - 停止服务"
echo -e "  ${YELLOW}email-system restart${NC} - 重启服务"
echo -e "  ${YELLOW}email-system logs${NC}    - 查看日志"
echo -e "  ${YELLOW}email-system status${NC}  - 查看状态"
echo ""
