# 🎯 CentOS 7 + VMware 部署指南

> 专门为VMware虚拟机上的CentOS 7系统定制的部署方案

## 📋 环境说明

- **虚拟机软件**：VMware Workstation/ESXi
- **操作系统**：CentOS 7
- **Python版本**：需要升级到Python 3（CentOS 7默认是Python 2.7）

## 🚀 快速部署步骤

### 第1步：系统准备

```bash
# 1. 更新系统
sudo yum update -y

# 2. 安装必要工具
sudo yum install -y epel-release
sudo yum install -y wget curl git nano vim net-tools

# 3. 关闭SELinux（避免权限问题）
sudo setenforce 0
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config

# 4. 配置防火墙
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### 第2步：安装Python 3

CentOS 7默认的Python 2.7不能删除（系统依赖），需要安装Python 3：

```bash
# 方法1：使用yum安装Python 3.6（推荐）
sudo yum install -y python3 python3-pip python3-devel

# 验证安装
python3 --version  # 应该显示 Python 3.6.x
pip3 --version

# 创建Python 3软链接（可选）
sudo alternatives --install /usr/bin/python python /usr/bin/python2 50
sudo alternatives --install /usr/bin/python python /usr/bin/python3 60
```

**如果需要更高版本的Python（3.8+）**：

```bash
# 安装开发工具
sudo yum groupinstall -y "Development Tools"
sudo yum install -y openssl-devel bzip2-devel libffi-devel

# 下载并编译Python 3.8
cd /tmp
wget https://www.python.org/ftp/python/3.8.10/Python-3.8.10.tgz
tar -xzf Python-3.8.10.tgz
cd Python-3.8.10
./configure --enable-optimizations
make altinstall  # 使用altinstall避免覆盖系统Python

# 创建软链接
sudo ln -s /usr/local/bin/python3.8 /usr/bin/python3.8
sudo ln -s /usr/local/bin/pip3.8 /usr/bin/pip3.8
```

### 第3步：安装Node.js

```bash
# 方法1：使用NodeSource仓库（推荐）
curl -sL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo yum install -y nodejs

# 验证安装
node --version  # v16.x.x
npm --version

# 方法2：使用nvm（Node版本管理器）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 16
nvm use 16
```

### 第4步：安装Nginx

```bash
# 1. 添加Nginx仓库
sudo yum install -y epel-release

# 2. 安装Nginx
sudo yum install -y nginx

# 3. 启动并设置开机自启
sudo systemctl start nginx
sudo systemctl enable nginx

# 4. 验证安装
sudo systemctl status nginx
curl http://localhost  # 应该看到Nginx欢迎页
```

### 第5步：上传项目文件

#### 方法1：使用SCP（从Windows/Mac）

```powershell
# Windows PowerShell
scp -r .\邮件群发助手\* root@虚拟机IP:/opt/

# Mac/Linux终端
scp -r ./邮件群发助手/* root@虚拟机IP:/opt/
```

#### 方法2：使用VMware共享文件夹

```bash
# 1. 在VMware中设置共享文件夹
# VMware设置 → 选项 → 共享文件夹 → 添加

# 2. 安装VMware Tools（如果未安装）
sudo yum install -y open-vm-tools

# 3. 挂载共享文件夹
sudo mkdir -p /mnt/shared
sudo /usr/bin/vmhgfs-fuse .host:/ /mnt/shared -o allow_other

# 4. 复制文件
sudo cp -r /mnt/shared/邮件群发助手 /opt/email-sender
```

### 第6步：部署应用

创建自动部署脚本：

```bash
cat > /root/deploy-centos7.sh << 'EOF'
#!/bin/bash

echo "=========================================="
echo "CentOS 7 邮件群发助手部署脚本"
echo "=========================================="

# 设置项目路径
PROJECT_DIR="/opt/email-sender"

# 检查Python 3
if ! command -v python3 &> /dev/null; then
    echo "错误：未找到Python 3，请先安装"
    exit 1
fi

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "错误：未找到Node.js，请先安装"
    exit 1
fi

# 创建项目目录
echo "[1/6] 创建项目目录..."
sudo mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 检查项目文件
if [ ! -d "$PROJECT_DIR/backend" ] || [ ! -d "$PROJECT_DIR/frontend" ]; then
    echo "错误：项目文件不存在，请先上传到 $PROJECT_DIR"
    echo "目录结构应该是："
    echo "  $PROJECT_DIR/backend/"
    echo "  $PROJECT_DIR/frontend/"
    exit 1
fi

# 安装Python依赖
echo "[2/6] 安装后端依赖..."
cd $PROJECT_DIR/backend
pip3 install -r requirements.txt
pip3 install gunicorn

# 修复可能的权限问题
sudo chown -R $USER:$USER $PROJECT_DIR

# 构建前端
echo "[3/6] 构建前端..."
cd $PROJECT_DIR/frontend
npm install
npm run build

# 配置Nginx
echo "[4/6] 配置Nginx..."
sudo tee /etc/nginx/conf.d/email-sender.conf > /dev/null << 'NGINX'
server {
    listen 80;
    server_name _;
    
    # 前端静态文件
    location / {
        root /opt/email-sender/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # 后端API代理
    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        client_max_body_size 50M;
    }
}
NGINX

# 测试Nginx配置
sudo nginx -t
if [ $? -ne 0 ]; then
    echo "Nginx配置错误，请检查"
    exit 1
fi

# 重启Nginx
sudo systemctl restart nginx

# 创建后端服务
echo "[5/6] 创建系统服务..."
sudo tee /etc/systemd/system/email-sender.service > /dev/null << 'SERVICE'
[Unit]
Description=Email Sender Backend Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/email-sender/backend
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3 -m gunicorn -w 2 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# 重载systemd并启动服务
sudo systemctl daemon-reload
sudo systemctl enable email-sender
sudo systemctl restart email-sender

# 检查服务状态
echo "[6/6] 检查服务状态..."
sleep 3
if systemctl is-active --quiet email-sender; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    sudo journalctl -u email-sender -n 50
fi

# 显示访问信息
echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo "访问地址："
echo "  内网IP: http://$(ip addr show | grep 'inet ' | grep -v '127.0.0.1' | awk '{print $2}' | cut -d'/' -f1 | head -1)"
echo "  本机访问: http://localhost"
echo ""
echo "管理命令："
echo "  查看后端状态: sudo systemctl status email-sender"
echo "  重启后端: sudo systemctl restart email-sender"
echo "  查看后端日志: sudo journalctl -u email-sender -f"
echo "  查看Nginx日志: sudo tail -f /var/log/nginx/error.log"
echo "=========================================="
EOF

# 赋予执行权限
chmod +x /root/deploy-centos7.sh

# 执行部署
/root/deploy-centos7.sh
```

## 🔧 CentOS 7 特殊配置

### 1. 解决Python依赖问题

CentOS 7可能缺少某些Python开发包：

```bash
# 安装常见的依赖
sudo yum install -y gcc gcc-c++ make
sudo yum install -y python3-devel mysql-devel
sudo yum install -y libxml2-devel libxslt-devel
sudo yum install -y libjpeg-devel zlib-devel

# 如果pip安装包失败，尝试升级pip
pip3 install --upgrade pip
```

### 2. 配置VMware网络

#### 桥接模式（推荐，局域网可访问）
1. VMware设置 → 网络适配器 → 桥接模式
2. 重启网络服务：
```bash
sudo systemctl restart network
```

#### NAT模式（仅主机访问）
1. VMware设置 → 网络适配器 → NAT模式
2. 编辑虚拟网络编辑器，添加端口转发：
   - 主机端口：8080
   - 虚拟机IP：虚拟机的IP
   - 虚拟机端口：80

### 3. 设置静态IP（可选）

```bash
# 编辑网络配置
sudo vi /etc/sysconfig/network-scripts/ifcfg-ens33

# 修改或添加以下内容
BOOTPROTO=static
IPADDR=192.168.1.100
NETMASK=255.255.255.0
GATEWAY=192.168.1.1
DNS1=8.8.8.8
DNS2=8.8.4.4

# 重启网络
sudo systemctl restart network
```

### 4. 优化CentOS 7性能

```bash
# 1. 关闭不必要的服务
sudo systemctl disable postfix
sudo systemctl disable chronyd

# 2. 调整内核参数（优化网络）
sudo tee -a /etc/sysctl.conf << EOF
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 1024
net.ipv4.tcp_fin_timeout = 30
EOF

sudo sysctl -p

# 3. 增加文件描述符限制
sudo tee -a /etc/security/limits.conf << EOF
* soft nofile 65536
* hard nofile 65536
EOF
```

## 🐛 故障排查

### 问题1：Python包安装失败

```bash
# 错误：error: Microsoft Visual C++ 14.0 is required
# 解决：安装开发工具
sudo yum groupinstall -y "Development Tools"
sudo yum install -y python3-devel

# 使用国内镜像源
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题2：Node.js版本太低

```bash
# CentOS 7默认仓库的Node.js版本可能太低
# 解决：使用NodeSource或nvm安装新版本
curl -sL https://rpm.nodesource.com/setup_16.x | sudo bash -
sudo yum install -y nodejs
```

### 问题3：SELinux阻止访问

```bash
# 临时关闭
sudo setenforce 0

# 永久关闭
sudo sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/selinux/config
sudo reboot
```

### 问题4：防火墙问题

```bash
# 查看防火墙状态
sudo firewall-cmd --list-all

# 开放端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --reload

# 或者临时关闭防火墙（不推荐生产环境）
sudo systemctl stop firewalld
```

## 📊 监控和日志

### 查看系统资源

```bash
# 安装监控工具
sudo yum install -y htop iotop nethogs

# 查看CPU和内存
htop

# 查看磁盘IO
iotop

# 查看网络流量
nethogs
```

### 查看应用日志

```bash
# 后端日志
sudo journalctl -u email-sender -f

# Nginx访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx错误日志
sudo tail -f /var/log/nginx/error.log
```

## 🔄 更新和维护

### 更新项目代码

```bash
# 1. 备份当前版本
sudo tar -czf /root/backup-$(date +%Y%m%d).tar.gz /opt/email-sender

# 2. 上传新代码到 /opt/email-sender

# 3. 更新依赖
cd /opt/email-sender/backend
pip3 install -r requirements.txt

# 4. 重新构建前端
cd /opt/email-sender/frontend
npm install
npm run build

# 5. 重启服务
sudo systemctl restart email-sender
sudo systemctl restart nginx
```

### 自动备份脚本

```bash
cat > /root/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/root/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据文件
tar -czf $BACKUP_DIR/data-$DATE.tar.gz \
    /opt/email-sender/backend/uploads \
    /opt/email-sender/backend/attachments \
    /opt/email-sender/backend/templates

# 保留最近7天的备份
find $BACKUP_DIR -name "data-*.tar.gz" -mtime +7 -delete

echo "备份完成: data-$DATE.tar.gz"
EOF

chmod +x /root/backup.sh

# 添加定时任务（每天凌晨2点备份）
echo "0 2 * * * /root/backup.sh" | crontab -
```

## ✅ 部署验证清单

- [ ] CentOS 7系统更新完成
- [ ] Python 3安装成功（python3 --version）
- [ ] Node.js安装成功（node --version）
- [ ] Nginx运行正常（systemctl status nginx）
- [ ] 项目文件上传到/opt/email-sender
- [ ] 后端服务运行正常（systemctl status email-sender）
- [ ] 可以访问前端页面（http://虚拟机IP）
- [ ] API测试通过（http://虚拟机IP/api/health）
- [ ] 邮件发送功能正常
- [ ] 防火墙规则配置正确

## 💡 性能优化建议

### VMware虚拟机优化

1. **分配足够的资源**
   - CPU：2-4核
   - 内存：2-4GB
   - 硬盘：使用SSD，分配20-50GB

2. **安装VMware Tools**
   ```bash
   sudo yum install -y open-vm-tools open-vm-tools-desktop
   ```

3. **启用硬件加速**
   - VMware设置 → 处理器 → 虚拟化引擎
   - 勾选"虚拟化 Intel VT-x/EPT 或 AMD-V/RVI"

### CentOS 7系统优化

```bash
# 1. 使用国内yum镜像源（阿里云）
wget -O /etc/yum.repos.d/CentOS-Base.repo http://mirrors.aliyun.com/repo/Centos-7.repo
yum clean all
yum makecache

# 2. 定期清理日志
echo "0 0 * * 0 /usr/bin/find /var/log -name '*.log' -mtime +30 -delete" | crontab -

# 3. 优化swap使用
echo "vm.swappiness = 10" >> /etc/sysctl.conf
sysctl -p
```

## 🎉 部署成功！

现在您的邮件群发助手已经在CentOS 7虚拟机上成功运行了！

访问地址：`http://虚拟机IP`

如有问题，请查看日志或参考故障排查部分。
