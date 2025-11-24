import re
import os
from werkzeug.utils import secure_filename
from functools import wraps
from flask import request, jsonify

def is_safe_email(email):
    """验证邮箱格式是否安全"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_smtp_config(config):
    """验证SMTP配置"""
    errors = []
    
    if not config.get('smtp_host'):
        errors.append('SMTP服务器地址不能为空')
    
    if not config.get('smtp_port') or not (1 <= int(config.get('smtp_port', 0)) <= 65535):
        errors.append('SMTP端口必须是1-65535之间的数字')
    
    if not config.get('sender_email'):
        errors.append('发件人邮箱不能为空')
    elif not is_safe_email(config.get('sender_email', '')):
        errors.append('发件人邮箱格式不正确')
    
    if not config.get('sender_name'):
        errors.append('发件人姓名不能为空')
    
    if not config.get('password'):
        errors.append('密码不能为空')
    
    return errors

def allowed_file(filename, allowed_extensions):
    """检查文件扩展名是否允许"""
    if not filename:
        return False
    
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in allowed_extensions

def sanitize_filename(filename):
    """清理文件名，防止路径遍历攻击"""
    if not filename:
        return 'unknown'
    
    # 使用werkzeug的secure_filename
    safe_name = secure_filename(filename)
    
    # 如果secure_filename返回空，使用时间戳
    if not safe_name:
        import time
        safe_name = f"file_{int(time.time())}"
    
    return safe_name

def validate_recipients(recipients):
    """验证收件人数据"""
    errors = []
    valid_recipients = []
    
    if not isinstance(recipients, list):
        errors.append('收件人数据必须是数组格式')
        return errors, valid_recipients
    
    for i, recipient in enumerate(recipients):
        if not isinstance(recipient, dict):
            errors.append(f'第{i+1}个收件人数据格式错误')
            continue
        
        # 验证邮箱
        email = recipient.get('email', '').strip()
        if not email:
            errors.append(f'第{i+1}个收件人邮箱不能为空')
            continue
        
        # 处理多个邮箱的情况
        emails = [e.strip() for e in re.split(r'[,、，]', email) if e.strip()]
        valid_emails = []
        
        for e in emails:
            if not is_safe_email(e):
                errors.append(f'第{i+1}个收件人邮箱格式不正确: {e}')
            else:
                valid_emails.append(e)
        
        if valid_emails:
            valid_recipients.append({
                'name': recipient.get('name', '').strip(),
                'email': valid_emails[0] if len(valid_emails) == 1 else valid_emails,
                'attachment': recipient.get('attachment', '').strip()
            })
    
    return errors, valid_recipients

def rate_limit(max_requests=10, window=60):
    """简单的API限流装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里可以实现基于内存的简单限流
            # 生产环境建议使用Redis
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json_request(required_fields=None):
    """验证JSON请求"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'success': False, 'message': '请求必须是JSON格式'}), 400
            
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'success': False, 
                        'message': f'缺少必需字段: {", ".join(missing_fields)}'
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator