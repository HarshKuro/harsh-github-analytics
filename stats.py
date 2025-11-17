import requests, json, os

TOKEN = os.getenv("TOKEN")
USERNAME = os.getenv("USERNAME")

headers = {"Authorization": f"Bearer {TOKEN}"}

# ================================
# FETCH ALL REPOS
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

# Format numbers with commas
def fmt(n):
    return f"{n:,}"

# ================================
# LINES OF CODE
# ================================
total_additions = 0
total_deletions = 0

page = 1
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
                total_additions += detail["stats"]["additions"]
                total_deletions += detail["stats"]["deletions"]

        page += 1

# ================================
# LANGUAGES (IGNORING C, C++, JAVA)
# ================================
IGNORE = {"C", "C++", "C#", "Java"}  # you can expand this anytime

language_map = {}

for repo in repos:
    lang_data = requests.get(repo["languages_url"], headers=headers).json()
    for lang, bytes_of_code in lang_data.items():
        if lang in IGNORE:
            continue
        language_map[lang] = language_map.get(lang, 0) + bytes_of_code

# Sort languages
sorted_langs = sorted(language_map.items(), key=lambda x: x[1], reverse=True)
top_languages = sorted_langs[:3]

# FINAL STATS
stats = {
    "stars": fmt(stars),
    "forks": fmt(forks),
    "loc_changed": fmt(total_additions + total_deletions),
    "repos_contributed": fmt(repo_count),
    "languages_used": fmt(len(language_map)),
    "top_languages": [lang for lang, _ in top_languages]
}

with open("stats.json", "w") as f:
    json.dump(stats, f, indent=2)

print("Stats updated.")
