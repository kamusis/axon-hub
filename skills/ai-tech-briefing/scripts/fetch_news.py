#!/usr/bin/env python3
"""
Product News Daily - High Concurrency Fetcher & Aggregator

Fetches 28 product news sources (RSS, Atom, and lightweight HTML) in parallel.
Filters items by time window (default 24h, or 7d/14d for low-frequency sources).
Handles Reddit rate-limiting, Anthropic status filtering, and emits structured JSON.
"""

import sys
import os
import re
import json
import html
import ssl
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
DEFAULT_TIMEOUT = 12  # seconds per request

# 28 Curated Sources Specification
DEFAULT_SOURCES = [
    # A. Open Source & Trending
    {
        "category": "open_source_trending",
        "name": "GitHub Trending Daily",
        "url": "https://github.com/trending?since=daily",
        "type": "github_trending_html",
        "window_days": 1,
        "max_items": 10,
    },
    # B. Monitoring / Observability / ITSM
    {
        "category": "observability_itsm",
        "name": "Jira Service Management",
        "url": "https://www.atlassian.com/blog/tag/jira-service-management/feed/atom",
        "type": "atom",
        "window_days": 14,
        "max_items": 5,
        "category_filter": "jira service management",
    },
    {
        "category": "observability_itsm",
        "name": "ServiceNow Platform",
        "url": "https://news.google.com/rss/search?q=ServiceNow+release+notes&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
        "window_days": 14,
        "max_items": 5,
        "title_prefix": "[ServiceNow] ",
    },
    {
        "category": "observability_itsm",
        "name": "ServiceNow Now Assist",
        "url": "https://news.google.com/rss/search?q=ServiceNow+Now+Assist+AI&hl=en-US&gl=US&ceid=US:en",
        "type": "rss",
        "window_days": 14,
        "max_items": 5,
        "title_prefix": "[Now Assist] ",
    },
    # C. Tools / Platforms
    {
        "category": "tools_and_platforms",
        "name": "Multica Releases",
        "url": "https://github.com/multica-ai/multica/releases.atom",
        "type": "atom",
        "window_days": 14,
        "max_items": 5,
    },
    {
        "category": "tools_and_platforms",
        "name": "Dify Releases",
        "url": "https://github.com/langgenius/dify/releases.atom",
        "type": "atom",
        "window_days": 14,
        "max_items": 5,
    },
    {
        "category": "tools_and_platforms",
        "name": "Coze Studio Releases",
        "url": "https://github.com/coze-dev/coze-studio/releases.atom",
        "type": "atom",
        "window_days": 14,
        "max_items": 5,
    },
    {
        "category": "tools_and_platforms",
        "name": "Product Hunt Daily",
        "url": "https://www.producthunt.com/feed",
        "type": "atom",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "tools_and_platforms",
        "name": "Obsidian Blog",
        "url": "https://obsidian.md/feed.xml",
        "type": "atom",
        "window_days": 14,
        "max_items": 5,
    },
    {
        "category": "tools_and_platforms",
        "name": "Obsidian Changelog",
        "url": "https://obsidian.md/changelog.xml",
        "type": "atom",
        "window_days": 14,
        "max_items": 5,
    },
    # D. Agent / IDE / Coding Assistant
    {
        "category": "agents_and_ides",
        "name": "Codex Releases",
        "url": "https://github.com/openai/codex/releases.atom",
        "type": "atom",
        "window_days": 14,
        "max_items": 5,
    },
    {
        "category": "agents_and_ides",
        "name": "Kiro Blog",
        "url": "https://kiro.dev/blog/feed.rss",
        "fallback_url": "https://kiro.dev/blog/feed.atom",
        "type": "rss",
        "window_days": 7,
        "max_items": 5,
    },
    {
        "category": "agents_and_ides",
        "name": "Cursor Blog",
        "url": "https://cursor.com/blog",
        "type": "html_links",
        "link_pattern": r'href="(/blog/[^"]+)"[^>]*>(.*?)</a>',
        "url_prefix": "https://cursor.com",
        "window_days": 7,
        "max_items": 5,
    },
    {
        "category": "agents_and_ides",
        "name": "Claude Code Changelog",
        "url": "https://docs.claude.com/en/docs/claude-code/changelog",
        "type": "html_simple",
        "window_days": 7,
        "max_items": 5,
    },
    # E. AI Vendors (Tier 1)
    {
        "category": "first_party_ai",
        "name": "OpenAI Blog",
        "url": "https://openai.com/blog/rss.xml",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "first_party_ai",
        "name": "Google AI Blog",
        "url": "https://blog.google/technology/ai/rss/",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "first_party_ai",
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co/blog/feed.xml",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "first_party_ai",
        "name": "Anthropic Status",
        "url": "https://status.anthropic.com/history.rss",
        "type": "rss",
        "window_days": 14,
        "max_items": 5,
        "title_must_start_with": "Resolved - ",
    },
    # F. Product Strategy / Growth / PM
    {
        "category": "product_strategy",
        "name": "Stratechery",
        "url": "https://stratechery.com/feed/",
        "type": "rss",
        "window_days": 14,
        "max_items": 5,
    },
    {
        "category": "product_strategy",
        "name": "Lenny's Newsletter",
        "url": "https://www.lennysnewsletter.com/feed",
        "type": "rss",
        "window_days": 14,
        "max_items": 5,
    },
    # G. Industry News & Community
    {
        "category": "industry_news",
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "industry_news",
        "name": "TechCrunch",
        "url": "https://techcrunch.com/feed/",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    # H. Reddit (Safe RSS fetching)
    {
        "category": "reddit",
        "name": "r/ClaudeAI",
        "url": "https://www.reddit.com/r/ClaudeAI/.rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "reddit",
        "name": "r/LocalLLaMA",
        "url": "https://www.reddit.com/r/LocalLLaMA/.rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "reddit",
        "name": "r/ChatGPT",
        "url": "https://www.reddit.com/r/ChatGPT/.rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "reddit",
        "name": "r/Anthropic",
        "url": "https://www.reddit.com/r/Anthropic/.rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "reddit",
        "name": "r/Cursor",
        "url": "https://www.reddit.com/r/Cursor/.rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "reddit",
        "name": "r/ChatGPTCoding",
        "url": "https://www.reddit.com/r/ChatGPTCoding/.rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
    {
        "category": "reddit",
        "name": "r/MachineLearning",
        "url": "https://www.reddit.com/r/MachineLearning/.rss",
        "type": "rss",
        "window_days": 1,
        "max_items": 5,
    },
]

def get_ssl_context():
    """Create a resilient SSL context that falls back to unverified on cert mismatch."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx

def clean_html(raw_html):
    """Strip HTML tags and unescape entities, truncating to 150 chars."""
    if not raw_html:
        return ""
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    clean = html.unescape(clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:150]

def parse_date(date_str):
    """Parse various RFC/ISO date formats to timezone-aware UTC datetime."""
    if not date_str:
        return None
    date_str = date_str.strip()
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    
    # Try ISO formats
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            if fmt.endswith("Z") and date_str.endswith("Z"):
                dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            else:
                dt = datetime.strptime(date_str, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None

def fetch_url(url, timeout=DEFAULT_TIMEOUT):
    """Fetch URL with custom UA and return raw bytes."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        }
    )
    ctx = get_ssl_context()
    with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
        return response.read()

def parse_feed_xml(xml_bytes, source_cfg, cutoff_dt):
    """Parse XML bytes into list of items matching cutoff."""
    items = []
    try:
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        return items, f"XML Parse Error: {e}"

    tag = root.tag.lower()
    
    # 1. RSS 2.0 / RDF format
    if "rss" in tag or tag.endswith("rdf") or root.find(".//item") is not None:
        for item_node in root.findall(".//item"):
            title_node = item_node.find("title")
            link_node = item_node.find("link")
            desc_node = item_node.find("description")
            date_node = item_node.find("pubDate")
            if date_node is None:
                date_node = item_node.find("{http://purl.org/dc/elements/1.1/}date")
            
            title = title_node.text.strip() if title_node is not None and title_node.text else ""
            link = link_node.text.strip() if link_node is not None and link_node.text else ""
            desc = clean_html(desc_node.text if desc_node is not None and desc_node.text else "")
            
            # Filters
            if source_cfg.get("title_must_start_with"):
                if not title.startswith(source_cfg["title_must_start_with"]):
                    continue
            
            dt = parse_date(date_node.text if date_node is not None and date_node.text else "")
            if dt and cutoff_dt and dt < cutoff_dt:
                continue

            if source_cfg.get("title_prefix"):
                title = source_cfg["title_prefix"] + title

            items.append({
                "title": title,
                "url": link,
                "published": dt.isoformat() if dt else "",
                "description": desc,
            })
            if len(items) >= source_cfg.get("max_items", 5):
                break

    # 2. Atom format
    elif "feed" in tag or root.find(".//{http://www.w3.org/2005/Atom}entry") is not None or root.find(".//entry") is not None:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entry_nodes = root.findall(".//atom:entry", ns)
        if not entry_nodes:
            entry_nodes = root.findall(".//entry")
        
        for entry in entry_nodes:
            title_node = entry.find("atom:title", ns) if ns else None
            if title_node is None:
                title_node = entry.find("title")
            
            link = ""
            link_nodes = entry.findall("atom:link", ns)
            if not link_nodes:
                link_nodes = entry.findall("link")
            for ln in link_nodes:
                if ln.get("rel") in (None, "alternate"):
                    link = ln.get("href", "")
                    break
            if not link and link_nodes:
                link = link_nodes[0].get("href", "") or link_nodes[0].text or ""

            # Date: updated or published
            date_node = entry.find("atom:published", ns)
            if date_node is None:
                date_node = entry.find("published")
            if date_node is None:
                date_node = entry.find("atom:updated", ns)
            if date_node is None:
                date_node = entry.find("updated")

            desc_node = entry.find("atom:summary", ns)
            if desc_node is None:
                desc_node = entry.find("summary")
            if desc_node is None:
                desc_node = entry.find("atom:content", ns)
            if desc_node is None:
                desc_node = entry.find("content")
            
            title = title_node.text.strip() if title_node is not None and title_node.text else ""
            desc = clean_html(desc_node.text if desc_node is not None and desc_node.text else "")
            
            # Category filter (e.g. Jira Service Management)
            if source_cfg.get("category_filter"):
                cat_found = False
                cats = entry.findall("atom:category", ns)
                if not cats:
                    cats = entry.findall("category")
                for cat in cats:
                    term = cat.get("term", "").lower()
                    if source_cfg["category_filter"].lower() in term:
                        cat_found = True
                        break
                if not cat_found:
                    continue

            dt = parse_date(date_node.text if date_node is not None and date_node.text else "")
            if dt and cutoff_dt and dt < cutoff_dt:
                continue

            items.append({
                "title": title,
                "url": link,
                "published": dt.isoformat() if dt else "",
                "description": desc,
            })
            if len(items) >= source_cfg.get("max_items", 5):
                break

    return items, ""

def parse_github_trending(html_str, max_items=10):
    """Fast regex parser for GitHub Trending HTML."""
    items = []
    article_pattern = re.compile(r'<article\s+class="Box-row"[^>]*>(.*?)</article>', re.DOTALL)
    repo_pattern = re.compile(r'<h2[^>]*>\s*<a\s+href="(/[^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    desc_pattern = re.compile(r'<p\s+class="col-9[^>]*>(.*?)</p>', re.DOTALL)
    lang_pattern = re.compile(r'<span\s+itemprop="programmingLanguage">(.*?)</span>', re.DOTALL)
    star_pattern = re.compile(r'<a\s+[^>]*href="[^"]+/stargazers"[^>]*>\s*<svg[^>]*>.*?</svg>\s*([\d,]+)', re.DOTALL)

    for match in article_pattern.finditer(html_str):
        block = match.group(1)
        repo_m = repo_pattern.search(block)
        if not repo_m:
            continue
        rel_url = repo_m.group(1).strip()
        repo_name = re.sub(r"\s+", "", repo_m.group(2)).strip("/")
        full_url = f"https://github.com{rel_url}"
        
        desc = ""
        desc_m = desc_pattern.search(block)
        if desc_m:
            desc = clean_html(desc_m.group(1))
            
        lang = ""
        lang_m = lang_pattern.search(block)
        if lang_m:
            lang = lang_m.group(1).strip()
            
        stars = ""
        star_m = star_pattern.search(block)
        if star_m:
            stars = star_m.group(1).strip()

        title = f"{repo_name} ({lang} ★{stars})" if lang else f"{repo_name} (★{stars})"
        items.append({
            "title": title,
            "url": full_url,
            "published": datetime.now(timezone.utc).isoformat(),
            "description": desc,
        })
        if len(items) >= max_items:
            break
    return items

def fetch_single_source(source_cfg, now_utc, default_window_days=1):
    """Fetches and parses a single source safely."""
    name = source_cfg["name"]
    category = source_cfg["category"]
    stype = source_cfg.get("type", "rss")
    window_days = source_cfg.get("window_days", default_window_days)
    cutoff_dt = now_utc - timedelta(days=window_days)
    
    url = source_cfg["url"]
    
    try:
        content = fetch_url(url)
    except urllib.error.HTTPError as e:
        if e.code == 429:
            return {"name": name, "category": category, "status": "rate_limited", "error": "HTTP 429 Rate Limit", "items": []}
        if source_cfg.get("fallback_url"):
            try:
                content = fetch_url(source_cfg["fallback_url"])
            except Exception as e2:
                return {"name": name, "category": category, "status": "fetch_failed", "error": f"{e}; fallback failed: {e2}", "items": []}
        else:
            return {"name": name, "category": category, "status": "fetch_failed", "error": f"HTTP {e.code}: {e.reason}", "items": []}
    except Exception as e:
        return {"name": name, "category": category, "status": "fetch_failed", "error": str(e), "items": []}

    # Parser dispatch
    if stype == "github_trending_html":
        try:
            items = parse_github_trending(content.decode("utf-8", errors="replace"), source_cfg.get("max_items", 10))
            return {"name": name, "category": category, "status": "ok", "error": "", "items": items}
        except Exception as e:
            return {"name": name, "category": category, "status": "parse_failed", "error": str(e), "items": []}

    elif stype == "html_links":
        # Extract direct links matching pattern
        html_str = content.decode("utf-8", errors="replace")
        items = []
        pat = source_cfg.get("link_pattern", r'href="([^"]+)"[^>]*>(.*?)</a>')
        prefix = source_cfg.get("url_prefix", "")
        for m in re.finditer(pat, html_str, re.DOTALL):
            href = m.group(1).strip()
            raw_title = clean_html(m.group(2))
            if raw_title and len(raw_title) > 5 and not any(k in raw_title.lower() for k in ("sign in", "privacy", "terms", "docs", "pricing")):
                full_url = href if href.startswith("http") else prefix + href
                items.append({
                    "title": raw_title,
                    "url": full_url,
                    "published": "",
                    "description": "",
                })
                if len(items) >= source_cfg.get("max_items", 5):
                    break
        return {"name": name, "category": category, "status": "ok", "error": "", "items": items}

    elif stype == "html_simple":
        # Simple extraction for documentation/changelog pages
        html_str = content.decode("utf-8", errors="replace")
        items = []
        links = re.findall(r'<a\s+[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html_str, re.DOTALL)
        for h, text in links:
            t = clean_html(text)
            if any(k in t.lower() for k in ("v0.", "v1.", "v2.", "release", "changelog", "update")):
                full = h if h.startswith("http") else url.rstrip("/") + "/" + h.lstrip("/")
                items.append({"title": t, "url": full, "published": "", "description": ""})
                if len(items) >= source_cfg.get("max_items", 5):
                    break
        return {"name": name, "category": category, "status": "ok", "error": "", "items": items}

    else:
        # Standard RSS / Atom
        items, err = parse_feed_xml(content, source_cfg, cutoff_dt)
        if err:
            return {"name": name, "category": category, "status": "parse_failed", "error": err, "items": []}
        return {"name": name, "category": category, "status": "ok", "error": "", "items": items}

def run_fetch(sources=None, window_days=1, max_workers=12, last_posted_at=None):
    """Main orchestrator: executes concurrent fetching and deduping."""
    if sources is None:
        sources = DEFAULT_SOURCES

    now_utc = datetime.now(timezone.utc)
    cutoff_baseline = None
    if last_posted_at:
        cutoff_baseline = parse_date(last_posted_at)

    results = []
    
    # Separate Reddit sources to avoid rate-limit chain
    non_reddit = [s for s in sources if s.get("category") != "reddit"]
    reddit = [s for s in sources if s.get("category") == "reddit"]

    # 1. Fetch non-reddit concurrently in worker pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_single_source, s, now_utc, window_days): s for s in non_reddit}
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    # 2. Fetch Reddit sources sequentially with rate-limit circuit breaking
    reddit_hit_429 = False
    for s in reddit:
        if reddit_hit_429:
            results.append({"name": s["name"], "category": "reddit", "status": "rate_limited", "error": "Skipped due to prior 429", "items": []})
            continue
        res = fetch_single_source(s, now_utc, window_days)
        if res.get("status") == "rate_limited":
            reddit_hit_429 = True
        results.append(res)

    # 3. Categorize and Deduplicate
    categories = {
        "first_party_ai": [],
        "agents_and_ides": [],
        "tools_and_platforms": [],
        "product_strategy": [],
        "observability_itsm": [],
        "industry_news": [],
        "open_source_trending": [],
        "reddit": [],
    }
    
    sources_summary = {}
    seen_urls = set()
    total_items = 0

    for r in results:
        name = r["name"]
        cat = r["category"]
        st = r["status"]
        items = r["items"]
        
        sources_summary[name] = {
            "status": st,
            "error": r.get("error", ""),
            "count": len(items),
        }

        for it in items:
            u = it.get("url")
            if u and u in seen_urls:
                continue
            if u:
                seen_urls.add(u)
                
            # Filter against last_posted_at baseline if present
            p_dt = parse_date(it.get("published"))
            if cutoff_baseline and p_dt and p_dt <= cutoff_baseline:
                continue

            it["source"] = name
            if cat in categories:
                categories[cat].append(it)
            else:
                categories.setdefault("other", []).append(it)
            total_items += 1

    return {
        "fetched_at": now_utc.astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S (Asia/Shanghai)"),
        "total_sources": len(sources),
        "total_sources_ok": sum(1 for r in results if r["status"] == "ok"),
        "total_sources_failed": sum(1 for r in results if r["status"] != "ok"),
        "total_items": total_items,
        "sources_summary": sources_summary,
        "categories": categories,
    }

def main():
    parser = argparse.ArgumentParser(description="Product News Daily High-Concurrency Fetcher")
    parser.add_argument("--window-days", type=int, default=1, help="Default lookback window in days (default: 1)")
    parser.add_argument("--last-posted-at", help="Baseline timestamp for deduplication (RFC3339)")
    parser.add_argument("--output", "-o", default="/tmp/news_fetch/news.json", help="Output JSON path")
    parser.add_argument("--workers", type=int, default=12, help="Concurrency workers")
    
    args = parser.parse_args()
    
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    data = run_fetch(
        window_days=args.window_days,
        max_workers=args.workers,
        last_posted_at=args.last_posted_at,
    )
    
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Fetched {data['total_items']} items from {data['total_sources_ok']}/{data['total_sources']} sources.")
    print(f"Saved to {args.output}")

if __name__ == "__main__":
    main()
