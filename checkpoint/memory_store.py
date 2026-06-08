"""In-memory Redis backend for dashboard dev when Redis is unavailable."""

from __future__ import annotations

from typing import Any


class MemoryRedisBackend:
    """Minimal Redis-like backend for LiveStateStore."""

    def __init__(self) -> None:
        self._kv: dict[str, str] = {}
        self._lists: dict[str, list[str]] = {}

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> str | None:
        return self._kv.get(key)

    def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._kv[key] = value

    def keys(self, pattern: str) -> list[str]:
        prefix = pattern.rstrip("*")
        return [k for k in self._kv if k.startswith(prefix)]

    def lpush(self, key: str, value: str) -> None:
        self._lists.setdefault(key, []).insert(0, value)

    def ltrim(self, key: str, start: int, end: int) -> None:
        if key in self._lists:
            self._lists[key] = self._lists[key][start : end + 1]

    def lrange(self, key: str, start: int, end: int) -> list[str]:
        return self._lists.get(key, [])[start : end + 1]
