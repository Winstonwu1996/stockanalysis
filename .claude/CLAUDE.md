# stockanalysis — Claude Code 启动指令 (薄 shim)

> Boot 时: **先读 `../AGENTS.md`** (canonical 项目说明 — 项目背景 / 技术栈 / 边界 / 命令 / 指针)
> 本文件只放 Claude Code 特有的额外指令.

## Claude Code 特有

1. **MCP servers**: 已注册 `openclaw` + `vault-search` (全局), 直接可用. 不要重复装.

2. **上游**: `upstream` remote 指向 `hsliuping/TradingAgents-CN`, 定期 `git fetch upstream` 拉新版本.

3. **Plan mode**: 修改 > 3 个文件前, 建议先出 plan 给 William 看.

4. **Remote Control 兼容**: 输出**简短** + 关键 diff 高亮, 方便手机看.

---

*薄 shim · 真背景在 ../AGENTS.md*
