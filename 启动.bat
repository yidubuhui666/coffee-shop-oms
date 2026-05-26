@echo off
chcp 936 >nul
title Coffee Shop OMS

cd /d "%~dp0src"

echo ========================================
echo   Coffee Shop OMS 启动中...
echo ========================================

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请安装 Python 3.10+
    pause
    exit /b 1
)

if not exist "venv\" (
    echo [1] 首次启动，安装依赖中（约30秒）...
    python -m venv venv
    .\venv\Scripts\pip.exe install -r requirements.txt --quiet
    echo [OK] 依赖安装完成
) else (
    echo [OK] 环境已就绪
)

echo [2] 启动服务中...
start "" /b cmd /c "timeout /t 4 /nobreak >nul && start http://127.0.0.1:5050"

echo ========================================
echo   地址: http://127.0.0.1:5050
echo   账号: admin/admin123  或  xuyueqian/xuyq123
echo   关闭此窗口即停止服务
echo ========================================

set DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@127.0.0.1:3306/coffee_shop?charset=utf8mb4
.\venv\Scripts\python.exe app.py

pause
