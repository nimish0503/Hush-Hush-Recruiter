'''This script extracts GitHub user data and saves it to a CSV file:
1. Connects to GitHub API using authentication tokens and rotates them when rate limits are reached.  
2. Searches for users based on a query (e.g., "data science") and retrieves profiles.  
3. Extracts user details like email, profile URL, avatar, public repositories, and followers.  
4. Collects repository metrics including stars, forks, commits, pull requests, and issue statistics.  
5. Gathers contribution data such as the number of contributed repositories and code reviews.  
6. Filters users to include only those with valid public email addresses.  
7. Saves the data into a CSV file for further analysis.  
8. Uses async processing for efficient API requests and data retrieval.'''

import aiohttp
import asyncio
import csv
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class GitHubUserExtractor:
    def __init__(self, tokens: List[str], search_query: str, pages: int):
        self.tokens = tokens
        self.search_query = search_query
        self.pages = pages
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.tokens[0]}"
        }
        self.current_token_index = 0

    async def fetch_users(self, session: aiohttp.ClientSession, page: int) -> Optional[Dict]:
        url = f"https://api.github.com/search/users?q={self.search_query}&sort=repositories&order=desc&page={page}&per_page=30"
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 403: 
                    print(f"Rate limit exceeded. Rotating token...")
                    self.rotate_token()
                    return await self.fetch_users(session, page)
                else:
                    print(f"Error fetching page {page}: {response.status}")
                    return None
        except Exception as e:
            print(f"Exception occurred while fetching users: {e}")
            return None

    def rotate_token(self):
        self.current_token_index = (self.current_token_index + 1) % len(self.tokens)
        self.headers["Authorization"] = f"Bearer {self.tokens[self.current_token_index]}"
        print(f"Switched to token index {self.current_token_index}")

    async def get_user_details(self, session: aiohttp.ClientSession, username: str) -> Optional[Dict]:
        url = f"https://api.github.com/users/{username}"
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    user_data = await response.json()
                    return {
                        "email": user_data.get("email"),
                        "html_url": user_data.get("html_url"),
                        "avatar_url": user_data.get("avatar_url"),
                        "public_repos": user_data.get("public_repos"),
                        "followers": user_data.get("followers")
                    }
                elif response.status == 403:  
                    print(f"Rate limit exceeded. Rotating token...")
                    self.rotate_token()
                    return await self.get_user_details(session, username)
                else:
                    print(f"Error fetching details for {username}: {response.status}")
                    return None
        except Exception as e:
            print(f"Exception occurred while fetching details for {username}: {e}")
            return None

    async def get_repo_metrics(self, session: aiohttp.ClientSession, username: str) -> Optional[Dict]:
        url = f"https://api.github.com/users/{username}/repos"
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    repos = await response.json()
                    total_stars = 0
                    total_forks = 0
                    total_pr_merged = 0
                    total_issues_opened = 0
                    total_issues_closed = 0
                    total_commits_last_year = 0
                    total_commits_all_time = 0
                    total_issue_close_time = 0
                    total_issues_with_close_time = 0

                    for repo in repos:
                        repo_name = repo.get("name")
                        total_stars += repo.get("stargazers_count", 0)
                        total_forks += repo.get("forks_count", 0)

                        
                        prs_url = f"https://api.github.com/repos/{username}/{repo_name}/pulls?state=closed"
                        issues_url = f"https://api.github.com/repos/{username}/{repo_name}/issues?state=all"

                        async with session.get(prs_url, headers=self.headers) as prs_response:
                            if prs_response.status == 200:
                                prs = await prs_response.json()
                                total_pr_merged += len([pr for pr in prs if pr.get("merged_at")])

                        async with session.get(issues_url, headers=self.headers) as issues_response:
                            if issues_response.status == 200:
                                issues = await issues_response.json()
                                for issue in issues:
                                    if issue.get("state") == "open":
                                        total_issues_opened += 1
                                    elif issue.get("state") == "closed":
                                        total_issues_closed += 1
                                        created_at = issue.get("created_at")
                                        closed_at = issue.get("closed_at")
                                        if created_at and closed_at:
                                            created = datetime.fromisoformat(created_at[:-1])  
                                            closed = datetime.fromisoformat(closed_at[:-1])
                                            total_issue_close_time += (closed - created).days
                                            total_issues_with_close_time += 1

                        
                        commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
                        since_date = (datetime.now() - timedelta(days=365)).isoformat()
                        params = {"since": since_date}
                        async with session.get(commits_url, headers=self.headers, params=params) as commits_response:
                            if commits_response.status == 200:
                                commits = await commits_response.json()
                                total_commits_last_year += len(commits)

                        
                        async with session.get(commits_url, headers=self.headers) as all_commits_response:
                            if all_commits_response.status == 200:
                                all_commits = await all_commits_response.json()
                                total_commits_all_time += len(all_commits)

                    
                    avg_commits_per_month = (total_commits_last_year / 12) if total_commits_last_year > 0 else 0

                    
                    avg_issue_close_time = (total_issue_close_time / total_issues_with_close_time) if total_issues_with_close_time > 0 else 0

                    return {
                        "total_stars": total_stars,
                        "total_forks": total_forks,
                        "total_pr_merged": total_pr_merged,
                        "total_issues_opened": total_issues_opened,
                        "total_issues_closed": total_issues_closed,
                        "total_commits_last_year": total_commits_last_year,
                        "total_commits_all_time": total_commits_all_time,
                        "avg_commits_per_month": avg_commits_per_month,
                        "avg_issue_close_time": avg_issue_close_time
                    }
                elif response.status == 403:  
                    print(f"Rate limit exceeded. Rotating token...")
                    self.rotate_token()
                    return await self.get_repo_metrics(session, username)
                else:
                    print(f"Error fetching repo metrics for {username}: {response.status}")
                    return None
        except Exception as e:
            print(f"Exception occurred while fetching repo metrics for {username}: {e}")
            return None

    async def get_contributed_repos(self, session: aiohttp.ClientSession, username: str) -> int:
        url = f"https://api.github.com/users/{username}/events"
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    events = await response.json()
                    repos = set()
                    for event in events:
                        if event.get("type") in ["PushEvent", "PullRequestEvent", "IssueCommentEvent"]:
                            repo = event.get("repo", {}).get("name")
                            if repo:
                                repos.add(repo)
                    return len(repos)
                else:
                    print(f"Error fetching events for {username}: {response.status}")
                    return 0
        except Exception as e:
            print(f"Exception occurred while fetching events for {username}: {e}")
            return 0

    async def get_code_reviews_count(self, session: aiohttp.ClientSession, username: str) -> int:
        url = f"https://api.github.com/users/{username}/events"
        try:
            async with session.get(url, headers=self.headers) as response:
                if response.status == 200:
                    events = await response.json()
                    reviews_count = 0
                    for event in events:
                        if event.get("type") == "PullRequestReviewEvent":
                            reviews_count += 1
                    return reviews_count
                else:
                    print(f"Error fetching events for {username}: {response.status}")
                    return 0
        except Exception as e:
            print(f"Exception occurred while fetching events for {username}: {e}")
            return 0

    def is_valid_email(self, email: str) -> bool:
        
        if not email:
            return False
        
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        return re.match(email_regex, email) is not None

    async def extract_users_with_details(self) -> List[Dict[str, str]]:
        users_with_details = []
        async with aiohttp.ClientSession() as session:
            for page in range(1, self.pages + 1):
                print(f"Fetching page {page}...")
                users_data = await self.fetch_users(session, page)
                if users_data and "items" in users_data:
                    for user in users_data["items"]:
                        username = user.get("login")
                        if username:
                            print(f"\nProcessing user: {username}")
                            user_details = await self.get_user_details(session, username)
                            if user_details and user_details.get("email") and self.is_valid_email(user_details["email"]):
                                repo_metrics = await self.get_repo_metrics(session, username)
                                contributed_repos = await self.get_contributed_repos(session, username)
                                code_reviews_count = await self.get_code_reviews_count(session, username)
                                if repo_metrics:
                                    users_with_details.append({
                                        "username": username,
                                        "email": user_details["email"],
                                        "user_url": user_details["html_url"],
                                        "avatar_url": user_details["avatar_url"],
                                        "public_repos": user_details["public_repos"],
                                        "followers": user_details["followers"],
                                        "total_stars": repo_metrics["total_stars"],
                                        "total_forks": repo_metrics["total_forks"],
                                        "total_pr_merged": repo_metrics["total_pr_merged"],
                                        "total_issues_opened": repo_metrics["total_issues_opened"],
                                        "total_issues_closed": repo_metrics["total_issues_closed"],
                                        "total_commits_last_year": repo_metrics["total_commits_last_year"],
                                        "total_commits_all_time": repo_metrics["total_commits_all_time"],
                                        "avg_commits_per_month": repo_metrics["avg_commits_per_month"],
                                        "avg_issue_close_time": repo_metrics["avg_issue_close_time"],
                                        "contributed_repos": contributed_repos,
                                        "code_reviews_count": code_reviews_count
                                    })
                                    print(f"Added details for user: {username}")
                                else:
                                    print(f"Failed to fetch repo metrics for user: {username}")
                            else:
                                print(f"Invalid or no email found for user: {username}")
                        else:
                            print(f"Invalid user data: {user}")
                else:
                    print(f"No user data found for page {page}")
        return users_with_details

    def save_to_csv(self, users_with_details: List[Dict[str, str]]):
        
        output_dir = "/home/ashwin_jayan/EXTRACT/data_science"
        os.makedirs(output_dir, exist_ok=True)
        csv_file_path = os.path.join(output_dir, "users_with_details_data_science_21to41.csv")

        
        with open(csv_file_path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=[
                "username", "email", "user_url", "avatar_url", "public_repos", "followers",
                "total_stars", "total_forks", "total_pr_merged", "total_issues_opened", "total_issues_closed",
                "total_commits_last_year", "total_commits_all_time", "avg_commits_per_month",
                "avg_issue_close_time", "contributed_repos", "code_reviews_count"
            ])
            writer.writeheader()
            for user in users_with_details:
                writer.writerow(user)
        print(f"Data saved to {csv_file_path}")

async def main(tokens: List[str], search_query: str, pages: int):
    extractor = GitHubUserExtractor(tokens, search_query, pages)
    users_with_details = await extractor.extract_users_with_details()
    if users_with_details:
        print("\nUsers with details:")
        for user in users_with_details:
            print(f"Username: {user['username']}, Email: {user['email']}, User URL: {user['user_url']}, "
                  f"Avatar URL: {user['avatar_url']}, Public Repos: {user['public_repos']}, "
                  f"Followers: {user['followers']}, Total Stars: {user['total_stars']}, "
                  f"Total Forks: {user['total_forks']}, Total PRs Merged: {user['total_pr_merged']}, "
                  f"Total Issues Opened: {user['total_issues_opened']}, Total Issues Closed: {user['total_issues_closed']}, "
                  f"Total Commits (Last Year): {user['total_commits_last_year']}, Total Commits (All Time): {user['total_commits_all_time']}, "
                  f"Avg Commits per Month: {user['avg_commits_per_month']}, Avg Issue Close Time: {user['avg_issue_close_time']}, "
                  f"Contributed Repos: {user['contributed_repos']}, Code Reviews Count: {user['code_reviews_count']}")
        
        extractor.save_to_csv(users_with_details)
    else:
        print("No users with valid public emails found.")


GITHUB_TOKENS = []

SEARCH_QUERY = "data+science"  
PAGES = 30  

asyncio.run(main(GITHUB_TOKENS, SEARCH_QUERY, PAGES))