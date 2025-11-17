import requests, json, os

TOKEN = os.getenv("TOKEN")
USERNAME = os.getenv("USERNAME")

headers = {"Authorization": f"Bearer {TOKEN}"}

# ================================
# FETCH ALL REPOS (public + private)
# ================================
repos = []
page = 1

while True:
    r = requests.get(
        f"https://api.github.com/user/repos?per_page=100&page={page}",
        headers=headers
    )
    batch = r.json()

    if not batch or isinstance(batch, dict):
        break

    repos.extend(batch)
    page += 1

# ================================
# BASIC METRICS
# ================================
stars = sum(repo["stargazers_count"] for repo in repos)
forks = sum(repo["forks_count"] for repo in repos)
repo_count = len(repos)

# ================================
# COMMITS + LINES OF CODE
# ================================
total_commits = 0
total_additions = 0
total_deletions = 0

for repo in repos:
    name = repo["name"]
    owner = repo["owner"]["login"]

    page = 1
    while True:
        commits = requests.get(
            f"https://api.github.com/repos/{owner}/{name}/commits?author={USERNAME}&per_page=100&page={page}",
            headers=headers
        ).json()

        if not commits or isinstance(commits, dict):
            break

        for commit in commits:
            sha = commit["sha"]
            detail = requests.get(
                f"https://api.github.com/repos/{owner}/{name}/commits/{sha}",
                headers=headers
            ).json()

            if "stats" in detail:
                total_commits += 1
                total_additions += detail["stats"]["additions"]
                total_deletions += detail["stats"]["deletions"]

        page += 1

# ================================
# LANGUAGES (TOP 3 + TOTAL COUNT)
# ================================
language_map = {}  # {lang: total_bytes}

for repo in repos:
    lang_url = repo["languages_url"]
    lang_data = requests.get(lang_url, headers=headers).json()

    for lang, bytes_of_code in lang_data.items():
        language_map[lang] = language_map.get(lang, 0) + bytes_of_code

sorted_langs = sorted(language_map.items(), key=lambda x: x[1], reverse=True)

top_languages = sorted_langs[:3]  # [(lang, bytes), ...]

languages_used = len(language_map)

# Convert top languages to simple list format
top_languages_formatted = [
    {"language": lang, "bytes": bytes_of_code}
    for lang, bytes_of_code in top_languages
]

# ================================
# OUTPUT FINAL METRICS
# ================================
stats = {
    "stars": stars,
    "forks": forks,
    "all_time_contributions": total_commits,
    "loc_changed": total_additions + total_deletions,
    "repos_contributed": repo_count,
    "languages_used": languages_used,
    "top_languages": top_languages_formatted,
}

with open("stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print("Stats generated successfully!")
