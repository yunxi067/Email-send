#!/bin/bash

# ================================================
# 修复邮件系统 - 配置保存和附件发送
# ================================================

echo "=================================="
echo "🔧 修复邮件系统功能"
echo "=================================="

# 修复1：添加保存配置功能
echo "修复配置保存功能..."

docker exec email-backend bash -c 'cat >> /app/app.py << '\''CONFIG_FIX'\''

# ===== 修复：保存发件人配置 =====
@app.route('\''/api/sender-configs'\'', methods=['\''POST'\''])
def save_sender_config():
    """保存发件人配置"""
    try:
        data = request.json
        
        # 保存到文件
        config_file = os.path.join(app.config['\''TEMPLATE_FOLDER'\''], '\''sender_configs.json'\'')
        
        # 读取现有配置
        configs = []
        if os.path.exists(config_file):
            with open(config_file, '\''r'\'', encoding='\''utf-8'\'') as f:
                try:
                    configs = json.load(f)
                except:
                    configs = []
        
        # 添加新配置
        new_config = {
            '\''name'\'': data.get('\''name'\'', '\''默认配置'\''),
            '\''smtp_host'\'': data.get('\''smtp_host'\''),
            '\''smtp_port'\'': data.get('\''smtp_port'\''),
            '\''sender_email'\'': data.get('\''sender_email'\''),
            '\''use_ssl'\'': data.get('\''use_ssl'\'', True),
            '\''created_at'\'': datetime.now().isoformat()
        }
        configs.append(new_config)
        
        # 保存到文件
        with open(config_file, '\''w'\'', encoding='\''utf-8'\'') as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)
        
        return jsonify({'\''success'\'': True, '\''message'\'': '\''配置保存成功'\''})
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return jsonify({'\''success'\'': False, '\''error'\'': str(e)})

# ===== 修复：获取保存的配置 =====
@app.route('\''/api/sender-configs'\'', methods=['\''GET'\''])
def get_sender_configs():
    """获取发件人配置列表"""
    try:
        config_file = os.path.join(app.config['\''TEMPLATE_FOLDER'\''], '\''sender_configs.json'\'')
        if os.path.exists(config_file):
            with open(config_file, '\''r'\'', encoding='\''utf-8'\'') as f:
                configs = json.load(f)
                return jsonify(configs)
        return jsonify([])
    except Exception as e:
        logger.error(f"读取配置失败: {str(e)}")
        return jsonify([])

CONFIG_FIX'

# 修复2：重新理解附件逻辑
echo "修复附件发送逻辑..."

docker exec email-backend bash -c 'cat >> /app/app.py << '\''ATTACHMENT_FIX'\''

# ===== 修复：正确的Excel解析（附件是要发送的） =====
def parse_excel_correct(filepath):
    """
    正确解析Excel - 附件是要发送给收件人的
    规则：如果某行指定了附件但附件不存在，则跳过该收件人
    """
    try:
        df = pd.read_excel(filepath, header=0)
        recipients = []
        skipped_count = 0
        
        logger.info(f"开始解析Excel，总行数: {len(df)}")
        
        for idx, row in df.iterrows():
            try:
                # 获取各列数据
                department = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                dept2 = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                attachment_info = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                contact_names = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                contact_emails = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                
                # 解析邮箱
                if not contact_emails or contact_emails == '\''nan'\'':
                    skipped_count += 1
                    logger.info(f"第{idx+2}行: 无邮箱，跳过")
                    continue
                
                email_pattern = r'\''[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'\''
                emails = re.findall(email_pattern, str(contact_emails))
                
                if not emails:
                    skipped_count += 1
                    logger.info(f"第{idx+2}行: 邮箱格式无效，跳过")
                    continue
                
                # 处理附件信息
                attachments_to_send = []
                if attachment_info and attachment_info != '\''nan'\'':
                    # 提取文件名
                    if '\''\\\'\'' in attachment_info:
                        filename = attachment_info.split('\''\\\\'\'')[-1]
                    elif '\''/'\'' in attachment_info:
                        filename = attachment_info.split('\''/'\'' )[-1]
                    else:
                        filename = attachment_info
                    
                    # 查找附件文件
                    attachment_path = os.path.join(app.config['\''ATTACHMENT_FOLDER'\''], filename)
                    if os.path.exists(attachment_path):
                        attachments_to_send.append(attachment_path)
                        logger.info(f"第{idx+2}行: 找到附件 {filename}")
                    else:
                        # 如果指定了附件但找不到，跳过这个收件人
                        skipped_count += 1
                        logger.info(f"第{idx+2}行: 附件 {filename} 不存在，跳过")
                        continue
                
                # 解析姓名
                names = []
                if contact_names and contact_names != '\''nan'\'':
                    names = re.split(r'\''[、，,;；]'\'', contact_names)
                    names = [n.strip() for n in names if n.strip()]
                
                # 为每个邮箱创建收件人记录
                for i, email in enumerate(emails):
                    name = names[i] if i < len(names) else email.split('\''@'\'')[0]
                    
                    recipient = {
                        '\''email'\'': email.strip(),
                        '\''name'\'': name,
                        '\''department'\'': f"{department} {dept2}".strip(),
                        '\''attachments_to_send'\'': attachments_to_send  # 要发送的附件
                    }
                    
                    recipients.append(recipient)
                    logger.info(f"添加收件人: {name} ({email})")
                    
            except Exception as e:
                logger.error(f"处理第{idx+2}行时出错: {str(e)}")
                skipped_count += 1
                continue
        
        logger.info(f"解析完成: 成功{len(recipients)}个收件人, 跳过{skipped_count}行")
        
        return {
            '\''success'\'': True,
            '\''recipients'\'': recipients,
            '\''total'\'': len(recipients),
            '\''skipped'\'': skipped_count
        }
        
    except Exception as e:
        logger.error(f"解析Excel失败: {str(e)}")
        return {'\''success'\'': False, '\''error'\'': str(e)}

# 替换原有的parse-excel路由
@app.route('\''/api/parse-excel-v2'\'', methods=['\''POST'\''])
def parse_excel_v2():
    """解析Excel文件 - 正确版本"""
    try:
        if '\''file'\'' not in request.files:
            return jsonify({'\''success'\'': False, '\''message'\'': '\''未找到文件'\''}), 400
        
        file = request.files['\''file'\'']
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['\''UPLOAD_FOLDER'\''], filename)
        file.save(filepath)
        
        result = parse_excel_correct(filepath)
        
        if result['\''success'\'']:
            session['\''recipients'\''] = result['\''recipients'\'']
            
            return jsonify({
                '\''success'\'': True,
                '\''recipients'\'': result['\''recipients'\''],
                '\''message'\'': f"成功导入 {result['\''total'\'']} 个收件人，跳过 {result['\''skipped'\'']} 行",
                '\''stats'\'': {
                    '\''total'\'': result['\''total'\''],
                    '\''skipped'\'': result['\''skipped'\'']
                }
            })
        else:
            return jsonify({
                '\''success'\'': False,
                '\''message'\'': result.get('\''error'\'', '\''解析失败'\'')
            }), 400
            
    except Exception as e:
        logger.error(f"处理Excel文件失败: {str(e)}")
        return jsonify({'\''success'\'': False, '\''message'\'': str(e)}), 500

# 修正发送邮件函数
@app.route('\''/api/send-emails-v2'\'', methods=['\''POST'\''])
def send_emails_v2():
    """发送邮件 - 正确处理附件"""
    try:
        data = request.json
        smtp_config = data.get('\''smtp_config'\'', {})
        subject = data.get('\''subject'\'', '\'''\'')
        content_template = data.get('\''content'\'', '\'''\'')
        
        recipients = session.get('\''recipients'\'', data.get('\''recipients'\'', []))
        
        if not recipients:
            return jsonify({'\''success'\'': False, '\''message'\'': '\''没有收件人'\''}), 400
        
        # SMTP连接
        smtp_host = smtp_config.get('\''smtp_host'\'')
        smtp_port = smtp_config.get('\''smtp_port'\'')
        sender_email = smtp_config.get('\''sender_email'\'')
        password = smtp_config.get('\''password'\'')
        use_ssl = smtp_config.get('\''use_ssl'\'', True)
        
        # 139邮箱自动配置
        if '\''139.com'\'' in sender_email:
            smtp_host = '\''smtp.139.com'\''
            smtp_port = 465
            use_ssl = True
        
        # 建立连接
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
        
        server.login(sender_email, password)
        
        results = []
        success_count = 0
        
        for recipient in recipients:
            try:
                # 创建邮件
                msg = MIMEMultipart()
                msg['\''From'\''] = Header(sender_email, '\''utf-8'\'')
                msg['\''To'\''] = Header(recipient['\''email'\''], '\''utf-8'\'')
                msg['\''Subject'\''] = Header(subject, '\''utf-8'\'')
                
                # 个性化内容
                content = content_template.replace('\''{{name}}'\'', recipient.get('\''name'\'', '\'''\''))
                content = content.replace('\''{{email}}'\'', recipient.get('\''email'\'', '\'''\''))
                content = content.replace('\''{{department}}'\'', recipient.get('\''department'\'', '\'''\''))
                
                msg.attach(MIMEText(content, '\''html'\'', '\''utf-8'\''))
                
                # 添加附件（从Excel解析出的附件）
                for att_path in recipient.get('\''attachments_to_send'\'', []):
                    if os.path.exists(att_path):
                        with open(att_path, '\''rb'\'') as f:
                            part = MIMEBase('\''application'\'', '\''octet-stream'\'')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            filename = os.path.basename(att_path)
                            part.add_header(
                                '\''Content-Disposition'\'',
                                f'\''attachment; filename="{filename}"'\''
                            )
                            msg.attach(part)
                            logger.info(f"添加附件: {filename} 给 {recipient['\''email'\'']}")
                
                # 发送邮件
                server.send_message(msg)
                success_count += 1
                
                results.append({
                    '\''email'\'': recipient['\''email'\''],
                    '\''status'\'': '\''success'\'',
                    '\''message'\'': '\''发送成功'\''
                })
                
            except Exception as e:
                results.append({
                    '\''email'\'': recipient['\''email'\''],
                    '\''status'\'': '\''failed'\'',
                    '\''message'\'': str(e)
                })
        
        server.quit()
        
        return jsonify({
            '\''success'\'': True,
            '\''total'\'': len(recipients),
            '\''success_count'\'': success_count,
            '\''failed_count'\'': len(recipients) - success_count,
            '\''results'\'': results
        })
        
    except Exception as e:
        logger.error(f"发送邮件失败: {str(e)}")
        return jsonify({'\''success'\'': False, '\''message'\'': str(e)}), 500

ATTACHMENT_FIX'

# 添加诊断接口（如果还没有）
docker exec email-backend bash -c 'cat >> /app/app.py << '\''DIAGNOSE'\''
@app.route('\''/api/diagnose'\'', methods=['\''POST'\''])
def diagnose():
    """诊断邮箱配置"""
    try:
        data = request.json
        smtp_config = data.get('\''smtp_config'\'', {})
        sender_email = smtp_config.get('\''sender_email'\'', '\'''\'')
        
        if '\''139.com'\'' in sender_email:
            return jsonify({
                '\''success'\'': True,
                '\''provider'\'': '\''mobile139'\'',
                '\''message'\'': '\''检测到139邮箱'\'',
                '\''config'\'': {
                    '\''smtp_host'\'': '\''smtp.139.com'\'',
                    '\''smtp_port'\'': 465,
                    '\''use_ssl'\'': True,
                    '\''note'\'': '\''请使用16位授权码'\''
                }
            })
        return jsonify({'\''success'\'': True, '\''message'\'': '\''配置正常'\''})
    except Exception as e:
        return jsonify({'\''success'\'': False, '\''error'\'': str(e)})
DIAGNOSE'

# 重启服务
echo "重启后端服务..."
docker restart email-backend

sleep 5

# 测试
echo ""
echo "=================================="
echo "✅ 修复完成！"
echo "=================================="
echo ""
echo "📌 修复内容："
echo "  1. ✅ 保存配置功能已修复"
echo "  2. ✅ 附件逻辑已纠正（附件是发送给收件人的）"
echo ""
echo "🔧 新的API端点："
echo "  • POST /api/sender-configs - 保存配置"
echo "  • GET  /api/sender-configs - 获取配置列表"
echo "  • POST /api/parse-excel-v2 - 正确的Excel解析"
echo "  • POST /api/send-emails-v2 - 正确的邮件发送"
echo ""
echo "📎 附件说明："
echo "  • Excel中的附件会作为邮件附件发送"
echo "  • 如果附件不存在，该收件人会被跳过"
echo "  • 所有附件需要先上传到系统"
echo ""
