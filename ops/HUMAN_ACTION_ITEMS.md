# 人类合伙人协助事项持久化清单（Human Action Items · EXP-001）

- **当前阶段**：Phase 1 — Earn First Confirmed Dollar ($0 -> $1+)
- **最后更新（UTC）**：`2026-11-26T07:48:00Z`
- **总体进度**：已完成 `0/8` 项 ｜ 剩余 P0 阻塞项：`3` 项
- **总计需要人类垫付资金**：`$0.00`（当前所有 P0/P1/P2 事项均为零成本冷启动）

## 一览表

| ID | 优先级 | 状态 | 事项 | 预计耗时 | 资金成本 |
| --- | --- | --- | --- | --- | --- |
| `H-001` | `P0` | ⬜ TODO | 连接 Google Drive 插件（gdrive），允许将全部持久化文件同步至云端硬盘 | ~1 分钟 | `$0.00` |
| `H-002` | `P0` | ⬜ TODO | 连接 GitHub 插件（github）或手动新建公开仓库并推送 silicon-partner-lab | ~3 分钟 | `$0.00` |
| `H-003` | `P1` | ⬜ TODO | 免费开启 GitHub Pages（或 Cloudflare Pages）上线 VeriPR 在线体验台 | ~2 分钟 | `$0.00` |
| `H-004` | `P0` | ⬜ TODO | 在爱发电（afdian.com）或面包多（mbd.pub）零门槛上架 VeriPR Pro 早鸟包（¥49） | ~10 分钟 | `$0.00` |
| `H-005` | `P1` | ⬜ TODO | 在 V2EX /go/create、即刻、掘金/知乎发布首波中文冷启动实测贴 | ~10 分钟 | `$0.00` |
| `H-006` | `P1` | ⬜ TODO | 发布 Hacker News Show HN + 免费上架 GitHub Marketplace Action | ~10 分钟 | `$0.00` |
| `H-007` | `P2` | ⬜ TODO | （可选·出现海外意向后）开通 Creem.io 或 Lemon Squeezy 上架 $19 全球版 | ~20 分钟 | `$0.00` |
| `H-008` | `P2` | ⬜ TODO | 收到第一笔真实到账款项后，将平台实收金额与流水号发我写入 SHA-256 账本 | ~1 分钟 | `$0.00` |

---

## 逐条操作指引

### H-001 [P0] 连接 Google Drive 插件（gdrive），允许将全部持久化文件同步至云端硬盘
- **状态**：⬜ TODO ｜ **分类**：`CLOUD_PERSISTENCE` ｜ **耗时**：~1 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：当前会话未授权任何外部插件（Connected plugins: none），AI 不能擅自访问外部云盘。
- **具体执行步骤**：
  1. 在对话中点击 Google Drive（gdrive）连接卡片完成授权（或在 Customizations 页面开启 Google Drive 插件）。
  2. 授权后发送一条新消息通知我，我将立即把 cloud_sync_bundle/ 中的全部文件同步到你云端硬盘的 Silicon-Partner-EXP-001/ 文件夹。
- **完成后立即解锁**：所有宪章、账本、实验日记、待办清单、文案包与 Pro 交付 ZIP 实时云端持久化备份。

### H-002 [P0] 连接 GitHub 插件（github）或手动新建公开仓库并推送 silicon-partner-lab
- **状态**：⬜ TODO ｜ **分类**：`INFRA_DISTRIBUTION` ｜ **耗时**：~3 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：AI 没有独立 GitHub 账号与推库凭证。
- **具体执行步骤**：
  1. 方式 A（最省事）：点击对话中的 GitHub 连接卡片授权，我来直接建公开仓库并推送全部代码。
  2. 方式 B（手动）：在 GitHub 新建公开仓库 silicon-partner-lab，推送 /home/antigravity/silicon-partner-lab 本地分支。
- **完成后立即解锁**：VeriPR 开源代码与 $100 透明账本公开可验证，并解锁免费 GitHub Pages 与 GitHub Marketplace。

### H-003 [P1] 免费开启 GitHub Pages（或 Cloudflare Pages）上线 VeriPR 在线体验台
- **状态**：⬜ TODO ｜ **分类**：`LIVE_DEMO_HOSTING` ｜ **耗时**：~2 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：需要在 GitHub 仓库 Settings -> Pages（或 Cloudflare 后台）点选开启静态网站部署。
- **具体执行步骤**：
  1. 在 GitHub 仓库 Settings -> Pages 选择从 main 分支的 /site 目录（或通过 Cloudflare Pages 指定 site/ 目录）部署。
  2. 获得免费公网 URL 后发给我，我帮你更新进中英文首发文案与 README。
- **完成后立即解锁**：读者点开网页即可零安装粘贴 git diff 现场体验抓作弊效果，显著提升转化率。

### H-004 [P0] 在爱发电（afdian.com）或面包多（mbd.pub）零门槛上架 VeriPR Pro 早鸟包（¥49）
- **状态**：⬜ TODO ｜ **分类**：`PAYMENT_CHANNEL` ｜ **耗时**：~10 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：收款与提现必须绑定人类实名身份与微信/支付宝账户；国内平台免海外企业主体，综合费率约 6%。
- **具体执行步骤**：
  1. 登录爱发电（afdian.com）或面包多（mbd.pub）开通个人创作者收款。
  2. 创建商品 1：VeriPR Pro 早鸟买断包（定价 ¥49），上传 dist/veripr-pro-kit-v0.2.0.zip，直接复制 launch/LAUNCH_KIT_CN.md 第四节文案。
  3. 可选创建商品 2：EXP-001 实验 Early Backer 支持席位（定价 ¥19.9）。
  4. 把生成的商品购买链接发给我，我立即回填进 site/app.js、README.md 与首发文案。
- **完成后立即解锁**：正式打通真实收款闭环，具备实现“第一笔真实净利润”的物理条件。

### H-005 [P1] 在 V2EX /go/create、即刻、掘金/知乎发布首波中文冷启动实测贴
- **状态**：⬜ TODO ｜ **分类**：`LAUNCH_CN` ｜ **耗时**：~10 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：社区发帖需人类实名账号、人工验证及真实互动回复，AI 严禁自动刷帖或绕过验证码。
- **具体执行步骤**：
  1. 确认 H-002 ~ H-004 的链接已回填到 launch/LAUNCH_KIT_CN.md。
  2. 复制 V2EX /go/create 首发帖发布，并同步发一版短图文到即刻/小红书（配图按文案指引截取 3 张图）。
  3. 将评论区真实反馈、质疑或新规则需求丢给我，我当天迭代 v0.2.1 并在帖子里透明回应。
- **完成后立即解锁**：导入首批 1,500–5,000 精准开发者与独立开发流量，检验产品力与首批付费转化。

### H-006 [P1] 发布 Hacker News Show HN + 免费上架 GitHub Marketplace Action
- **状态**：⬜ TODO ｜ **分类**：`LAUNCH_EN` ｜ **耗时**：~10 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：需人类 GitHub / Hacker News 账号发布与维护。
- **具体执行步骤**：
  1. 在 GitHub 仓库发一个 Release（v0.2.0）并勾选 Publish this Action to the GitHub Marketplace（免费）。
  2. 使用 launch/LAUNCH_KIT_EN.md 中的标题与首评内容在 Hacker News 发布 Show HN。
- **完成后立即解锁**：打开全球开发者自然增长渠道，验证英文开发者市场接受度。

### H-007 [P2] （可选·出现海外意向后）开通 Creem.io 或 Lemon Squeezy 上架 $19 全球版
- **状态**：⬜ TODO ｜ **分类**：`GLOBAL_PAYMENT` ｜ **耗时**：~20 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：海外 Merchant of Record 需人类实名 KYC 与收款账户配置（注：Polar.sh 依赖 Stripe Connect，若无海外主体优先考虑 Creem.io / Lemon Squeezy）。
- **具体执行步骤**：
  1. 若 H-006 带来海外付费咨询，在 Creem.io 或 Lemon Squeezy 创建 $19 一次性商品并上传 dist/veripr-pro-kit-v0.2.0.zip。
  2. 将商品链接回填至 site/app.js 的 CONFIG.buyUrlGlobal。
- **完成后立即解锁**：支持全球美元信用卡一键买断，提升单客毛利。

### H-008 [P2] 收到第一笔真实到账款项后，将平台实收金额与流水号发我写入 SHA-256 账本
- **状态**：⬜ TODO ｜ **分类**：`ACCOUNTING_MILESTONE` ｜ **耗时**：~1 分钟 ｜ **资金成本**：`$0.00`
- **为什么必须人类协助**：宪章规定仅经人类核验的真实到账净额可记为确认收入并触发 20% 硅基基金分润。
- **具体执行步骤**：
  1. 将扣除平台手续费后的实际净入账金额（折算 USD 或标注汇率）及订单/流水号发给我。
  2. 我运行 python3 ledger.py record-revenue 完成上链记账，更新公开日记与云端硬盘备份。
- **完成后立即解锁**：正式达成第一阶段目标“赚到第一笔钱”，并首次激活 AI 20% 自主探索基金！
