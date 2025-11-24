# ⚙️ 快速开始配置指南（Linux / Windows）

本指南拆分为 Linux 与 Windows 两种环境，帮助你在几分钟内完成邮件群发助手的本地/内网部署与基础配置。除常规手动部署外，还给出了 Docker Compose 与常见排障建议，方便不同团队复用。

---

## 1. 通用准备

### 1.1 需要提前准备的账号与素材
- **SMTP 账号与授权码**：支持 QQ、163、139、Outlook 等；企业邮箱需自备 SMTP Host、端口、是否启用 SSL/TLS 等信息。
- **收件人 Excel**：可通过 `GET /api/download-template` 或前端向导下载模板，按既定列结构填写。
- **附件文件**：所有个性化附件建议统一放在 `backend/attachments` 目录下，Excel 中只填写文件名或与之对应的路径，方便脚本自动匹配。
- **可选：公共附件**（所有人都需要）：可通过前端「常用附件」上传功能维护。

### 1.2 关键目录速览

| 目录 | 作用 | 是否自动创建 | 备注 |
| --- | --- | --- | --- |
| `backend/uploads/` | 存放上传后的 Excel | ✅ | 仅运行期间使用，可定期清理 |
| `backend/attachments/` | 存放个性化附件 | ✅ | 建议提前拷贝所有附件文件以便匹配 |
| `backend/templates/` | Excel 模板及生成文件 | ✅ | 当首次调用模板下载接口时自动生成 |
| `frontend/src/` | React + Ant Design 前端代码 | - | 通过 `npm run dev/build` 构建 |
| `docker-compose.yml` | 容器化编排文件 | - | 用于一键启动前后端 + Nginx |

### 1.3 默认端口与服务
- **后端 Flask API**：`http://localhost:5000`，所有接口挂载在 `/api/*`。
- **前端 Vite Dev Server**：`http://localhost:3000`，通过 `vite.config.ts` 将 `/api` 代理到 5000 端口。
- **Docker/Nginx 部署**：容器内仍使用 3000/5000，对外暴露端口可在 `docker-compose.yml` 中调整。

> 若需在生产环境暴露服务，请在操作系统或防火墙层面开放对应端口，并根据需要配置反向代理（例如仓库中的 `nginx.conf`）。

---

## 2. Linux 快速开始

### 2.1 环境要求
| 组件 | 推荐版本 |
| --- | --- |
| 操作系统 | 任意主流 Linux 发行版 (Ubuntu 20.04+, CentOS 7+, Debian 11+) |
| Python | 3.9 ~ 3.12（与 `backend/requirements.txt` 兼容） |
| Node.js / npm | Node 18 LTS / npm 9+ |
| Git | 2.30+ |
| Docker & Docker Compose | 可选（用于容器化部署） |

```bash
# Ubuntu 示例：安装常用依赖
sudo apt update && sudo apt install -y python3 python3-venv python3-pip nodejs npm git
```

> 国内网络可按需配置 pip / npm 镜像（如 TUNA、npmmirror），以加速依赖安装。

### 2.2 克隆代码
```bash
git clone https://github.com/yunxi067/Email-send.git
cd Email-send
```

### 2.3 配置并启动后端
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

> 如果需要手动加速，可执行 `pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple` 后再安装依赖。

准备个性化附件：
```bash
mkdir -p attachments uploads templates
cp /path/to/your/files/*.xlsx attachments/
```

启动 Flask API（默认监听 `0.0.0.0:5000`）：
```bash
python app.py
```

健康检查：
```bash
curl http://localhost:5000/api/health
```

### 2.4 配置并启动前端
在新终端中：
```bash
cd Email-send/frontend
npm install
npm run dev
```

- 前端地址：`http://localhost:3000`
- `/api` 请求会被代理至 `http://localhost:5000`
- 如需前端访问远程后端，可编辑 `frontend/vite.config.ts`，将 `proxy['/api'].target` 修改为实际后端地址。

### 2.5 Docker Compose 一键方案（可选）
```bash
cd Email-send
docker-compose up -d --build
# 查看状态
docker-compose ps
```
- 首次运行会自动构建 `email-backend` 与 `email-frontend` 镜像，由 Nginx 统一对外暴露。
- 更新代码后可执行 `docker-compose up -d --build` 重新构建。

### 2.6 常用维护操作
| 场景 | 命令 |
| --- | --- |
| 查看实时日志 | `docker-compose logs -f` 或 `tail -f backend/*.log` |
| 停止 Docker 服务 | `docker-compose down` |
| 清理旧镜像 | `docker rmi email-backend email-frontend` |
| 关闭前端 dev server | `Ctrl+C` |
| 关闭后端 | `Ctrl+C` |

---

## 3. Windows 快速开始

### 3.1 环境要求
| 组件 | 推荐版本 |
| --- | --- |
| 操作系统 | Windows 10/11 (64 位) |
| Python | 3.11.x 或 3.12.x（避免 3.13 兼容性问题） |
| Node.js / npm | Node 18 LTS（安装包会自带 npm 9+） |
| Git for Windows | 2.40+（可选，亦可直接下载 ZIP） |
| VS Code / PowerShell | 可选（便于开发调试） |

> 安装 Python 时记得勾选 “Add python.exe to PATH”。

### 3.2 获取代码
```powershell
git clone https://github.com/yunxi067/Email-send.git
cd Email-send
```
或直接下载 ZIP，解压至无空格/中文目录（例如 `D:\Email-send`）。

### 3.3 启动后端
仓库根目录下提供了 `start_backend.bat` 脚本，可双击或在 PowerShell 中执行：
```powershell
.\start_backend.bat
```
脚本会自动：
1. 检查 Python 是否可用。
2. 安装 Flask、pandas、openpyxl 等依赖（如首次运行）。
3. 提供常见故障排查指引（例如 Python 3.13 不兼容）。

如果更倾向于手动执行，可参考：
```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

> 若依赖安装缓慢，可执行 `pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt` 使用清华镜像。

### 3.4 启动前端
同样可直接运行 `start_frontend.bat`，它会：
1. 检测 Node.js。
2. 自动执行 `npm install`（若 `node_modules` 不存在）。
3. 启动 Vite (`npm run dev`) 并输出可访问地址。

手动步骤：
```powershell
cd frontend
npm install
npm run dev
```

如果需要切换 npm 镜像，可先执行：
```powershell
npm config set registry https://registry.npmmirror.com
```

### 3.5 放置附件与模板
- 将所有个性化附件拷贝到 `backend\attachments`，保持与 Excel 中引用的文件名一致。
- 若 Excel 中使用绝对路径（如 `D:\附件\xx.xlsx`），系统会尝试在 `backend\attachments` 中匹配同名文件；若不存在会跳过该行。
- 通过前端的「Excel 模板下载」按钮可生成 `backend\templates\邮件发送模板.xlsx`，方便复用。

### 3.6 访问与验证
- 浏览器访问 `http://localhost:3000`，按照四步向导完成 SMTP 配置 → 导入 Excel → 录入邮件正文 → 发送。
- 「SMTP 连接测试」会实时调用后端 `/api/test-connection`，可用于验证授权码是否正确。
- 所有解析、上传、发送日志会输出在执行 `python app.py` 的终端中，必要时可截图或复制日志排查。

---

## 4. 常见配置与问题排查

| 场景 | 解决方式 |
| --- | --- |
| 前端需要访问远程后端 | 编辑 `frontend/vite.config.ts`，将 `proxy['/api'].target` 设置为远端地址（如 `http://10.0.0.5:5000`），重新运行 `npm run dev/build`。 |
| 新增/调整邮箱服务商参数 | 修改 `backend/app.py` 中的 `EMAIL_PROVIDERS` 字典，可自定义 SMTP Host、端口以及是否强制使用授权码。修改后重启后端。 |
| 上传 Excel 后提示“无附件，跳过” | 确认 Excel 第 C 列（附件位置）可解析出真实文件名，并已将文件复制到 `backend/attachments`。 |
| 需要公共附件 | 在前端第三步（撰写邮件）中通过「上传公共附件」按钮添加，后端会保存到 `backend/attachments` 并在每封邮件中附带。 |
| 想要一次性部署到服务器 | 推荐在服务器上执行 `deploy.sh` 或 `docker-compose up -d --build`。记得放置附件、配置域名/反代，并在防火墙开放 80/443/3000/5000 等端口。 |
| 想清理临时文件 | 停止后端后，可安全删除 `backend/uploads` 中的 Excel 副本，附件目录建议保留。 |

如需更多自定义（Nginx、HTTPS、自动化脚本等），可在现有基础上扩展仓库内的 `Dockerfile.*`、`nginx.conf` 或 Shell 脚本。祝使用顺利！
