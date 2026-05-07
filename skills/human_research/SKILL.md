---
name: human_research
description: >
  Deep public-person research / OSINT workflow for investigating a person's public profile from names, URLs, handles, emails, companies, schools, or other identity seeds. Use this whenever the user asks to 调研一个人, research someone, investigate a person's background, find their public information, identify who a GitHub/LinkedIn/X profile belongs to, or summarize a person's career, location, affiliations, online footprint, credibility, and publicly available biographical information. This skill should trigger even if the user only provides one URL or handle, because the expected behavior is broad cross-platform research rather than reading only the provided page.
---

# Human Research Skill

Use this skill to research a person's publicly available information across the open web and social/professional platforms. The goal is to produce a careful, evidence-backed profile, not a shallow summary of the first page the user shared.

This is an OSINT-style workflow for benign public-interest research. Stay within publicly accessible information. Do not bypass authentication, scrape private data, dox, infer sensitive attributes without evidence, or provide harassment-enabling details such as exact home addresses, private phone numbers, private emails, family member targeting, or real-time location.

## Core principle

A single user-provided URL is only a seed. Treat it as the starting point for entity resolution and wider research.

When the user says something like `https://github.com/kamusis help me to do the research, who is this guy`, they likely expect:

- Who this person appears to be.
- Career and education history.
- Public professional profiles such as LinkedIn, GitHub, Google Scholar, company pages, conference bios, personal websites, patents, papers, talks, podcasts, interviews, and news.
- Public social footprint such as X/Twitter, Reddit, Hacker News, Stack Overflow, Medium, YouTube, GitHub activity, Wikipedia, Baidu Baike, WeChat articles, and Chinese-language sources when relevant.
- Likely city/region only when supported by public evidence.
- Confidence levels, source links, and explicit uncertainty.

## Safety and privacy boundaries

Research only public information and report it responsibly.

- Do not reveal private contact information, exact residential addresses, government IDs, financial records, family details, or other sensitive personal data.
- Do not help track a person in real time or enable unwanted contact, harassment, intimidation, stalking, social engineering, or credential attacks.
- Do not use hacked/leaked databases or instructions for bypassing paywalls, logins, privacy settings, rate limits, CAPTCHAs, or platform restrictions.
- If a public page contains sensitive data that is not necessary for the user's benign goal, omit it or summarize at a high level.
- For location, prefer broad wording such as `likely based in the San Francisco Bay Area` or `public profiles mention Seattle`; avoid street-level details.
- Separate verified facts from inferences. Never merge two people with the same name unless the linking evidence is strong.

## Research workflow

### 1. Parse the seed and define the target

Extract all identity clues from the user's request:

- Names, aliases, usernames, handles, emails, domains, organizations, schools, repositories, papers, locations, profile URLs, avatars, and bio text.
- Name variants: full name, Chinese name, pinyin, initials, old usernames, hyphenation, middle names, and common transliterations.
- Context from the seed page: linked websites, pinned repositories, commit metadata, profile README, company names, location field, social links, package names, domains, and email-like identifiers.

If the request is ambiguous, continue with a scoped assumption instead of stopping immediately. State the assumption in the report, for example: `I treated GitHub user forrestchang and the name Jiayuan Zhang as the same target unless evidence indicates otherwise.`

### 2. Build a search matrix

Search broadly. Do not stop after reading the seed page or one platform.

Use combinations of:

- Exact name in quotes.
- Name + username/handle.
- Name + organization/company/school.
- Name + city/country if surfaced by public profiles.
- Name + technical keywords from repositories, publications, projects, or job titles.
- Username + platform/domain.
- Email/domain fragments if public and relevant.
- Chinese and English variants when applicable.

Suggested query examples:

```text
"Jiayuan Zhang" forrestchang
"Jiayuan Zhang" GitHub
"Jiayuan Zhang" LinkedIn
"Jiayuan Zhang" software engineer
"Jiayuan Zhang" site:linkedin.com/in
"forrestchang" -github
"forrestchang" Twitter OR X OR Reddit OR Hacker News
"Jiayuan Zhang" Google Scholar OR publication OR patent
"Jiayuan Zhang" 百度百科 OR 知乎 OR 微信
```

### 3. Search priority by source type

Use available web/search/platform tools. If `agent-reach` is available, use it for broad platform coverage.

Prioritize sources in this order:

1. **Self-authored / official sources**: personal website, GitHub profile, LinkedIn profile, Google Scholar, ORCID, company bio, university page, conference speaker profile.
2. **Professional footprints**: GitHub repositories and commits, package registries, Stack Overflow, Kaggle, Hugging Face, arXiv, patents, talks, slides, podcasts, technical blogs, Medium/Substack.
3. **Social footprints**: X/Twitter, Reddit, Hacker News, Instagram, YouTube, Bilibili, Weibo, Zhihu, V2EX, Xiaohongshu, WeChat articles.
4. **Third-party references**: news, press releases, event pages, hiring pages, alumni directories, podcasts, interviews, organization member pages.
5. **Knowledge bases**: Wikipedia, Wikidata, Baidu Baike, Crunchbase-like summaries when publicly accessible.

Do not treat low-quality people-search aggregator pages as authoritative. They may be useful only as leads and should be marked low confidence.

### 4. Entity resolution and confidence scoring

Before summarizing, decide whether each finding belongs to the target.

Use evidence such as:

- Same unique username or linked account.
- Cross-links between profiles.
- Matching avatar, personal website, email domain, repository ownership, organization, education, job timeline, location, or project names.
- Consistent writing style or repeated bio phrases.

Assign confidence:

- **High**: Directly linked from the seed or confirmed by multiple independent strong signals.
- **Medium**: Several matching signals but no direct cross-link.
- **Low**: Name match only, weak contextual overlap, or possible same-name collision.

Exclude or quarantine likely false positives in a separate section instead of mixing them into the main profile.

### 5. Extract useful fields

For each reliable source, extract only information relevant to a public profile:

- **Identity**: name, aliases, handles, public avatar only if useful, languages.
- **Current role**: title, company, affiliation, project, public bio.
- **Career timeline**: roles, organizations, dates, notable transitions.
- **Education**: schools, degrees, labs, advisors, graduation years if public.
- **Location**: broad city/region/country and source; mark as current, historical, or uncertain.
- **Technical/professional focus**: domains, technologies, publications, repositories, talks, open-source contributions.
- **Public online footprint**: profiles and activity by platform.
- **Notable achievements**: awards, products, papers, patents, media mentions, conference talks.
- **Open questions**: missing or contradictory information.

## Required report format

Respond in the user's language unless they request otherwise. Keep source titles and URLs intact.

```markdown
# Public Research Report: [Person / Handle]

## Executive summary
- **Likely identity**: ...
- **Current/most recent role**: ...
- **Known affiliations**: ...
- **Likely location**: ...
- **Confidence**: High/Medium/Low, with one-sentence rationale.

## Source coverage
- **Seed reviewed**: [URL]
- **Platforms searched**: GitHub, LinkedIn, web search, X/Twitter, Reddit, Wikipedia/Baidu Baike, ...
- **Useful sources found**: [count]
- **Major gaps**: ...

## Confirmed findings
### Identity and aliases
- **Finding**: ...
- **Evidence**: [source title](URL)
- **Confidence**: High/Medium/Low

### Career and education
- **Finding**: ...
- **Evidence**: [source title](URL)
- **Confidence**: High/Medium/Low

### Location
- **Finding**: ...
- **Evidence**: [source title](URL)
- **Confidence**: High/Medium/Low

### Projects, publications, and technical footprint
- **Finding**: ...
- **Evidence**: [source title](URL)
- **Confidence**: High/Medium/Low

### Social and community footprint
- **Finding**: ...
- **Evidence**: [source title](URL)
- **Confidence**: High/Medium/Low

## Possible matches / unverified leads
- **Lead**: ...
- **Why uncertain**: ...
- **Source**: [source title](URL)

## Chronological timeline
- **YYYY-MM**: Event, role, education, publication, project, or public activity. Source: [link]

## Assessment
- **Most likely profile**: ...
- **What is well-supported**: ...
- **What remains uncertain**: ...
- **Recommended next searches**: ...

## Sources
1. [Title](URL) — what it supports.
2. [Title](URL) — what it supports.
```

## Execution checklist

Before finalizing, verify that you have:

- Read the user-provided seed URL/profile if any.
- Performed general web searches, not just platform-specific searches.
- Searched at least GitHub and LinkedIn when relevant.
- Searched both English and Chinese sources if the name/context suggests bilingual coverage.
- Looked for personal site, company/university pages, publications, talks, and social profiles.
- Checked for same-name collisions and separated uncertain leads.
- Included source links for every material claim.
- Stated confidence and uncertainty clearly.
- Avoided private/sensitive data and exact residential details.

## When information is sparse

Do not pad the report with guesses. Say what was searched and what was not found. Provide a short list of additional high-value search directions, such as alternate spellings, known employer, school, email domain, or another profile URL that would disambiguate the person.
