"""
OAuth Helper Utilities

Provides utilities for securely storing and managing OAuth tokens using encryption.
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from cryptography.fernet import Fernet


class TokenManager:
    """
    Manages OAuth tokens with encryption.

    Tokens are encrypted using Fernet (symmetric encryption) before storage.
    The encryption key should be stored in ENCRYPTION_KEY environment variable.
    """

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize TokenManager.

        Args:
            encryption_key: Base64-encoded Fernet key (defaults to ENCRYPTION_KEY env var)

        Raises:
            ValueError: If encryption key is not provided
        """
        key = encryption_key or os.getenv("ENCRYPTION_KEY")
        if not key:
            raise ValueError("ENCRYPTION_KEY must be set in environment or provided")

        self.cipher = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt_token(self, token: str) -> str:
        """
        Encrypt a token.

        Args:
            token: Plain text token

        Returns:
            Encrypted token (base64 encoded)
        """
        encrypted = self.cipher.encrypt(token.encode())
        return encrypted.decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt a token.

        Args:
            encrypted_token: Encrypted token

        Returns:
            Decrypted plain text token

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
        """
        decrypted = self.cipher.decrypt(encrypted_token.encode())
        return decrypted.decode()

    def encrypt_token_dict(self, token_dict: Dict[str, Any]) -> str:
        """
        Encrypt a dictionary of token data.

        Args:
            token_dict: Dictionary containing token and metadata

        Returns:
            Encrypted JSON string
        """
        json_str = json.dumps(token_dict)
        return self.encrypt_token(json_str)

    def decrypt_token_dict(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt a token dictionary.

        Args:
            encrypted_data: Encrypted JSON string

        Returns:
            Decrypted dictionary

        Raises:
            cryptography.fernet.InvalidToken: If decryption fails
            json.JSONDecodeError: If JSON parsing fails
        """
        json_str = self.decrypt_token(encrypted_data)
        return json.loads(json_str)

    @staticmethod
    def generate_encryption_key() -> str:
        """
        Generate a new Fernet encryption key.

        Returns:
            Base64-encoded encryption key

        Example:
            >>> key = TokenManager.generate_encryption_key()
            >>> print(f"ENCRYPTION_KEY={key}")
        """
        return Fernet.generate_key().decode()


class OAuthToken:
    """
    Represents an OAuth token with metadata.

    Stores access token, refresh token, expiry time, and scope information.
    """

    def __init__(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        scope: Optional[str] = None,
        token_type: str = "Bearer",
    ):
        """
        Initialize OAuthToken.

        Args:
            access_token: OAuth access token
            refresh_token: OAuth refresh token (optional)
            expires_at: Token expiry datetime (optional)
            scope: OAuth scopes (space-separated string)
            token_type: Token type (usually "Bearer")
        """
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        self.scope = scope
        self.token_type = token_type

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """
        Check if token is expired or about to expire.

        Args:
            buffer_seconds: Consider token expired this many seconds before actual expiry

        Returns:
            True if token is expired or will expire within buffer period
        """
        if not self.expires_at:
            # No expiry time set, assume valid
            return False

        buffer = timedelta(seconds=buffer_seconds)
        return datetime.utcnow() + buffer >= self.expires_at

    def needs_refresh(self) -> bool:
        """Check if token needs refresh"""
        return self.is_expired() and self.refresh_token is not None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "scope": self.scope,
            "token_type": self.token_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OAuthToken":
        """Create from dictionary"""
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])

        return cls(
            access_token=data["access_token"],
            refresh_token=data.get("refresh_token"),
            expires_at=expires_at,
            scope=data.get("scope"),
            token_type=data.get("token_type", "Bearer"),
        )

    @classmethod
    def from_oauth_response(
        cls, response: Dict[str, Any], expires_in_seconds: Optional[int] = None
    ) -> "OAuthToken":
        """
        Create from OAuth provider response.

        Args:
            response: OAuth response dictionary
            expires_in_seconds: Override expires_in from response

        Returns:
            OAuthToken instance
        """
        # Calculate expiry time
        expires_at = None
        expires_in = expires_in_seconds or response.get("expires_in")
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        return cls(
            access_token=response["access_token"],
            refresh_token=response.get("refresh_token"),
            expires_at=expires_at,
            scope=response.get("scope"),
            token_type=response.get("token_type", "Bearer"),
        )

    def __repr__(self) -> str:
        masked_access = f"{self.access_token[:8]}..." if self.access_token else "None"
        return (
            f"OAuthToken(access_token={masked_access}, "
            f"expires_at={self.expires_at}, "
            f"has_refresh={self.refresh_token is not None})"
        )


class SecureTokenStorage:
    """
    Secure storage for OAuth tokens using encryption.

    Combines TokenManager (encryption) with dict-like interface for token storage.
    """

    def __init__(self, token_manager: TokenManager):
        """
        Initialize SecureTokenStorage.

        Args:
            token_manager: TokenManager instance for encryption
        """
        self.token_manager = token_manager
        self._tokens: Dict[str, OAuthToken] = {}

    def store_token(self, key: str, token: OAuthToken, encrypt: bool = True) -> str:
        """
        Store an OAuth token.

        Args:
            key: Unique identifier for this token (e.g., "gmail_user@example.com")
            token: OAuthToken to store
            encrypt: Whether to encrypt the token

        Returns:
            Encrypted token data (if encrypt=True) or JSON string (if encrypt=False)
        """
        token_dict = token.to_dict()

        if encrypt:
            encrypted = self.token_manager.encrypt_token_dict(token_dict)
            self._tokens[key] = token
            return encrypted
        else:
            self._tokens[key] = token
            return json.dumps(token_dict)

    def retrieve_token(self, key: str, encrypted_data: Optional[str] = None) -> Optional[OAuthToken]:
        """
        Retrieve an OAuth token.

        Args:
            key: Token identifier
            encrypted_data: Encrypted token data (if not in memory)

        Returns:
            OAuthToken if found, None otherwise
        """
        # Check in-memory cache first
        if key in self._tokens:
            return self._tokens[key]

        # Decrypt if provided
        if encrypted_data:
            try:
                token_dict = self.token_manager.decrypt_token_dict(encrypted_data)
                token = OAuthToken.from_dict(token_dict)
                self._tokens[key] = token
                return token
            except Exception:
                return None

        return None

    def delete_token(self, key: str) -> bool:
        """
        Delete a token from storage.

        Args:
            key: Token identifier

        Returns:
            True if token was deleted, False if not found
        """
        if key in self._tokens:
            del self._tokens[key]
            return True
        return False

    def list_tokens(self) -> list[str]:
        """
        List all stored token keys.

        Returns:
            List of token identifiers
        """
        return list(self._tokens.keys())

    def clear_all(self) -> None:
        """Clear all tokens from memory"""
        self._tokens.clear()


def create_token_manager() -> TokenManager:
    """
    Factory function to create TokenManager with default settings.

    Returns:
        TokenManager instance

    Raises:
        ValueError: If ENCRYPTION_KEY is not set
    """
    return TokenManager()


def create_secure_storage() -> SecureTokenStorage:
    """
    Factory function to create SecureTokenStorage with default settings.

    Returns:
        SecureTokenStorage instance
    """
    token_manager = create_token_manager()
    return SecureTokenStorage(token_manager)


# Utility functions for Google OAuth

def build_google_auth_url(
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: Optional[str] = None,
) -> str:
    """
    Build Google OAuth authorization URL.

    Args:
        client_id: Google OAuth client ID
        redirect_uri: Redirect URI
        scopes: List of OAuth scopes
        state: Optional state parameter for CSRF protection

    Returns:
        Authorization URL
    """
    from urllib.parse import urlencode

    base_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",  # Request refresh token
        "prompt": "consent",  # Force consent screen to get refresh token
    }

    if state:
        params["state"] = state

    return f"{base_url}?{urlencode(params)}"


# Common OAuth scopes

GOOGLE_CALENDAR_SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
]

GOOGLE_GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
]

GOOGLE_COMBINED_SCOPES = GOOGLE_CALENDAR_SCOPES + GOOGLE_GMAIL_SCOPES
