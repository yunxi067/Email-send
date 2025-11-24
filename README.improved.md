# 📧 邮件群发助手 (改进版)

基于Flask和React的企业级邮件群发系统，支持Excel批量导入、个性化附件发送和模板管理。

## 🚀 新功能特点

### 🔒 安全性改进
- ✅ 环境变量配置，避免硬编码密钥
- ✅ 输入验证和文件类型检查
- ✅ 文件名安全处理，防止路径遍历
- ✅ SQL注入防护（使用参数化查询）
- ✅ CORS策略配置
- ✅ 文件大小限制

### 🗄️ 数据持久化
- ✅ SQLite数据库存储模板和配置
- ✅ 邮件发送日志记录
- ✅ 发送统计和审计功能
- ✅ 模板和发件人配置管理

### 🏗️ 代码架构改进
- ✅ 模块化组件设计
- ✅ TypeScript类型安全
- ✅ 统一的API服务层
- ✅ 配置文件分离
- ✅ 错误处理标准化

### 🐳 部署优化
- ✅ 多阶段Docker构建
- ✅ 健康检查机制
- ✅ 环境变量管理
- ✅ 自动化启动脚本
- ✅ Redis缓存支持（可选）

### 📊 用户体验
- ✅ 实时发送进度显示
- ✅ 批量操作支持
- ✅ 结果导出功能
- ✅ 失败重试机制
- ✅ 响应式设计

## 📦 快速开始

### 方式一：使用改进版Docker（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd Email-send

# 使用改进版启动脚本
./start-improved.sh start

# 或者手动启动
docker-compose -f docker-compose.improved.yml up -d
```

### 方式二：开发环境

```bash
# 启动开发环境
./start-improved.sh dev

# 或者分别启动
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

# 前端（新终端）
cd frontend
npm install
npm run dev
```

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件（或使用 `.env.example` 作为模板）：

```bash
# Flask应用配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# CORS配置
CORS_ORIGINS=http://localhost:3000

# 文件上传配置
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=uploads
ATTACHMENT_FOLDER=attachments
TEMPLATE_FOLDER=templates

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/email_sender.log

# 邮件发送配置
MAX_RECIPIENTS_PER_BATCH=100
EMAIL_RATE_LIMIT=10

# 数据库配置
DATABASE_PATH=email_sender.db
```

### SMTP配置

支持常见邮箱服务商的自动配置：

- **QQ邮箱**: smtp.qq.com (端口465，使用授权码)
- **163邮箱**: smtp.163.com (端口465，使用授权码)  
- **139邮箱**: smtp.139.com (端口465，自动识别)

## 📁 项目结构

```
Email-send/
├── backend/                 # 后端代码
│   ├── app.py              # 主应用文件（已改进）
│   ├── config.py           # 配置管理（新增）
│   ├── validators.py       # 输入验证（新增）
│   ├── database.py        # 数据库管理（新增）
│   ├── requirements.txt   # Python依赖
│   └── .env.example      # 环境变量示例
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── components/    # React组件（新增）
│   │   ├── types.ts      # TypeScript类型（新增）
│   │   ├── api.ts        # API服务层（新增）
│   │   └── App.tsx       # 主应用（原版）
│   ├── .env.development   # 开发环境变量（新增）
│   ├── .env.production    # 生产环境变量（新增）
│   └── package.json
├── Dockerfile.improved     # 改进的Dockerfile（新增）
├── docker-compose.improved.yml  # 改进的Docker Compose（新增）
├── start-improved.sh      # 改进的启动脚本（新增）
└── README.improved.md      # 本文件
```

## 📄 API接口

### 核心接口
- `GET /api/health` - 健康检查
- `POST /api/test-connection` - 测试SMTP连接
- `POST /api/parse-excel` - 解析Excel文件
- `POST /api/send-emails` - 批量发送邮件
- `POST /api/upload-attachment` - 上传附件
- `GET /api/download-template` - 下载Excel模板

### 模板管理
- `GET /api/templates` - 获取模板列表
- `POST /api/templates` - 创建模板
- `DELETE /api/templates/<id>` - 删除模板

### 发件人配置
- `GET /api/sender-configs` - 获取配置列表
- `POST /api/sender-configs` - 创建配置
- `DELETE /api/sender-configs/<id>` - 删除配置

## 🔒 安全特性

1. **输入验证**: 所有用户输入都经过严格验证
2. **文件安全**: 文件类型和大小限制，安全的文件名处理
3. **SQL安全**: 使用参数化查询防止SQL注入
4. **配置安全**: 敏感信息通过环境变量配置
5. **CORS保护**: 可配置的跨域策略
6. **日志审计**: 完整的操作日志记录

## 📊 监控和日志

### 日志文件位置
- 应用日志: `logs/email_sender.log`
- 数据库: `email_sender.db`
- 上传文件: `uploads/`
- 附件文件: `attachments/`

### 健康检查
```bash
# 检查服务状态
curl http://localhost:5000/api/health

# 查看Docker日志
docker-compose -f docker-compose.improved.yml logs -f
```

## 🛠️ 开发指南

### 后端开发
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 代码规范
- 后端遵循PEP 8规范
- 前端使用TypeScript和ESLint
- 提交前运行测试和代码检查

## 🔧 故障排除

### 常见问题

1. **Docker启动失败**
   ```bash
   # 检查Docker状态
   docker info
   
   # 重新构建镜像
   docker-compose -f docker-compose.improved.yml build --no-cache
   ```

2. **邮件发送失败**
   - 检查SMTP配置
   - 确认授权码正确
   - 查看应用日志

3. **文件上传失败**
   - 检查文件大小限制
   - 确认文件类型支持
   - 检查目录权限

## 📝 更新日志

### v2.0.0 (改进版)
- 🔒 全面安全性改进
- 🗄️ 添加数据持久化
- 🏗️ 重构代码架构
- 🐳 优化Docker部署
- 📊 改进用户体验
- 🔧 添加监控和日志

### v1.0.0 (原版)
- 基础邮件发送功能
- Excel文件解析
- 简单的Web界面

## 📞 支持

如有问题，请：
1. 查看日志文件
2. 检查配置文件
3. 提交Issue或联系管理员

## 📄 License

MIT License