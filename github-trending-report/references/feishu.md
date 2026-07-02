# Feishu Push Channel Specifications

This reference document defines the Feishu custom robot integration specifications.

## Message Format
Use Feishu Message Card (msg_type: `interactive`). 

### Card Header
- Template: `blue`
- Title: `GitHub Trending 晨报 · YYYY-MM-DD` or `GitHub Trending 周报 · YYYY-MM-DD`

### Elements
The elements should form a clean structure:
1. **Trend Summary (div)**: `lark_md` block with `**趋势判断**` or `**本周判断**` followed by 1-2 (daily) or 2-3 (weekly) sentences.
2. **Separator (hr)**
3. **Trending Repositories (divs)**: Each repository listed in a single `lark_md` div.
   - Format:
     ```
     **No. [owner/repo](GitHub URL)**  ·  语言  ·  ⭐ 今日/本周星数
     一句话推荐理由
     ```
   - Note: Do NOT wrap the language or stars in backticks (`` `语言` ``) as this rendering might be broken on some mobile clients. Use standard spaces and middle dots (`·`) to separate fields.
4. **Separator (hr)**
5. **Retrospective (div)**: For weekly report only.
   - Title: `**值得复盘**`
   - Content: Three short points summarizing changes.
6. **Separator (hr)**: If weekly report or daily report.
7. **Rust Dev Tools (div)**:
   - Title: `**Rust 小工具**`
   - Content: Each tool on a new line: `[工具名](GitHub URL)`：用途和推荐理由
8. **Action area**: A primary button linking to the source GitHub Trending page.
   - Button text: "查看 GitHub Trending" or "查看 GitHub Weekly Trending"
   - URL: `https://github.com/trending?since=daily` or `https://github.com/trending?since=weekly`
   - Type: `primary`

## Signature Authentication
Feishu custom bots require HMAC-SHA256 signature verification if enabled:
1. Generate current timestamp in seconds: `timestamp` (e.g. `1603856834`).
2. Construct the signing string: `string_to_sign = timestamp + "\n" + <signing_secret>`.
3. Compute HMAC-SHA256:
   - Key: `string_to_sign`
   - Message: `""` (empty string)
4. Base64 encode the resulting digest: `sign`.
5. Include both `timestamp` and `sign` at the top level of the JSON body.

Example payload:
```json
{
  "timestamp": "1603856834",
  "sign": "generated_sign_here",
  "msg_type": "interactive",
  "card": {
    "header": {
      "template": "blue",
      "title": {
        "tag": "plain_text",
        "content": "GitHub Trending 晨报 · 2026-07-02"
      }
    },
    "elements": [
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**趋势判断**\n今日趋势主要集中在 AI agent 的本地化部署以及新型开发工具上。"
        }
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "**1. [danielmiessler/fabric](https://github.com/danielmiessler/fabric)**  ·  Python  ·  ⭐ 120\n一个用于通过 AI 解决生活和工作问题的开源框架。"
        }
      }
    ]
  }
}
```

## Error Handling & Retries
- Limit the total card payload to 20 KB.
- If payload is rejected with a "Bad Request", retry once.
- If it fails again, downgrade to `msg_type: text` and send as plain text keeping structure and numbering.
