from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import traceback
from werkzeug.utils import secure_filename
import json
import ssl
import socket

app = Flask(__name__)
CORS(app)

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
ATTACHMENTS_FOLDER = 'attachments'
TEMPLATES_FOLDER = 'templates'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ATTACHMENTS_FOLDER, exist_ok=True)
os.makedirs(TEMPLATES_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ATTACHMENTS_FOLDER'] = ATTACHMENTS_FOLDER
app.config['TEMPLATES_FOLDER'] = TEMPLATES_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email(smtp_config, recipient_email, recipient_name, subject, content, attachments=None):
    """
    发送单封邮件（增强版，使用改进的连接逻辑）
    """
    try:
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = f"{smtp_config['sender_name']} <{smtp_config['sender_email']}>"
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # 个性化内容（替换占位符）
        personalized_content = content.replace('{{name}}', recipient_name)
        personalized_content = personalized_content.replace('{{email}}', recipient_email)
        
        # 添加邮件正文
        if smtp_config.get('html_mode', False):
            msg.attach(MIMEText(personalized_content, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(personalized_content, 'plain', 'utf-8'))
        
        # 添加附件
        if attachments:
            for attachment_path in attachments:
                if os.path.exists(attachment_path):
                    with open(attachment_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        filename = os.path.basename(attachment_path)
                        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                        msg.attach(part)
        
        # 连接SMTP服务器并发送（使用改进的连接逻辑）
        server = None
        try:
            if smtp_config.get('use_ssl', True):
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(
                    smtp_config['smtp_host'], 
                    smtp_config['smtp_port'],
                    timeout=15,
                    context=context
                )
            else:
                server = smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port'], timeout=15)
                server.ehlo()
                if smtp_config.get('use_tls', False):
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
            
            server.login(smtp_config['sender_email'], smtp_config['password'])
            server.send_message(msg)
            server.quit()
            
            return {'success': True, 'message': '发送成功'}
            
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
                    
    except smtplib.SMTPAuthenticationError:
        return {'success': False, 'message': '认证失败：请检查邮箱和密码/授权码'}
    except smtplib.SMTPException as e:
        return {'success': False, 'message': f'SMTP错误: {str(e)}'}
    except Exception as e:
        return {'success': False, 'message': str(e)}

@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """
    测试SMTP连接（增强版，带详细错误诊断）
    """
    try:
        data = request.json
        smtp_config = data.get('smtp_config')
        
        # 打印调试信息
        print(f"[DEBUG] 尝试连接到: {smtp_config['smtp_host']}:{smtp_config['smtp_port']}")
        print(f"[DEBUG] 使用SSL: {smtp_config.get('use_ssl', True)}, 使用TLS: {smtp_config.get('use_tls', False)}")
        print(f"[DEBUG] 发件人邮箱: {smtp_config['sender_email']}")
        
        # 增加更详细的错误处理
        server = None
        
        try:
            # 首先测试网络连接
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((smtp_config['smtp_host'], smtp_config['smtp_port']))
            sock.close()
            
            if result != 0:
                return jsonify({
                    'success': False, 
                    'message': f'无法连接到服务器 {smtp_config["smtp_host"]}:{smtp_config["smtp_port"]}，请检查服务器地址和端口是否正确，以及防火墙设置'
                })
            
            # 创建SMTP连接
            if smtp_config.get('use_ssl', True):
                # SSL连接（端口465）
                context = ssl.create_default_context()
                # 对于某些自签名证书的邮箱服务器，可能需要禁用证书验证
                # context.check_hostname = False
                # context.verify_mode = ssl.CERT_NONE
                
                try:
                    server = smtplib.SMTP_SSL(
                        smtp_config['smtp_host'], 
                        smtp_config['smtp_port'], 
                        timeout=15,
                        context=context
                    )
                except ssl.SSLError as ssl_err:
                    return jsonify({
                        'success': False, 
                        'message': f'SSL连接失败: {str(ssl_err)}。如果使用端口587，请关闭SSL并开启TLS；如果使用端口465，请确保SSL已开启'
                    })
            else:
                # 普通连接或TLS连接（端口25/587）
                server = smtplib.SMTP(smtp_config['smtp_host'], smtp_config['smtp_port'], timeout=15)
                
                # 设置调试级别以获取更多信息
                server.set_debuglevel(1)
                
                # 发送EHLO命令
                server.ehlo()
                
                if smtp_config.get('use_tls', False):
                    # STARTTLS升级连接
                    if not server.has_extn('STARTTLS'):
                        server.quit()
                        return jsonify({
                            'success': False, 
                            'message': '服务器不支持STARTTLS。请尝试使用SSL（端口465）或普通连接（端口25）'
                        })
                    
                    context = ssl.create_default_context()
                    # context.check_hostname = False
                    # context.verify_mode = ssl.CERT_NONE
                    server.starttls(context=context)
                    server.ehlo()  # 重新发送EHLO
            
            # 尝试登录
            print(f"[DEBUG] 尝试登录...")
            server.login(smtp_config['sender_email'], smtp_config['password'])
            print(f"[DEBUG] 登录成功！")
            
            # 关闭连接
            server.quit()
            
            return jsonify({
                'success': True, 
                'message': 'SMTP连接测试成功！邮箱配置正确。'
            })
            
        except smtplib.SMTPAuthenticationError as auth_err:
            error_msg = str(auth_err)
            print(f"[ERROR] 认证失败: {error_msg}")
            
            # 提供更具体的错误提示
            if 'username and password not accepted' in error_msg.lower():
                suggestion = "\n\n💡 建议：\n"
                if 'qq.com' in smtp_config['smtp_host']:
                    suggestion += "- QQ邮箱需要使用授权码而不是QQ密码\n- 请在QQ邮箱设置中生成授权码"
                elif '163.com' in smtp_config['smtp_host']:
                    suggestion += "- 163邮箱需要使用授权码而不是登录密码\n- 请在163邮箱设置中开启SMTP并获取授权码"
                elif 'gmail.com' in smtp_config['smtp_host']:
                    suggestion += "- Gmail需要使用应用专用密码\n- 请开启两步验证并生成应用专用密码"
                elif '139.com' in smtp_config['smtp_host']:
                    suggestion += "- 中国移动邮箱需要先开启SMTP服务\n- 可以使用邮箱密码或客户端授权码\n- 请在139邮箱设置中开启SMTP功能"
                else:
                    suggestion += "- 请确认是否需要使用授权码/应用密码而非登录密码\n- 检查邮箱的安全设置是否允许第三方应用访问"
                
                return jsonify({
                    'success': False, 
                    'message': f'认证失败：用户名或密码错误{suggestion}'
                })
            else:
                return jsonify({
                    'success': False, 
                    'message': f'认证失败：{error_msg}'
                })
                
        except smtplib.SMTPServerDisconnected:
            return jsonify({
                'success': False, 
                'message': '服务器意外断开连接。可能是SSL/TLS配置不正确，请检查端口和加密设置的匹配：\n- 端口465通常使用SSL\n- 端口587通常使用TLS\n- 端口25通常不加密'
            })
            
        except smtplib.SMTPException as smtp_err:
            print(f"[ERROR] SMTP错误: {str(smtp_err)}")
            return jsonify({
                'success': False, 
                'message': f'SMTP错误：{str(smtp_err)}'
            })
            
        except socket.timeout:
            return jsonify({
                'success': False, 
                'message': '连接超时。请检查网络连接和防火墙设置，确保能访问邮件服务器'
            })
            
        except ConnectionRefusedError:
            return jsonify({
                'success': False, 
                'message': f'连接被拒绝。端口{smtp_config["smtp_port"]}可能不正确或被防火墙阻止'
            })
            
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
                    
    except Exception as e:
        print(f"[ERROR] 未知错误: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'连接失败: {str(e)}'})

@app.route('/api/parse-excel', methods=['POST'])
def parse_excel():
    """
    解析上传的Excel文件
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式，请上传xlsx、xls或csv文件'})
        
        # 保存文件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 解析Excel
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        # 验证必需的列
        required_columns = ['email', 'name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                'success': False, 
                'message': f'Excel缺少必需的列: {", ".join(missing_columns)}',
                'hint': '请确保Excel包含以下列：email（邮箱）、name（姓名）、attachment（附件路径，可选）'
            })
        
        # 转换为列表
        recipients = []
        for index, row in df.iterrows():
            recipient = {
                'email': str(row['email']).strip(),
                'name': str(row['name']).strip(),
                'attachment': str(row.get('attachment', '')).strip() if pd.notna(row.get('attachment')) else ''
            }
            # 添加其他自定义字段
            for col in df.columns:
                if col not in ['email', 'name', 'attachment']:
                    recipient[col] = str(row[col]) if pd.notna(row[col]) else ''
            
            recipients.append(recipient)
        
        return jsonify({
            'success': True,
            'message': f'成功解析{len(recipients)}条收件人信息',
            'data': {
                'recipients': recipients,
                'total': len(recipients),
                'columns': list(df.columns)
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'解析失败: {str(e)}'})

@app.route('/api/upload-attachment', methods=['POST'])
def upload_attachment():
    """
    上传附件文件
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有上传文件'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': '文件名为空'})
        
        # 保存附件
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['ATTACHMENTS_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'message': '附件上传成功',
            'data': {
                'filename': filename,
                'filepath': filepath
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'上传失败: {str(e)}'})

@app.route('/api/send-emails', methods=['POST'])
def send_emails():
    """
    批量发送邮件
    """
    try:
        data = request.json
        smtp_config = data.get('smtp_config')
        recipients = data.get('recipients', [])
        subject = data.get('subject', '')
        content = data.get('content', '')
        common_attachments = data.get('common_attachments', [])  # 统一附件
        
        if not recipients:
            return jsonify({'success': False, 'message': '收件人列表为空'})
        
        results = []
        success_count = 0
        fail_count = 0
        
        for recipient in recipients:
            # 准备附件列表
            attachments = common_attachments.copy()
            
            # 如果Excel中指定了附件路径，添加到附件列表
            if recipient.get('attachment'):
                attachment_path = recipient['attachment']
                # 如果是相对路径，从attachments文件夹查找
                if not os.path.isabs(attachment_path):
                    attachment_path = os.path.join(app.config['ATTACHMENTS_FOLDER'], attachment_path)
                
                if os.path.exists(attachment_path):
                    attachments.append(attachment_path)
            
            # 发送邮件
            result = send_email(
                smtp_config=smtp_config,
                recipient_email=recipient['email'],
                recipient_name=recipient['name'],
                subject=subject,
                content=content,
                attachments=attachments if attachments else None
            )
            
            result['recipient'] = recipient['email']
            results.append(result)
            
            if result['success']:
                success_count += 1
            else:
                fail_count += 1
        
        return jsonify({
            'success': True,
            'message': f'发送完成！成功: {success_count}, 失败: {fail_count}',
            'data': {
                'results': results,
                'summary': {
                    'total': len(recipients),
                    'success': success_count,
                    'fail': fail_count
                }
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'发送失败: {str(e)}'})

@app.route('/api/templates', methods=['GET'])
def get_templates():
    """
    获取所有模板
    """
    try:
        templates_file = os.path.join(app.config['TEMPLATES_FOLDER'], 'templates.json')
        if os.path.exists(templates_file):
            with open(templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        else:
            templates = []
        
        return jsonify({'success': True, 'data': templates})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取模板失败: {str(e)}'})

@app.route('/api/templates', methods=['POST'])
def save_template():
    """
    保存邮件模板
    """
    try:
        data = request.json
        template_name = data.get('name', '')
        subject = data.get('subject', '')
        content = data.get('content', '')
        html_mode = data.get('html_mode', False)
        
        if not template_name or not subject or not content:
            return jsonify({'success': False, 'message': '模板名称、主题和内容不能为空'})
        
        # 读取现有模板
        templates_file = os.path.join(app.config['TEMPLATES_FOLDER'], 'templates.json')
        if os.path.exists(templates_file):
            with open(templates_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        else:
            templates = []
        
        # 检查是否已存在同名模板
        existing_index = next((i for i, t in enumerate(templates) if t['name'] == template_name), None)
        
        new_template = {
            'id': str(datetime.now().timestamp()),
            'name': template_name,
            'subject': subject,
            'content': content,
            'html_mode': html_mode,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if existing_index is not None:
            # 更新现有模板
            new_template['id'] = templates[existing_index]['id']
            templates[existing_index] = new_template
            message = '模板已更新'
        else:
            # 添加新模板
            templates.append(new_template)
            message = '模板保存成功'
        
        # 保存到文件
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': message, 'data': new_template})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存模板失败: {str(e)}'})

@app.route('/api/templates/<template_id>', methods=['DELETE'])
def delete_template(template_id):
    """
    删除邮件模板
    """
    try:
        templates_file = os.path.join(app.config['TEMPLATES_FOLDER'], 'templates.json')
        if not os.path.exists(templates_file):
            return jsonify({'success': False, 'message': '模板文件不存在'})
        
        with open(templates_file, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        # 删除指定模板
        templates = [t for t in templates if t['id'] != template_id]
        
        with open(templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': '模板已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除模板失败: {str(e)}'})

@app.route('/api/diagnose', methods=['POST'])
def diagnose_smtp():
    """
    诊断SMTP配置问题
    """
    try:
        data = request.json
        smtp_config = data.get('smtp_config')
        
        diagnosis = {
            'network': {'status': 'pending', 'message': ''},
            'port': {'status': 'pending', 'message': ''},
            'ssl_tls': {'status': 'pending', 'message': ''},
            'authentication': {'status': 'pending', 'message': ''},
            'recommendations': []
        }
        
        # 1. 测试网络连接
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((smtp_config['smtp_host'], smtp_config['smtp_port']))
            sock.close()
            
            if result == 0:
                diagnosis['network']['status'] = 'success'
                diagnosis['network']['message'] = f"✅ 能够连接到 {smtp_config['smtp_host']}:{smtp_config['smtp_port']}"
            else:
                diagnosis['network']['status'] = 'error'
                diagnosis['network']['message'] = f"❌ 无法连接到 {smtp_config['smtp_host']}:{smtp_config['smtp_port']}"
                diagnosis['recommendations'].append("检查服务器地址是否正确")
                diagnosis['recommendations'].append("检查防火墙是否阻止了该端口")
        except Exception as e:
            diagnosis['network']['status'] = 'error'
            diagnosis['network']['message'] = f"❌ 网络测试失败: {str(e)}"
        
        # 2. 检查端口配置
        port = smtp_config['smtp_port']
        use_ssl = smtp_config.get('use_ssl', False)
        use_tls = smtp_config.get('use_tls', False)
        
        if port == 465:
            if use_ssl:
                diagnosis['port']['status'] = 'success'
                diagnosis['port']['message'] = "✅ 端口465配置正确（SSL）"
            else:
                diagnosis['port']['status'] = 'warning'
                diagnosis['port']['message'] = "⚠️ 端口465通常需要开启SSL"
                diagnosis['recommendations'].append("建议开启SSL选项")
        elif port == 587:
            if use_tls and not use_ssl:
                diagnosis['port']['status'] = 'success'
                diagnosis['port']['message'] = "✅ 端口587配置正确（TLS）"
            else:
                diagnosis['port']['status'] = 'warning'
                diagnosis['port']['message'] = "⚠️ 端口587通常使用TLS，不使用SSL"
                diagnosis['recommendations'].append("建议关闭SSL并开启TLS")
        elif port == 25:
            if not use_ssl and not use_tls:
                diagnosis['port']['status'] = 'success'
                diagnosis['port']['message'] = "✅ 端口25配置正确（无加密）"
            else:
                diagnosis['port']['status'] = 'warning'
                diagnosis['port']['message'] = "⚠️ 端口25通常不使用加密"
                diagnosis['recommendations'].append("建议关闭SSL和TLS")
        else:
            diagnosis['port']['status'] = 'info'
            diagnosis['port']['message'] = f"ℹ️ 使用非标准端口{port}"
        
        # 3. 检查邮箱服务商特定配置
        smtp_host = smtp_config['smtp_host'].lower()
        
        if 'qq.com' in smtp_host:
            diagnosis['recommendations'].append("QQ邮箱注意事项：")
            diagnosis['recommendations'].append("• 必须使用授权码，不是QQ密码")
            diagnosis['recommendations'].append("• 在QQ邮箱设置中开启SMTP服务并生成授权码")
            diagnosis['recommendations'].append("• 推荐配置：端口465 + SSL 或 端口587 + TLS")
        elif '163.com' in smtp_host:
            diagnosis['recommendations'].append("163邮箱注意事项：")
            diagnosis['recommendations'].append("• 必须使用授权码，不是登录密码")
            diagnosis['recommendations'].append("• 在设置中开启SMTP服务并设置授权码")
            diagnosis['recommendations'].append("• 推荐配置：端口465 + SSL 或 端口25（无加密）")
        elif 'gmail.com' in smtp_host:
            diagnosis['recommendations'].append("Gmail注意事项：")
            diagnosis['recommendations'].append("• 需要使用应用专用密码")
            diagnosis['recommendations'].append("• 开启两步验证后生成应用专用密码")
            diagnosis['recommendations'].append("• 推荐配置：端口465 + SSL 或 端口587 + TLS")
        elif 'outlook' in smtp_host or 'office365' in smtp_host:
            diagnosis['recommendations'].append("Outlook/Office365注意事项：")
            diagnosis['recommendations'].append("• 使用完整的邮箱地址作为用户名")
            diagnosis['recommendations'].append("• 推荐配置：端口587 + TLS")
        elif '139.com' in smtp_host:
            diagnosis['recommendations'].append("中国移动邮箱注意事项：")
            diagnosis['recommendations'].append("• 需要先在139邮箱网页版开启SMTP服务")
            diagnosis['recommendations'].append("• 使用邮箱密码或客户端授权码登录")
            diagnosis['recommendations'].append("• 推荐配置：端口465 + SSL 或 端口25（无加密）")
            diagnosis['recommendations'].append("• 如遇到发送限制，检查是否需要实名认证")
        
        return jsonify({
            'success': True,
            'diagnosis': diagnosis
        })
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'诊断失败: {str(e)}'
        })

@app.route('/api/sender-configs', methods=['GET'])
def get_sender_configs():
    """
    获取所有发件人配置模板
    """
    try:
        configs_file = os.path.join(app.config['TEMPLATES_FOLDER'], 'sender_configs.json')
        if os.path.exists(configs_file):
            with open(configs_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
        else:
            # 提供默认的配置模板
            configs = [
                {
                    'id': 'qq',
                    'name': 'QQ邮箱',
                    'smtp_host': 'smtp.qq.com',
                    'smtp_port': 465,
                    'use_ssl': True,
                    'use_tls': False,
                    'description': '需要使用授权码'
                },
                {
                    'id': '163',
                    'name': '163邮箱',
                    'smtp_host': 'smtp.163.com',
                    'smtp_port': 465,
                    'use_ssl': True,
                    'use_tls': False,
                    'description': '需要使用授权码'
                },
                {
                    'id': '139',
                    'name': '中国移动邮箱',
                    'smtp_host': 'smtp.139.com',
                    'smtp_port': 465,
                    'use_ssl': True,
                    'use_tls': False,
                    'description': '使用邮箱密码或授权码'
                },
                {
                    'id': 'gmail',
                    'name': 'Gmail',
                    'smtp_host': 'smtp.gmail.com',
                    'smtp_port': 587,
                    'use_ssl': False,
                    'use_tls': True,
                    'description': '需要应用专用密码'
                }
            ]
        
        return jsonify({'success': True, 'data': configs})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取发件人配置失败: {str(e)}'})

@app.route('/api/sender-configs', methods=['POST'])
def save_sender_config():
    """
    保存发件人配置模板
    """
    try:
        data = request.json
        config_name = data.get('name', '')
        smtp_host = data.get('smtp_host', '')
        smtp_port = data.get('smtp_port', 465)
        sender_email = data.get('sender_email', '')
        sender_name = data.get('sender_name', '')
        use_ssl = data.get('use_ssl', True)
        use_tls = data.get('use_tls', False)
        html_mode = data.get('html_mode', False)
        
        if not config_name or not smtp_host:
            return jsonify({'success': False, 'message': '配置名称和SMTP服务器不能为空'})
        
        # 读取现有配置
        configs_file = os.path.join(app.config['TEMPLATES_FOLDER'], 'sender_configs.json')
        if os.path.exists(configs_file):
            with open(configs_file, 'r', encoding='utf-8') as f:
                configs = json.load(f)
        else:
            configs = []
        
        # 检查是否已存在同名配置
        existing_index = next((i for i, c in enumerate(configs) if c['name'] == config_name), None)
        
        new_config = {
            'id': str(datetime.now().timestamp()),
            'name': config_name,
            'smtp_host': smtp_host,
            'smtp_port': smtp_port,
            'sender_email': sender_email,
            'sender_name': sender_name,
            'use_ssl': use_ssl,
            'use_tls': use_tls,
            'html_mode': html_mode,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if existing_index is not None:
            # 更新现有配置
            new_config['id'] = configs[existing_index]['id']
            configs[existing_index] = new_config
            message = '发件人配置已更新'
        else:
            # 添加新配置
            configs.append(new_config)
            message = '发件人配置保存成功'
        
        # 保存到文件
        with open(configs_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': message, 'data': new_config})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'保存发件人配置失败: {str(e)}'})

@app.route('/api/sender-configs/<config_id>', methods=['DELETE'])
def delete_sender_config(config_id):
    """
    删除发件人配置模板
    """
    try:
        configs_file = os.path.join(app.config['TEMPLATES_FOLDER'], 'sender_configs.json')
        if not os.path.exists(configs_file):
            return jsonify({'success': False, 'message': '配置文件不存在'})
        
        with open(configs_file, 'r', encoding='utf-8') as f:
            configs = json.load(f)
        
        # 过滤掉默认配置（不允许删除）
        protected_ids = ['qq', '163', '139', 'gmail']
        if config_id in protected_ids:
            return jsonify({'success': False, 'message': '默认配置不能删除'})
        
        # 删除指定配置
        configs = [c for c in configs if c['id'] != config_id]
        
        with open(configs_file, 'w', encoding='utf-8') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        
        return jsonify({'success': True, 'message': '发件人配置已删除'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除发件人配置失败: {str(e)}'})

@app.route('/api/health', methods=['GET'])
def health():
    """
    健康检查
    """
    return jsonify({'status': 'ok', 'message': '邮件群发助手服务运行中'})

if __name__ == '__main__':
    print('=' * 60)
    print('邮件群发助手 - 后端服务')
    print('服务地址: http://localhost:5000')
    print('=' * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)

