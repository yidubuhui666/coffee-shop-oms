# ☕ 咖啡店订单管理系统

西南大学 2024 级计算机科学与技术 ·《数据库原理与应用》课程设计  
Coffee Shop Order Management System (Flask + SQLAlchemy + SQLite/MySQL)

**团队成员**
- **114 杨帆**（组长）— 数据库设计、Flask 后端、集成测试
- **092 许跃骞** — 前端模板与样式、演示数据、5 张截图、报告撰写、一键启动脚本

---

## 🚀 一键启动

| 平台 | 操作 |
|---|---|
| **macOS** | 双击 `启动咖啡店系统.command` |
| **Windows** | 双击 `启动咖啡店系统.bat` |

首次启动会自动创建虚拟环境、安装依赖（约 30 秒），然后浏览器自动打开 `http://127.0.0.1:5050`。

**登录账号**：
- 管理员：`admin / admin123`
- 咖啡师：`barista / barista123`
- 收银员：`cashier / cashier123`

---

## 🛠️ 前置环境

仅需 **Python 3.10+**：
- macOS：系统自带（或 `brew install python`）
- Windows：[官网下载](https://www.python.org/downloads/) — 安装时务必勾选 **"Add Python to PATH"**

---

## 📂 目录结构

```
├── 启动咖啡店系统.command / .bat    ← 一键启动脚本
├── readme.txt                       ← 老师查阅用的简短说明
├── docs/                            ← 实验报告 + ER 图 + 界面截图
│   ├── 114Yangfan-...docx           (英文实验报告)
│   ├── ER_Diagram.png
│   └── screenshots/
├── sql/                             ← 数据库 DDL/DML 脚本
│   ├── schema.sql                   (9 表 + 2 视图 + 3 触发器 + 存储过程)
│   └── data.sql
└── src/                             ← Flask 应用源码
    ├── app.py / models.py / config.py
    ├── requirements.txt
    ├── templates/                   (12 个 Jinja2 模板)
    └── static/
        ├── style.css
        └── img/products/            (12 张商品图)
```

---

## 👥 协作流程（GitHub + Git）

### 一次性设置（每人各做一次）

```bash
# 1) Clone 仓库（把 URL 换成你们仓库的地址）
git clone https://github.com/<你的用户名>/<仓库名>.git
cd <仓库名>

# 2) 配置身份
git config user.name "你的名字"
git config user.email "你的邮箱"
```

### 日常开发流程

```bash
# 1) 开始干活前：拉最新代码
git pull

# 2) 改文件...（用 VS Code / PyCharm / 任何编辑器）

# 3) 看一下都改了啥
git status
git diff

# 4) 提交本地
git add .
git commit -m "feat: 加了导出 Excel 功能"

# 5) 推到云端
git push
```

### Commit 信息规范（建议）

| 前缀 | 含义 | 例 |
|---|---|---|
| `feat:` | 新功能 | `feat: 菜单页加搜索框` |
| `fix:`  | 修 bug | `fix: 库存负数不报错的问题` |
| `docs:` | 改文档/报告 | `docs: 报告第 3 章补 SQL 截图` |
| `style:`| 仅样式/格式 | `style: 统一按钮圆角` |
| `refactor:` | 重构 | `refactor: 抽离 Order 业务逻辑` |
| `chore:` | 杂项 | `chore: 升级 Flask 版本` |

### 任务认领（GitHub Issues）

在仓库 Issues 标签下新建任务，互相 @ 对方，标 Label（`bug` / `enhancement` / `report` 等）。提交 commit 时带上 `#issue编号`，会自动关联。

---

## 📦 提交给老师

把整个项目压缩成 zip 即可（实际是 `git archive` 也行）：

```bash
# 排除 venv / __pycache__ / coffee.db
zip -r submission.zip . -x "venv/*" "*/__pycache__/*" "*.pyc" "instance/*" ".git/*" ".DS_Store"
```

或者直接用根目录已有的 `docs/` + `sql/` + `src/` 目录手动打包。

---

## 📝 课程项目信息

- **项目名**：咖啡店订单管理系统 / Coffee Shop Order Management System
- **团队成员**：
  - 114 杨帆（组长）
  - 092 许跃骞
- **截止**：2026 年 5 月 31 日
- **报告位置**（每人一份，内容相同）：
  - `docs/114Yangfan-Coffee Shop Order Management System.docx`
  - `docs/092Xuyueqian-Coffee Shop Order Management System.docx`
