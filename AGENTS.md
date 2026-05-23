# stockanalysis — AGENTS.md

> 业界 spec ([agents.md](https://agents.md/)) 项目级 canonical 启动手册.
> 任何 AI 编程工具 (Claude Code / Codex CLI / Cursor) 进入这个 repo 时第一个该读的文件.

## Project Overview

**W-Agents**（产品对外名；代码/仓库名仍是 stockanalysis）—— A 股个股多智能体分析系统，
fork 自开源 [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN)。
目标：整合 quant-slowbull 慢牛策略，部署 `bull.knowulearning.com`，对外卖会员（SaaS）。

- 多 Agent 协作：市场/基本面/新闻/社媒分析师 + 多空研究员辩论 + 交易员 + 风控。
- 用户输入 A 股代码 → 生成分析报告（可下载 md/Word/PDF、可对报告追问讨论）。
- **品牌**：UI 一律显示 **W-Agents**（不显示 TradingAgents；保留 About/学习中心对开源项目的归属，许可证合规）。

### 技术栈
- 前端：Vue 3 + TypeScript + Element Plus + Vite，nginx 静态托管 → 容器 `:3000`
- 后端：FastAPI (Python 3.10) → 容器 `:8000`
- 存储：MongoDB（账号/报告/配置/缓存）+ Redis
- 部署：Docker Compose（本地 MacMini）；上线走 Cloudflare Tunnel（同 slowbull）
- LLM：默认 **DeepSeek V4**（deep=deepseek-v4-pro / quick=deepseek-v4-flash），可选 Qwen / Claude
- A 股数据：AKShare（免费，爬东方财富/新浪/同花顺）；上线收费时计划接 Tushare Pro（见 STATE.md 待办）

## Boundaries (3 层)

### Must (必须保持)
- **数据源海外IP容错**：东方财富(eastmoney)实时+历史接口对海外 IP 会 502/断连，必须保留新浪兜底
  (`tradingagents/dataflows/providers/china/akshare.py` get_historical_data；`app/services/data_sources/akshare_adapter.py`)。
- **财报三大报表需带交易所前缀**：`stock_{balance,profit,cash}_sheet_by_report_em` 要 `SH/SZ/BJ` 前缀，裸代码返回 None。
- **DeepSeek 关思考模式**：V4 思考模式与多轮工具调用不兼容，`openai_client.py` 对 deepseek 注入 `extra_body={"thinking":{"type":"disabled"}}`，勿删。
- **固定 Mongo 库名**：docker-compose 设 `MONGODB_DATABASE_SCOPE=explicit` + 库名 `tradingagentscn`，否则 auto 模式按容器ID生成哈希导致重启丢账号。
- **PDF 导出过 pikepdf**：wkhtmltopdf 偶发页面树损坏(/Count=0)，`report_exporter._normalize_pdf` 必须保留。
- **viewer 安全模式**：非 admin 不得看到管理界面（系统配置/模型/密钥）；侧栏 `v-if=isAdmin` + 路由守卫。

### Ask First (问 William 才动)
- 加新依赖 / schema migration / 主版本升级 / 平台账号·密钥相关
- 改默认大模型 / 数据源主备策略

### Never (绝对不动)
- 提交 secrets (`.env*` / 任何 key) — 已 gitignore
- 改 `vendor/` / `node_modules/`
- 公网部署 / 真实收款 / 改定价 → 红线，走严肃模式 + William 亲自配 CF/Stripe

## Commands

```bash
cd ~/projects/stockanalysis

# 启动全套 (MongoDB+Redis+backend+frontend)
docker compose up -d

# 改了 Python 后端代码 (app/ 或 tradingagents/) → 重启即可 (代码已挂载, 无需重建)
docker compose restart backend

# 改了前端 Vue 代码 → 必须重建镜像 (Vite 编译)
docker compose build frontend && docker compose up -d frontend

# 改了后端依赖 (requirements.txt) → 重建后端镜像
docker compose build backend && docker compose up -d backend

# 看日志 / 健康
docker logs --since 2m tradingagents-backend 2>&1 | tail -30
docker inspect tradingagents-backend --format='{{.State.Health.Status}}'

# 默认账号: admin/admin123 (管理员), member/member123 (普通会员, 测 viewer 模式)
# 访问: http://localhost:3000
```

## Pointers

| 内容 | 路径 |
|------|------|
| 项目状态 (上次到哪了) | `~/ObsidianVault/10-Projects/stockanalysis/STATE.md` (待建) |
| Session 交接棒 | `~/ObsidianVault/10-Projects/stockanalysis/CONTINUITY.md` (待建) |
| 已知坑 | `~/ObsidianVault/20-Knowledge/wiki/concepts/known-gotchas.md` |
| 共享记忆查询 | `python3 ~/.openclaw/workspace/scripts/l2-search.py "query"` |

**重要**: 不要猜. 不确定就 l2-search.py 查 Vault, 或问 William.

## Reminders

- 改完跑相关 test, 没专门 test 时至少跑 build
- **不可逆动作** (deploy / migration / 客户邮件 / incident) → 走严肃模式 Task Pack, 不直接 vibe
- 简单 bug fix / UI 调整 / 文案改动 → 直接 vibe coding

## Decision Log (★ v12.2 Day 6 Observation Quick Win 1 — 硬约束)

> AI 重要决定后必须主动写 Decision Log, 否则 William 看不见, 等于讨论白费.

**写到哪**: `~/ObsidianVault/10-Projects/stockanalysis/STATE.md` 的 `## last_5_decisions` section.

**格式** (严格一行一条):
```
- YYYY-MM-DD HH:MM — 决定 X (一句话 context, 可选触发原因)
```

## 协议层

本文件是 vendor-neutral 启动契约 (agents.md spec). 工具特有指令在 shim 文件 (`.claude/CLAUDE.md` / `.codex/AGENTS.md` / `.cursor/rules`), 都引用本文件作 source of truth. **冲突以本文件为准**.

---

*Created via Dashboard 新建项目 入口 · slug=`stockanalysis` · type=`other`*
