#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Dict, List
from zoneinfo import ZoneInfo

USERNAME = os.getenv("GITHUB_USERNAME", "fengye404")
PROFILE_EMAIL = os.getenv("PROFILE_EMAIL", "1129126684@qq.com")
PROFILE_LOCATION = os.getenv("PROFILE_LOCATION", "Hangzhou, China")
PROFILE_COMPANY = os.getenv("PROFILE_COMPANY", "Alibaba")
PROFILE_NAME = os.getenv("PROFILE_NAME", "FengYe")

ACTIVE_PRIORITY = [
    "muse-work",
    "llm-training-learning",
    "ADK-demo",
    "spring-ai-demo",
    "ts-ai-sdk-demo",
    "mcp-demo",
]
ACTIVE_LIMIT = 6
ACTIVE_EXCLUDE = {f"{USERNAME}", f"{USERNAME}.github.io-back"}

REP_PRIORITY = ["Raft-KV-Java", "freshcup", "SAST.2021-backendWoc"]
REP_LIMIT = 3

PROJECT_META = {
    "muse-work": {
        "stack": "Electron, React, TypeScript",
        "en_desc": "Desktop AI workspace powered by Claude Agent SDK",
        "zh_desc": "基于 Claude Agent SDK 的桌面 AI 工作台",
    },
    "llm-training-learning": {
        "stack": "Python, Jupyter",
        "en_desc": "End-to-end LLM training learning workspace (SFT / DPO / GRPO / RLHF)",
        "zh_desc": "覆盖 SFT / DPO / GRPO / RLHF 的端到端 LLM 训练学习仓库",
    },
    "ADK-demo": {
        "stack": "Java",
        "en_desc": "Java ADK experiment with simple agent runner",
        "zh_desc": "Java ADK 实验仓库，包含基础 Agent Runner",
    },
    "spring-ai-demo": {
        "stack": "Java, Spring AI",
        "en_desc": "Spring AI demo with chat flow and tool integration",
        "zh_desc": "Spring AI 示例，包含聊天流程与工具调用",
    },
    "ts-ai-sdk-demo": {
        "stack": "TypeScript",
        "en_desc": "Minimal AI SDK usage demo in TypeScript",
        "zh_desc": "TypeScript 版最小化 AI SDK 使用示例",
    },
    "mcp-demo": {
        "stack": "Java",
        "en_desc": "Java MCP client/server demo (includes weather tool example)",
        "zh_desc": "Java MCP Client/Server 示例（含天气工具调用）",
    },
    "Raft-KV-Java": {
        "stack": "Java, Vert.x, Raft",
        "en_desc": "Raft-based key/value database, async networking with Vert.x",
        "zh_desc": "基于 Raft 的 Key/Value 数据库，采用 Vert.x 异步网络模型",
    },
    "freshcup": {
        "stack": "Java",
        "en_desc": "Early backend project",
        "zh_desc": "早期后端实践项目",
    },
    "SAST.2021-backendWoc": {
        "stack": "Java",
        "en_desc": "Backend workshop project",
        "zh_desc": "后端训练营项目",
    },
}


def gh_get(path: str):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "profile-readme-sync",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def fetch_user() -> Dict:
    return gh_get(f"/users/{urllib.parse.quote(USERNAME)}")


def fetch_repos() -> List[Dict]:
    repos: List[Dict] = []
    page = 1
    while True:
        data = gh_get(
            f"/users/{urllib.parse.quote(USERNAME)}/repos?per_page=100&page={page}&sort=updated&type=owner"
        )
        if not data:
            break
        repos.extend(data)
        if len(data) < 100:
            break
        page += 1
    return repos


def to_ym(iso_time: str | None) -> str:
    if not iso_time:
        return "-"
    return iso_time[:7]


def sync_date() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")


def find_repo(repos: List[Dict], name: str) -> Dict | None:
    for repo in repos:
        if repo["name"] == name:
            return repo
    return None


def select_active_repos(non_fork_repos: List[Dict]) -> List[Dict]:
    ordered = sorted(non_fork_repos, key=lambda r: r.get("pushed_at") or "", reverse=True)
    selected: List[Dict] = []
    selected_names = set()

    for name in ACTIVE_PRIORITY:
        repo = find_repo(ordered, name)
        if repo and repo["name"] not in ACTIVE_EXCLUDE:
            selected.append(repo)
            selected_names.add(repo["name"])

    for repo in ordered:
        name = repo["name"]
        if len(selected) >= ACTIVE_LIMIT:
            break
        if name in selected_names or name in ACTIVE_EXCLUDE or repo.get("archived"):
            continue
        selected.append(repo)
        selected_names.add(name)

    return selected[:ACTIVE_LIMIT]


def select_representative_repos(non_fork_repos: List[Dict]) -> List[Dict]:
    selected: List[Dict] = []
    selected_names = set()

    for name in REP_PRIORITY:
        repo = find_repo(non_fork_repos, name)
        if repo:
            selected.append(repo)
            selected_names.add(name)

    if len(selected) >= REP_LIMIT:
        return selected[:REP_LIMIT]

    rest = [r for r in non_fork_repos if r["name"] not in selected_names and r["name"] not in ACTIVE_EXCLUDE]
    rest.sort(
        key=lambda r: (
            (r.get("stargazers_count") or 0) + (r.get("forks_count") or 0),
            r.get("stargazers_count") or 0,
            r.get("forks_count") or 0,
            r.get("pushed_at") or "",
        ),
        reverse=True,
    )

    selected.extend(rest[: max(0, REP_LIMIT - len(selected))])
    return selected[:REP_LIMIT]


def active_year_range(active_repos: List[Dict]) -> str:
    years = sorted({(repo.get("pushed_at") or "0000")[:4] for repo in active_repos if repo.get("pushed_at")})
    if not years:
        return "Recent"
    if len(years) == 1:
        return years[0]
    return f"{years[0]}-{years[-1]}"


def active_table_en(active_repos: List[Dict]) -> str:
    lines = [
        "| Project | What it is | Stack | Last push |",
        "| --- | --- | --- | --- |",
    ]
    for repo in active_repos:
        name = repo["name"]
        meta = PROJECT_META.get(name, {})
        desc = meta.get("en_desc") or repo.get("description") or "No description yet"
        stack = meta.get("stack") or repo.get("language") or "-"
        lines.append(
            f"| [{name}](https://github.com/{USERNAME}/{name}) | {desc} | {stack} | {to_ym(repo.get('pushed_at'))} |"
        )
    return "\n".join(lines)


def active_table_zh(active_repos: List[Dict]) -> str:
    lines = [
        "| 项目 | 项目说明 | 技术栈 | 最近提交 |",
        "| --- | --- | --- | --- |",
    ]
    for repo in active_repos:
        name = repo["name"]
        meta = PROJECT_META.get(name, {})
        desc = meta.get("zh_desc") or repo.get("description") or "暂无描述"
        stack = meta.get("stack") or repo.get("language") or "-"
        lines.append(
            f"| [{name}](https://github.com/{USERNAME}/{name}) | {desc} | {stack} | {to_ym(repo.get('pushed_at'))} |"
        )
    return "\n".join(lines)


def rep_highlight_en(repo: Dict) -> str:
    name = repo["name"]
    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    base = PROJECT_META.get(name, {}).get("en_desc") or repo.get("description") or "Representative project"
    metrics = []
    if stars:
        metrics.append(f"`{stars}★`")
    if forks:
        metrics.append(f"`{forks} forks`")
    if metrics:
        return f"{base} ({', '.join(metrics)})"
    return base


def rep_highlight_zh(repo: Dict) -> str:
    name = repo["name"]
    stars = repo.get("stargazers_count") or 0
    forks = repo.get("forks_count") or 0
    base = PROJECT_META.get(name, {}).get("zh_desc") or repo.get("description") or "代表项目"
    metrics = []
    if stars:
        metrics.append(f"`{stars}★`")
    if forks:
        metrics.append(f"`{forks} forks`")
    if metrics:
        return f"{base}（{', '.join(metrics)}）"
    return base


def rep_table_en(repos: List[Dict]) -> str:
    lines = [
        "| Project | Highlights | Link |",
        "| --- | --- | --- |",
    ]
    for repo in repos:
        name = repo["name"]
        lines.append(
            f"| {name} | {rep_highlight_en(repo)} | [Repo](https://github.com/{USERNAME}/{name}) |"
        )
    return "\n".join(lines)


def rep_table_zh(repos: List[Dict]) -> str:
    lines = [
        "| 项目 | 亮点 | 链接 |",
        "| --- | --- | --- |",
    ]
    for repo in repos:
        name = repo["name"]
        lines.append(
            f"| {name} | {rep_highlight_zh(repo)} | [仓库](https://github.com/{USERNAME}/{name}) |"
        )
    return "\n".join(lines)


def build_readme_en(user: Dict, active: List[Dict], reps: List[Dict]) -> str:
    date_str = sync_date()
    year_range = active_year_range(active)
    public_repos = user.get("public_repos", "-")
    display_name = user.get("name") or PROFILE_NAME
    company = (user.get("company") or PROFILE_COMPANY).lstrip("@")
    location = user.get("location") or PROFILE_LOCATION
    return f"""<h1 align=\"center\">Hi, I'm {display_name}</h1>

<p align=\"center\">English | <a href=\"./README.zh-CN.md\">简体中文</a></p>

<p align=\"center\">
  <a href=\"https://github.com/{USERNAME}\">
    <img src=\"https://komarev.com/ghpvc/?username={USERNAME}&label=Profile%20views&color=0e75b6&style=flat\" alt=\"profile views\" />
  </a>
  <a href=\"https://github.com/{USERNAME}?tab=followers\">
    <img src=\"https://img.shields.io/github/followers/{USERNAME}?label=Followers&style=flat\" alt=\"followers\" />
  </a>
</p>

<p align=\"center\">
  Java & Backend Developer at {company} · {location}
</p>

<p align=\"center\">
  <a href=\"https://github.com/{USERNAME}\">GitHub</a> ·
  <a href=\"https://{USERNAME}.github.io\">Blog</a> ·
  <a href=\"mailto:{PROFILE_EMAIL}\">Email</a>
</p>

## Snapshot

- `@{company}` Java / Backend engineer
- Focus on distributed systems and AI application engineering
- Recent direction: agent tooling, MCP/Spring AI demos, LLM training practice
- Public repos: `{public_repos}` (data synced on `{date_str}`)

## Active Projects ({year_range})

{active_table_en(active)}

## Representative Repos

{rep_table_en(reps)}

## Tech I Use

<p>
  <img src=\"https://img.shields.io/badge/Java-007396?style=flat&logo=openjdk&logoColor=white\" alt=\"Java\" />
  <img src=\"https://img.shields.io/badge/Spring-6DB33F?style=flat&logo=spring&logoColor=white\" alt=\"Spring\" />
  <img src=\"https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white\" alt=\"TypeScript\" />
  <img src=\"https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white\" alt=\"Python\" />
  <img src=\"https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white\" alt=\"PostgreSQL\" />
  <img src=\"https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white\" alt=\"MySQL\" />
  <img src=\"https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white\" alt=\"Redis\" />
  <img src=\"https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white\" alt=\"Docker\" />
</p>

## GitHub Stats

<p>
  <img height=\"160\" src=\"https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&hide_border=true\" alt=\"github stats\" />
  <img height=\"160\" src=\"https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&hide_border=true\" alt=\"top langs\" />
</p>

## Current Focus

- Build practical AI developer tools (desktop + backend)
- Learn LLM training workflows in public with runnable examples
- Keep projects concise, documented, and production-minded

---

If you're working on backend systems or AI developer tooling, feel free to connect.
"""


def build_readme_zh(user: Dict, active: List[Dict], reps: List[Dict]) -> str:
    date_str = sync_date()
    year_range = active_year_range(active)
    public_repos = user.get("public_repos", "-")
    display_name = user.get("name") or PROFILE_NAME
    company = (user.get("company") or PROFILE_COMPANY).lstrip("@")
    location = user.get("location") or PROFILE_LOCATION
    return f"""<h1 align=\"center\">你好，我是 {display_name}</h1>

<p align=\"center\"><a href=\"./README.md\">English</a> | 简体中文</p>

<p align=\"center\">
  <a href=\"https://github.com/{USERNAME}\">
    <img src=\"https://komarev.com/ghpvc/?username={USERNAME}&label=Profile%20views&color=0e75b6&style=flat\" alt=\"profile views\" />
  </a>
  <a href=\"https://github.com/{USERNAME}?tab=followers\">
    <img src=\"https://img.shields.io/github/followers/{USERNAME}?label=Followers&style=flat\" alt=\"followers\" />
  </a>
</p>

<p align=\"center\">
  {company} Java / 后端工程师 · {location}
</p>

<p align=\"center\">
  <a href=\"https://github.com/{USERNAME}\">GitHub</a> ·
  <a href=\"https://{USERNAME}.github.io\">博客</a> ·
  <a href=\"mailto:{PROFILE_EMAIL}\">邮箱</a>
</p>

## 个人概览

- `@{company}` Java / 后端工程师
- 关注方向：分布式系统与 AI 应用工程
- 近期重点：Agent 工具链、MCP/Spring AI 示例、LLM 训练实践
- 公开仓库：`{public_repos}`（数据同步于 `{date_str}`）

## 活跃项目（{year_range}）

{active_table_zh(active)}

## 代表项目

{rep_table_zh(reps)}

## 技术栈

<p>
  <img src=\"https://img.shields.io/badge/Java-007396?style=flat&logo=openjdk&logoColor=white\" alt=\"Java\" />
  <img src=\"https://img.shields.io/badge/Spring-6DB33F?style=flat&logo=spring&logoColor=white\" alt=\"Spring\" />
  <img src=\"https://img.shields.io/badge/TypeScript-3178C6?style=flat&logo=typescript&logoColor=white\" alt=\"TypeScript\" />
  <img src=\"https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white\" alt=\"Python\" />
  <img src=\"https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white\" alt=\"PostgreSQL\" />
  <img src=\"https://img.shields.io/badge/MySQL-4479A1?style=flat&logo=mysql&logoColor=white\" alt=\"MySQL\" />
  <img src=\"https://img.shields.io/badge/Redis-DC382D?style=flat&logo=redis&logoColor=white\" alt=\"Redis\" />
  <img src=\"https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white\" alt=\"Docker\" />
</p>

## GitHub 统计

<p>
  <img height=\"160\" src=\"https://github-readme-stats.vercel.app/api?username={USERNAME}&show_icons=true&hide_border=true\" alt=\"github stats\" />
  <img height=\"160\" src=\"https://github-readme-stats.vercel.app/api/top-langs/?username={USERNAME}&layout=compact&hide_border=true\" alt=\"top langs\" />
</p>

## 当前关注

- 打造实用的 AI 开发者工具（桌面端 + 后端）
- 通过可运行示例持续公开学习 LLM 训练流程
- 保持项目小步快跑、文档清晰、可长期维护

---

如果你也在做后端系统或 AI 开发工具，欢迎交流。
"""


def main() -> None:
    user = fetch_user()
    repos = fetch_repos()

    non_fork_repos = [repo for repo in repos if not repo.get("fork")]
    active = select_active_repos(non_fork_repos)
    reps = select_representative_repos(non_fork_repos)

    readme_en = build_readme_en(user, active, reps)
    readme_zh = build_readme_zh(user, active, reps)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_en)

    with open("README.zh-CN.md", "w", encoding="utf-8") as f:
        f.write(readme_zh)

    print(f"Synced README.md and README.zh-CN.md for @{USERNAME}")


if __name__ == "__main__":
    main()
