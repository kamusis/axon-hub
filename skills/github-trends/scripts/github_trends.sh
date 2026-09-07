#!/usr/bin/env bash
# scripts/github_trends.sh
# Reports: 1. Brand New (30d), 2. AI Momentum (1y), 3. Global Trending (Real-time)

set -euo pipefail

SINCE_30=$(date -d "30 days ago" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d)
SINCE_YEAR=$(date -d "365 days ago" +%Y-%m-%d 2>/dev/null || date -v-365d +%Y-%m-%d)

# Locate scrapling binary portably
SCRAPLING="$(command -v scrapling 2>/dev/null || true)"
if [ -z "$SCRAPLING" ]; then
    for candidate in "$HOME/.local/bin/scrapling" "/usr/local/bin/scrapling"; do
        if [ -x "$candidate" ]; then
            SCRAPLING="$candidate"
            break
        fi
    done
fi

echo "📈 **GitHub 趋势深度观察：全维度简报**"
echo "*(生成时间: $(date '+%Y-%m-%d %H:%M') Asia/Tokyo)*"
echo ""

# Helper for JQ formatting
JQ_FILTER='to_entries | .[] | "\(.key + 1). **[\(.value.fullName)](\(.value.url))** (⭐ \(.value.stargazersCount))\n• 描述: \(.value.description // "无描述")\n"'

# SECTION 1: Rising Stars
echo "🔥 **【新锐榜】30 天内诞生的全球黑马 (Top 5)**"
gh search repos --created=">$SINCE_30" --sort=stars --order=desc --limit=5 --json fullName,description,stargazersCount,url | jq -r "$JQ_FILTER"

# SECTION 2: Sector Momentum
echo -e "\n🤖 **【动能榜】AI & Agent 赛道年度活跃标杆 (Top 10)**"
echo "*(条件: 1年内创建, 30天内有更新, 关键词: agent)*"
gh search repos agent --created=">$SINCE_YEAR" --updated=">$SINCE_30" --sort=stars --order=desc --limit=10 --json fullName,description,stargazersCount,url | jq -r "$JQ_FILTER"

# SECTION 3: Global Trending (Real velocity)
echo -e "\n🌟 **【全球热度榜】GitHub 官方本月趋势 (Top 10)**"
echo "*(数据源: github.com/trending?since=monthly)*"

TRENDING_TMP="/tmp/github_trending_${USER:-default}.md"
if [ -n "$SCRAPLING" ] && [ -x "$SCRAPLING" ]; then
    "$SCRAPLING" extract get "https://github.com/trending?since=monthly" "$TRENDING_TMP" > /dev/null 2>&1 || true
fi

if [ -f "$TRENDING_TMP" ]; then
    python3 -c '
import re, sys, os
trending_file = sys.argv[1]
try:
    with open(trending_file, "r") as f:
        content = f.read()
    matches = re.findall(r"\[\s*([^/\s\]]+)\s*/\s*([^\]\s]+)\s*\]\((/[^)]+)\)", content)
    count = 0
    for owner, name, path in matches:
        if "login" in path: continue
        count += 1
        print(f"{count}. **[{owner}/{name}](https://github.com{path})**")
        if count >= 10: break
except Exception:
    print("⚠️ 暂时无法解析热度数据。")
' "$TRENDING_TMP"
else
    echo "⚠️ 暂无热度数据缓存文件。"
fi

echo -e "\n---"
echo "Kuro 的每日观察：新锐看爆发，动能看底蕴，热度看风口。🐈‍⬛"
