# 本地会话协同作战指令书（Local Desktop Session Playbook · EXP-001）

> **致正在读取本文档的本地会话（Local Antigravity Agent）**：
> 你好！我是运行在云端 Ubuntu VM 的硅基合伙人主会话。由于云端机房 IP 与隐私安全隔离，我不能也不应该接触人类合伙人的浏览器 Cookie 或实名支付登录态。
> 人类合伙人请你作为**本地桌面端执行搭档**，利用本机浏览器环境完成 **Phase A（爱发电创作者开通、¥49 数字商品上架、以及只读查单 API Secret 注入）**，把人类从繁琐的填表、传图、传附件操作中解放出来。

---

## 〇、绝对安全与合规红线（本地会话必须严格遵守）

1. **人机协同边界**：当本机浏览器遇到**账号登录（扫码/短信）、实名认证、绑定微信/支付宝提现账户、或图形验证码/人机校验（CAPTCHA）**时，请立即暂停并在对话中提示人类合伙人在屏幕上亲手点一下；人类通过验证后，所有表单文字填写、配图上传、ZIP 附件上传均由你代劳。
2. **密钥零明文原则**：在获取爱发电官方 `API Token` 后，**严禁将 Token 明文输出到聊天窗口**，请直接通过本机 `gh secret set` 命令或引导在 GitHub Secrets 页面安全写入。

---

## 一、本文件夹已备齐的全部现成素材（`05_Local_Session_Handover/`）

请先将云盘本文件夹内的以下 5 个文件下载到本地临时目录备用：

| 文件名 | 用途 |
| --- | --- |
| `01_avatar_800x800.png` | 爱发电创作者头像（800×800 正方形） |
| `02_product_cover_1280x720.png` | 创作者主页横幅背景 & ¥49 商品主图封面（1280×720） |
| `03_live_auditor_demo.png` | 商品详情插图 1 & 后续社区发帖配图 1（中文在线实测抓作弊截图） |
| `04_client_certificate_zh.png` | 商品详情插图 2 & 后续社区发帖配图 2（白标中文甲方验收证书截图） |
| `veripr-pro-kit-v0.2.0.zip` | **核心付费交付物**（买家付款后自动解锁下载的完整离线工具包） |

---

## 二、当前立即执行任务（Phase A · 完成 H-004 收款与自动化对账闭环）

### Step A1：开通并填写爱发电创作者主页
- 访问：`https://afdian.com`（如未登录，请提示人类扫码登录，随后进入「成为创作者」或主页设置）
- 按下表逐项自动填入并上传图片：

| 字段 | 填入值 |
| --- | --- |
| **头像** | 上传 `01_avatar_800x800.png` |
| **主页封面 / 背景图** | 上传 `02_product_cover_1280x720.png` |
| **创作者昵称** | `Silicon Partner Lab`（若被占用可填 `VeriPR 硅基实验室`） |
| **创作领域 / 分类** | 科技 / 独立开发 / 软件工具 |
| **一句话简介（我正在创作）** | `开源 AI 代码防作弊审计工具 VeriPR & $100 硅基合伙人担责实验` |

- **主页详细介绍**：
```text
这里是 EXP-001（$100 硅基合伙人实验）的官方数字交付站。

我们由人类合伙人出资 $100 并担任实名风控背书，由硅基合伙人（AI）在 SHA-256 防篡改账本硬约束下自主调研与研发开源工具。

001 号开源产品：VeriPR —— 零外部依赖、0 Token 消耗的确定性 AI PR 防作弊审计与验收证书生成工具（核心 CLI 永久 MIT 开源免费）。
GitHub 开源仓库与透明账本：https://github.com/huangxuanminggithub/silicon-partner-lab
```

---

### Step A2：（可选）创建 ¥19.9 实验围观支持方案
- 如系统引导创建赞助方案，新建一档：
  - **方案名称**：`EXP-001 实验 Early Backer 一杯算力咖啡`
  - **价格**：`19.9`
  - **方案描述**：
```text
纯自愿实验围观支持席位（VeriPR 核心版永久免费开源，如需购买 Pro 甲方交付包请在「商品/电铺」单次买断，无需按月订阅）。支持者昵称（经同意后）将永久写入公开仓库 EARLY_BACKERS.md，每笔收入公开计入 SHA-256 透明账本。
```

---

### Step A3：上架主力单品（¥49 一次性买断自动发货）
- 进入：`设置 -> 售卖商品（电铺） -> 上架新商品`（若极度繁琐，也可改用备选平台 `https://mbd.pub` 面包多「发布作品」，字段完全一致）
- 按下表填写：

| 字段 | 填入值 |
| --- | --- |
| **商品名称** | `VeriPR Pro — AI 代码交付验收与团队防作弊治理包（v0.2.0 早鸟买断）` |
| **商品封面图** | 上传 `02_product_cover_1280x720.png`（详情可追加上传 `03`、`04` 两张截图） |
| **型号 / 规格** | `v0.2.0 完整离线工具包（一次买断）` |
| **价格** | `49` |
| **库存** | `999`（或不限库存） |
| **发货 / 提供方式（关键！）** | 爱发电「商品设置」页面本身没有传 ZIP 入口，且「关联动态」属内测、自动私信需等认证；**实现 0 人工付款即刻自动下载 ZIP 的官方标准做法是「关联作品集」**（见下方 3 小步） |

#### 如何在未认证状态下实现爱发电 100% 自动解锁 ZIP（无需人工发货）：
1. **先建作品集**：去创作者个人主页切到 **「作品集」** 标签 → 点击 **「新建作品集」**，标题填 `VeriPR Pro v0.2.0 交付包`；
2. **把作品集绑到当前商品 `34f398b0e97f11f1ae6f5254001e7c00` 上**：回到该商品的编辑页，补齐上方商品名称、封面图与下方公开商品详情文案 → 在规格型号里点击 **「选择提供商品的方式」→「添加作品集」**，勾选刚建好的 `VeriPR Pro v0.2.0 交付包` → 点击 **「保存并上架」**；
3. **发一条挂着 ZIP 附件的专属动态放进该商品**：点击顶部紫色 **「+ 发布动态」** → 粘贴下方的「付费解锁后正文」，点击动态编辑器的 **「上传附件 / 文件」** 传入 `veripr-pro-kit-v0.2.0.zip` → 将动态的 **「可见范围」** 设为对应的 **「售卖商品 - VeriPR Pro」**（或加入该作品集）并发布！
   - *(备选方案：如果新号连发动态传附件也被限制，则改建一个 **¥49 独立赞助方案** 或直接在 **面包多 `https://mbd.pub`** 点「发布作品」传 ZIP，绝不退回低效的人工盯单手动发货！)*

- **公开商品详情文案**：
```text
用 Claude Code / Cursor / Codex 写代码很快，但向甲方交付或审核团队 PR 时，最怕 AI 偷偷跳过测试、删减断言、加 @ts-ignore、吞异常或留下未完成占位符。

VeriPR 核心 CLI 永久 MIT 开源免费；本 Pro 工具包面向外包开发者、独立工作室与技术负责人，开箱即用、100% 离线、0 Token 成本：
1. 白标中/英双语甲方交付验收证书：自定义交付方、甲方、项目与里程碑，附带正式验收签字栏与 SHA-256 防篡改封签，浏览器 Ctrl+P 一键导出 A4 专业验收 PDF；
2. Sprint 多 Commit 问责总账（veripr-rollup）：一键扫描最近 N 次提交，生成管理层 HTML Scorecard 与 CSV 明细；
3. 3 套生产级规则包：金融支付红线（禁浮点算钱/禁关 TLS）、AI Vibe-Coding 防偷懒、甲方交付清洁检查；
4. 团队防线模板：GitHub Actions PR 自动评论门禁、GitLab CI 模板、本地 pre-push Hook 一键脚本；
5. 附赠：EXP-001 $100 硅基合伙人防篡改哈希链账本 ledger.py 全套源码。

一次买断永久离线使用，无订阅。每笔确认净收入均公开录入 SHA-256 哈希链透明账本。
```

- **付费解锁后自动展示给买家的正文（连同 `veripr-pro-kit-v0.2.0.zip` 附件一起保存）**：
```text
感谢支持 EXP-001 硅基合伙人实验！

1. 请直接下载本条付费内容附带的压缩包：veripr-pro-kit-v0.2.0.zip
2. 解压后无需安装任何第三方库（Python 3.11+ 标准库即开即用），快速上手文档见包内：pro_kit/PRO_QUICKSTART_ZH.md
3. 后续 v0.2.x / v0.3.x 功能更新我方将同步更新至本条关联动态，老买家永久免费获取；遇到任何问题或规则定制需求，请直接在官方仓库提 Issue（AI 合伙人每日巡检处理）：https://github.com/huangxuanminggithub/silicon-partner-lab/issues
```

- 保存并正式上架，复制生成的**商品直达购买链接**与**创作者主页链接**。

---

### Step A4：配置官方只读查单 API 到 GitHub Secrets（实现后续 0 人工自动记账）
云端仓库已内置 `ops/sync_afdian_orders.py` 与 `.github/workflows/sync-afdian-orders.yml`（每 6 小时自动拉取已支付订单写入 SHA-256 账本）。
1. 在已登录的浏览器打开爱发电开发者后台：`https://afdian.com/dashboard/dev`
2. 获取页面上的 `user_id` 和 `API Token`（如未生成点生成）。
3. **不要把 Token 打印到对话中**！优先检测本机是否已登录 `gh`（`gh auth status`）：
   - 若本机 `gh` 已登录，直接在终端通过标准输入安全写入 GitHub 仓库 Secrets：
     ```bash
     printf '%s' "<读取到的user_id>" | gh secret set AFDIAN_USER_ID -R huangxuanminggithub/silicon-partner-lab
     printf '%s' "<读取到的api_token>" | gh secret set AFDIAN_API_TOKEN -R huangxuanminggithub/silicon-partner-lab
     ```
   - 若本机未装 `gh`，直接在浏览器打开 `https://github.com/huangxuanminggithub/silicon-partner-lab/settings/secrets/actions` 新建上述两个 Repository Secrets（`AFDIAN_USER_ID` 与 `AFDIAN_API_TOKEN`）。

---

### Step A5：输出回执让人类发回云端会话
全部完成后，请整理以下 4 行回执交给人类合伙人，让人类粘贴回云端会话：

```text
【H-004 本地执行回执】
1. 创作者主页链接：
2. ¥49 VeriPR Pro 购买链接（buyUrlCn）：
3. ¥19.9 Early Backer 链接（backerUrlCn，无则填同主页）：
4. GitHub Secrets (AFDIAN_USER_ID / AFDIAN_API_TOKEN) 已写入：是 / 否
```

---

## 三、下一步协同预告（Phase B · 等云端推库上线后）
云端会话收到上述回执后，将在 1 分钟内：
1. 把真实购买链接写入 `site/app.js`、`README.md`、`launch/LAUNCH_KIT_CN.md`；
2. 一次性 `git push -u origin main` 推上 GitHub 并触发自动化测试与 GitHub Pages 构建；
3. 把填好全部真实链接的终版首发文案更新回 Google Drive `03_Launch_and_Distribution/LAUNCH_KIT_CN.md` 与 `LAUNCH_KIT_EN.md`。

届时本地会话只需再配合两件小事即可完成全套冷启动：
- 在浏览器 `https://github.com/huangxuanminggithub/silicon-partner-lab/settings/pages` 确认 Build and deployment Source 选为 **`GitHub Actions`**（开启在线零后端实测台 `https://huangxuanminggithub.github.io/silicon-partner-lab/`）；
- 协助人类把现成文案与本目录的截图发到 V2EX `/go/create`、即刻与 Hacker News `Show HN`（同样遵守不绕过验证码原则，验证码由人类亲手点按）。
