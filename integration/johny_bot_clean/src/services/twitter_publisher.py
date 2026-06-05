"""Minimal Twitter/X API v2 publisher for a johny-bot-clean-like host."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
from urllib import error, parse, request

DEFAULT_API_BASE_URL = "https://api.x.com"
DEFAULT_PUBLIC_POST_BASE_URL = "https://x.com/i/web/status"


class TwitterPublishError(Exception):
    """Raised when Twitter/X rejects or cannot complete publication."""


@dataclass(frozen=True)
class TwitterPublishResult:
    """Result returned after a successful Post creation."""

    post_id: str
    text: str
    public_post_base_url: str = DEFAULT_PUBLIC_POST_BASE_URL

    @property
    def tweet_id(self) -> str:
        """Backward-compatible alias for projects that still say tweet_id."""
        return self.post_id

    @property
    def url(self) -> str:
        return f"{self.public_post_base_url.rstrip('/')}/{self.post_id}"


class TwitterPublisher:
    """Publish text Posts to Twitter/X via API v2."""

    CREATE_POST_PATH = "/2/tweets"

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
        """Create one Post with *text* and return its public id."""
        if not self.is_configured:
            raise TwitterPublishError(
                "Twitter API не настроен: заполните TWITTER_API_KEY, "
                "TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN и "
                "TWITTER_ACCESS_TOKEN_SECRET."
            )
        clean_text = text.strip()
        if not clean_text:
            raise TwitterPublishError("Нельзя опубликовать пустой твит.")
        if len(clean_text) > 280:
            raise TwitterPublishError(
                f"Твит длиннее лимита Twitter/X: {len(clean_text)} символов."
            )
        return await asyncio.to_thread(self._publish_sync, clean_text)

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
                f"Unexpected Twitter API response: {json.dumps(data)[:500]}"
            ) from exc
        return TwitterPublishResult(
            post_id=post_id,
            text=post_text,
            public_post_base_url=self.public_post_base_url,
        )

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
                f"Twitter API error {exc.code}: {raw_error[:800]}"
            ) from exc
        except error.URLError as exc:
            raise TwitterPublishError(f"Twitter API network error: {exc.reason}") from exc
        except Exception as exc:  # noqa: BLE001 - surface API/network detail
            raise TwitterPublishError(f"Twitter API error: {exc}") from exc

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise TwitterPublishError(
                f"Twitter returned non-JSON response: {raw[:500]}"
            ) from exc
        if not isinstance(data, dict):
            raise TwitterPublishError(
                f"Twitter returned unexpected response: {raw[:500]}"
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

