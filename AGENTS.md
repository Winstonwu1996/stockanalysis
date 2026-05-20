# stockanalysis — AGENTS.md

> 业界 spec ([agents.md](https://agents.md/)) 项目级 canonical 启动手册.
> 任何 AI 编程工具 (Claude Code / Codex CLI / Cursor) 进入这个 repo 时第一个该读的文件.

## Project Overview

stockanalysis — 暂时不确定.

自己使用的股票分析系统

## Boundaries (3 层)

### Must (必须保持)
- (项目落地后填: 必须保持不破坏的 API/契约/数据形状)

### Ask First (问 William 才动)
- 加新依赖
- schema / migration
- 主版本升级
- 平台账号 / 密钥相关

### Never (绝对不动)
- 提交 secrets (`.env*` / 任何 key)
- 改 `vendor/` / `node_modules/`
- 直接 push main (必须 PR)

## Commands

```bash
# (项目落地后填: 启动 / 构建 / 测试 命令)
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
