import os
import requests
from typing import List, Dict
from groq import Groq
from datetime import datetime, timedelta
import pytz
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
import json
from bs4 import BeautifulSoup
from rich.markdown import Markdown


class GitHubTrendingReporter:
    def __init__(self, groq_api_key: str):
        self.groq_client = Groq(api_key=groq_api_key)
        self.console = Console()
        self.cache_file = "github_trending_cache.json"

    def should_refresh_cache(self) -> bool:
        if not os.path.exists(self.cache_file):
            return True

        file_timestamp = datetime.fromtimestamp(os.path.getmtime(self.cache_file))
        current_time = datetime.now()
        return (current_time - file_timestamp) > timedelta(hours=24)

    def load_cached_report(self) -> dict:
        with open(self.cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_cache(self, report_data: dict):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=4)

    # def fetch_trending_repos(self, language: str = None) -> List[Dict]:
    #     base_url = "https://api.github.com/search/repositories"
    #     params = {
    #         "q": f"created:>{datetime.now(pytz.UTC).strftime('%Y-%m-%d')} " +
    #               ("language:" + language if language else ""),
    #         "sort": "stars",
    #         "order": "desc",
    #         "per_page": 10
    #     }



    #     response = requests.get(base_url, params=params)
    #     print(response)
    #     response.raise_for_status()

    #     data = response.json()
    #     print(data)
    #     return data.get('items', [])

    def fetch_trending_repos(self, language: str = None) -> List[Dict]:
        url = f"https://github.com/trending/{language if language else ''}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        trending_repos = []
        articles = soup.select('article.Box-row')

        for article in articles:
            # Get repository name and owner
            title_element = article.select_one('h2.h3')
            full_name = title_element.get_text().strip().replace('\n', '').replace(' ', '')

            # Get description
            description_element = article.select_one('p.col-9')
            description = description_element.text.strip() if description_element else ''

            # Get stars
            stars_element = article.select('a.Link--muted')[1]  # Second element contains total stars
            stars = stars_element.text.strip()

            repo = {
                'full_name': full_name,
                'description': description,
                'html_url': f"https://github.com/{full_name}",
                'stargazers_count': stars
            }
            trending_repos.append(repo)

        return trending_repos[:10]

    def generate_repo_summary(self, repos: List[Dict]) -> str:
        repo_details = "\n\n".join([
            f"Repository: {repo['full_name']}\n"
            f"Description: {repo.get('description', 'No description')}\n"
            f"Stars: {repo['stargazers_count']}\n"
            f"URL: {repo['html_url']}"
            for repo in repos
        ])

        prompt = f"""Provide a professional summary of the following trending GitHub repositories.
        Highlight their purpose, key features, and potential use cases:

        {repo_details}
        """

        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are an expert software analyst summarizing GitHub repositories."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192"
        )

        return chat_completion.choices[0].message.content

    # def display_report(self, report: str):
    #     self.console.print("\n")
    #     title = Text("🚀 GitHub Trending Repositories Report", style="bold magenta")
    #     self.console.print(Panel(title, border_style="bright_blue"))

    #     date_text = Text(f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", style="italic cyan")
    #     self.console.print(date_text)
    #     self.console.print("\n")

    #     sections = report.split("---")
    #     for section in sections:
    #         if section.strip():
    #             section_title = Text(section.split("\n")[0], style="bold yellow")
    #             section_content = "\n".join(section.split("\n")[1:])
    #             self.console.print(Panel(
    #                 Text(section_content, style="bright_white"),
    #                 title=section_title,
    #                 border_style="green"
    #             ))
    #             self.console.print("\n")
    def display_report(self, report: str):
        self.console.print("\n")
        title = Text("🚀 GitHub Trending Repositories Report", style="bold magenta")
        self.console.print(Panel(title, border_style="bright_blue"))

        date_text = Text(f"Generated on: {datetime.now().strftime('%Y-%m-%d')}", style="italic cyan")
        self.console.print(date_text)
        self.console.print("\n")

        sections = report.split("---")
        for section in sections:
            if section.strip():
                # Parse section title and content
                lines = section.strip().split('\n')
                section_title = Text(lines[0], style="bold yellow")
                section_content = '\n'.join(lines[1:])

                # Render markdown content
                markdown = Markdown(section_content)
                self.console.print(Panel(
                    markdown,
                    title=section_title,
                    border_style="green"
                ))
                self.console.print("\n")


    def generate_daily_report(self):
        if not self.should_refresh_cache():
            self.console.print("📂 Loading report from cache...", style="bold blue")
            cached_data = self.load_cached_report()
            self.display_report(cached_data['full_report'])
            return

        self.console.print("🔄 Fetching fresh data...", style="bold green")

        all_trending = self.fetch_trending_repos()

        print(all_trending)
        all_repos_summary = self.generate_repo_summary(all_trending)

        golang_trending = self.fetch_trending_repos(language='go')
        golang_repos_summary = self.generate_repo_summary(golang_trending)

        full_report = f"""Daily GitHub Trending Repositories Report
{datetime.now().strftime('%Y-%m-%d')}

--- All Trending Repositories ---
{all_repos_summary}

--- Trending Golang Repositories ---
{golang_repos_summary}
"""
        # Cache the report
        cache_data = {
            'timestamp': datetime.now().isoformat(),
            'full_report': full_report
        }
        self.save_cache(cache_data)

        self.display_report(full_report)
        self.console.print("✨ Fresh report generated and cached!", style="bold green")

def main():
    groq_api_key = os.getenv('GROQ_API_KEY')

    reporter = GitHubTrendingReporter(groq_api_key)
    # print("Treding repose")
    # data = reporter.fetch_trending_repos()
    reporter.generate_daily_report()

if __name__ == "__main__":
    main()
