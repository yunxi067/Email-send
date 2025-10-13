# -*- coding: utf-8 -*-
"""
增强版app.py - 支持自动附件上传
"""
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
import zipfile
import shutil

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ATTACHMENT_FOLDER'] = 'attachments'
app.config['TEMPLATE_FOLDER'] = 'templates'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# 创建必要的目录
for folder in ['uploads', 'attachments', 'templates', 'temp']:
    if not os.path.exists(folder):
        os.makedirs(folder)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/api/upload-batch-attachments', methods=['POST'])
def upload_batch_attachments():
    """批量上传附件（支持ZIP包）"""
    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'}), 400
        
        files = request.files.getlist('files')
        uploaded_files = []
        
        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename)
            
            # 如果是ZIP文件，解压所有内容
            if filename.endswith('.zip'):
                zip_path = os.path.join('temp', filename)
                file.save(zip_path)
                
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    # 解压到附件目录
                    zip_ref.extractall(app.config['ATTACHMENT_FOLDER'])
                    # 获取解压的文件列表
                    for name in zip_ref.namelist():
                        if not name.endswith('/'):  # 排除目录
                            uploaded_files.append(os.path.basename(name))
                
                os.remove(zip_path)  # 删除临时ZIP文件
            else:
                # 直接保存文件
                filepath = os.path.join(app.config['ATTACHMENT_FOLDER'], filename)
                file.save(filepath)
                uploaded_files.append(filename)
        
        logger.info(f"批量上传成功: {uploaded_files}")
        
        return jsonify({
            'success': True,
            'message': f'成功上传 {len(uploaded_files)} 个文件',
            'files': uploaded_files
        })
        
    except Exception as e:
        logger.error(f"批量上传失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/parse-excel-with-attachments', methods=['POST'])
def parse_excel_with_attachments():
    """解析Excel并同时上传相关附件"""
    try:
        # 获取Excel文件
        if 'excel' not in request.files:
            return jsonify({'success': False, 'message': '未找到Excel文件'}), 400
        
        excel_file = request.files['excel']
        excel_filename = secure_filename(excel_file.filename)
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)
        excel_file.save(excel_path)
        
        # 获取附件文件（如果有）
        attachment_files = request.files.getlist('attachments')
        for att_file in attachment_files:
            if att_file.filename:
                att_filename = secure_filename(att_file.filename)
                att_path = os.path.join(app.config['ATTACHMENT_FOLDER'], att_filename)
                att_file.save(att_path)
                logger.info(f"保存附件: {att_filename}")
        
        # 解析Excel
        result = parse_custom_excel_with_smart_match(excel_path)
        
        if result['success']:
            session['recipients'] = result['recipients']
            
            message = f"成功导入 {result['total']} 个有附件的收件人"
            if result['skipped'] > 0:
                message += f"，跳过 {result['skipped']} 行（无附件或无效数据）"
            
            return jsonify({
                'success': True,
                'recipients': result['recipients'],
                'message': message,
                'stats': {
                    'total': result['total'],
                    'skipped': result['skipped'],
                    'matched_files': result.get('matched_files', [])
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': f"解析失败: {result.get('error', '未知错误')}"
            }), 400
            
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

def parse_custom_excel_with_smart_match(filepath):
    """智能匹配附件的Excel解析"""
    try:
        df = pd.read_excel(filepath, header=0)
        recipients = []
        skipped_count = 0
        matched_files = []
        
        # 获取所有已上传的附件
        attachment_dir = app.config['ATTACHMENT_FOLDER']
        available_attachments = {}
        if os.path.exists(attachment_dir):
            for file in os.listdir(attachment_dir):
                # 创建多种匹配键（文件名、不带扩展名的文件名等）
                available_attachments[file.lower()] = os.path.join(attachment_dir, file)
                name_without_ext = os.path.splitext(file)[0].lower()
                available_attachments[name_without_ext] = os.path.join(attachment_dir, file)
        
        logger.info(f"可用附件: {list(available_attachments.keys())}")
        
        for idx, row in df.iterrows():
            try:
                # 获取各列数据
                department = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
                dept2 = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
                attachment_path = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
                contact_names = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
                contact_emails = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
                
                # 智能匹配附件
                matched_attachment = None
                if attachment_path and attachment_path != 'nan':
                    # 提取文件名（处理Windows路径）
                    if '\\' in attachment_path:
                        filename = attachment_path.split('\\')[-1]
                    elif '/' in attachment_path:
                        filename = attachment_path.split('/')[-1]
                    else:
                        filename = attachment_path
                    
                    # 尝试多种匹配方式
                    filename_lower = filename.lower()
                    name_without_ext = os.path.splitext(filename)[0].lower()
                    
                    # 精确匹配
                    if filename_lower in available_attachments:
                        matched_attachment = available_attachments[filename_lower]
                        matched_files.append(filename)
                    # 不带扩展名匹配
                    elif name_without_ext in available_attachments:
                        matched_attachment = available_attachments[name_without_ext]
                        matched_files.append(filename)
                    # 模糊匹配（包含关键词）
                    else:
                        # 尝试用部门名称匹配
                        dept_keywords = [department, dept2]
                        for keyword in dept_keywords:
                            if keyword and keyword != 'nan':
                                for avail_name, avail_path in available_attachments.items():
                                    if keyword in avail_name or avail_name in keyword.lower():
                                        matched_attachment = avail_path
                                        matched_files.append(os.path.basename(avail_path))
                                        break
                            if matched_attachment:
                                break
                
                # 没有找到附件，跳过
                if not matched_attachment:
                    skipped_count += 1
                    logger.info(f"第{idx+2}行: 未找到匹配的附件 ({attachment_path})，跳过")
                    continue
                
                # 解析邮箱
                if not contact_emails or contact_emails == 'nan':
                    skipped_count += 1
                    continue
                
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, str(contact_emails))
                
                if not emails:
                    skipped_count += 1
                    continue
                
                # 解析姓名
                names = []
                if contact_names and contact_names != 'nan':
                    names = re.split(r'[、，,;；]', contact_names)
                    names = [n.strip() for n in names if n.strip()]
                
                # 为每个邮箱创建收件人记录
                for i, email in enumerate(emails):
                    name = names[i] if i < len(names) else email.split('@')[0]
                    
                    recipient = {
                        'email': email.strip(),
                        'name': name,
                        'department': f"{department} {dept2}".strip(),
                        'attachment': matched_attachment,
                        'attachment_name': os.path.basename(matched_attachment)
                    }
                    
                    recipients.append(recipient)
                    logger.info(f"添加收件人: {name} ({email}) - 附件: {os.path.basename(matched_attachment)}")
                    
            except Exception as e:
                logger.error(f"处理第{idx+2}行时出错: {str(e)}")
                skipped_count += 1
                continue
        
        logger.info(f"解析完成: 成功{len(recipients)}个收件人, 跳过{skipped_count}行")
        
        return {
            'success': True,
            'recipients': recipients,
            'total': len(recipients),
            'skipped': skipped_count,
            'matched_files': list(set(matched_files))
        }
        
    except Exception as e:
        logger.error(f"解析Excel失败: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/api/list-attachments', methods=['GET'])
def list_attachments():
    """列出所有已上传的附件"""
    try:
        attachment_dir = app.config['ATTACHMENT_FOLDER']
        attachments = []
        
        if os.path.exists(attachment_dir):
            for file in os.listdir(attachment_dir):
                file_path = os.path.join(attachment_dir, file)
                if os.path.isfile(file_path):
                    attachments.append({
                        'name': file,
                        'size': os.path.getsize(file_path),
                        'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
                    })
        
        return jsonify({
            'success': True,
            'attachments': attachments,
            'total': len(attachments)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/clear-attachments', methods=['POST'])
def clear_attachments():
    """清空所有附件"""
    try:
        attachment_dir = app.config['ATTACHMENT_FOLDER']
        if os.path.exists(attachment_dir):
            for file in os.listdir(attachment_dir):
                file_path = os.path.join(attachment_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        
        return jsonify({'success': True, 'message': '附件已清空'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# 保留原有的所有其他路由...
# （这里包含原app.py的其他所有功能）
