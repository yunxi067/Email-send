#!/bin/bash

# 邮件群发系统启动脚本
# 支持开发环境和生产环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 命令未找到，请先安装"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p data/{uploads,attachments,templates,logs}
    chmod 755 data
    chmod 755 data/uploads
    chmod 755 data/attachments
    chmod 755 data/templates
    chmod 755 data/logs
    log_success "目录创建完成"
}

# 生成环境变量文件
generate_env_file() {
    if [ ! -f .env ]; then
        log_info "生成环境变量文件..."
        cat > .env << EOF
# Flask应用配置
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)

# CORS配置
CORS_ORIGINS=http://localhost:3000

# 文件上传配置
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=uploads
ATTACHMENT_FOLDER=attachments
TEMPLATE_FOLDER=templates

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/email_sender.log

# 邮件发送配置
MAX_RECIPIENTS_PER_BATCH=100
EMAIL_RATE_LIMIT=10

# 数据库配置
DATABASE_PATH=email_sender.db
EOF
        log_success "环境变量文件已生成: .env"
        log_warning "请根据需要修改 .env 文件中的配置"
    else
        log_info "环境变量文件已存在"
    fi
}

# 检查Docker环境
check_docker() {
    log_info "检查Docker环境..."
    check_command docker
    check_command docker-compose
    
    if ! docker info &> /dev/null; then
        log_error "Docker守护进程未运行，请启动Docker"
        exit 1
    fi
    
    log_success "Docker环境检查通过"
}

# 构建镜像
build_images() {
    log_info "构建Docker镜像..."
    docker-compose -f docker-compose.improved.yml build --no-cache
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    docker-compose -f docker-compose.improved.yml up -d
    
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose -f docker-compose.improved.yml ps | grep -q "Up"; then
        log_success "服务启动成功"
        
        # 显示服务状态
        echo ""
        log_info "服务状态:"
        docker-compose -f docker-compose.improved.yml ps
        
        echo ""
        log_info "访问地址:"
        echo "  前端: http://localhost:3000"
        echo "  后端API: http://localhost:5000/api/health"
        
        echo ""
        log_info "查看日志命令:"
        echo "  docker-compose -f docker-compose.improved.yml logs -f"
    else
        log_error "服务启动失败"
        docker-compose -f docker-compose.improved.yml logs
        exit 1
    fi
}

# 开发环境启动
start_development() {
    log_info "启动开发环境..."
    
    # 后端
    cd backend
    if [ ! -f .env ]; then
        cp ../.env.example .env
    fi
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python app.py &
    BACKEND_PID=$!
    cd ..
    
    # 前端
    cd frontend
    npm install
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    
    log_success "开发环境启动成功"
    log_info "后端PID: $BACKEND_PID"
    log_info "前端PID: $FRONTEND_PID"
    log_info "按 Ctrl+C 停止服务"
    
    # 等待中断信号
    trap 'kill $BACKEND_PID $FRONTEND_PID; exit' INT
    wait
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose -f docker-compose.improved.yml down
    log_success "服务已停止"
}

# 清理资源
cleanup() {
    log_info "清理Docker资源..."
    docker-compose -f docker-compose.improved.yml down -v --remove-orphans
    docker system prune -f
    log_success "清理完成"
}

# 显示帮助信息
show_help() {
    echo "邮件群发系统启动脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动生产环境 (默认)"
    echo "  dev       启动开发环境"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  build     重新构建镜像"
    echo "  logs      查看日志"
    echo "  cleanup   清理所有资源"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动生产环境"
    echo "  $0 dev      # 启动开发环境"
    echo "  $0 logs     # 查看日志"
}

# 主函数
main() {
    case "${1:-start}" in
        "start")
            check_docker
            create_directories
            generate_env_file
            build_images
            start_services
            ;;
        "dev")
            start_development
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            sleep 2
            start_services
            ;;
        "build")
            check_docker
            build_images
            ;;
        "logs")
            docker-compose -f docker-compose.improved.yml logs -f
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"