"""
Unit Tests for OAuth Utilities

Tests for token management and encryption.
"""

import pytest
import json
from datetime import datetime, timedelta
from cryptography.fernet import Fernet, InvalidToken
from app.utils.oauth import (
    TokenManager,
    OAuthToken,
    SecureTokenStorage,
    create_token_manager,
    build_google_auth_url,
    GOOGLE_CALENDAR_SCOPES,
    GOOGLE_GMAIL_SCOPES,
)


class TestTokenManager:
    """Test TokenManager encryption/decryption"""

    @pytest.fixture
    def token_manager(self):
        """Create TokenManager with test key"""
        key = Fernet.generate_key().decode()
        return TokenManager(encryption_key=key)

    def test_encrypt_decrypt_token(self, token_manager):
        """Test basic token encryption and decryption"""
        token = "test_access_token_12345"

        encrypted = token_manager.encrypt_token(token)
        assert encrypted != token  # Should be encrypted

        decrypted = token_manager.decrypt_token(encrypted)
        assert decrypted == token  # Should match original

    def test_encrypt_decrypt_token_dict(self, token_manager):
        """Test encrypting and decrypting a token dictionary"""
        token_dict = {
            "access_token": "test_access_12345",
            "refresh_token": "test_refresh_12345",
            "expires_at": "2026-01-15T10:00:00",
            "scope": "calendar gmail",
        }

        encrypted = token_manager.encrypt_token_dict(token_dict)
        assert encrypted != json.dumps(token_dict)  # Should be encrypted

        decrypted = token_manager.decrypt_token_dict(encrypted)
        assert decrypted == token_dict  # Should match original

    def test_decrypt_invalid_token(self, token_manager):
        """Test decrypting invalid token raises error"""
        with pytest.raises(InvalidToken):
            token_manager.decrypt_token("invalid_encrypted_data")

    def test_decrypt_with_wrong_key(self):
        """Test decrypting with wrong key raises error"""
        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        tm1 = TokenManager(encryption_key=key1)
        tm2 = TokenManager(encryption_key=key2)

        token = "test_token"
        encrypted = tm1.encrypt_token(token)

        with pytest.raises(InvalidToken):
            tm2.decrypt_token(encrypted)

    def test_generate_encryption_key(self):
        """Test generating a new encryption key"""
        key = TokenManager.generate_encryption_key()

        # Should be base64 encoded Fernet key
        assert isinstance(key, str)
        assert len(key) > 0

        # Should be usable to create TokenManager
        tm = TokenManager(encryption_key=key)
        assert tm is not None

    def test_initialization_without_key(self, monkeypatch):
        """Test that initialization fails without encryption key"""
        monkeypatch.delenv("ENCRYPTION_KEY", raising=False)

        with pytest.raises(ValueError):
            TokenManager()


class TestOAuthToken:
    """Test OAuthToken class"""

    def test_oauth_token_creation(self):
        """Test creating an OAuthToken"""
        expires_at = datetime.utcnow() + timedelta(hours=1)

        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
            scope="calendar gmail",
        )

        assert token.access_token == "test_access"
        assert token.refresh_token == "test_refresh"
        assert token.expires_at == expires_at
        assert token.scope == "calendar gmail"
        assert token.token_type == "Bearer"

    def test_is_expired_not_expired(self):
        """Test token is not expired"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = OAuthToken("test_access", expires_at=expires_at)

        assert not token.is_expired()

    def test_is_expired_expired(self):
        """Test token is expired"""
        expires_at = datetime.utcnow() - timedelta(hours=1)
        token = OAuthToken("test_access", expires_at=expires_at)

        assert token.is_expired()

    def test_is_expired_with_buffer(self):
        """Test token expiry with buffer"""
        # Expires in 4 minutes
        expires_at = datetime.utcnow() + timedelta(minutes=4)
        token = OAuthToken("test_access", expires_at=expires_at)

        # With 5-minute buffer, should be considered expired
        assert token.is_expired(buffer_seconds=300)

        # With 3-minute buffer, should not be expired
        assert not token.is_expired(buffer_seconds=180)

    def test_is_expired_no_expiry(self):
        """Test token without expiry time"""
        token = OAuthToken("test_access")

        # Should never be expired if no expiry set
        assert not token.is_expired()

    def test_needs_refresh(self):
        """Test needs_refresh method"""
        # Expired with refresh token
        expires_at = datetime.utcnow() - timedelta(hours=1)
        token = OAuthToken("test_access", refresh_token="test_refresh", expires_at=expires_at)
        assert token.needs_refresh()

        # Expired without refresh token
        token = OAuthToken("test_access", expires_at=expires_at)
        assert not token.needs_refresh()

        # Not expired with refresh token
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = OAuthToken("test_access", refresh_token="test_refresh", expires_at=expires_at)
        assert not token.needs_refresh()

    def test_to_dict(self):
        """Test converting token to dictionary"""
        expires_at = datetime(2026, 1, 15, 10, 0, 0)
        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
            scope="calendar",
        )

        token_dict = token.to_dict()

        assert token_dict["access_token"] == "test_access"
        assert token_dict["refresh_token"] == "test_refresh"
        assert token_dict["expires_at"] == "2026-01-15T10:00:00"
        assert token_dict["scope"] == "calendar"

    def test_from_dict(self):
        """Test creating token from dictionary"""
        token_dict = {
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "expires_at": "2026-01-15T10:00:00",
            "scope": "calendar",
            "token_type": "Bearer",
        }

        token = OAuthToken.from_dict(token_dict)

        assert token.access_token == "test_access"
        assert token.refresh_token == "test_refresh"
        assert token.expires_at == datetime(2026, 1, 15, 10, 0, 0)
        assert token.scope == "calendar"

    def test_from_oauth_response(self):
        """Test creating token from OAuth provider response"""
        response = {
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "expires_in": 3600,  # 1 hour
            "scope": "calendar gmail",
            "token_type": "Bearer",
        }

        token = OAuthToken.from_oauth_response(response)

        assert token.access_token == "test_access"
        assert token.refresh_token == "test_refresh"
        assert token.scope == "calendar gmail"
        assert token.expires_at is not None
        # Should expire in approximately 1 hour
        time_until_expiry = token.expires_at - datetime.utcnow()
        assert 3590 <= time_until_expiry.total_seconds() <= 3610


class TestSecureTokenStorage:
    """Test SecureTokenStorage"""

    @pytest.fixture
    def token_storage(self):
        """Create SecureTokenStorage with test key"""
        key = Fernet.generate_key().decode()
        tm = TokenManager(encryption_key=key)
        return SecureTokenStorage(tm)

    def test_store_and_retrieve_token(self, token_storage):
        """Test storing and retrieving a token"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        # Store token
        encrypted = token_storage.store_token("user@example.com", token, encrypt=True)
        assert encrypted is not None

        # Retrieve token
        retrieved = token_storage.retrieve_token("user@example.com")
        assert retrieved is not None
        assert retrieved.access_token == "test_access"

    def test_retrieve_from_encrypted_data(self, token_storage):
        """Test retrieving token from encrypted data"""
        expires_at = datetime.utcnow() + timedelta(hours=1)
        token = OAuthToken(
            access_token="test_access",
            refresh_token="test_refresh",
            expires_at=expires_at,
        )

        # Store token and get encrypted data
        encrypted = token_storage.store_token("user@example.com", token, encrypt=True)

        # Clear in-memory cache
        token_storage.clear_all()

        # Retrieve from encrypted data
        retrieved = token_storage.retrieve_token("user@example.com", encrypted_data=encrypted)
        assert retrieved is not None
        assert retrieved.access_token == "test_access"

    def test_retrieve_nonexistent_token(self, token_storage):
        """Test retrieving non-existent token"""
        retrieved = token_storage.retrieve_token("nonexistent@example.com")
        assert retrieved is None

    def test_delete_token(self, token_storage):
        """Test deleting a token"""
        token = OAuthToken("test_access")

        # Store token
        token_storage.store_token("user@example.com", token)

        # Delete token
        deleted = token_storage.delete_token("user@example.com")
        assert deleted is True

        # Should not be retrievable
        retrieved = token_storage.retrieve_token("user@example.com")
        assert retrieved is None

    def test_delete_nonexistent_token(self, token_storage):
        """Test deleting non-existent token"""
        deleted = token_storage.delete_token("nonexistent@example.com")
        assert deleted is False

    def test_list_tokens(self, token_storage):
        """Test listing stored tokens"""
        token1 = OAuthToken("access1")
        token2 = OAuthToken("access2")

        token_storage.store_token("user1@example.com", token1)
        token_storage.store_token("user2@example.com", token2)

        tokens = token_storage.list_tokens()
        assert len(tokens) == 2
        assert "user1@example.com" in tokens
        assert "user2@example.com" in tokens

    def test_clear_all(self, token_storage):
        """Test clearing all tokens"""
        token = OAuthToken("test_access")

        token_storage.store_token("user@example.com", token)
        assert len(token_storage.list_tokens()) == 1

        token_storage.clear_all()
        assert len(token_storage.list_tokens()) == 0


class TestGoogleOAuthHelpers:
    """Test Google OAuth helper functions"""

    def test_build_google_auth_url(self):
        """Test building Google OAuth authorization URL"""
        url = build_google_auth_url(
            client_id="test_client_id",
            redirect_uri="http://localhost:8000/callback",
            scopes=["https://www.googleapis.com/auth/calendar.readonly"],
            state="test_state",
        )

        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test_client_id" in url
        assert "redirect_uri=http" in url
        assert "response_type=code" in url
        assert "scope=https" in url
        assert "access_type=offline" in url
        assert "state=test_state" in url

    def test_google_scopes_defined(self):
        """Test that Google scope constants are defined"""
        assert len(GOOGLE_CALENDAR_SCOPES) > 0
        assert len(GOOGLE_GMAIL_SCOPES) > 0
        assert "calendar" in GOOGLE_CALENDAR_SCOPES[0]
        assert "gmail" in GOOGLE_GMAIL_SCOPES[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
