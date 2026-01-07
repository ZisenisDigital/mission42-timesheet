"""
PocketBase Authentication Utilities

Simple authentication system using PocketBase user accounts.
"""

from typing import Optional
from fastapi import HTTPException, Cookie, Response
from pocketbase import PocketBase
from pocketbase.client import ClientResponseError
import os


class PocketBaseAuth:
    """Handle PocketBase authentication for FastAPI."""

    def __init__(self):
        self.pb_url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090")

    def authenticate(self, email: str, password: str) -> tuple[str, dict]:
        """
        Authenticate user with PocketBase.

        Args:
            email: User email
            password: User password

        Returns:
            Tuple of (token, user_data)

        Raises:
            HTTPException: If authentication fails
        """
        try:
            pb = PocketBase(self.pb_url)
            auth_data = pb.collection('users').auth_with_password(email, password)

            return auth_data.token, {
                'id': auth_data.record.id,
                'email': auth_data.record.email,
                'name': getattr(auth_data.record, 'name', email),
            }

        except ClientResponseError as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Authentication failed: {str(e)}"
            )

    def verify_token(self, token: str) -> dict:
        """
        Verify PocketBase auth token.

        Args:
            token: JWT token from PocketBase

        Returns:
            User data dict

        Raises:
            HTTPException: If token is invalid
        """
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Not authenticated"
            )

        try:
            pb = PocketBase(self.pb_url)
            pb.auth_store.save(token, None)

            # Verify token by fetching user data
            if pb.auth_store.is_valid:
                # Get current user
                user = pb.collection('users').auth_refresh()
                return {
                    'id': user.record.id,
                    'email': user.record.email,
                    'name': getattr(user.record, 'name', user.record.email),
                }
            else:
                raise HTTPException(status_code=401, detail="Invalid token")

        except ClientResponseError:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        except Exception as e:
            raise HTTPException(status_code=401, detail="Authentication required")


# Global auth instance
auth_service = PocketBaseAuth()


def get_current_user(auth_token: Optional[str] = Cookie(None)) -> dict:
    """
    FastAPI dependency to get current authenticated user.

    Args:
        auth_token: JWT token from cookie

    Returns:
        User data dict

    Raises:
        HTTPException: If not authenticated
    """
    return auth_service.verify_token(auth_token)


def optional_auth(auth_token: Optional[str] = Cookie(None)) -> Optional[dict]:
    """
    FastAPI dependency for optional authentication.

    Returns user data if authenticated, None otherwise.
    """
    if not auth_token:
        return None

    try:
        return auth_service.verify_token(auth_token)
    except:
        return None
