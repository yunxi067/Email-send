#!/bin/bash

# 邮件群发系统部署脚本
# 适用于生产环境部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置变量
DEPLOY_DIR="/opt/email-sender"
SERVICE_NAME="email-sender"
BACKUP_DIR="/opt/backups/email-sender"
LOG_FILE="/var/log/email-sender-deploy.log"

# 日志函数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
}

# 检查系统要求
check_requirements() {
    log_info "检查系统要求..."
    
    # 检查操作系统
    if ! command -v systemctl &> /dev/null; then
        log_error "需要systemd支持"
        exit 1
    fi
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_warning "Docker未安装，开始安装..."
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        systemctl enable docker
        systemctl start docker
        rm get-docker.sh
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warning "Docker Compose未安装，开始安装..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    fi
    
    log_success "系统要求检查完成"
}

# 创建目录结构
create_directories() {
    log_info "创建目录结构..."
    
    mkdir -p $DEPLOY_DIR
    mkdir -p $BACKUP_DIR
    mkdir -p /opt/data/{uploads,attachments,templates,logs}
    mkdir -p /opt/ssl
    
    chown -R root:root $DEPLOY_DIR
    chown -R root:root /opt/data
    
    chmod 755 $DEPLOY_DIR
    chmod 755 /opt/data
    chmod 755 /opt/data/*
    
    log_success "目录结构创建完成"
}

# 备份现有数据
backup_data() {
    if [ -d "$DEPLOY_DIR" ] && [ "$(ls -A $DEPLOY_DIR)" ]; then
        log_info "备份现有数据..."
        
        BACKUP_NAME="backup-$(date +%Y%m%d-%H%M%S)"
        BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"
        
        mkdir -p $BACKUP_PATH
        
        # 备份数据文件
        if [ -d "/opt/data" ]; then
            cp -r /opt/data $BACKUP_PATH/
        fi
        
        # 备份配置文件
        if [ -f "$DEPLOY_DIR/.env" ]; then
            cp $DEPLOY_DIR/.env $BACKUP_PATH/
        fi
        
        # 备份数据库
        if [ -f "/opt/data/email_sender.db" ]; then
            cp /opt/data/email_sender.db $BACKUP_PATH/
        fi
        
        log_success "数据备份完成: $BACKUP_PATH"
    fi
}

# 部署应用
deploy_app() {
    log_info "部署应用..."
    
    # 复制应用文件
    cp -r . $DEPLOY_DIR/
    
    # 设置权限
    chown -R root:root $DEPLOY_DIR
    chmod +x $DEPLOY_DIR/start-improved.sh
    
    # 生成环境变量文件
    if [ ! -f "$DEPLOY_DIR/.env" ]; then
        log_info "生成生产环境配置..."
        cat > $DEPLOY_DIR/.env << EOF
# 生产环境配置
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# CORS配置（根据实际情况修改）
CORS_ORIGINS=https://yourdomain.com

# 文件上传配置
MAX_CONTENT_LENGTH=52428800
UPLOAD_FOLDER=/opt/data/uploads
ATTACHMENT_FOLDER=/opt/data/attachments
TEMPLATE_FOLDER=/opt/data/templates

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=/opt/data/logs/email_sender.log

# 邮件发送配置
MAX_RECIPIENTS_PER_BATCH=100
EMAIL_RATE_LIMIT=10

# 数据库配置
DATABASE_PATH=/opt/data/email_sender.db
EOF
        log_warning "请修改 $DEPLOY_DIR/.env 中的CORS_ORIGINS配置"
    fi
    
    log_success "应用部署完成"
}

# 创建systemd服务
create_service() {
    log_info "创建systemd服务..."
    
    cat > /etc/systemd/system/$SERVICE_NAME.service << EOF
[Unit]
Description=Email Sender Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$DEPLOY_DIR
ExecStart=$DEPLOY_DIR/start-improved.sh start
ExecStop=$DEPLOY_DIR/start-improved.sh stop
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    
    log_success "systemd服务创建完成"
}

# 配置Nginx（可选）
configure_nginx() {
    if command -v nginx &> /dev/null; then
        log_info "配置Nginx..."
        
        cat > /etc/nginx/sites-available/email-sender << EOF
server {
    listen 80;
    server_name your-domain.com;  # 修改为实际域名
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;  # 修改为实际域名
    
    # SSL配置
    ssl_certificate /opt/ssl/cert.pem;
    ssl_certificate_key /opt/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    # 前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 后端API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # 文件上传大小限制
    client_max_body_size 50M;
}
EOF
        
        ln -sf /etc/nginx/sites-available/email-sender /etc/nginx/sites-enabled/
        nginx -t && systemctl reload nginx
        
        log_success "Nginx配置完成"
    else
        log_warning "Nginx未安装，跳过配置"
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    cd $DEPLOY_DIR
    ./start-improved.sh start
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if systemctl is-active --quiet $SERVICE_NAME; then
        log_success "服务启动成功"
    else
        log_error "服务启动失败"
        journalctl -u $SERVICE_NAME --no-pager
        exit 1
    fi
}

# 设置定时备份
setup_cron() {
    log_info "设置定时备份..."
    
    # 添加每日备份任务
    (crontab -l 2>/dev/null; echo "0 2 * * * $DEPLOY_DIR/backup.sh") | crontab -
    
    # 创建备份脚本
    cat > $DEPLOY_DIR/backup.sh << EOF
#!/bin/bash
BACKUP_DIR="$BACKUP_DIR/\$(date +%Y%m%d-%H%M%S)"
mkdir -p \$BACKUP_DIR
cp -r /opt/data \$BACKUP_DIR/
find $BACKUP_DIR -type d -mtime +7 -exec rm -rf {} +
EOF
    
    chmod +x $DEPLOY_DIR/backup.sh
    
    log_success "定时备份设置完成"
}

# 主函数
main() {
    log_info "开始部署邮件群发系统..."
    
    check_root
    check_requirements
    create_directories
    backup_data
    deploy_app
    create_service
    configure_nginx
    start_services
    setup_cron
    
    log_success "部署完成！"
    log_info "访问地址: http://localhost:3000"
    log_info "服务管理: systemctl $SERVICE_NAME start|stop|restart|status"
    log_info "查看日志: journalctl -u $SERVICE_NAME -f"
}

# 执行主函数
main "$@"