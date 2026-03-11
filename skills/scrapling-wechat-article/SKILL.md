---
name: scrapling-wechat-article
description: WeChat public account (微信公众号) article scraping addon for Scrapling. Use this skill alongside the scrapling-official skill when the task involves scraping WeChat articles from mp.weixin.qq.com — either a single article URL or a list of URLs from a text file — and saving them as Markdown files. Provides WeChat-specific CSS selectors, correct fetcher settings, and a batch processing pattern using DynamicSession.
---

# Scrapling — WeChat Article Addon

This is an addon to the `scrapling-official` skill. Load and follow both skills together.

**Prerequisites:** `pip install "scrapling[all]>=0.4.1"` and `scrapling install` must already be done.
Do **not** add `html2text` as a dependency — Scrapling's built-in `markdownify` conversion handles HTML→Markdown correctly.

---

## Environment

The `scrapling` tool and its dependencies are installed in a dedicated virtual environment. **You MUST use the absolute paths provided below** for all CLI commands and Python scripts:

- **Scrapling CLI**: `/home/kamus/.openclaw/python-envs/scrapling/bin/scrapling`
- **Python Interpreter**: `/home/kamus/.openclaw/python-envs/scrapling/bin/python`

---

## Rule 1: Always Use `fetch`, Never `get`

WeChat articles are JS-rendered. `get` returns an empty shell. Skip the escalation ladder entirely — always go straight to `fetch`.

**Required parameters every time:**

| Parameter                              | Value       | Reason                                                   |
| -------------------------------------- | ----------- | -------------------------------------------------------- |
| `--network-idle` / `network_idle=True` | always      | waits for JS rendering to finish                         |
| `--timeout 60000` / `timeout=60000`    | always (ms) | articles can be slow to load                             |
| `--css-selector "#js_content"`         | always      | extracts only article body, drops nav/ads/follow buttons |

---

## Rule 2: WeChat Page CSS Selectors

| Element                            | CSS Selector     |
| ---------------------------------- | ---------------- |
| Article body (正文)                | `#js_content`    |
| Article title (标题)               | `#activity-name` |
| Public account name (公众号名)     | `#js_name`       |
| Publish time (发布时间)            | `#publish_time`  |
| Article summary (摘要, if present) | `#js_desc`       |

Always use `#js_content` for Markdown extraction. The other selectors are for metadata in Python code.

---

## Single URL — CLI

```bash
scrapling extract fetch "https://mp.weixin.qq.com/s/ARTICLE_ID" "article_title.md" \
  --network-idle \
  --timeout 60000 \
  --css-selector "#js_content"
```

---

## Batch URLs — Python with DynamicSession

When given a list of URLs (text file, one URL per line), **do not loop the CLI command**. Each CLI call launches and shuts down a new browser instance. Use `DynamicSession` to keep one browser open for all requests.

```python
from pathlib import Path
from scrapling.fetchers import DynamicSession
from scrapling.core.shell import Convertor

urls = Path("urls.txt").read_text(encoding="utf-8").strip().splitlines()
urls = [u.strip() for u in urls if u.strip()]

output_dir = Path("articles")
output_dir.mkdir(exist_ok=True)

with DynamicSession(headless=True, network_idle=True, timeout=60000) as session:
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{len(urls)}] {url}")
        try:
            page = session.fetch(url)
            title = page.css("#activity-name::text").get()
            if title:
                safe_title = "".join(c for c in title.strip() if c not in r'\/:*?"<>|')[:80]
            else:
                safe_title = f"article_{i}"
            out_path = output_dir / f"{safe_title}.md"
            Convertor.write_content_to_file(page, str(out_path), css_selector="#js_content")
            print(f"  → saved: {out_path}")
        except Exception as e:
            print(f"  ✗ failed: {e}")
```

---

## Anti-patterns

| Wrong                         | Right                                                                         |
| ----------------------------- | ----------------------------------------------------------------------------- |
| `scrapling extract get <url>` | `scrapling extract fetch <url>`                                               |
| No `--css-selector`           | Always `--css-selector "#js_content"`                                         |
| CLI loop over URL list        | `DynamicSession` in Python                                                    |
| `page.get_all_text()`         | `Convertor.write_content_to_file(page, "out.md", css_selector="#js_content")` |
| Adding `html2text` library    | Use Scrapling's built-in `.md` output                                         |

---

## Notes

- `.md` extension triggers Scrapling's internal `markdownify` conversion — links are preserved.
- WeChat CDN images may not render outside the WeChat environment (CDN access control). This is expected.
- If a page returns empty content, verify `--network-idle` is set and consider increasing `--timeout`.
