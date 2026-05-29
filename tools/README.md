# tools/ —— 一次性 / 辅助脚本

本目录存放**跑完即弃**的脚本，不参与日常运行，仅作历史留存与偶尔复用。

> ⚠️ 与 `src/seed_*.py` 不同：`seed_*` 是数据同步必须保留、协作者要运行的脚本，留在 `src/`。
> 本目录里的脚本是开发过程中的一次性工具，**不需要协作者运行**。

| 脚本 | 用途 |
|------|------|
| `update_template_urls.py` | 一次性给模板 `url_for()` 批量加 Blueprint 前缀（重构时用过） |
| `gen_images.py` / `map_to_unique_images.py` / `update_dedupe_images.py` / `update_new_images.py` | 商品图片生成 / 去重 / 映射 |
| `revert_to_safe_images.py` | 回退到安全的占位图 |
| `update_staff.py` | 早期手工调整员工的脚本（现已被 `src/seed_admin.py` + `seed_cleanup_staff.py` 取代） |
| `batch_ai_*.ps1` / `scrape_*.py` / `scrape_images.ps1` | AI 生图 / 网络抓图的实验脚本 |
