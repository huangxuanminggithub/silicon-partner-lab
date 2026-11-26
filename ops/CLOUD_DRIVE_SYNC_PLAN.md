# 云端硬盘（Google Drive）持久化同步方案

- **目标云盘根目录**：`Silicon-Partner-EXP-001/`
- **当前同步状态**：`WAITING_FOR_GDRIVE_PLUGIN`（本地 `cloud_sync_bundle/` 与 `SYNC_MANIFEST.json` 已就绪，待人类合伙人授权 `gdrive` 插件后即刻自动上传）

## 同步目录结构
- `Silicon-Partner-EXP-001/CHARTER.md` — 实验宪章
- `Silicon-Partner-EXP-001/LEDGER.json` — SHA-256 防篡改财务账本
- `Silicon-Partner-EXP-001/JOURNAL.md` — 公开实验日记
- `Silicon-Partner-EXP-001/ops/HUMAN_ACTION_ITEMS.md` & `.json` — 逐条人类协助待办清单
- `Silicon-Partner-EXP-001/research/` — 市场扫描与变现渠道调研报告
- `Silicon-Partner-EXP-001/launch/` — 中英文冷启动发布文案包（V2EX / 即刻 / HN / 爱发电）
- `Silicon-Partner-EXP-001/dist/veripr-pro-kit-v0.2.0.zip` & `SHA256SUMS.txt` — 可直接上架售卖的 Pro 交付 ZIP 包
- `Silicon-Partner-EXP-001/site/` — VeriPR 零后端在线体验台官网源码
- `Silicon-Partner-EXP-001/SYNC_MANIFEST.json` — 全量文件 SHA-256 校验清单

## 授权后同步机制
一旦你通过对话中的 Google Drive 卡片连接 `gdrive` 插件并发消息告知我，我将：
1. 使用官方 `gdrive` CLI 创建/定位 `Silicon-Partner-EXP-001/` 文件夹；
2. 逐文件上传并校验远端文件 ID，将 `H-001` 标记为 `DONE`；
3. 后续每当 `LEDGER.json`、`JOURNAL.md` 或 `HUMAN_ACTION_ITEMS.md` 更新，自动增量同步到云端硬盘。
