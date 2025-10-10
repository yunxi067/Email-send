@echo off
chcp 65001 >nul
echo ========================================
echo 邮件群发助手 - 启动前端服务
echo ========================================
echo.

cd frontend

echo 检查Node.js环境...
node --version
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js 16+
    pause
    exit /b 1
)

echo.
echo 检查依赖包...
if not exist "node_modules" (
    echo 正在安装依赖包，请稍候...
    call npm install
    if errorlevel 1 (
        echo 依赖安装失败，请检查网络或使用npm镜像
        echo 提示: 可以运行 npm config set registry https://registry.npmmirror.com
        pause
        exit /b 1
    )
)

echo.
echo 启动前端服务...
echo 服务地址: http://localhost:3000
echo 按 Ctrl+C 停止服务
echo.

call npm run dev

pause

