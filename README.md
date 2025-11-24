# 📧 邮件群发助手

基于Flask和React的企业级邮件群发系统，支持Excel批量导入和个性化附件发送。

## 🚀 功能特点

- ✅ 支持自定义Excel格式导入（前级|备注|附件位置|联系人|邮箱）
- ✅ 自动识别并分发个性化附件
- ✅ 无附件收件人自动跳过
- ✅ 支持多个收件人（顿号、逗号分隔）
- ✅ Excel模板下载功能
- ✅ SMTP连接测试
- ✅ 批量发送进度显示

## 📦 快速部署

### 使用Docker Compose（推荐）

```bash
# 克隆项目
git clone https://github.com/yunxi067/Email-send.git
cd Email-send

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
```

访问：
- 前端界面：http://localhost:3000
- 后端API：http://localhost:5000/api/health

### 本地开发

#### 后端启动
```bash
cd backend
pip install -r requirements.txt
python app.py
```

#### 前端启动
```bash
cd frontend
npm install
npm run dev
```

## 📘 快速开始配置

想要按照 Linux 或 Windows 环境分别完成依赖安装、脚本启动与常见问题排查，请查阅 [docs/quickstart-config.md](docs/quickstart-config.md)。

## 📝 Excel格式说明

系统支持以下Excel格式：

| 列序号 | 列名 | 说明 | 示例 |
|-------|------|------|------|
| A | 前级 | 部门/分公司 | 北京分公司 |
| B | 备注 | 可选备注 | - |
| C | 附件位置 | 附件路径 | D:\附件\文件.xlsx |
| D | 奖金联系人 | 收件人姓名 | 张三、李四 |
| E | 奖金联系人邮箱 | 收件人邮箱 | zhang@company.com |

**注意**：
- 多个收件人用顿号（、）或逗号（，）分隔
- 无附件的行会自动跳过
- 支持下载Excel模板：`GET /api/download-template`

## 🔧 配置说明

### SMTP配置
支持常见邮箱服务商：
- QQ邮箱：smtp.qq.com (端口465，使用授权码)
- 163邮箱：smtp.163.com (端口465，使用授权码)
- 企业邮箱：根据企业配置

### 文件上传限制
- 单个文件最大：50MB
- 支持的附件格式：不限

## 🐳 Docker镜像构建

```bash
# 构建后端镜像
docker build -f Dockerfile.backend -t email-backend .

# 构建前端镜像
docker build -f Dockerfile.frontend -t email-frontend .
```

## 📄 API接口

- `GET /api/health` - 健康检查
- `POST /api/test-connection` - 测试SMTP连接
- `POST /api/parse-excel` - 解析Excel文件
- `GET /api/download-template` - 下载Excel模板
- `POST /api/send-emails` - 批量发送邮件
- `POST /api/upload-attachment` - 上传附件

## 🛠️ 技术栈

- **后端**: Python 3.9 + Flask + pandas
- **前端**: React + TypeScript + Vite
- **部署**: Docker + Docker Compose + Nginx

## 📞 支持

如有问题，请提交Issue或联系管理员。

## 📄 License

MIT