@echo off
chcp 65001 >nul
echo ========================================
echo 邮件群发助手 - 启动后端服务
echo ========================================
echo.

cd backend

echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

REM 检查Python版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo 检测到Python版本: %PYTHON_VERSION%

echo.
echo 检查依赖包...
pip show flask >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    echo.
    echo 提示: 如果安装失败，请查看 backend\安装依赖问题解决方案.md
    echo 推荐使用Python 3.11或3.12版本以获得最佳兼容性
    echo.
    
    REM 尝试使用国内镜像加速
    pip install -i https://pypi.tuna.tsinghua.edu.cn/simple Flask flask-cors pandas openpyxl xlrd Werkzeug
    if errorlevel 1 (
        echo.
        echo ============================================
        echo 依赖安装失败！
        echo ============================================
        echo.
        echo 可能的原因:
        echo 1. 使用了Python 3.13（太新，兼容性问题）
        echo 2. 网络连接问题
        echo 3. 缺少编译工具
        echo.
        echo 解决方案:
        echo 1. 【推荐】卸载Python 3.13，安装Python 3.11或3.12
        echo    下载: https://www.python.org/downloads/
        echo.
        echo 2. 查看详细解决方案:
        echo    backend\安装依赖问题解决方案.md
        echo.
        echo 3. 使用虚拟环境:
        echo    python -m venv venv
        echo    venv\Scripts\activate
        echo    pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo 启动后端服务...
echo 服务地址: http://localhost:5000
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python app.py

pause

