"""Supabase access-token verification for protected API routes."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWTError

from app.config.settings import Settings, get_settings


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Trusted identity extracted from a verified Supabase access token."""

    user_id: str
    email: str | None = None


class SupabaseJWTVerifier:
    """Verify Supabase JWTs using the project's cached public signing keys."""

    def __init__(self, supabase_url: str) -> None:
        self._issuer = f"{supabase_url.rstrip('/')}/auth/v1"
        self._jwks = PyJWKClient(
            f"{self._issuer}/.well-known/jwks.json",
            cache_jwk_set=True,
            lifespan=600,
        )

    def _verify_sync(self, token: str) -> AuthenticatedUser:
        signing_key = self._jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
            issuer=self._issuer,
            options={"require": ["exp", "iat", "sub", "aud", "iss"]},
        )
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise jwt.InvalidTokenError("Token subject is missing.")
        email = claims.get("email")
        return AuthenticatedUser(
            user_id=subject,
            email=email if isinstance(email, str) else None,
        )

    async def verify(self, token: str) -> AuthenticatedUser:
        """Run the JWKS lookup outside the event loop."""
        return await asyncio.to_thread(self._verify_sync, token)


@lru_cache
def get_jwt_verifier(supabase_url: str) -> SupabaseJWTVerifier:
    return SupabaseJWTVerifier(supabase_url)


_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    settings: Settings = Depends(get_settings),
) -> AuthenticatedUser:
    """Require and verify a Supabase user access token."""
    if not settings.auth_required:
        return AuthenticatedUser(user_id="local-development-user")

    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured.",
        )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return await get_jwt_verifier(settings.supabase_url).verify(credentials.credentials)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your session is invalid or has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication could not be verified. Please try again.",
        ) from None
