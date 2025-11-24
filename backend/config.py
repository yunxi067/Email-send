import os
import secrets
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """应用配置类"""
    
    # 安全配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 50 * 1024 * 1024))  # 50MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    ATTACHMENT_FOLDER = os.environ.get('ATTACHMENT_FOLDER', 'attachments')
    TEMPLATE_FOLDER = os.environ.get('TEMPLATE_FOLDER', 'templates')
    
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {
        'xlsx', 'xls',  # Excel文件
        'pdf', 'doc', 'docx', 'txt',  # 文档
        'jpg', 'jpeg', 'png', 'gif',  # 图片
        'zip', 'rar', '7z'  # 压缩文件
    }
    
    # CORS配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'email_sender.log')
    
    # 邮件发送限制
    MAX_RECIPIENTS_PER_BATCH = int(os.environ.get('MAX_RECIPIENTS_PER_BATCH', 100))
    EMAIL_RATE_LIMIT = int(os.environ.get('EMAIL_RATE_LIMIT', 10))  # 每秒最多发送邮件数
    
    # 数据库配置
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'email_sender.db')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    # 生产环境应该设置更严格的CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '').split(',') if os.environ.get('CORS_ORIGINS') else []

# 配置映射
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}