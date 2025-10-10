# 邮件群发助手

一个功能完善的邮件群发系统，支持Excel批量导入、SMTP群发、附件自动上传等功能。

## 功能特性

✨ **核心功能**
- 📧 基于SMTP协议的邮件群发
- 📊 Excel文件批量导入收件人信息
- ✏️ 手动添加和编辑收件人
- 📎 支持统一附件和个性化附件
- 🎨 个性化邮件内容（支持变量替换）
- 💾 邮件模板保存和管理
- 👤 发件人配置模板（快速切换邮箱账号）
- 🔍 SMTP连接测试和智能诊断
- 📈 实时发送进度追踪
- 🔐 安全的SMTP配置管理
- 🌐 支持多种邮箱服务商（QQ、163、Gmail、中国移动等）

✨ **技术特性**
- 🎯 前后端分离架构
- 💻 现代化UI界面（React + Ant Design）
- 🚀 高性能后端（Python Flask）
- 📱 响应式设计，支持多设备访问

## 技术栈

### 后端
- Python 3.8+
- Flask - Web框架
- Pandas - Excel数据处理
- smtplib - SMTP邮件发送

### 前端
- React 18
- TypeScript
- Vite - 构建工具
- Ant Design - UI组件库

## 快速开始

### 1. 环境要求

- Python 3.8 或更高版本
- Node.js 16 或更高版本
- npm 或 yarn

### 2. 安装依赖

#### 后端
```bash
cd backend
pip install -r requirements.txt
```

#### 前端
```bash
cd frontend
npm install
```

### 3. 启动服务

#### 启动后端服务
```bash
cd backend
python app.py
```
后端服务将运行在 http://localhost:5000

#### 启动前端服务
```bash
cd frontend
npm run dev
```
前端服务将运行在 http://localhost:3000

### 4. 访问应用

打开浏览器访问: http://localhost:3000

## 使用指南

### 步骤1: 配置SMTP

1. 填写SMTP服务器信息
2. 输入发件人邮箱和密码（或授权码）
3. 选择加密方式（SSL/TLS）
4. 点击"测试连接"验证配置

**常见SMTP配置：**

| 邮箱类型 | SMTP地址 | SSL端口 | TLS端口 | 说明 |
|---------|---------|---------|---------|------|
| QQ邮箱 | smtp.qq.com | 465 | 587 | 需使用授权码 |
| 163邮箱 | smtp.163.com | 465 | 25 | 需使用授权码 |
| Gmail | smtp.gmail.com | 465 | 587 | 需开启两步验证 |
| 企业邮箱 | 咨询管理员 | - | - | - |

### 步骤2: 导入收件人

准备Excel文件，包含以下列：

| 列名 | 是否必需 | 说明 |
|-----|---------|------|
| email | 必需 | 收件人邮箱地址 |
| name | 必需 | 收件人姓名 |
| attachment | 可选 | 个性化附件路径 |

**示例Excel：**

| email | name | attachment |
|-------|------|-----------|
| zhang@example.com | 张三 | file1.pdf |
| li@example.com | 李四 | file2.pdf |
| wang@example.com | 王五 | |

上传Excel文件后，系统会自动解析并显示收件人列表。

### 步骤3: 编写邮件

1. **快速应用模板**（可选）
   - 如果有保存的模板，点击模板标签快速应用
   - 系统自动填充主题和内容

2. **编写邮件内容**
   - 输入邮件主题
   - 编写邮件内容
   - 使用 `{{name}}` 插入收件人姓名
   - 使用 `{{email}}` 插入收件人邮箱
   - 上传统一附件（可选）

3. **保存为模板**（可选）
   - 点击"保存为模板"按钮
   - 输入模板名称
   - 下次可直接使用

4. **预览和发送**
   - 预览邮件效果
   - 点击"开始发送"

**邮件内容示例：**
```
尊敬的{{name}}:

您好！这是一封测试邮件，您的邮箱是：{{email}}

此致
敬礼
```

### 步骤4: 查看结果

- 实时查看发送进度
- 查看成功/失败统计
- 查看每封邮件的发送详情
- 可重新发送或返回编辑

## 附件处理说明

### 统一附件
所有收件人都会收到的附件，在步骤3中上传。

### 个性化附件
根据Excel中的`attachment`列为每个收件人添加专属附件：

1. 在Excel中填写附件文件名（如：`contract.pdf`）
2. 将附件文件上传到后端的`attachments`文件夹
3. 系统会自动为对应收件人添加该附件

**支持的路径格式：**
- 相对路径：`document.pdf`（从attachments文件夹查找）
- 绝对路径：`D:/files/document.pdf`

## 目录结构

```
邮件群发助手/
├── backend/                      # 后端服务
│   ├── app.py                   # Flask应用主文件
│   ├── requirements.txt         # Python依赖
│   ├── uploads/                 # Excel上传目录
│   ├── attachments/             # 附件存储目录
│   └── templates/               # 邮件模板存储目录
├── frontend/                    # 前端应用
│   ├── src/
│   │   ├── App.tsx             # 主应用组件
│   │   ├── main.tsx            # 入口文件
│   │   └── index.css           # 样式文件
│   ├── package.json            # 前端依赖
│   └── vite.config.ts          # Vite配置
├── examples/                    # 示例文件
│   ├── recipients.csv          # 收件人模板
│   └── README.md              # 示例说明
├── README.md                   # 项目主文档
├── 快速开始.md                 # 快速上手指南
├── 模板功能说明.md             # 模板功能详细说明
├── 功能更新说明.md             # 功能更新记录
└── 项目结构.md                 # 项目结构说明
```

## 邮件模板功能

### 模板管理

系统支持保存和管理邮件模板，避免重复输入相同内容。

**保存模板：**
1. 编写好邮件主题和内容
2. 点击"保存为模板"按钮
3. 输入模板名称（如"新年祝福"）
4. 点击保存

**使用模板：**
1. 在编写邮件步骤，顶部显示所有模板
2. 点击模板标签，自动填充内容
3. 可以继续编辑模板内容

**删除模板：**
- 点击模板标签的"×"按钮
- 确认删除

**模板包含：**
- 邮件主题
- 邮件内容
- HTML模式设置
- 创建时间

详细使用说明请查看：`模板功能说明.md`

## API接口文档

### 1. 测试SMTP连接
```
POST /api/test-connection
Body: {
  "smtp_config": {
    "smtp_host": "smtp.qq.com",
    "smtp_port": 465,
    "sender_email": "your@email.com",
    "password": "your_password",
    "use_ssl": true
  }
}
```

### 2. 解析Excel文件
```
POST /api/parse-excel
Content-Type: multipart/form-data
Body: file (Excel文件)
```

### 3. 上传附件
```
POST /api/upload-attachment
Content-Type: multipart/form-data
Body: file (附件文件)
```

### 4. 批量发送邮件
```
POST /api/send-emails
Body: {
  "smtp_config": {...},
  "recipients": [...],
  "subject": "邮件主题",
  "content": "邮件内容",
  "common_attachments": [...]
}
```

### 5. 模板管理
```
# 获取所有模板
GET /api/templates

# 保存模板
POST /api/templates
Body: {
  "name": "模板名称",
  "subject": "邮件主题",
  "content": "邮件内容",
  "html_mode": true/false
}

# 删除模板
DELETE /api/templates/{template_id}
```

## 常见问题

### Q1: 提示"连接失败"怎么办？
- 检查SMTP服务器地址和端口是否正确
- 确认网络连接正常
- 确认密码或授权码正确
- 尝试切换SSL/TLS模式

### Q2: QQ邮箱/163邮箱密码错误？
这些邮箱需要使用"授权码"而非登录密码：
- QQ邮箱：设置 → 账户 → 开启SMTP服务 → 生成授权码
- 163邮箱：设置 → POP3/SMTP/IMAP → 开启SMTP服务 → 设置授权密码

### Q3: 如何实现个性化内容？
在邮件内容中使用以下变量：
- `{{name}}` - 替换为收件人姓名
- `{{email}}` - 替换为收件人邮箱

### Q4: Excel格式要求？
- 支持 .xlsx、.xls、.csv 格式
- 必须包含 `email` 和 `name` 列
- 列名严格区分大小写

### Q5: 附件大小限制？
- 单次上传限制：50MB
- 建议单封邮件附件总大小不超过25MB

### Q6: 发送速度慢？
- 邮件群发是顺序发送，发送速度受SMTP服务器限制
- 某些邮箱提供商有发送频率限制
- 建议分批发送大量邮件

## 安全建议

1. ⚠️ 不要将SMTP密码提交到版本控制系统
2. 🔐 定期更换邮箱密码/授权码
3. 🚫 避免在公共网络使用
4. 📝 注意遵守邮件发送相关法律法规
5. ✉️ 确保收件人同意接收邮件

## 开发说明

### 后端开发
```bash
cd backend
# 开启调试模式
python app.py
```

### 前端开发
```bash
cd frontend
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 部署建议

### 生产环境部署

1. **后端部署**
   - 使用Gunicorn或uWSGI运行Flask应用
   - 配置Nginx反向代理
   - 设置环境变量管理敏感信息

2. **前端部署**
   - 运行 `npm run build` 构建静态文件
   - 部署dist目录到Web服务器
   - 配置反向代理到后端API

## 更新日志

### v1.0.0 (2024-10-09)
- ✨ 初始版本发布
- 🎉 支持SMTP邮件群发
- 📊 支持Excel批量导入
- 📎 支持附件功能
- 🎨 现代化UI界面

## 许可证

MIT License

## 技术支持

如有问题或建议，欢迎提交Issue。

---

**开发者提示：** 本系统仅供学习和合法用途使用，请勿用于垃圾邮件发送或其他违法行为。

