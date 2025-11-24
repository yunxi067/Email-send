import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Any
import json

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.environ.get('DATABASE_PATH', 'email_sender.db')
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 邮件模板表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS email_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    subject TEXT NOT NULL,
                    content TEXT NOT NULL,
                    html_mode BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 发件人配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sender_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    smtp_host TEXT NOT NULL,
                    smtp_port INTEGER NOT NULL,
                    sender_email TEXT NOT NULL,
                    sender_name TEXT NOT NULL,
                    use_ssl BOOLEAN DEFAULT 1,
                    use_tls BOOLEAN DEFAULT 0,
                    html_mode BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 发送日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS send_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    recipient_email TEXT NOT NULL,
                    recipient_name TEXT,
                    subject TEXT NOT NULL,
                    status TEXT NOT NULL,  # success, failed, skipped
                    message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_send_logs_batch_id ON send_logs(batch_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_send_logs_status ON send_logs(status)')
            
            conn.commit()
    
    # 邮件模板相关方法
    def create_template(self, name: str, subject: str, content: str, html_mode: bool = False) -> int:
        """创建邮件模板"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO email_templates (name, subject, content, html_mode, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, subject, content, html_mode, datetime.now()))
            conn.commit()
            return cursor.lastrowid
    
    def get_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_templates ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_template(self, template_id: int) -> Optional[Dict[str, Any]]:
        """获取单个模板"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM email_templates WHERE id = ?', (template_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_template(self, template_id: int, **kwargs) -> bool:
        """更新模板"""
        if not kwargs:
            return False
        
        kwargs['updated_at'] = datetime.now()
        set_clause = ', '.join([f'{key} = ?' for key in kwargs.keys()])
        values = list(kwargs.values()) + [template_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE email_templates SET {set_clause} WHERE id = ?', values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_template(self, template_id: int) -> bool:
        """删除模板"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM email_templates WHERE id = ?', (template_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # 发件人配置相关方法
    def create_sender_config(self, name: str, **config) -> int:
        """创建发件人配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sender_configs (name, smtp_host, smtp_port, sender_email, 
                                         sender_name, use_ssl, use_tls, html_mode, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, config.get('smtp_host'), config.get('smtp_port'), 
                  config.get('sender_email'), config.get('sender_name'),
                  config.get('use_ssl', True), config.get('use_tls', False),
                  config.get('html_mode', False), datetime.now()))
            conn.commit()
            return cursor.lastrowid
    
    def get_sender_configs(self) -> List[Dict[str, Any]]:
        """获取所有发件人配置"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sender_configs ORDER BY created_at DESC')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_sender_config(self, config_id: int) -> Optional[Dict[str, Any]]:
        """获取单个发件人配置"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sender_configs WHERE id = ?', (config_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_sender_config(self, config_id: int, **kwargs) -> bool:
        """更新发件人配置"""
        if not kwargs:
            return False
        
        kwargs['updated_at'] = datetime.now()
        set_clause = ', '.join([f'{key} = ?' for key in kwargs.keys()])
        values = list(kwargs.values()) + [config_id]
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE sender_configs SET {set_clause} WHERE id = ?', values)
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_sender_config(self, config_id: int) -> bool:
        """删除发件人配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sender_configs WHERE id = ?', (config_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    # 发送日志相关方法
    def create_send_log(self, batch_id: str, recipient_email: str, recipient_name: str,
                       subject: str, status: str, message: str = None) -> int:
        """创建发送日志"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO send_logs (batch_id, recipient_email, recipient_name, subject, status, message)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (batch_id, recipient_email, recipient_name, subject, status, message))
            conn.commit()
            return cursor.lastrowid
    
    def get_send_logs(self, batch_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取发送日志"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            if batch_id:
                cursor.execute('''
                    SELECT * FROM send_logs WHERE batch_id = ? 
                    ORDER BY sent_at DESC LIMIT ?
                ''', (batch_id, limit))
            else:
                cursor.execute('''
                    SELECT * FROM send_logs 
                    ORDER BY sent_at DESC LIMIT ?
                ''', (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_send_statistics(self, batch_id: str = None) -> Dict[str, Any]:
        """获取发送统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            if batch_id:
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM send_logs WHERE batch_id = ? 
                    GROUP BY status
                ''', (batch_id,))
            else:
                cursor.execute('''
                    SELECT status, COUNT(*) as count 
                    FROM send_logs GROUP BY status
                ''')
            
            results = dict(cursor.fetchall())
            total = sum(results.values())
            
            return {
                'total': total,
                'success': results.get('success', 0),
                'failed': results.get('failed', 0),
                'skipped': results.get('skipped', 0)
            }