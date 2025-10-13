# -*- coding: utf-8 -*-
"""
Excel处理模块 - 自动识别格式并跳过无附件行
"""
import pandas as pd
import os
import re
import logging

logger = logging.getLogger(__name__)

def parse_excel_with_attachment_check(filepath):
    """
    解析Excel并只返回有附件的收件人
    
    Excel格式:
    A列: 前级
    B列: 部门
    C列: 附件位置
    D列: 奖金联系人
    E列: 奖金联系人邮箱
    """
    try:
        df = pd.read_excel(filepath, header=0)
        recipients = []
        skipped = 0
        
        for idx, row in df.iterrows():
            # 获取附件路径
            attachment_path = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else ""
            
            # 没有附件，跳过
            if not attachment_path or attachment_path == 'nan' or attachment_path.strip() == '':
                skipped += 1
                logger.info(f"第{idx+2}行: 无附件，跳过")
                continue
            
            # 获取邮箱
            emails_str = str(row.iloc[4]) if len(row) > 4 and pd.notna(row.iloc[4]) else ""
            if not emails_str or emails_str == 'nan':
                skipped += 1
                continue
            
            # 解析邮箱地址
            email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            emails = re.findall(email_pattern, emails_str)
            
            if not emails:
                skipped += 1
                continue
            
            # 解析姓名
            names_str = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else ""
            names = re.split(r'[、，,;；]', names_str) if names_str and names_str != 'nan' else []
            names = [n.strip() for n in names if n.strip()]
            
            # 处理附件路径
            filename = attachment_path.split('\\')[-1] if '\\' in attachment_path else attachment_path
            local_path = f'/app/attachments/{filename}'
            
            # 部门信息
            dept1 = str(row.iloc[0]) if pd.notna(row.iloc[0]) else ""
            dept2 = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else ""
            department = f"{dept1} {dept2}".strip()
            
            # 为每个邮箱创建收件人
            for i, email in enumerate(emails):
                name = names[i] if i < len(names) else email.split('@')[0]
                recipients.append({
                    'email': email.strip(),
                    'name': name,
                    'department': department,
                    'attachment': local_path
                })
        
        return {
            'success': True,
            'recipients': recipients,
            'total': len(recipients),
            'skipped': skipped
        }
        
    except Exception as e:
        logger.error(f"解析Excel失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'recipients': [],
            'total': 0,
            'skipped': 0
        }
