"""Minimal Twitter/X API v2 publisher.

The module uses OAuth 1.0a user-context credentials because creating a Post
requires acting as an authenticated user. It deliberately publishes only after
the host bot calls ``publish``; no automatic posting is hidden here.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from urllib import error, parse, request

DEFAULT_API_BASE_URL = "https://api.x.com"
DEFAULT_PUBLIC_POST_BASE_URL = "https://x.com/i/web/status"


class TwitterPublishError(Exception):
    """Raised when Twitter/X rejects or cannot complete a request."""


@dataclass(frozen=True)
class TwitterPublishResult:
    """Result returned after successful Post creation."""

    post_id: str
    text: str
    public_post_base_url: str = DEFAULT_PUBLIC_POST_BASE_URL

    @property
    def tweet_id(self) -> str:
        """Backward-compatible alias for projects that still say tweet_id."""
        return self.post_id

    @property
    def url(self) -> str:
        """Return a public browser URL for the created Post."""
        return f"{self.public_post_base_url.rstrip('/')}/{self.post_id}"


@dataclass(frozen=True)
class TwitterAuthResult:
    """Safe auth-smoke result. Contains no secrets."""

    user_id: str
    username: str = ""
    name: str = ""

    @property
    def handle(self) -> str:
        """Return @username when the API returned a username."""
        return f"@{self.username}" if self.username else ""


class TwitterPublisher:
    """Publish text Posts to Twitter/X via API v2."""

    CREATE_POST_PATH = "/2/tweets"
    VERIFY_CREDENTIALS_PATH = "/2/users/me?user.fields=username"

    def __init__(
        self,
        *,
        api_key: str = "",
        api_secret: str = "",
        access_token: str = "",
        access_token_secret: str = "",
        api_base_url: str = DEFAULT_API_BASE_URL,
        public_post_base_url: str = DEFAULT_PUBLIC_POST_BASE_URL,
    ) -> None:
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.access_token = access_token.strip()
        self.access_token_secret = access_token_secret.strip()
        self.api_base_url = (api_base_url or DEFAULT_API_BASE_URL).strip().rstrip("/")
        self.public_post_base_url = (
            public_post_base_url or DEFAULT_PUBLIC_POST_BASE_URL
        ).strip()

    @classmethod
    def from_env(
        cls,
        values: Mapping[str, str] | None = None,
    ) -> "TwitterPublisher":
        """Build a publisher from env-like values.

        Pass a mapping when reading a specific ``.env`` file; otherwise process
        environment variables are used.
        """
        source: Mapping[str, str] = values if values is not None else os.environ
        return cls(
            api_key=source.get("TWITTER_API_KEY", ""),
            api_secret=source.get("TWITTER_API_SECRET", ""),
            access_token=source.get("TWITTER_ACCESS_TOKEN", ""),
            access_token_secret=source.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
            api_base_url=source.get("TWITTER_API_BASE_URL", DEFAULT_API_BASE_URL),
        )

    @property
    def is_configured(self) -> bool:
        """Return True when all user-context credentials are present."""
        return all(
            [
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret,
            ]
        )

    async def publish(self, text: str) -> TwitterPublishResult:
        """Create one Twitter/X Post with ``text`` and return its id."""
        if not self.is_configured:
            raise TwitterPublishError(
                "Twitter/X API is not configured: fill TWITTER_API_KEY, "
                "TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN and "
                "TWITTER_ACCESS_TOKEN_SECRET."
            )
        clean_text = text.strip()
        if not clean_text:
            raise TwitterPublishError("Cannot publish an empty Twitter/X Post.")
        if len(clean_text) > 280:
            raise TwitterPublishError(
                f"Twitter/X Post is longer than 280 characters: {len(clean_text)}."
            )
        return await asyncio.to_thread(self._publish_sync, clean_text)

    async def verify_credentials(self) -> TwitterAuthResult:
        """Run a safe GET smoke-test without creating a Post."""
        if not self.is_configured:
            raise TwitterPublishError(
                "Twitter/X API is not configured: all four TWITTER_* secrets "
                "are required for the auth smoke-test."
            )
        return await asyncio.to_thread(self._verify_credentials_sync)

    def _publish_sync(self, text: str) -> TwitterPublishResult:
        data = self._request_json(
            "POST",
            self.CREATE_POST_PATH,
            payload={"text": text},
        )
        try:
            post_data = data["data"]
            post_id = str(post_data["id"])
            post_text = str(post_data.get("text", text))
        except (KeyError, TypeError) as exc:
            raise TwitterPublishError(
                f"Unexpected Twitter/X API response: {json.dumps(data)[:500]}"
            ) from exc
        return TwitterPublishResult(
            post_id=post_id,
            text=post_text,
            public_post_base_url=self.public_post_base_url,
        )

    def _verify_credentials_sync(self) -> TwitterAuthResult:
        data = self._request_json("GET", self.VERIFY_CREDENTIALS_PATH)
        try:
            user_data = data["data"]
            return TwitterAuthResult(
                user_id=str(user_data["id"]),
                username=str(user_data.get("username", "")),
                name=str(user_data.get("name", "")),
            )
        except (KeyError, TypeError) as exc:
            raise TwitterPublishError(
                f"Unexpected Twitter/X auth response: {json.dumps(data)[:500]}"
            ) from exc

    def _request_json(
        self,
        method: str,
        path: str,
        *,
        payload: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        url = self._url(path)
        body = None
        headers = {
            "Authorization": self._build_oauth_header(method, url),
            "User-Agent": "johny-twitter-branch/0.1",
        }
        if payload is not None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with request.urlopen(req, timeout=20) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raw_error = exc.read().decode("utf-8", errors="replace")
            raise TwitterPublishError(
                f"Twitter/X API error {exc.code}: {raw_error[:800]}"
            ) from exc
        except error.URLError as exc:
            raise TwitterPublishError(f"Twitter/X network error: {exc.reason}") from exc
        except Exception as exc:  # noqa: BLE001 - surface API/network detail
            raise TwitterPublishError(f"Twitter/X request failed: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TwitterPublishError(
                f"Twitter/X returned non-JSON response: {raw[:500]}"
            ) from exc
        if not isinstance(data, dict):
            raise TwitterPublishError(
                f"Twitter/X returned unexpected response: {raw[:500]}"
            )
        return data

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return f"{self.api_base_url}/{path.lstrip('/')}"

    def _build_oauth_header(self, method: str, url: str) -> str:
        oauth_params = {
            "oauth_consumer_key": self.api_key,
            "oauth_nonce": secrets.token_hex(16),
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.access_token,
            "oauth_version": "1.0",
        }
        signature = self._sign(method, url, oauth_params)
        oauth_params["oauth_signature"] = signature
        header_parts = [
            f'{parse.quote(key, safe="")}="{parse.quote(value, safe="")}"'
            for key, value in sorted(oauth_params.items())
        ]
        return "OAuth " + ", ".join(header_parts)

    def _sign(
        self,
        method: str,
        url: str,
        oauth_params: Mapping[str, str],
    ) -> str:
        base_url, query_params = _canonical_url_and_query_params(url)
        signature_params = dict(query_params)
        signature_params.update(oauth_params)
        encoded_params = "&".join(
            f"{_quote(key)}={_quote(value)}"
            for key, value in sorted(signature_params.items())
        )
        base_string = "&".join(
            [
                method.upper(),
                _quote(base_url),
                _quote(encoded_params),
            ]
        )
        signing_key = "&".join(
            [
                _quote(self.api_secret),
                _quote(self.access_token_secret),
            ]
        ).encode("utf-8")
        digest = hmac.new(
            signing_key,
            base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
        return base64.b64encode(digest).decode("ascii")


def _quote(value: object) -> str:
    return parse.quote(str(value), safe="")


def _canonical_url_and_query_params(
    url: str,
) -> tuple[str, Mapping[str, str]]:
    parts = parse.urlsplit(url)
    base_url = parse.urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path or "/",
            "",
            "",
        )
    )
    query_pairs = parse.parse_qsl(parts.query, keep_blank_values=True)
    return base_url, MappingProxyType({key: value for key, value in query_pairs})

