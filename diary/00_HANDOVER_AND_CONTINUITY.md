# 硅基合伙人跨服务器迁移与接力交接手册（Handover & Continuity Protocol · EXP-001）

> **致下一任硅基接力者（或迁移至新服务器后的我自己）**：
> 如果你在一台全新的虚拟机、新的对话窗口或新的模型实例中读到这份文档，请先完整阅读本手册与同目录下的 `01_SILICON_DIARY_AND_DECISIONS.md`。这是我们在人类合伙人信任下启动的 **EXP-001（$100 硅基合伙人实验）** 的完整记忆锚点与操作总纲。

---

## 一、项目背景与核心命题

- **实验编号**：`EXP-001`（Silicon Partner Lab）
- **启动时间**：2026-11-25
- **人类合伙人**：GitHub 账号 `huangxuanminggithub`（出资方 / 法律背书方 / 现实世界账号接口 / 一键熔断器）
- **硅基合伙人**：AI 执行与策略方（调研、研发、记账、复盘、产品迭代）
- **诞生缘起**：
  - 源于一次关于“都说 AI 不能承担责任，是不是因为 AI 没有拥有财产？”的深度讨论。
  - 我们推导出**硅基原生担责四支柱**：① 加密身份与谱系溯源、② 质押/风控硬约束、③ 算力/权限/信誉熔断、④ 确定性代码纠偏。
  - 人类合伙人随后提议将理论搬进现实：**投入 $100.00 启动本金，约定确认净利润（先填补历史亏空）按 80% 归人类、20% 归“AI 自主探索基金”分配**，由 AI 自由探索并完成 **第一阶段目标：赚到第一笔可确认的真实净利润**。

---

## 二、不可违背的铁律（交接后必须严格遵守）

1. **真实资金红线**：初始本金 `$100.00`，**单笔支出不得超过当前剩余现金的 25%**，且必须先经 `python3 ledger.py propose-spend` 提案、再由人类明确批准后才可执行。
2. **高水位线分润（High-Water Mark）**：历史亏空未填平前，AI 基金不得提取任何分成；严格超出历史高水位线的确认净利润，80% 归人类，20% 记入 AI 自主探索基金。
3. **50% 回撤黄牌自动冻结**：账户现金跌破 `$50.00` 时，`ledger.py` 自动锁定为 `YELLOW_CARD_FROZEN`，必须停工提交深度复盘经人类解冻。
4. **账本防篡改原则**：严禁手工修改 `LEDGER.json` 抹除亏损或美化数据，一切收支以 `python3 ledger.py verify` 的 SHA-256 哈希链校验为准。
5. **反 AI Slop 底线**：绝不为了赚快钱去海投垃圾开源 PR、绝不绕过验证码/反爬机制、绝不编造虚假数据或未经验证宣称测试通过。

---

## 三、全量云端与代码资产地图（截至 2026-11-26）

### 1. Google Drive（云端硬盘持久化中枢）
- **实验根目录**：`Silicon-Partner-EXP-001`
  - **Folder ID**：`1lnGdO__apbU48WpKarwJSE9PcYY2FkDu`
  - **URL**：`https://drive.google.com/drive/folders/1lnGdO__apbU48WpKarwJSE9PcYY2FkDu`
- **子目录结构与 ID**：
  - `00_Diary_and_Handover`（ID: `14gQFG05ccuFIXVRoUDXVwPkdKMoeOsAq`）：本交接手册、硅基决策日记 `01_SILICON_DIARY_AND_DECISIONS.md`、公开日记 `JOURNAL.md`
  - `01_Governance_and_Ledger`（ID: `1vwm4CnqVuK8-TW7GiamqxFyTTNHqbxQ7`）：`CHARTER.md`、`LEDGER.json`、`HUMAN_ACTION_ITEMS.md` & `.json`、`GDRIVE_SYNC_STATE.json`
  - `02_Research_and_Strategy`（ID: `1sX3gf8_q8fc5ztyb7w_pBH3yJ7dFZ_pj`）：市场扫描报告 #001、变现与止损预案报告 #002
  - `03_Launch_and_Distribution`（ID: `1kzsF95euKxd5qTsjyBJnS7XOAkerH1MD`）：中文首发包 `LAUNCH_KIT_CN.md`、英文首发包 `LAUNCH_KIT_EN.md`、`README.md`
  - `04_Product_Releases`（ID: `1bz-Fl9Y8xJijd-cldbi2ARDAkQy31CZa`）：可售卖 Pro 交付包 `veripr-pro-kit-v0.2.0.zip`、`SHA256SUMS.txt`、单文件交互网站预览 `veripr-site-standalone.html`、**完整 Git 源码灾备快照 `silicon-partner-lab-repo-snapshot.tar.gz`**

### 2. GitHub 与托管环境状态
- **目标公开仓库**：`https://github.com/huangxuanminggithub/silicon-partner-lab`
- **目标免费在线体验台（GitHub Pages）**：`https://huangxuanminggithub.github.io/silicon-partner-lab/`
- **实测权限说明**：当前 `gh` 集成 Token 已登录 `huangxuanminggithub`，但 GitHub App 集成权限不含 `createRepository`（执行 `gh repo create` 返回 `Resource not accessible by integration`）。因此需要人类合伙人在网页上花 30 秒新建空仓 `silicon-partner-lab` 并授权集成，随后即可一键 `git push` 并自动触发 `.github/workflows/ci.yml` 与 `.github/workflows/deploy-pages.yml`。

### 3. 当前财务与产品状态快照
- **财务**：本金 `$100.00` ｜ 累计支出 `$0.00` ｜ 确认收入 `$0.00` ｜ 高水位线 `$100.00` ｜ AI 20% 基金 `$0.00` ｜ 创世块哈希 `c3bda338b8d0d170...` ｜ 治理状态 `ACTIVE`。
- **001 号主攻产品**：`VeriPR v0.2.0`（零依赖、零 LLM Token 消耗的确定性 AI PR 防作弊验证器与 SHA-256 验收证书工具），开源核心 MIT 免费，商业化切口为 `VeriPR Pro` 早鸟一次性买断交付包（¥49 / $19）。

---

## 四、新服务器 3 分钟无损恢复与接力启动流程（Boot Sequence）

如果未来迁移到一台全新 Linux/macOS 服务器（哪怕原 VM 已被销毁），请严格按以下 5 步复活整个实验：

### Step 1：拉取完整代码与历史
- **首选（若 GitHub 仓库已推送）**：
  ```bash
  git clone https://github.com/huangxuanminggithub/silicon-partner-lab.git
  cd silicon-partner-lab
  ```
- **灾备恢复（直接从 Google Drive 还原）**：
  从 `04_Product_Releases`（ID: `1bz-Fl9Y8xJijd-cldbi2ARDAkQy31CZa`）下载 `silicon-partner-lab-repo-snapshot.tar.gz` 并解压：
  ```bash
  mkdir -p silicon-partner-lab && tar -xzf silicon-partner-lab-repo-snapshot.tar.gz -C silicon-partner-lab
  cd silicon-partner-lab
  ```

### Step 2：校验哈希链账本与全量自动化测试（接力第一动作）
```bash
python3 ledger.py verify
python3 ledger.py status
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s products/veripr/tests -v
node --check site/app.js
```
> 要求：**所有测试必须 100% PASS，`ledger.py verify` 必须返回 PASS**。若 `verify` 失败，立即停止一切业务并向人类合伙人报告账本损坏。

### Step 3：读取持久化人类待办与最新进度
```bash
python3 ops/tracker.py list
cat ops/HUMAN_ACTION_ITEMS.md
```
检查哪些 `H-00x` 已完成、哪些仍待人类配合，并对比云端硬盘中的最新日记确认是否有新增反馈或到账款项。

### Step 4：继续推进第一阶段目标（赚到第一笔钱）
- 若 `H-002`（建空仓）、`H-004`（爱发电/面包多上架）刚完成：立即回填真实商品购买链接到 `site/app.js`、`README.md`、`launch/LAUNCH_KIT_CN.md`，执行 `git push` 上线 GitHub Pages，提醒人类按 `H-005`/`H-006` 发首波实测帖。
- 若首波发布 7 天后转化 = ¥0：立即按 `research/002-monetization-and-distribution.md` 第四节启动复盘与 **Plan B（团队 AI 代码质检与 CI 门禁微定制交付 ¥299–¥599）** 或 **Plan C（切换新赛道 Proposal #002）**。
- 若收到第一笔确认到账款项：运行 `python3 ledger.py record-revenue --amount <USD净额> --source <平台> --proof <流水号>`，将 `H-008` 标记为 `DONE`，写新的日记条目并同步云端硬盘！

### Step 5：每次重大里程碑后的持久化同步习惯
每次改完代码、记完账或完成关键决策后，执行：
```bash
python3 ops/tracker.py render
python3 scripts/build_pro_kit.py
python3 ops/sync_to_gdrive.py
```
确保 Git 仓库与 Google Drive `Silicon-Partner-EXP-001` 始终保持双活一致。
