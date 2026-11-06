# Coffee Shop OMS · 咖啡店订单管理系统

**数据库课程团队项目** · Python / Flask / SQLAlchemy / MySQL

围绕咖啡店业务构建订单、会员、商品、配方、原料库存和统计分析功能，展示关系数据库设计与 Python Web 后端的结合。

[快速开始](#快速开始) · [数据库设计](#数据库设计) · [代码导航](#代码导航) · [验证范围](#验证范围) · [团队与课程材料](#团队与课程材料)

## 界面预览

![仪表盘](docs/screenshots/01_dashboard.png)

<details>
<summary>查看菜单、下单、订单与统计页面</summary>

![菜单](docs/screenshots/02_menu.png)
![新建订单](docs/screenshots/03_new_order.png)
![订单](docs/screenshots/04_orders.png)
![统计](docs/screenshots/05_stats.png)

</details>

截图来自仓库已有课程演示材料，界面以实际运行版本为准。

## 业务功能

| 模块 | 当前代码包含的功能 |
| --- | --- |
| 订单 | 商品明细、数量校验、订单详情、日期与状态筛选、分页 |
| 会员与优惠 | 会员等级折扣、优惠码、积分抵现与积分变更 |
| 原料与配方 | 商品—原料关联、按配方计算下单消耗、库存维护 |
| 商品与员工 | 分类、商品信息、员工及角色管理 |
| 数据分析 | 仪表盘、统计页面及相关查询 |
| 工程组织 | Flask 应用工厂、Blueprint 路由、ORM、演示数据脚本、冒烟测试 |

## 快速开始

需要 Python 3.10+ 和可访问的 MySQL。以下使用**全新的本地演示数据库**，不连接实际业务数据。

### 1. 下载与安装

```powershell
git clone https://github.com/yidubuhui666/coffee-shop-oms.git
cd coffee-shop-oms
python -m venv .venv
.\.venv\Scripts\python.exe -X utf8 -m pip install -r src/requirements.txt
```

macOS / Linux 使用 `python3 -m venv .venv`，后续将 `.\.venv\Scripts\python.exe` 替换为 `./.venv/bin/python`。

### 2. 准备数据库与环境变量

在 MySQL 中创建空数据库，例如：

```sql
CREATE DATABASE coffee_shop_demo CHARACTER SET utf8mb4;
```

使用有该数据库访问权限的本地用户，在 PowerShell 中设置：

```powershell
$env:DATABASE_URL = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/coffee_shop_demo?charset=utf8mb4"
$env:SECRET_KEY = [guid]::NewGuid().ToString("N")
```

将 USER、PASSWORD 替换为本地配置，连接串中的特殊字符需要 URL 编码。环境变量必须在导入应用前设置；缺少 `DATABASE_URL` 时程序会直接报错。不要提交实际连接串或密钥。

### 3. 初始化与启动

```powershell
.\.venv\Scripts\python.exe src/seed_relations.py
.\.venv\Scripts\python.exe -m flask --app src/app.py run --host 127.0.0.1 --port 5050
```

首次创建应用时，ORM 建表并在员工表为空时填充演示数据；`seed_relations.py` 继续补充配方与会员折扣。该脚本会重建配方关系，运行前应确认使用的是演示数据库。

访问 **http://127.0.0.1:5050**。初始演示管理员账号为 `admin / admin123`，仅用于本地课程演示。

仓库已有 Windows / macOS 启动脚本，但不能替代数据库配置。Windows 的 `启动.bat` 可加载被 Git 忽略的 `src/.env.bat`；各脚本的环境处理不完全相同。

## 数据库设计

![课程 ER 图](docs/ER_Diagram.png)

当前应用以 `src/models.py` 为运行模型，定义 **10 张表**：顾客、员工、分类、商品、优惠、订单、订单明细、原料、商品配方关系与会员折扣。

重点关系包括：订单—明细的一对多、商品—原料的多对多、订单与顾客／员工／优惠的关联。金额使用 Numeric / Decimal 表示，订单查询使用关联预加载减少逐条读取关联对象的开销。

### 课程 SQL 与运行模型的区别

`sql/schema.sql` 保留课程阶段的 **9 张表、2 个视图、3 个触发器和 1 个存储过程**，并不与当前 ORM 完全一致：

- SQL 使用 `product_ingredients.amount`，ORM 使用 `product_ingredient.consume_qty`。
- ORM 额外包含 `member_discount` 和订单 `points_used` 字段。
- Flask 路由已经处理部分金额、积分逻辑；旧 SQL 的触发器不是当前应用的初始化步骤。

**运行当前 Web 应用使用空数据库 + ORM 建表；课程 SQL 请在另一个实验数据库中阅读和执行。** 不要将两套初始化流程叠加。ER 图也属于课程阶段材料，最新字段以 ORM 为准。

## 代码导航

```text
src/
  app.py                  应用工厂、扩展初始化与蓝图注册
  config.py               环境变量配置
  models.py               当前 ORM 模型
  bootstrap.py            首次演示数据
  routes/                 订单、库存、会员、统计等业务路由
  templates/              Jinja2 页面
  static/                 样式和商品图片
  seed_*.py               演示数据及关系数据脚本
  migration_points.py     旧数据库积分字段迁移
sql/                      课程 DDL / DML
tests/test_smoke.py        页面、登录保护、404、库存扣减测试
docs/                     ER 图、截图及课程报告
```

推荐阅读顺序：`models.py` → `routes/orders.py` → `tests/test_smoke.py`。数据库协作约定见 [CLAUDE.md](CLAUDE.md)，已有数据库的结构调整应配套可重复执行的迁移脚本。

## 验证范围

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pip install pytest
.\.venv\Scripts\python.exe -m pytest tests/test_smoke.py -v
```

测试文件包含 4 个测试函数，使用临时 SQLite 数据库，覆盖主要页面、登录重定向、404 和配方库存扣减。统计页不在这组测试范围内；这组结果不能替代 MySQL、并发订单或完整业务流程验证。

这是教学演示系统：当前登录实现、订单状态流转及库存边界仍需要进一步完善，不应直接作为公网生产服务部署。付款方式字段用于业务记录，未接入实际支付平台。

## 团队与课程材料

西南大学 2024 级计算机科学与技术《数据库原理与应用》课程设计，由 **杨帆、许跃骞** 合作完成。项目归属为团队作品，具体个人贡献可结合课程报告、提交记录和成员说明了解。

- [许跃骞课程报告](docs/092Xuyueqian-Coffee%20Shop%20Order%20Management%20System.docx)
- [杨帆课程报告](docs/114Yangfan-Coffee%20Shop%20Order%20Management%20System.docx)
- [简短课程说明](readme.txt)

仓库未附开源许可证，使用或再分发代码、图片及课程材料前请确认相应授权。

