import pytest
import tempfile
import os
from app import create_app
from database import DatabaseManager
from validators import validate_smtp_config, is_safe_email, validate_recipients

@pytest.fixture
def app():
    """创建测试应用"""
    app, db = create_app('testing')
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        yield app, db

@pytest.fixture
def client(app):
    """创建测试客户端"""
    app_instance, _ = app
    return app_instance.test_client()

@pytest.fixture
def temp_db():
    """创建临时数据库"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    db = DatabaseManager(db_path)
    yield db
    
    # 清理
    os.unlink(db_path)

class TestValidators:
    """测试验证器"""
    
    def test_validate_smtp_config_valid(self):
        """测试有效的SMTP配置"""
        config = {
            'smtp_host': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'test@gmail.com',
            'sender_name': 'Test User',
            'password': 'password123'
        }
        errors = validate_smtp_config(config)
        assert len(errors) == 0
    
    def test_validate_smtp_config_invalid(self):
        """测试无效的SMTP配置"""
        config = {
            'smtp_host': '',
            'smtp_port': 'invalid',
            'sender_email': 'invalid-email',
            'sender_name': '',
            'password': ''
        }
        errors = validate_smtp_config(config)
        assert len(errors) > 0
    
    def test_is_safe_email_valid(self):
        """测试有效邮箱"""
        assert is_safe_email('test@example.com')
        assert is_safe_email('user.name+tag@domain.co.uk')
    
    def test_is_safe_email_invalid(self):
        """测试无效邮箱"""
        assert not is_safe_email('invalid-email')
        assert not is_safe_email('@domain.com')
        assert not is_safe_email('user@')
    
    def test_validate_recipients_valid(self):
        """测试有效收件人"""
        recipients = [
            {'email': 'test1@example.com', 'name': 'Test 1'},
            {'email': 'test2@example.com', 'name': 'Test 2', 'attachment': 'file.pdf'}
        ]
        errors, valid = validate_recipients(recipients)
        assert len(errors) == 0
        assert len(valid) == 2
    
    def test_validate_recipients_invalid(self):
        """测试无效收件人"""
        recipients = [
            {'email': 'invalid-email', 'name': 'Test 1'},
            {'email': '', 'name': 'Test 2'}
        ]
        errors, valid = validate_recipients(recipients)
        assert len(errors) > 0
        assert len(valid) == 0

class TestDatabase:
    """测试数据库操作"""
    
    def test_create_template(self, temp_db):
        """测试创建模板"""
        template_id = temp_db.create_template(
            name='Test Template',
            subject='Test Subject',
            content='Test Content'
        )
        assert template_id > 0
    
    def test_get_templates(self, temp_db):
        """测试获取模板列表"""
        temp_db.create_template('Test 1', 'Subject 1', 'Content 1')
        temp_db.create_template('Test 2', 'Subject 2', 'Content 2')
        
        templates = temp_db.get_templates()
        assert len(templates) == 2
        assert templates[0]['name'] in ['Test 1', 'Test 2']
    
    def test_create_sender_config(self, temp_db):
        """测试创建发件人配置"""
        config_id = temp_db.create_sender_config(
            name='Test Config',
            smtp_host='smtp.test.com',
            smtp_port=587,
            sender_email='test@test.com',
            sender_name='Test'
        )
        assert config_id > 0
    
    def test_create_send_log(self, temp_db):
        """测试创建发送日志"""
        log_id = temp_db.create_send_log(
            batch_id='test-batch',
            recipient_email='test@example.com',
            recipient_name='Test',
            subject='Test Subject',
            status='success'
        )
        assert log_id > 0

class TestAPI:
    """测试API端点"""
    
    def test_health_check(self, client):
        """测试健康检查"""
        app_instance, _ = client.application
        response = app_instance.test_client().get('/api/health')
        assert response.status_code == 200
    
    def test_get_providers(self, client):
        """测试获取邮箱服务商"""
        app_instance, _ = client.application
        response = app_instance.test_client().get('/api/email-providers')
        assert response.status_code == 200
        data = response.get_json()
        assert 'mobile139' in data
    
    def test_test_connection_invalid(self, client):
        """测试无效的SMTP连接"""
        app_instance, _ = client.application
        response = app_instance.test_client().post('/api/test-connection', 
            json={
                'smtp_config': {
                    'smtp_host': 'invalid.host',
                    'smtp_port': 587,
                    'sender_email': 'test@test.com',
                    'password': 'test'
                }
            })
        assert response.status_code in [400, 500]
    
    def test_parse_excel_no_file(self, client):
        """测试没有文件的Excel解析"""
        app_instance, _ = client.application
        response = app_instance.test_client().post('/api/parse-excel')
        assert response.status_code == 400

if __name__ == '__main__':
    pytest.main([__file__, '-v'])