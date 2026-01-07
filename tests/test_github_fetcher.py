"""
Unit Tests for GitHub Fetcher

Tests for GitHub API integration and commit/issue fetching.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from github import GithubException, RateLimitExceededException

from app.services.fetchers.github_fetcher import GitHubAPI, GitHubFetcher
from app.services.fetchers.base import FetchResult
from app.pocketbase_client import PocketBaseClient


class TestGitHubAPI:
    """Test GitHub API wrapper"""

    @pytest.fixture
    def api(self):
        """Create GitHub API instance"""
        with patch("app.services.fetchers.github_fetcher.Github") as mock_github:
            api = GitHubAPI(access_token="test_token_123")
            api.github = mock_github.return_value
            return api

    def test_initialization(self):
        """Test API initialization"""
        with patch("app.services.fetchers.github_fetcher.Github") as mock_github:
            api = GitHubAPI(access_token="test_token_123")
            mock_github.assert_called_once_with("test_token_123")
            assert api.access_token == "test_token_123"

    def test_get_repository(self, api):
        """Test getting repository"""
        mock_repo = Mock()
        api.github.get_repo.return_value = mock_repo

        repo = api.get_repository("owner/repo")

        assert repo == mock_repo
        api.github.get_repo.assert_called_once_with("owner/repo")

    def test_get_commits(self, api):
        """Test getting commits"""
        mock_repo = Mock()
        mock_commits = [Mock(), Mock()]
        mock_repo.get_commits.return_value = mock_commits

        since = datetime(2024, 1, 1)
        until = datetime(2024, 1, 7)

        commits = api.get_commits(mock_repo, since=since, until=until, author="testuser")

        assert len(commits) == 2
        mock_repo.get_commits.assert_called_once_with(
            since=since, until=until, author="testuser"
        )

    def test_get_user_issues(self, api):
        """Test getting user issues"""
        mock_repo = Mock()
        mock_issues = [Mock(), Mock()]
        mock_repo.get_issues.return_value = mock_issues

        since = datetime(2024, 1, 1)

        issues = api.get_user_issues(mock_repo, assignee="testuser", since=since)

        assert len(issues) == 2
        mock_repo.get_issues.assert_called_once_with(
            assignee="testuser", state='all', since=since
        )

    def test_get_current_user(self, api):
        """Test getting current user"""
        mock_user = Mock()
        mock_user.login = "testuser"
        api.github.get_user.return_value = mock_user

        username = api.get_current_user()

        assert username == "testuser"

    def test_test_connection_success(self, api):
        """Test successful connection"""
        api.github.get_user.return_value = Mock()

        assert api.test_connection() is True

    def test_test_connection_failure(self, api):
        """Test failed connection"""
        api.github.get_user.side_effect = Exception("Connection failed")

        assert api.test_connection() is False

    def test_get_rate_limit(self, api):
        """Test getting rate limit info"""
        mock_rate_limit = Mock()
        mock_rate_limit.core.limit = 5000
        mock_rate_limit.core.remaining = 4999
        mock_rate_limit.core.reset = datetime(2024, 1, 7, 12, 0, 0)
        api.github.get_rate_limit.return_value = mock_rate_limit

        rate_limit = api.get_rate_limit()

        assert rate_limit['core']['limit'] == 5000
        assert rate_limit['core']['remaining'] == 4999


class TestGitHubFetcher:
    """Test GitHub Fetcher"""

    @pytest.fixture
    def mock_pb_client(self):
        """Create mock PocketBase client"""
        client = Mock(spec=PocketBaseClient)
        client.COLLECTION_RAW_EVENTS = "raw_events"
        return client

    @pytest.fixture
    def fetcher(self, mock_pb_client):
        """Create GitHub fetcher instance"""
        with patch("app.services.fetchers.github_fetcher.GitHubAPI"):
            fetcher = GitHubFetcher(
                pb_client=mock_pb_client,
                access_token="test_token_123",
            )
            fetcher.api = Mock(spec=GitHubAPI)
            return fetcher

    def test_initialization(self, mock_pb_client):
        """Test fetcher initialization"""
        fetcher = GitHubFetcher(
            pb_client=mock_pb_client,
            access_token="test_token_123",
        )

        assert fetcher.source_name == "github"
        assert fetcher.priority == 40
        assert fetcher.access_token == "test_token_123"

    def test_validate_configuration_success(self, fetcher):
        """Test successful configuration validation"""
        fetcher.api.test_connection.return_value = True
        fetcher.api.get_current_user.return_value = "testuser"

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is True
        assert error is None
        assert fetcher.username == "testuser"

    def test_validate_configuration_no_token(self, mock_pb_client):
        """Test validation with no token"""
        fetcher = GitHubFetcher(
            pb_client=mock_pb_client,
            access_token=None,
        )

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "GITHUB_TOKEN" in error

    def test_validate_configuration_connection_failed(self, fetcher):
        """Test validation with connection failure"""
        fetcher.api.test_connection.return_value = False

        is_valid, error = fetcher.validate_configuration()

        assert is_valid is False
        assert "Failed to connect" in error

    def test_get_monitored_repositories(self, fetcher, mock_pb_client):
        """Test getting monitored repositories"""
        mock_pb_client.get_setting.return_value = "owner/repo1, owner/repo2, owner/repo3"

        repos = fetcher._get_monitored_repositories()

        assert len(repos) == 3
        assert "owner/repo1" in repos
        assert "owner/repo2" in repos
        assert "owner/repo3" in repos

    def test_get_monitored_repositories_empty(self, fetcher, mock_pb_client):
        """Test with no repositories configured"""
        mock_pb_client.get_setting.return_value = ""

        repos = fetcher._get_monitored_repositories()

        assert len(repos) == 0

    def test_get_monitored_repositories_invalid_format(self, fetcher, mock_pb_client):
        """Test filtering invalid repository formats"""
        mock_pb_client.get_setting.return_value = "owner/repo1, invalid-repo, owner/repo2"

        repos = fetcher._get_monitored_repositories()

        assert len(repos) == 2
        assert "invalid-repo" not in repos

    def test_should_track_commits(self, fetcher, mock_pb_client):
        """Test commit tracking setting"""
        mock_pb_client.get_setting.return_value = "true"

        assert fetcher._should_track_commits() is True

    def test_should_track_issues(self, fetcher, mock_pb_client):
        """Test issue tracking setting"""
        mock_pb_client.get_setting.return_value = "true"

        assert fetcher._should_track_issues() is True

    def test_should_track_prs(self, fetcher, mock_pb_client):
        """Test PR tracking setting (default disabled)"""
        mock_pb_client.get_setting.side_effect = Exception("Setting not found")

        assert fetcher._should_track_prs() is False

    def test_estimate_commit_duration_small(self, fetcher):
        """Test duration estimation for small commits"""
        mock_commit = Mock()
        mock_commit.stats.additions = 20
        mock_commit.stats.deletions = 10

        duration = fetcher._estimate_commit_duration(mock_commit)

        assert duration == 30

    def test_estimate_commit_duration_medium(self, fetcher):
        """Test duration estimation for medium commits"""
        mock_commit = Mock()
        mock_commit.stats.additions = 80
        mock_commit.stats.deletions = 40

        duration = fetcher._estimate_commit_duration(mock_commit)

        assert duration == 60

    def test_estimate_commit_duration_large(self, fetcher):
        """Test duration estimation for large commits"""
        mock_commit = Mock()
        mock_commit.stats.additions = 300
        mock_commit.stats.deletions = 100

        duration = fetcher._estimate_commit_duration(mock_commit)

        assert duration == 120

    def test_estimate_commit_duration_very_large(self, fetcher):
        """Test duration estimation for very large commits"""
        mock_commit = Mock()
        mock_commit.stats.additions = 800
        mock_commit.stats.deletions = 200

        duration = fetcher._estimate_commit_duration(mock_commit)

        assert duration == 180

    def test_extract_issue_numbers(self, fetcher):
        """Test extracting issue numbers from text"""
        text = "Fix bug in login (issue #123) and resolve #456"

        issue_numbers = fetcher._extract_issue_numbers(text)

        assert len(issue_numbers) == 2
        assert 123 in issue_numbers
        assert 456 in issue_numbers

    def test_extract_issue_numbers_no_issues(self, fetcher):
        """Test extracting issue numbers when none present"""
        text = "Just a regular commit message"

        issue_numbers = fetcher._extract_issue_numbers(text)

        assert len(issue_numbers) == 0

    def test_process_commit(self, fetcher):
        """Test processing a commit"""
        mock_commit = Mock()
        mock_commit.sha = "abc123def456"
        mock_commit.commit.author.date = datetime(2024, 1, 8, 10, 0)
        mock_commit.commit.message = "Fix authentication bug (issue #123)"
        mock_commit.stats.additions = 30
        mock_commit.stats.deletions = 10
        mock_commit.files = [Mock(), Mock()]
        mock_commit.html_url = "https://github.com/owner/repo/commit/abc123"

        event = fetcher._process_commit(mock_commit, "owner/repo")

        assert event is not None
        assert "Commit: Fix authentication bug" in event["description"]
        assert "(issue #123)" in event["description"]
        assert event["duration_minutes"] == 30
        assert event["metadata"]["repo"] == "owner/repo"
        assert event["metadata"]["short_sha"] == "abc123d"
        assert 123 in event["metadata"]["issue_numbers"]

    def test_process_issue(self, fetcher):
        """Test processing an issue"""
        mock_issue = Mock()
        mock_issue.number = 350
        mock_issue.title = "Implement supplier identifier"
        mock_issue.state = "open"
        mock_issue.updated_at = datetime(2024, 1, 8, 10, 0)
        mock_issue.created_at = datetime(2024, 1, 7, 10, 0)
        mock_issue.labels = [Mock(name="bug"), Mock(name="priority-high")]
        mock_issue.pull_request = None
        mock_issue.html_url = "https://github.com/owner/repo/issues/350"

        event = fetcher._process_issue(mock_issue, "owner/repo")

        assert event is not None
        assert "Working on Issue #350" in event["description"]
        assert "Implement supplier identifier" in event["description"]
        assert event["duration_minutes"] == 60
        assert event["metadata"]["repo"] == "owner/repo"
        assert event["metadata"]["issue_number"] == 350
        assert event["metadata"]["state"] == "open"

    def test_process_issue_skip_pull_request(self, fetcher):
        """Test that pull requests are skipped"""
        mock_issue = Mock()
        mock_issue.pull_request = Mock()  # Has pull_request attribute

        event = fetcher._process_issue(mock_issue, "owner/repo")

        assert event is None

    def test_fetch_disabled(self, fetcher):
        """Test fetch when disabled"""
        fetcher.is_enabled = Mock(return_value=False)

        result = fetcher.fetch()

        assert result.success is False
        assert "disabled" in result.error.lower()

    def test_fetch_invalid_config(self, fetcher):
        """Test fetch with invalid configuration"""
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(False, "Invalid token"))

        result = fetcher.fetch()

        assert result.success is False
        assert result.error == "Invalid token"

    def test_fetch_no_repositories(self, fetcher, mock_pb_client):
        """Test fetch with no repositories configured"""
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))
        mock_pb_client.get_setting.return_value = ""

        result = fetcher.fetch()

        assert result.success is False
        assert "No GitHub repositories" in result.error

    def test_fetch_success(self, fetcher, mock_pb_client):
        """Test successful fetch"""
        # Setup
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))
        fetcher.username = "testuser"

        def mock_get_setting(key):
            settings = {
                "github_repositories": "owner/repo1",
                "github_track_commits": "true",
                "github_track_issues": "true",
            }
            return settings.get(key, "")

        mock_pb_client.get_setting = Mock(side_effect=mock_get_setting)

        # Mock repository
        mock_repo = Mock()
        fetcher.api.get_repository.return_value = mock_repo

        # Mock commits
        mock_commit = Mock()
        mock_commit.sha = "abc123"
        mock_commit.commit.author.date = datetime(2024, 1, 8, 10, 0)
        mock_commit.commit.message = "Test commit"
        mock_commit.stats.additions = 20
        mock_commit.stats.deletions = 10
        mock_commit.files = []
        mock_commit.html_url = "https://github.com/test"

        fetcher.api.get_commits.return_value = [mock_commit]

        # Mock issues
        mock_issue = Mock()
        mock_issue.number = 123
        mock_issue.title = "Test issue"
        mock_issue.state = "open"
        mock_issue.updated_at = datetime(2024, 1, 8, 11, 0)
        mock_issue.created_at = datetime(2024, 1, 7, 10, 0)
        mock_issue.labels = []
        mock_issue.pull_request = None
        mock_issue.html_url = "https://github.com/test/issues/123"

        fetcher.api.get_user_issues.return_value = [mock_issue]

        fetcher.event_exists = Mock(return_value=False)
        fetcher.create_raw_event = Mock()
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8, 23, 59, 59),
        ))

        # Execute
        result = fetcher.fetch()

        # Verify
        assert result.success is True
        assert result.events_fetched == 2  # 1 commit + 1 issue
        assert result.events_created == 2
        assert fetcher.create_raw_event.call_count == 2

    def test_fetch_only_commits(self, fetcher, mock_pb_client):
        """Test fetching only commits"""
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))
        fetcher.username = "testuser"

        def mock_get_setting(key):
            settings = {
                "github_repositories": "owner/repo1",
                "github_track_commits": "true",
                "github_track_issues": "false",
            }
            return settings.get(key, "")

        mock_pb_client.get_setting = Mock(side_effect=mock_get_setting)

        mock_repo = Mock()
        fetcher.api.get_repository.return_value = mock_repo

        # Return an actual list, not a Mock
        fetcher.api.get_commits.return_value = []
        # Also mock get_user_issues even though it shouldn't be called
        fetcher.api.get_user_issues.return_value = []

        fetcher.event_exists = Mock(return_value=False)
        fetcher.create_raw_event = Mock()
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8, 23, 59, 59),
        ))

        result = fetcher.fetch()

        assert result.success is True
        # These are stored as booleans in the metadata
        assert result.metadata["track_commits"] == True
        assert result.metadata["track_issues"] == False

    def test_fetch_rate_limit_exceeded(self, fetcher, mock_pb_client):
        """Test handling rate limit exceeded"""
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))
        fetcher.username = "testuser"

        def mock_get_setting(key):
            settings = {
                "github_repositories": "owner/repo1",
                "github_track_commits": "true",
                "github_track_issues": "false",
            }
            return settings.get(key, "")

        mock_pb_client.get_setting = Mock(side_effect=mock_get_setting)

        mock_repo = Mock()
        fetcher.api.get_repository.return_value = mock_repo

        # Mock rate limit exception when getting commits
        rate_limit_error = RateLimitExceededException(
            status=403,
            data={'reset': 1609459200},
            headers={}
        )
        fetcher.api.get_commits.side_effect = rate_limit_error
        fetcher.api.get_rate_limit.return_value = {
            'core': {'reset': datetime(2024, 1, 8, 12, 0, 0)}
        }
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8, 23, 59, 59),
        ))

        result = fetcher.fetch()

        assert result.success is False
        assert "rate limit" in result.error.lower()

    def test_fetch_skips_existing_events(self, fetcher, mock_pb_client):
        """Test that existing events are skipped"""
        fetcher.is_enabled = Mock(return_value=True)
        fetcher.validate_configuration = Mock(return_value=(True, None))
        fetcher.username = "testuser"

        def mock_get_setting(key):
            settings = {
                "github_repositories": "owner/repo1",
                "github_track_commits": "true",
                "github_track_issues": "false",
            }
            return settings.get(key, "")

        mock_pb_client.get_setting = Mock(side_effect=mock_get_setting)

        mock_repo = Mock()
        fetcher.api.get_repository.return_value = mock_repo

        mock_commit = Mock()
        mock_commit.sha = "abc123def456"
        mock_commit.commit.author.date = datetime(2024, 1, 8, 10, 0)
        mock_commit.commit.message = "Test commit"
        mock_commit.stats.additions = 20
        mock_commit.stats.deletions = 10
        mock_commit.files = []
        mock_commit.html_url = "https://github.com/test"

        # Return a list with one commit
        fetcher.api.get_commits.return_value = [mock_commit]
        # Also mock get_user_issues
        fetcher.api.get_user_issues.return_value = []

        fetcher.event_exists = Mock(return_value=True)  # Event already exists
        fetcher.create_raw_event = Mock()
        fetcher.get_default_date_range = Mock(return_value=(
            datetime(2024, 1, 1),
            datetime(2024, 1, 8, 23, 59, 59),
        ))

        result = fetcher.fetch()

        assert result.success is True
        assert result.events_fetched == 1
        assert result.events_created == 0
        fetcher.create_raw_event.assert_not_called()
