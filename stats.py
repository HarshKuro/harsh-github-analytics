import requests, json, os

TOKEN = os.getenv("TOKEN")
USERNAME = os.getenv("USERNAME")

headers = {"Authorization": f"Bearer {TOKEN}"}

# Fetch repos
repos = []
page = 1
while True:
    r = requests.get(f"https://api.github.com/user/repos?per_page=100&page={page}", headers=headers)
    batch = r.json()
    if not batch or isinstance(batch, dict):
        break
    repos.extend(batch)
    page += 1

stars = sum(r["stargazers_count"] for r in repos)
forks = sum(r["forks_count"] for r in repos)
repo_count = len(repos)

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

# Traffic API (14-day repo views)
views = 0
for repo in repos:
    traffic = requests.get(
        f"https://api.github.com/repos/{repo['owner']['login']}/{repo['name']}/traffic/views",
        headers=headers
    ).json()
    if "count" in traffic:
        views += traffic["count"]

stats = {
    "stars": stars,
    "forks": forks,
    "all_time_contributions": total_commits,
    "loc_changed": total_additions + total_deletions,
    "repo_views_14d": views,
    "repos_contributed": repo_count
}

with open("stats.json", "w") as f:
    json.dump(stats, f, indent=2)
