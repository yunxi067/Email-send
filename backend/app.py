from flask import Flask, request, jsonify, send_file, session
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header
import pandas as pd
import re
import logging
from datetime import datetime
import traceback
import uuid

# 导入自定义模块
from config import config
from validators import (
    validate_smtp_config, allowed_file, sanitize_filename, 
    validate_recipients, validate_json_request
)
from database import DatabaseManager

# 初始化应用
def create_app(config_name=None):
    app = Flask(__name__)
    
    # 加载配置
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # 配置CORS
    CORS(app, resources={r"/api/*": {"origins": app.config['CORS_ORIGINS']}})
    
    # 创建必要的目录
    for folder in [app.config['UPLOAD_FOLDER'], app.config['ATTACHMENT_FOLDER'], app.config['TEMPLATE_FOLDER']]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(app.config['LOG_FILE']),
            logging.StreamHandler()
        ]
    )
    
    # 初始化数据库
    db = DatabaseManager()
    
    return app, db

app, db = create_app()

logger = logging.getLogger(__name__)

# 邮箱服务商配置
EMAIL_PROVIDERS = {
    'mobile139': {
        'name': '中国移动139邮箱',
        'smtp_host': 'smtp.139.com',
        'smtp_port_ssl': 465,
        'smtp_port': 25,
        'pop3_host': 'pop.139.com',
        'pop3_port_ssl': 995,
        'pop3_port': 110,
        'imap_host': 'imap.139.com',
        'imap_port_ssl': 993,
        'imap_port': 143,
        'use_auth_code': True,
        'help_text': '请使用16位授权码'
    },
    'qq': {
        'name': 'QQ邮箱',
        'smtp_host': 'smtp.qq.com',
        'smtp_port_ssl': 465,
        'smtp_port': 587,
        'pop3_host': 'pop.qq.com',
        'pop3_port_ssl': 995,
        'imap_host': 'imap.qq.com',
        'imap_port_ssl': 993,
        'use_auth_code': True,
        'help_text': '请使用授权码，非登录密码'
    },
    '163': {
        'name': '163邮箱',
        'smtp_host': 'smtp.163.com',
        'smtp_port_ssl': 465,
        'smtp_port': 25,
        'pop3_host': 'pop.163.com',
        'pop3_port_ssl': 995,
        'imap_host': 'imap.163.com',
        'imap_port_ssl': 993,
        'use_auth_code': True,
        'help_text': '请使用授权码'
    },
    'outlook': {
        'name': 'Outlook',
        'smtp_host': 'smtp-mail.outlook.com',
        'smtp_port': 587,
        'use_tls': True,
        'use_auth_code': False
    }
}

def parse_custom_excel(filepath):
    """
    解析自定义格式的Excel
    重要：只处理有附件的行，没有附件的直接跳过
    """
    try:
        # 读取Excel
        df = pd.read_excel(filepath, header=0)
        
        recipients = []
        skipped_count = 0  # 统计跳过的数量
        
        logger.info(f"开始解析Excel，总行数: {len(df)}")
        
        for idx, row in df.iterrows():
            try:
                # 获取各列数据 - 根据您的Excel格式
                # A列:前级 B列:部门 C列:附件位置 D列:奖金联系人 E列:奖金标题(邮箱)
                department = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                dept2 = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                attachment_path = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                contact_names = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                contact_emails = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                
                # 重要：先检查是否有附件，没有附件直接跳过
                if not attachment_path or attachment_path == 'nan' or attachment_path.strip() == '':
                    skipped_count += 1
                    logger.info(f"第{idx+2}行: 无附件，跳过此行")
                    continue
                
                # 解析附件路径
                attachments = []
                # 处理Windows路径 D:\AutoEmail\域名\分公司\2025年1[CD:\AutoEmail\附件\2025年10月]\新疆分配-域名.x
                if '\\' in attachment_path:
                    # 提取实际的文件路径
                    # 可能包含多个路径，用分号或其他符号分隔
                    paths = re.split(r'[;；]', attachment_path)
                    for path in paths:
                        path = path.strip()
                        if path:
                            # 提取文件名
                            filename = path.split('\\')[-1]
                            # 在附件目录查找
                            local_path = os.path.join(app.config['ATTACHMENT_FOLDER'], filename)
                            if os.path.exists(local_path):
                                attachments.append(local_path)
                                logger.info(f"找到附件: {filename}")
                            else:
                                logger.warning(f"附件未找到: {filename} (路径: {local_path})")
                
                # 如果解析后还是没有找到附件，跳过
                if not attachments:
                    skipped_count += 1
                    logger.info(f"第{idx+2}行: 附件文件不存在，跳过")
                    continue
                
                # 解析邮箱 - 支持多个邮箱
                if not contact_emails or contact_emails == 'nan':
                    skipped_count += 1
                    logger.info(f"第{idx+2}行: 无邮箱地址，跳过")
                    continue
                
                # 提取所有邮箱地址
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, str(contact_emails))
                
                if not emails:
                    skipped_count += 1
                    logger.info(f"第{idx+2}行: 邮箱格式无效，跳过")
                    continue
                
                # 解析姓名
                names = []
                if contact_names and contact_names != 'nan':
                    # 支持多种分隔符
                    names = re.split(r'[、，,;；]', contact_names)
                    names = [n.strip() for n in names if n.strip()]
                
                # 为每个邮箱创建收件人记录
                for i, email in enumerate(emails):
                    name = names[i] if i < len(names) else email.split('@')[0]
                    
                    recipient = {
                        'email': email.strip(),
                        'name': name,
                        'department': f"{department} {dept2}".strip(),
                        'attachment': attachments[0],  # 个性化附件
                        'all_attachments': attachments  # 所有附件
                    }
                    
                    recipients.append(recipient)
                    logger.info(f"添加收件人: {name} ({email}) - 部门: {recipient['department']}, 附件数: {len(attachments)}")
                    
            except Exception as e:
                logger.error(f"处理第{idx+2}行时出错: {str(e)}")
                continue
        
        logger.info(f"解析完成: 成功{len(recipients)}个收件人, 跳过{skipped_count}行(无附件或无效)")
        
        return {
            'success': True,
            'recipients': recipients,
            'total': len(recipients),
            'skipped': skipped_count
        }
        
    except Exception as e:
        logger.error(f"解析Excel失败: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'message': '邮件群发助手服务运行中',
        'features': {
            'auto_skip_no_attachment': True,  # 自动跳过无附件
            'mobile_139_support': True,       # 支持中国移动139邮箱
            'excel_format': 'custom'           # 自定义Excel格式
        }
    })

@app.route('/api/email-providers', methods=['GET'])
def get_email_providers():
    """获取支持的邮箱服务商配置"""
    return jsonify(EMAIL_PROVIDERS)

@app.route('/api/test-connection', methods=['POST', 'OPTIONS'])
@validate_json_request(['smtp_config'])
def test_connection():
    """测试SMTP连接"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        smtp_config = data.get('smtp_config', {})
        
        # 验证SMTP配置
        validation_errors = validate_smtp_config(smtp_config)
        if validation_errors:
            return jsonify({
                'success': False,
                'message': '配置验证失败: ' + '; '.join(validation_errors)
            }), 400
        
        smtp_host = smtp_config.get('smtp_host')
        smtp_port = int(smtp_config.get('smtp_port'))
        sender_email = smtp_config.get('sender_email')
        password = smtp_config.get('password')
        use_ssl = smtp_config.get('use_ssl', True)
        use_tls = smtp_config.get('use_tls', False)
        
        # 中国移动139邮箱特殊处理
        if '139.com' in sender_email:
            logger.info("检测到139邮箱，使用139邮箱配置")
            smtp_host = EMAIL_PROVIDERS['mobile139']['smtp_host']
            smtp_port = EMAIL_PROVIDERS['mobile139']['smtp_port_ssl']
            use_ssl = True
            use_tls = False
        
        # 创建SMTP连接
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=10)
        elif use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
            
        server.login(sender_email, password)
        server.quit()
        
        logger.info(f"SMTP连接测试成功: {sender_email}")
        return jsonify({'success': True, 'message': '连接成功'})
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP认证失败: {str(e)}")
        return jsonify({'success': False, 'message': '认证失败，请检查邮箱和密码'}), 400
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP连接失败: {str(e)}")
        return jsonify({'success': False, 'message': '连接服务器失败，请检查主机和端口'}), 400
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        return jsonify({'success': False, 'message': f'连接失败: {str(e)}'}), 500

@app.route('/api/parse-excel', methods=['POST'])
def parse_excel():
    """解析Excel文件 - 只处理有附件的行"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '未找到文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        # 验证文件类型
        if not allowed_file(file.filename, {'xlsx', 'xls'}):
            return jsonify({'success': False, 'message': '只支持Excel文件（.xlsx, .xls）'}), 400
        
        # 保存文件
        filename = sanitize_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 使用自定义解析器
        result = parse_custom_excel(filepath)
        
        if result['success']:
            # 验证解析结果
            validation_errors, valid_recipients = validate_recipients(result['recipients'])
            if validation_errors:
                logger.warning(f"收件人验证警告: {validation_errors}")
            
            # 保存到session
            session['recipients'] = valid_recipients
            
            message = f"成功导入 {len(valid_recipients)} 个有附件的收件人"
            if result['skipped'] > 0:
                message += f"，跳过 {result['skipped']} 行（无附件或无效数据）"
            
            return jsonify({
                'success': True,
                'data': {
                    'recipients': valid_recipients,
                    'stats': {
                        'total': len(valid_recipients),
                        'skipped': result['skipped']
                    }
                },
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': f"解析失败: {result.get('error', '未知错误')}"
            }), 400
            
    except Exception as e:
        logger.error(f"处理Excel文件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '文件处理失败，请检查文件格式是否正确'
        }), 500

@app.route('/api/download-template', methods=['GET'])
def download_template():
    """下载Excel模板"""
    try:
        template_path = os.path.join(app.config['TEMPLATE_FOLDER'], '邮件发送模板.xlsx')
        
        # 如果模板不存在，创建它
        if not os.path.exists(template_path):
            data = {
                '前级': ['新疆分公司', '北京分公司', '上海分公司'],
                '部门': ['一分公司', '二分公司', '三分公司'],
                '附件位置': [
                    'D:\\AutoEmail\\附件\\2025年10月\\新疆分配-域区.xlsx',
                    'D:\\AutoEmail\\附件\\2025年10月\\北京分配-域区.pdf',
                    'D:\\AutoEmail\\附件\\2025年10月\\上海分配-域区.docx'
                ],
                '奖金联系人': ['张三', '李四、王五', '赵六'],
                '奖金标题': [
                    'zhangsan@tj.chinamobile.com',
                    'lisi@tj.chinamobile.com、wangwu@tj.chinamobile.com',
                    'zhaoliu@tj.chinamobile.com'
                ]
            }
            df = pd.DataFrame(data)
            
            # 创建Excel
            with pd.ExcelWriter(template_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='收件人列表', index=False)
                
                # 获取工作表并设置列宽
                worksheet = writer.sheets['收件人列表']
                column_widths = {'A': 15, 'B': 15, 'C': 60, 'D': 30, 'E': 60}
                for column, width in column_widths.items():
                    worksheet.column_dimensions[column].width = width
            
            logger.info("Excel模板创建成功")
        
        return send_file(
            template_path,
            as_attachment=True,
            download_name='邮件发送模板.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
    except Exception as e:
        logger.error(f"下载模板失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-emails', methods=['POST'])
@validate_json_request(['smtp_config', 'subject', 'content'])
def send_emails():
    """发送邮件 - 只发送给有附件的收件人"""
    batch_id = str(uuid.uuid4())
    
    try:
        data = request.json
        smtp_config = data.get('smtp_config', {})
        subject = data.get('subject', '')
        content_template = data.get('content', '')
        common_attachments = data.get('common_attachments', [])
        
        # 获取收件人列表
        recipients = session.get('recipients', data.get('recipients', []))
        
        # 再次过滤，确保只发送给有附件的收件人
        recipients_with_attachments = [r for r in recipients if r.get('attachment') or r.get('all_attachments')]
        
        if not recipients_with_attachments:
            return jsonify({'success': False, 'message': '没有符合条件的收件人（需要有附件）'}), 400
        
        results = []
        success_count = 0
        
        # SMTP连接配置
        smtp_host = smtp_config.get('smtp_host')
        smtp_port = smtp_config.get('smtp_port')
        sender_email = smtp_config.get('sender_email')
        password = smtp_config.get('password')
        use_ssl = smtp_config.get('use_ssl', True)
        use_tls = smtp_config.get('use_tls', False)
        
        # 139邮箱自动配置
        if '139.com' in sender_email:
            smtp_host = EMAIL_PROVIDERS['mobile139']['smtp_host']
            smtp_port = EMAIL_PROVIDERS['mobile139']['smtp_port_ssl']
            use_ssl = True
            use_tls = False
        
        # 建立SMTP连接
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
        elif use_tls:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
        
        server.login(sender_email, password)
        
        for recipient in recipients_with_attachments:
            try:
                # 个性化内容
                content = content_template.replace('{{name}}', recipient.get('name', ''))
                content = content.replace('{{email}}', recipient.get('email', ''))
                content = content.replace('{{department}}', recipient.get('department', ''))
                
                # 创建邮件
                msg = MIMEMultipart()
                msg['From'] = Header(sender_email, 'utf-8')
                msg['To'] = Header(recipient['email'], 'utf-8')
                msg['Subject'] = Header(subject, 'utf-8')
                
                # 添加正文
                msg.attach(MIMEText(content, 'html', 'utf-8'))
                
                # 添加个性化附件（必须有）
                attachments_added = False
                if recipient.get('all_attachments'):
                    for attachment_path in recipient['all_attachments']:
                        try:
                            with open(attachment_path, 'rb') as f:
                                part = MIMEBase('application', 'octet-stream')
                                part.set_payload(f.read())
                                encoders.encode_base64(part)
                                filename = os.path.basename(attachment_path)
                                part.add_header(
                                    'Content-Disposition',
                                    f'attachment; filename="{filename}"'
                                )
                                msg.attach(part)
                                attachments_added = True
                        except Exception as e:
                            logger.warning(f"无法添加附件 {attachment_path}: {str(e)}")
                elif recipient.get('attachment'):
                    try:
                        with open(recipient['attachment'], 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(recipient['attachment'])
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{filename}"'
                            )
                            msg.attach(part)
                            attachments_added = True
                    except Exception as e:
                        logger.warning(f"无法添加附件 {recipient['attachment']}: {str(e)}")
                
                # 如果没有成功添加任何附件，跳过发送
                if not attachments_added:
                    results.append({
                        'email': recipient['email'],
                        'name': recipient.get('name', ''),
                        'status': 'skipped',
                        'message': '无有效附件，跳过发送'
                    })
                    continue
                
                # 添加公共附件（如果有）
                for attachment_path in common_attachments:
                    try:
                        with open(attachment_path, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(attachment_path)
                            part.add_header(
                                'Content-Disposition',
                                f'attachment; filename="{filename}"'
                            )
                            msg.attach(part)
                    except Exception as e:
                        logger.warning(f"无法添加公共附件 {attachment_path}: {str(e)}")
                
                # 发送邮件
                server.send_message(msg)
                success_count += 1
                
                results.append({
                    'email': recipient['email'],
                    'name': recipient.get('name', ''),
                    'status': 'success',
                    'message': '发送成功'
                })
                
            except Exception as e:
                results.append({
                    'email': recipient['email'],
                    'name': recipient.get('name', ''),
                    'status': 'failed',
                    'message': str(e)
                })
        
        server.quit()
        
        return jsonify({
            'success': True,
            'total': len(recipients_with_attachments),
            'success_count': success_count,
            'failed_count': len(recipients_with_attachments) - success_count,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"发送邮件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# 模板管理API
@app.route('/api/templates', methods=['GET'])
def get_templates():
    """获取邮件模板列表"""
    try:
        templates = db.get_templates()
        return jsonify({
            'success': True,
            'data': templates
        })
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取模板列表失败'
        }), 500

@app.route('/api/templates', methods=['POST'])
@validate_json_request(['name', 'subject', 'content'])
def create_template():
    """创建邮件模板"""
    try:
        data = request.get_json()
        
        template_id = db.create_template(
            name=data['name'],
            subject=data['subject'],
            content=data['content'],
            html_mode=data.get('html_mode', False)
        )
        
        return jsonify({
            'success': True,
            'message': '模板创建成功',
            'data': {'id': template_id}
        })
    except Exception as e:
        logger.error(f"创建模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '创建模板失败'
        }), 500

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    """删除邮件模板"""
    try:
        if db.delete_template(template_id):
            return jsonify({
                'success': True,
                'message': '模板删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '模板不存在'
            }), 404
    except Exception as e:
        logger.error(f"删除模板失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除模板失败'
        }), 500

# 发件人配置API
@app.route('/api/sender-configs', methods=['GET'])
def get_sender_configs():
    """获取发件人配置列表"""
    try:
        configs = db.get_sender_configs()
        return jsonify({
            'success': True,
            'data': configs
        })
    except Exception as e:
        logger.error(f"获取发件人配置列表失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '获取发件人配置列表失败'
        }), 500

@app.route('/api/sender-configs', methods=['POST'])
@validate_json_request(['name', 'smtp_host', 'smtp_port', 'sender_email', 'sender_name'])
def create_sender_config():
    """创建发件人配置"""
    try:
        data = request.get_json()
        
        # 验证配置
        validation_errors = validate_smtp_config(data)
        if validation_errors:
            return jsonify({
                'success': False,
                'message': '配置验证失败: ' + '; '.join(validation_errors)
            }), 400
        
        config_id = db.create_sender_config(
            name=data['name'],
            smtp_host=data['smtp_host'],
            smtp_port=data['smtp_port'],
            sender_email=data['sender_email'],
            sender_name=data['sender_name'],
            use_ssl=data.get('use_ssl', True),
            use_tls=data.get('use_tls', False),
            html_mode=data.get('html_mode', False)
        )
        
        return jsonify({
            'success': True,
            'message': '发件人配置创建成功',
            'data': {'id': config_id}
        })
    except Exception as e:
        logger.error(f"创建发件人配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '创建发件人配置失败'
        }), 500

@app.route('/api/sender-configs/<int:config_id>', methods=['DELETE'])
def delete_sender_config(config_id):
    """删除发件人配置"""
    try:
        if db.delete_sender_config(config_id):
            return jsonify({
                'success': True,
                'message': '发件人配置删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '发件人配置不存在'
            }), 404
    except Exception as e:
        logger.error(f"删除发件人配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '删除发件人配置失败'
        }), 500

@app.route('/api/upload-attachment', methods=['POST'])
def upload_attachment():
    """上传附件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'}), 400
        
        # 验证文件类型
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            return jsonify({
                'success': False, 
                'message': f'不支持的文件类型。支持的类型: {", ".join(app.config["ALLOWED_EXTENSIONS"])}'
            }), 400
        
        # 检查文件大小（已经在Flask层面检查，但双重保险）
        if hasattr(file, 'content_length') and file.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({
                'success': False,
                'message': f'文件太大，最大允许 {app.config["MAX_CONTENT_LENGTH"] // (1024*1024)}MB'
            }), 400
        
        # 安全处理文件名
        filename = sanitize_filename(file.filename)
        filepath = os.path.join(app.config['ATTACHMENT_FOLDER'], filename)
        
        # 如果文件已存在，添加时间戳
        if os.path.exists(filepath):
            import time
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{int(time.time())}{ext}"
            filepath = os.path.join(app.config['ATTACHMENT_FOLDER'], filename)
        
        file.save(filepath)
        
        logger.info(f"附件上传成功: {filename}")
        return jsonify({
            'success': True,
            'data': {
                'filename': filename,
                'filepath': filepath
            },
            'message': '附件上传成功'
        })
    except Exception as e:
        logger.error(f"附件上传失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': '附件上传失败'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)