#!/bin/bash
# ==========================================================
#  Coffee Shop OMS - One-click launcher (macOS)
#  双击此文件即可启动系统
# ==========================================================
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  ☕  Coffee Shop OMS  启动中...${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 检查 python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 未找到 python3，请先安装 Python 3.10+${NC}"
    echo "   下载地址: https://www.python.org/downloads/"
    read -p "按回车关闭..." ; exit 1
fi
echo -e "${YELLOW}✓ Python:${NC} $(python3 --version)"

cd src

# 2. 首次运行：建虚拟环境并装依赖
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}首次启动，正在创建虚拟环境并安装依赖（约 30 秒）...${NC}"
    python3 -m venv venv
    ./venv/bin/pip install --quiet --upgrade pip
    ./venv/bin/pip install --quiet -r requirements.txt
    echo -e "${GREEN}✓ 依赖安装完成${NC}"
else
    echo -e "${YELLOW}✓ 已存在虚拟环境，跳过安装${NC}"
fi

# 3. 3 秒后自动打开浏览器
(sleep 3 && open "http://127.0.0.1:5050") &

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  🚀 启动成功！浏览器会自动打开${NC}"
echo -e "${GREEN}  📍 地址: http://127.0.0.1:5050${NC}"
echo -e "${GREEN}  👤 账号: admin / admin123${NC}"
echo -e "${GREEN}  🛑 关闭窗口或按 Ctrl+C 停止服务${NC}"
echo -e "${GREEN}========================================${NC}"

# 4. 用 SQLite 启动（零配置，无需 MySQL）
export DATABASE_URL="sqlite:///coffee.db"
exec ./venv/bin/python app.py
