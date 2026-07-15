# Persistent Report Format

Read this file only when the user explicitly requests a saved or fuller guide.
Default to `docs/codebase/CODEBASE_GUIDE.md` unless another path is given. Create
or update only that report.

## Evidence Labels

| Label | Use |
| --- | --- |
| `Confirmed` | Source directly connects the claim to current behavior. |
| `Runtime verified` | A named safe command observed the behavior. |
| `Inferred` | Static evidence supports the claim but an edge is unobserved. |
| `Unknown` | The evidence required to decide is unavailable. |

Use repository-relative locations such as `src/server.ts:L18-L44`. A parser,
test, or `--help` command verifies only the behavior it exercised.

## Report Shape

Keep the report scoped to the user's reading question:

```markdown
# 代码库阅读指南

## 1. 阅读结论
## 2. 分析快照
## 3. 入口与初始化
## 4. 主执行链
## 5. 必读执行单元
## 6. 推荐阅读顺序
## 7. 尚未确认事项
```

Add state and side effects, failure and concurrency, Web lifecycle, agent loop,
worker lifecycle, or concentrated-file regions only when they materially affect
the selected spine. Do not create empty feature sections.

For each must-read unit, include:

- symbol and repository-relative location
- current responsibility
- upstream trigger and downstream transition
- relevant input and output
- material state, external effects, and failure behavior
- evidence label

Keep supporting units grouped by responsibility. Prefer an ordered path over a
large architecture diagram. End with unknowns and the specific missing evidence
needed to resolve them.
