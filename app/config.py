"""
Configuration Management

Provides configuration loading and settings management for the application.
Settings are stored in PocketBase and cached in memory for performance.
"""

import os
from typing import Any, Dict, Optional
from pocketbase import PocketBase
from pocketbase.client import ClientResponseError
from app.models.settings import Settings


class SettingsManager:
    """
    Manages application settings stored in PocketBase.

    Provides a high-level interface for reading and updating settings with:
    - Automatic caching for performance
    - Type conversion (string → number/boolean)
    - Integration with Pydantic Settings model
    - Cache invalidation on updates
    """

    def __init__(self, pb_client: PocketBase):
        """
        Initialize SettingsManager.

        Args:
            pb_client: Authenticated PocketBase client instance
        """
        self.pb = pb_client
        self._cache: Optional[Settings] = None

    def get_all(self, force_reload: bool = False) -> Settings:
        """
        Fetch all settings from PocketBase and return as Settings object.

        Args:
            force_reload: If True, bypass cache and reload from database

        Returns:
            Settings object with all configuration values

        Raises:
            ClientResponseError: If PocketBase request fails
            ValueError: If settings cannot be parsed/validated
        """
        # Return cached settings if available
        if self._cache and not force_reload:
            return self._cache

        # Fetch all settings from PocketBase
        try:
            # Check if pb is a wrapper with get_full_list method or raw client
            if hasattr(self.pb, 'get_full_list'):
                # It's a PocketBaseClient wrapper
                records = self.pb.get_full_list("settings")
            else:
                # It's a raw PocketBase SDK client
                records = self.pb.collection("settings").get_full_list()
        except ClientResponseError as e:
            if e.status == 404:
                raise ValueError(
                    "Settings collection not found. Please run migrations and seed data first."
                )
            raise

        # Convert records to flat dictionary
        settings_dict = {}
        for record in records:
            # Access record fields using getattr for compatibility
            key = getattr(record, 'key', None)
            value = getattr(record, 'value', None)
            record_type = getattr(record, 'type', 'string')

            if key is None or value is None:
                continue  # Skip invalid records

            parsed_value = self._parse_value(value, record_type)
            settings_dict[key] = parsed_value

        # Validate we have all required settings (31 total: 10+1+2+3+5+1+7+2)
        expected_count = 31
        if len(settings_dict) != expected_count:
            raise ValueError(
                f"Expected {expected_count} settings, but found {len(settings_dict)}. "
                f"Please run seed_settings.py to populate default values."
            )

        # Convert to nested Settings model
        self._cache = Settings.from_flat_dict(settings_dict)
        return self._cache

    def get(self, key: str) -> Any:
        """
        Get a single setting value by key.

        Args:
            key: Setting key (e.g., "work_week_start_day")

        Returns:
            Setting value (str, int, or bool)

        Raises:
            ClientResponseError: If setting not found or request fails
        """
        try:
            if hasattr(self.pb, 'get_first_list_item'):
                # It's a PocketBaseClient wrapper
                record = self.pb.get_first_list_item("settings", f'key="{key}"')
            else:
                # It's a raw PocketBase SDK client
                record = self.pb.collection("settings").get_first_list_item(f'key="{key}"')

            value = getattr(record, 'value', None)
            record_type = getattr(record, 'type', 'string')
            return self._parse_value(value, record_type)
        except ClientResponseError as e:
            if e.status == 404:
                raise KeyError(f"Setting '{key}' not found")
            raise

    def update(self, key: str, value: Any) -> None:
        """
        Update a single setting value.

        Args:
            key: Setting key to update
            value: New value (will be converted to string for storage)

        Raises:
            ClientResponseError: If setting not found or update fails
        """
        try:
            # Get existing record
            if hasattr(self.pb, 'get_first_list_item'):
                # It's a PocketBaseClient wrapper
                record = self.pb.get_first_list_item("settings", f'key="{key}"')
            else:
                # It's a raw PocketBase SDK client
                record = self.pb.collection("settings").get_first_list_item(f'key="{key}"')

            # Convert value to string for storage
            str_value = self._value_to_string(value)

            # Update in PocketBase
            if hasattr(self.pb, 'update'):
                # It's a PocketBaseClient wrapper
                self.pb.update("settings", record.id, {"value": str_value})
            else:
                # It's a raw PocketBase SDK client
                self.pb.collection("settings").update(record.id, {"value": str_value})

            # Invalidate cache
            self._cache = None

        except ClientResponseError as e:
            if e.status == 404:
                raise KeyError(f"Setting '{key}' not found")
            raise

    def update_many(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple settings at once.

        Args:
            updates: Dictionary of key-value pairs to update

        Raises:
            ClientResponseError: If any update fails
        """
        for key, value in updates.items():
            self.update(key, value)

    def reload(self) -> Settings:
        """
        Force reload settings from database, bypassing cache.

        Returns:
            Fresh Settings object from database
        """
        return self.get_all(force_reload=True)

    def clear_cache(self) -> None:
        """Clear the settings cache"""
        self._cache = None

    @staticmethod
    def _parse_value(value: str, type_str: str) -> Any:
        """
        Parse setting value from string based on type.

        Args:
            value: String value from database
            type_str: Type indicator ("string", "number", "boolean")

        Returns:
            Parsed value in appropriate Python type
        """
        if type_str == "number":
            # Try int first, fall back to float
            try:
                return int(value)
            except ValueError:
                return float(value)
        elif type_str == "boolean":
            return value.lower() in ("true", "1", "yes", "on")
        else:  # string
            return value

    @staticmethod
    def _value_to_string(value: Any) -> str:
        """
        Convert Python value to string for storage.

        Args:
            value: Value to convert (str, int, float, bool)

        Returns:
            String representation
        """
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)


class Config:
    """
    Application configuration loader.

    Loads configuration from environment variables and provides
    access to PocketBase settings via SettingsManager.
    """

    def __init__(self):
        """Initialize configuration from environment variables"""

        # PocketBase configuration
        self.pocketbase_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")
        self.pb_admin_email = os.getenv("PB_ADMIN_EMAIL")
        self.pb_admin_password = os.getenv("PB_ADMIN_PASSWORD")

        # API Keys
        self.wakatime_api_key = os.getenv("WAKATIME_API_KEY")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_username = os.getenv("GITHUB_USERNAME")

        # Google OAuth
        self.google_client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.google_redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")

        # Security
        self.encryption_key = os.getenv("ENCRYPTION_KEY")

        # FastAPI configuration
        self.fastapi_host = os.getenv("FASTAPI_HOST", "0.0.0.0")
        self.fastapi_port = int(os.getenv("FASTAPI_PORT", "8000"))
        self.fastapi_debug = os.getenv("FASTAPI_DEBUG", "false").lower() == "true"

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "logs/app.log")

        # Initialize PocketBase client (will be set up by application)
        self._pb_client: Optional[PocketBase] = None
        self._settings_manager: Optional[SettingsManager] = None

    def setup_pocketbase(self, pb_client) -> None:
        """
        Set up PocketBase client and settings manager.

        Args:
            pb_client: Authenticated PocketBase client (can be PocketBaseClient wrapper or raw client)
        """
        self._pb_client = pb_client
        # SettingsManager now handles both wrappers and raw clients
        self._settings_manager = SettingsManager(pb_client)

    @property
    def settings(self):
        """
        Get settings from PocketBase.

        Returns:
            Settings instance with all configuration

        Raises:
            RuntimeError: If PocketBase not set up yet
        """
        if not self._settings_manager:
            raise RuntimeError(
                "Settings manager not initialized. Call setup_pocketbase() first."
            )
        return self._settings_manager.get_all()

    def validate(self) -> list[str]:
        """
        Validate that required configuration is present.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check PocketBase admin credentials
        if not self.pb_admin_email:
            errors.append("PB_ADMIN_EMAIL not set")
        if not self.pb_admin_password:
            errors.append("PB_ADMIN_PASSWORD not set")

        # Check encryption key
        if not self.encryption_key:
            errors.append("ENCRYPTION_KEY not set (required for OAuth token storage)")

        # Warn about missing API keys (not critical for startup)
        if not self.wakatime_api_key:
            errors.append("Warning: WAKATIME_API_KEY not set (WakaTime fetcher disabled)")

        if not self.github_token:
            errors.append("Warning: GITHUB_TOKEN not set (GitHub fetcher disabled)")

        if not self.google_client_id or not self.google_client_secret:
            errors.append(
                "Warning: Google OAuth not configured (Calendar/Gmail fetchers disabled)"
            )

        return errors


# Global configuration instance
config = Config()
