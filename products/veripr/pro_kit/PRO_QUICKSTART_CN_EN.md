# VeriPR Pro — Client Delivery & Team Governance Kit (v0.2.0)

感谢支持 **VeriPR Pro**（以及 `$100` 硅基合伙人实验 EXP-001）！
本工具包 100% 离线运行、零外部依赖、零 LLM Token 费用，适用于自由职业者、外包/软件交付团队与技术负责人。

---

## 包含内容 / What's Inside

1. **`veripr/` 完整零依赖 Python 包**：支持 `pip install .` 或直接 `python3 -m veripr` 运行。
2. **白标双语甲方验收证书模式（White-Label Client Delivery Certificate）**：
   - 支持中/英文切换（`--lang zh` / `--lang en`）、自定义交付方/甲方/项目/里程碑信息，并附带可直接打印为 PDF 的**正式验收签字栏（`--signoff`）**与 SHA-256 不可篡改封签。
3. **多 Commit / Sprint 迭代问责总账（`veripr-rollup`）**：
   - 一键扫描整个迭代或发版区间的所有 Commit，输出管理层可直接阅读的 HTML Scorecard + CSV 明细（干净率、作弊拦截数、测试断言净增减趋势）。
4. **3 套开箱即用的生产级规则包（`rulepacks/`）**：
   - `strict-fintech-payments.toml`：金融/支付/账本零容忍规则（禁浮点算钱、禁关闭 TLS 校验、禁硬编码鉴权旁路）
   - `ai-vibe-coding-guard.toml`：专治 Claude Code / Cursor / Codex 常见偷懒手法（`assert True` 假测试、未实现占位符、全文件关 Lint）
   - `agency-client-delivery.toml`：甲方交付前清洁检查（禁硬编码 `localhost`、禁残留 `NotImplementedError`、提醒调试日志）
5. **团队门禁模板（`templates/` & `scripts/`）**：
   - GitHub Actions PR 自动评论 + 阻断门禁模板
   - GitLab CI 模板
   - 本地 `pre-push` Git Hook 一键安装脚本

---

## 3 分钟快速上手 / Quick Start

### 1. 生成带甲方签字栏的中文交付验收证书（可 Ctrl+P 另存为 PDF）
```bash
python3 -m veripr \
  --repo /path/to/your/project \
  --config pro_kit/rulepacks/agency-client-delivery.toml \
  --cmd "pytest -q" \
  --vendor "极光软件工作室" \
  --client "星辰科技有限公司" \
  --project "订单支付中心 v2.3" \
  --milestone "Milestone 2 · 支付回调重构" \
  --lang zh \
  --signoff \
  --html delivery-certificate.html \
  --fail-on-cheat
```

### 2. 生成整个 Sprint 的团队审计总账（HTML + CSV）
```bash
python3 -m veripr.rollup \
  --repo /path/to/your/project \
  --limit 20 \
  --config pro_kit/rulepacks/ai-vibe-coding-guard.toml \
  --html sprint-scorecard.html \
  --csv sprint-scorecard.csv
```

### 3. 给仓库装上本地推代码前防作弊门禁
```bash
bash pro_kit/scripts/install-pre-push-hook.sh
```
