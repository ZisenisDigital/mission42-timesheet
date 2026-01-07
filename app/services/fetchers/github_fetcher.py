"""
GitHub Data Fetcher

Fetches commits and issues from GitHub API (priority: 40).
Tracks development activity and issue work.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from github import Github, GithubException, RateLimitExceededException
from github.Repository import Repository
from github.Commit import Commit
from github.Issue import Issue

from app.services.fetchers.base import BaseFetcher, FetchResult
from app.pocketbase_client import PocketBaseClient
from app.utils.priority import SOURCE_GITHUB


class GitHubAPI:
    """
    Wrapper for GitHub API using PyGithub.

    API Documentation: https://docs.github.com/en/rest
    """

    def __init__(self, access_token: str):
        """
        Initialize GitHub API client.

        Args:
            access_token: GitHub personal access token
        """
        self.access_token = access_token
        self.github = Github(access_token)

    def get_repository(self, repo_name: str) -> Repository:
        """
        Get a repository by full name.

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            Repository object

        Raises:
            GithubException: If repository not found or access denied
        """
        return self.github.get_repo(repo_name)

    def get_commits(
        self,
        repo: Repository,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        author: Optional[str] = None,
    ) -> List[Commit]:
        """
        Get commits from a repository.

        Args:
            repo: Repository object
            since: Only commits after this date
            until: Only commits before this date
            author: Filter by commit author (username)

        Returns:
            List of Commit objects
        """
        kwargs = {}
        if since:
            kwargs['since'] = since
        if until:
            kwargs['until'] = until
        if author:
            kwargs['author'] = author

        commits = repo.get_commits(**kwargs)
        return list(commits)

    def get_user_issues(
        self,
        repo: Repository,
        assignee: str,
        since: Optional[datetime] = None,
        state: str = 'all',
    ) -> List[Issue]:
        """
        Get issues assigned to a specific user.

        Args:
            repo: Repository object
            assignee: GitHub username
            since: Only issues updated since this date
            state: Issue state ('open', 'closed', 'all')

        Returns:
            List of Issue objects
        """
        issues = repo.get_issues(assignee=assignee, state=state, since=since)
        return list(issues)

    def get_current_user(self) -> str:
        """
        Get the authenticated user's username.

        Returns:
            Username string

        Raises:
            GithubException: If authentication fails
        """
        return self.github.get_user().login

    def test_connection(self) -> bool:
        """
        Test API connection and authentication.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.github.get_user()
            return True
        except Exception:
            return False

    def get_rate_limit(self) -> Dict[str, Any]:
        """
        Get current rate limit status.

        Returns:
            Dictionary with rate limit info
        """
        rate_limit = self.github.get_rate_limit()
        return {
            'core': {
                'limit': rate_limit.core.limit,
                'remaining': rate_limit.core.remaining,
                'reset': rate_limit.core.reset,
            }
        }


class GitHubFetcher(BaseFetcher):
    """
    Fetches commits and issues from GitHub API.

    GitHub is a lower priority source (40) for supplementary development tracking.
    """

    def __init__(
        self,
        pb_client: PocketBaseClient,
        access_token: Optional[str] = None,
    ):
        """
        Initialize GitHub fetcher.

        Args:
            pb_client: PocketBase client instance
            access_token: GitHub personal access token (defaults to GITHUB_TOKEN env var)
        """
        super().__init__(
            pb_client=pb_client,
            source_name=SOURCE_GITHUB,
            enabled_setting_key="github_enabled",
        )

        self.access_token = access_token or os.getenv("GITHUB_TOKEN")
        self.api = GitHubAPI(self.access_token) if self.access_token else None
        self.username = None

    def validate_configuration(self) -> tuple[bool, Optional[str]]:
        """
        Validate GitHub configuration.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.access_token:
            return (False, "GITHUB_TOKEN not set in environment")

        if not self.api:
            return (False, "GitHub API client not initialized")

        # Test API connection
        try:
            if not self.api.test_connection():
                return (False, "Failed to connect to GitHub API (invalid token?)")

            # Store username for filtering
            self.username = self.api.get_current_user()

        except Exception as e:
            return (False, f"GitHub API connection error: {str(e)}")

        return (True, None)

    def _get_monitored_repositories(self) -> List[str]:
        """
        Get list of repositories to monitor from settings.

        Returns:
            List of repository names in "owner/repo" format
        """
        try:
            repos_str = self.pb_client.get_setting("github_repositories")
            if not repos_str:
                return []

            # Parse comma-separated list
            repos = [repo.strip() for repo in repos_str.split(",")]
            return [r for r in repos if r and '/' in r]  # Filter invalid formats

        except Exception:
            return []

    def _should_track_commits(self) -> bool:
        """Check if commit tracking is enabled"""
        try:
            value = self.pb_client.get_setting("github_track_commits")
            # Handle string booleans
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        except Exception:
            return True  # Default to enabled

    def _should_track_issues(self) -> bool:
        """Check if issue tracking is enabled"""
        try:
            value = self.pb_client.get_setting("github_track_issues")
            # Handle string booleans
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        except Exception:
            return True  # Default to enabled

    def _should_track_prs(self) -> bool:
        """Check if PR tracking is enabled"""
        try:
            value = self.pb_client.get_setting("github_track_prs")
            # Handle string booleans
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        except Exception:
            return False  # Default to disabled

    def _estimate_commit_duration(self, commit: Commit) -> int:
        """
        Estimate duration in minutes based on commit size.

        Args:
            commit: GitHub Commit object

        Returns:
            Estimated duration in minutes

        Logic:
        - Small commits (< 50 lines): 30 min
        - Medium commits (50-200 lines): 60 min
        - Large commits (200-500 lines): 120 min
        - Very large commits (> 500 lines): 180 min
        """
        try:
            additions = commit.stats.additions
            deletions = commit.stats.deletions
            total_changes = additions + deletions

            if total_changes < 50:
                return 30
            elif total_changes < 200:
                return 60
            elif total_changes < 500:
                return 120
            else:
                return 180

        except Exception:
            return 30  # Default

    def _extract_issue_numbers(self, text: str) -> List[int]:
        """
        Extract issue numbers from text (e.g., #123, #456).

        Args:
            text: Text to search (commit message, PR title, etc.)

        Returns:
            List of issue numbers
        """
        import re
        # Match #123 pattern
        pattern = r'#(\d+)'
        matches = re.findall(pattern, text)
        return [int(num) for num in matches]

    def _process_commit(
        self, commit: Commit, repo_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single commit into an event.

        Args:
            commit: GitHub Commit object
            repo_name: Repository name

        Returns:
            Event dictionary or None if should be skipped
        """
        try:
            # Get commit details
            commit_date = commit.commit.author.date
            message = commit.commit.message.split('\n')[0]  # First line only
            sha = commit.sha[:7]  # Short SHA

            # Extract issue numbers from message
            issue_numbers = self._extract_issue_numbers(message)

            # Build description
            if issue_numbers:
                issue_ref = f" (issue #{issue_numbers[0]})"
                description = f"Commit: {message}{issue_ref}"
            else:
                description = f"Commit: {message}"

            # Estimate duration
            duration = self._estimate_commit_duration(commit)

            # Create unique source ID
            source_id = f"github_commit_{repo_name}_{sha}".replace('/', '_')

            # Metadata
            metadata = {
                "repo": repo_name,
                "sha": commit.sha,
                "short_sha": sha,
                "message": commit.commit.message,
                "files_changed": len(commit.files) if commit.files else 0,
                "additions": commit.stats.additions,
                "deletions": commit.stats.deletions,
                "issue_numbers": issue_numbers,
                "url": commit.html_url,
            }

            return {
                "source_id": source_id,
                "timestamp": commit_date,
                "duration_minutes": duration,
                "description": description,
                "metadata": metadata,
            }

        except Exception as e:
            print(f"Error processing commit {commit.sha}: {e}")
            return None

    def _process_issue(
        self, issue: Issue, repo_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single issue into an event.

        Args:
            issue: GitHub Issue object
            repo_name: Repository name

        Returns:
            Event dictionary or None if should be skipped
        """
        try:
            # Skip pull requests (they have a pull_request attribute)
            if issue.pull_request:
                return None

            # Use updated_at as the timestamp
            timestamp = issue.updated_at

            # Build description
            description = f"Working on Issue #{issue.number}: {issue.title}"

            # Estimate duration (default 60 min for issue work)
            # Could be enhanced to calculate based on time between updates
            duration = 60

            # Create unique source ID
            source_id = f"github_issue_{repo_name}_{issue.number}".replace('/', '_')

            # Metadata
            metadata = {
                "repo": repo_name,
                "issue_number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "labels": [label.name for label in issue.labels],
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "url": issue.html_url,
            }

            return {
                "source_id": source_id,
                "timestamp": timestamp,
                "duration_minutes": duration,
                "description": description,
                "metadata": metadata,
            }

        except Exception as e:
            print(f"Error processing issue #{issue.number}: {e}")
            return None

    def fetch(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> FetchResult:
        """
        Fetch commits and issues from GitHub and save to PocketBase.

        Args:
            start_date: Optional start date (defaults to last fetch or 7 days ago)
            end_date: Optional end date (defaults to now)

        Returns:
            FetchResult with success status and statistics
        """
        # Check if enabled
        if not self.is_enabled():
            return FetchResult(
                success=False,
                error="GitHub fetcher is disabled in settings",
            )

        # Validate configuration
        is_valid, error_msg = self.validate_configuration()
        if not is_valid:
            return FetchResult(success=False, error=error_msg)

        # Get monitored repositories
        repositories = self._get_monitored_repositories()
        if not repositories:
            return FetchResult(
                success=False,
                error="No GitHub repositories configured in settings",
            )

        # Get tracking preferences
        track_commits = self._should_track_commits()
        track_issues = self._should_track_issues()

        if not track_commits and not track_issues:
            return FetchResult(
                success=False,
                error="Both commit and issue tracking are disabled",
            )

        # Get date range
        if not start_date or not end_date:
            start_date, end_date = self.get_default_date_range(days_back=7)

        events_fetched = 0
        events_created = 0
        repos_processed = 0
        errors = []

        try:
            for repo_name in repositories:
                try:
                    # Get repository
                    repo = self.api.get_repository(repo_name)
                    repos_processed += 1

                    # Fetch commits
                    if track_commits:
                        commits = self.api.get_commits(
                            repo=repo,
                            since=start_date,
                            until=end_date,
                            author=self.username,
                        )

                        for commit in commits:
                            event_data = self._process_commit(commit, repo_name)
                            if event_data:
                                events_fetched += 1

                                # Check if event already exists
                                if not self.event_exists(event_data["source_id"]):
                                    self.create_raw_event(**event_data)
                                    events_created += 1

                    # Fetch assigned issues
                    if track_issues and self.username:
                        issues = self.api.get_user_issues(
                            repo=repo,
                            assignee=self.username,
                            since=start_date,
                            state='all',
                        )

                        for issue in issues:
                            # Filter by date range
                            if issue.updated_at < start_date or issue.updated_at > end_date:
                                continue

                            event_data = self._process_issue(issue, repo_name)
                            if event_data:
                                events_fetched += 1

                                # Check if event already exists
                                if not self.event_exists(event_data["source_id"]):
                                    self.create_raw_event(**event_data)
                                    events_created += 1

                except RateLimitExceededException as e:
                    # Rate limit should stop the entire fetch
                    raise

                except GithubException as e:
                    error_msg = f"Error fetching {repo_name}: {e.data.get('message', str(e))}"
                    errors.append(error_msg)
                    print(f"[github] {error_msg}")
                    continue

            result = FetchResult(
                success=True,
                events_fetched=events_fetched,
                events_created=events_created,
                metadata={
                    "username": self.username,
                    "repositories": repositories,
                    "repos_processed": repos_processed,
                    "track_commits": track_commits,
                    "track_issues": track_issues,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "errors": errors,
                },
            )

            self.log_fetch_result(result)
            return result

        except RateLimitExceededException:
            # Get rate limit info if possible
            try:
                rate_info = self.api.get_rate_limit()
                reset_time = rate_info['core']['reset']
                return FetchResult(
                    success=False,
                    error=f"GitHub API rate limit exceeded. Resets at {reset_time}",
                )
            except Exception:
                return FetchResult(
                    success=False,
                    error="GitHub API rate limit exceeded",
                )

        except Exception as e:
            return FetchResult(success=False, error=f"Unexpected error: {str(e)}")
