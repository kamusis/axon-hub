#!/usr/bin/env bash
# scripts/github_trends.sh
# Reports: 1. Brand New (30d), 2. Global Trending (Real-time), 3. AI Momentum (1y)

set -euo pipefail

SINCE_30=$(date -d "30 days ago" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d)
SINCE_YEAR=$(date -d "365 days ago" +%Y-%m-%d 2>/dev/null || date -v-365d +%Y-%m-%d)


echo "📈 **GitHub 趋势深度观察：全维度简报**"
echo "*(生成时间: $(date '+%Y-%m-%d %H:%M') Asia/Tokyo)*"
echo ""

# Helper for JQ formatting
JQ_FILTER='to_entries | .[] | "\(.key + 1). **[\(.value.fullName)](\(.value.url))** (⭐ \(.value.stargazersCount))\n• 描述: \(.value.description // "无描述")\n"'

# SECTION 1: Rising Stars
echo "🔥 **【新锐榜】30 天内诞生的全球黑马 (Top 10)**"
gh search repos --created=">$SINCE_30" --sort=stars --order=desc --limit=10 --json fullName,description,stargazersCount,url | jq -r "$JQ_FILTER"

# SECTION 2: Global Trending (Real velocity)
echo -e "\n🌟 **【全球热度榜】GitHub 官方本月趋势 (Top 10)**"
echo "*(数据源: github.com/trending?since=monthly)*"

python3 -c '
import urllib.request, re, html, subprocess

url = "https://github.com/trending?since=monthly"
ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"

page = None
try:
    req = urllib.request.Request(url, headers={"User-Agent": ua})
    with urllib.request.urlopen(req, timeout=15) as resp:
        page = resp.read().decode("utf-8", errors="ignore")
except Exception:
    try:
        res = subprocess.run(["curl", "-sL", "-H", f"User-Agent: {ua}", url], capture_output=True, text=True, timeout=15)
        if res.returncode == 0 and res.stdout:
            page = res.stdout
    except Exception:
        pass

if not page:
    print("⚠️ 暂时无法获取官方热度数据。")
else:
    try:
        articles = re.findall(r"<article class=\"Box-row\">(.*?)</article>", page, re.DOTALL)
        count = 0
        for art in articles:
            m_repo = re.search(r"<h2[^>]*>\s*<a[^>]*href=\"/([^/\"]+/[^/\"]+)\"", art)
            if not m_repo:
                continue
            repo = m_repo.group(1).strip()
            if "login" in repo:
                continue

            m_desc = re.search(r"<p[^>]*class=\"[^\"]*color-fg-muted[^\"]*\"[^>]*>(.*?)</p>", art, re.DOTALL)
            desc = html.unescape(m_desc.group(1).strip()) if m_desc else "无描述"
            desc = re.sub(r"\s+", " ", desc)

            m_stars = re.search(r"href=\"/[^/\"]+/[^/\"]+/stargazers\"[^>]*>\s*(?:<svg[^>]*>.*?</svg>)?\s*([\d,]+)", art, re.DOTALL)
            stars = m_stars.group(1).strip().replace(",", "") if m_stars else ""
            stars_str = f" (⭐ {stars})" if stars else ""

            count += 1
            print(f"{count}. **[{repo}](https://github.com/{repo})**{stars_str}")
            print(f"• 描述: {desc}\n")
            if count >= 10:
                break
        if count == 0:
            print("⚠️ 未能解析到热度数据。")
    except Exception:
        print("⚠️ 解析热度数据失败。")
'

# SECTION 3: Sector Momentum
echo -e "\n🤖 **【动能榜】AI & Agent 赛道年度活跃标杆 (Top 10)**"
echo "*(条件: 1年内创建, 30天内有更新, 关键词: agent)*"
gh search repos agent --created=">$SINCE_YEAR" --updated=">$SINCE_30" --sort=stars --order=desc --limit=10 --json fullName,description,stargazersCount,url | jq -r "$JQ_FILTER"

echo -e "\n---"
echo "Kuro 的每日观察：新锐看爆发，热度看风口，动能看底蕴。🐈‍⬛"

