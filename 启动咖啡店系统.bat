@echo off
chcp 936
setlocal enabledelayedexpansion
title Coffee Shop OMS - 咖啡店订单管理系统

cd /d "%~dp0"

echo ========================================
echo   Coffee Shop OMS  启动中...
echo ========================================

REM 1. 检查 Python
python --version
if errorlevel 1 (
    echo.
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo        下载地址: https://www.python.org/downloads/
    echo        安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

cd src

REM 2. 首次运行：建虚拟环境并装依赖
if not exist "venv\" (
    echo.
    echo [...] 首次启动，正在创建虚拟环境并安装依赖（约 30 秒）...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
) else (
    echo [OK] 已存在虚拟环境，跳过安装
    call venv\Scripts\activate.bat
)

REM 3. 启动浏览器（延迟 3 秒，等 Flask 就绪）
start "" /b cmd /c "timeout /t 3 /nobreak && start http://127.0.0.1:5050"

echo ========================================
echo   启动成功！浏览器会自动打开
echo   地址: http://127.0.0.1:5050
echo   账号: admin / admin123
echo   关闭本窗口或按 Ctrl+C 停止服务
echo ========================================

REM 4. 用 SQLite 启动
set DATABASE_URL=sqlite:///coffee.db
python app.py

pause
