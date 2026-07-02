# Console Push Channel Specifications

This reference document defines the local console/chat output integration.

## Message Format
Output the generated Markdown report directly to the command line output or the current chat message.

## Formatting
Use standard GitHub Flavored Markdown (GFM) as defined in `SKILL.md`.

### Example Output for Daily Report (`console`)
```markdown
# GitHub Trending 晨报 · 2026-07-02

**趋势判断**
今日趋势主要集中在 AI agent 的本地化部署以及新型开发工具上。

---

**1. [danielmiessler/fabric](https://github.com/danielmiessler/fabric)**  ·  Python  ·  ⭐ 120
一个用于通过 AI 解决工作流程问题的开源框架。

**2. [owner/repo](https://github.com/owner/repo)**  ·  TypeScript  ·  ⭐ 95
这是一个用于演示的仓库。

...

---

**Rust 小工具**
- [ripgrep](https://github.com/BurntSushi/ripgrep)：快如闪电的文本搜索工具。
- [fd](https://github.com/sharkdp/fd)：简单、快速且人性化的 find 替代品。
```

## Setup & Credentials
- No webhooks or API keys are required.
- Ideal for offline runs, local developer preview, or standard interactive terminal use.
