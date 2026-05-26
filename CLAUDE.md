# Coffee Shop OMS — 协作约定

## 关键约束：数据库改动必须配套种子脚本

本仓库由两人共同协作开发（许跃骞 + 杨帆），各自在本地维护独立的 MySQL 数据库，
代码通过 GitHub 同步，但**数据库内容不进仓库**（见 `.gitignore` 中的 `*.db` 等规则）。

**任何对数据库的 SQL 改动，都必须同时提供可重复执行的 Python 种子脚本**，
确保协作者只需 `git pull` + 运行脚本即可让数据保持一致。

### 具体规则

1. **新增表**：写在 `models.py`，由 `db.create_all()` 自动建表（无需额外脚本）。
2. **修改已有表结构**（ALTER TABLE，例如加列、改类型）：
   - 必须新增 `src/migration_xxxx.py` 脚本，使用 `db.session.execute(text("ALTER TABLE ..."))`，
     并在执行前 `SHOW COLUMNS` 判断是否已存在，做到幂等。
   - 在 commit message 里注明「⚠️ 协作者需运行 migration_xxxx.py」。
3. **插入/修改业务数据**（INSERT、UPDATE）：
   - 写在 `src/seed_*.py` 脚本中，逻辑必须幂等（先查再插，或先清空再重建）。
   - 文件命名约定：
     - `seed_relations.py`  —— 关系表（配方、会员折扣等）
     - `seed_more.py`       —— 演示数据（订单、会员）
     - `seed_admin.py`      —— 特定账号
     - 新功能再新建 `seed_<功能>.py`
4. **种子脚本的注释开头必须写清**：朋友执行什么命令、什么时候需要重跑。
5. **每次 push 前自检清单**：
   - [ ] 改了数据库结构？→ 有对应的 migration_xxxx.py 吗？
   - [ ] 改了业务数据？→ 有对应的 seed_*.py 吗？
   - [ ] 脚本是幂等的吗？重复执行不会报错或重复插入吗？

## 项目运行环境

- **本地 MySQL**：`root` / `YOUR_MYSQL_PASSWORD` / 数据库 `coffee_shop`
- **MySQL 可执行文件路径**：`D:\mysql\mysql-8.0.45-winx64\bin\mysql.exe`
- **项目路径**：`C:\Users\许yq\coffee-shop-oms\`
- **启动方式**：桌面快捷方式 `启动咖啡店系统.lnk` 或运行 `src/app.py`
- **访问地址**：http://127.0.0.1:5050
- **GitHub 仓库**：https://github.com/yidubuhui666/coffee-shop-oms

## 当前账号

| 用户名 | 密码 | 姓名 | 角色 |
|--------|------|------|------|
| admin | admin123 | 杨帆 | ADMIN |
| barista | barista123 | 李明 | BARISTA |
| cashier | cashier123 | 王磊 | CASHIER |
| xuyueqian | xuyq123 | 许跃骞 | ADMIN |
| xyq | 070203 | 许跃骞 | ADMIN |
