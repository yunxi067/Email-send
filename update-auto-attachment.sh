#!/bin/bash

# ================================================
# 邮件系统 - 自动附件识别功能更新脚本
# ================================================

echo "=================================="
echo "📎 更新系统支持自动附件上传"
echo "=================================="

# 1. 进入容器，添加新的路由
echo "添加附件管理功能..."

docker exec email-backend bash -c 'cat >> /app/app.py << '\''ATTACHMENT_EOF'\''

# ===== 附件自动管理功能 =====

@app.route('\''/api/upload-attachments'\'', methods=['\''POST'\''])
def upload_attachments():
    """上传多个附件"""
    try:
        if '\''files'\'' not in request.files:
            return jsonify({'\''success'\'': False, '\''message'\'': '\''没有文件'\''}), 400
        
        files = request.files.getlist('\''files'\'')
        uploaded = []
        
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['\''ATTACHMENT_FOLDER'\''], filename)
                file.save(filepath)
                uploaded.append(filename)
                logger.info(f"上传附件: {filename}")
        
        return jsonify({
            '\''success'\'': True,
            '\''message'\'': f'\''成功上传 {len(uploaded)} 个附件'\'',
            '\''files'\'': uploaded
        })
    except Exception as e:
        return jsonify({'\''success'\'': False, '\''error'\'': str(e)}), 500

@app.route('\''/api/list-attachments'\'', methods=['\''GET'\''])
def list_attachments():
    """列出所有附件"""
    try:
        attachments = []
        att_dir = app.config['\''ATTACHMENT_FOLDER'\'']
        if os.path.exists(att_dir):
            for f in os.listdir(att_dir):
                if os.path.isfile(os.path.join(att_dir, f)):
                    attachments.append(f)
        
        return jsonify({
            '\''success'\'': True,
            '\''attachments'\'': attachments,
            '\''total'\'': len(attachments)
        })
    except Exception as e:
        return jsonify({'\''success'\'': False, '\''error'\'': str(e)}), 500

@app.route('\''/api/smart-parse-excel'\'', methods=['\''POST'\''])  
def smart_parse_excel():
    """智能解析Excel - 自动匹配附件"""
    try:
        # 处理Excel文件
        excel_file = request.files.get('\''excel'\'')
        if not excel_file:
            return jsonify({'\''success'\'': False, '\''message'\'': '\''缺少Excel文件'\''}), 400
        
        # 处理附件文件
        attachment_files = request.files.getlist('\''attachments'\'')
        
        # 保存所有附件
        for att in attachment_files:
            if att.filename:
                filename = secure_filename(att.filename)
                att.save(os.path.join(app.config['\''ATTACHMENT_FOLDER'\''], filename))
                logger.info(f"保存附件: {filename}")
        
        # 保存Excel
        excel_filename = secure_filename(excel_file.filename)
        excel_path = os.path.join(app.config['\''UPLOAD_FOLDER'\''], excel_filename)
        excel_file.save(excel_path)
        
        # 智能解析
        result = smart_match_parse(excel_path)
        
        if result['\''success'\'']:
            session['\''recipients'\''] = result['\''recipients'\'']
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({'\''success'\'': False, '\''error'\'': str(e)}), 500

def smart_match_parse(filepath):
    """智能匹配附件"""
    try:
        df = pd.read_excel(filepath, header=0)
        recipients = []
        skipped = 0
        
        # 获取所有可用附件
        att_dir = app.config['\''ATTACHMENT_FOLDER'\'']
        available = {}
        if os.path.exists(att_dir):
            for f in os.listdir(att_dir):
                fpath = os.path.join(att_dir, f)
                if os.path.isfile(fpath):
                    # 多种匹配键
                    available[f.lower()] = fpath
                    name_only = os.path.splitext(f)[0].lower()
                    available[name_only] = fpath
        
        logger.info(f"可用附件: {list(available.keys())}")
        
        for idx, row in df.iterrows():
            # 获取附件路径
            att_path = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
            
            if not att_path or att_path == '\''nan'\'':
                skipped += 1
                continue
            
            # 智能匹配
            matched = None
            
            # 提取文件名
            if '\''\\\'\'' in att_path:
                fname = att_path.split('\''\\\\'\'')[-1]
            elif '\''/'\'' in att_path:
                fname = att_path.split('\''/'\'' )[-1]
            else:
                fname = att_path
            
            fname_lower = fname.lower()
            name_only = os.path.splitext(fname)[0].lower()
            
            # 尝试匹配
            if fname_lower in available:
                matched = available[fname_lower]
            elif name_only in available:
                matched = available[name_only]
            else:
                # 模糊匹配
                dept = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                if dept and dept != '\''nan'\'':
                    for key, path in available.items():
                        if dept.lower() in key or key in dept.lower():
                            matched = path
                            break
            
            if not matched:
                skipped += 1
                logger.info(f"第{idx+2}行: 未找到附件")
                continue
            
            # 解析邮箱
            emails_str = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
            if not emails_str or emails_str == '\''nan'\'':
                skipped += 1
                continue
            
            emails = re.findall(r'\''[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'\'', emails_str)
            if not emails:
                skipped += 1
                continue
            
            # 解析姓名
            names_str = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            names = re.split(r'\''[、，,;；]'\'', names_str) if names_str != '\''nan'\'' else []
            
            # 创建收件人
            for i, email in enumerate(emails):
                name = names[i].strip() if i < len(names) else email.split('\''@'\'')[0]
                dept = f"{str(row.iloc[0])} {str(row.iloc[1])}".strip()
                
                recipients.append({
                    '\''email'\'': email.strip(),
                    '\''name'\'': name,
                    '\''department'\'': dept,
                    '\''attachment'\'': matched,
                    '\''attachment_name'\'': os.path.basename(matched)
                })
                logger.info(f"匹配成功: {name} - {os.path.basename(matched)}")
        
        return {
            '\''success'\'': True,
            '\''recipients'\'': recipients,
            '\''total'\'': len(recipients),
            '\''skipped'\'': skipped,
            '\''message'\'': f'\''成功匹配 {len(recipients)} 个收件人，跳过 {skipped} 行'\''
        }
    except Exception as e:
        logger.error(f"解析失败: {str(e)}")
        return {'\''success'\'': False, '\''error'\'': str(e)}

ATTACHMENT_EOF'

# 2. 重启后端
echo "重启后端服务..."
docker restart email-backend

# 3. 等待启动
sleep 5

# 4. 测试新接口
echo "测试新功能..."
curl -s http://localhost:5000/api/list-attachments | python3 -m json.tool

echo ""
echo "=================================="
echo "✅ 更新完成！"
echo "=================================="
echo ""
echo "📎 新增功能："
echo "  1. 批量上传附件: POST /api/upload-attachments"
echo "  2. 列出所有附件: GET /api/list-attachments"
echo "  3. 智能解析Excel: POST /api/smart-parse-excel"
echo ""
echo "🎯 使用方法："
echo "  1. 先上传所有附件文件"
echo "  2. 再上传Excel文件"
echo "  3. 系统会自动匹配附件"
echo ""
echo "💡 智能匹配规则："
echo "  - 精确匹配文件名"
echo "  - 不带扩展名匹配"
echo "  - 部门名称模糊匹配"
echo ""
