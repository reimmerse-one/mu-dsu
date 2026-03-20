"""Synchronous event bus with pub/sub and pattern matching."""

from __future__ import annotations

import fnmatch
from collections import deque
from typing import Callable

from mu_dsu.events.types import Event, Subscription


class EventBus:
    """Synchronous pub/sub event bus.

    Matches events to subscriptions via glob-style patterns
    (e.g., "file.*" matches "file.changed"). Returns matched
    subscriptions sorted by priority for the caller to handle.
    """

    def __init__(self, history_size: int = 1000) -> None:
        self._subscriptions: dict[str, Subscription] = {}
        self._history: deque[Event] = deque(maxlen=history_size)

    def subscribe(self, sub: Subscription) -> str:
        """Register a subscription. Returns its id."""
        self._subscriptions[sub.id] = sub
        return sub.id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns True if found."""
        return self._subscriptions.pop(subscription_id, None) is not None

    def match(self, event: Event) -> list[Subscription]:
        """Find all active subscriptions matching this event, sorted by priority (desc)."""
        matched = []
        for sub in self._subscriptions.values():
            if not sub.active:
                continue
            if not self._matches_pattern(sub.event_pattern, event.type):
                continue
            if sub.filter is not None and not sub.filter(event):
                continue
            matched.append(sub)
        return sorted(matched, key=lambda s: -s.priority)

    def publish(self, event: Event) -> list[Subscription]:
        """Record event in history and return matched subscriptions."""
        self._history.append(event)
        return self.match(event)

    @property
    def history(self) -> list[Event]:
        return list(self._history)

    @property
    def subscriptions(self) -> list[Subscription]:
        return list(self._subscriptions.values())

    @staticmethod
    def _matches_pattern(pattern: str, event_type: str) -> bool:
        """Glob-style matching: 'file.*' matches 'file.changed'."""
        return fnmatch.fnmatch(event_type, pattern)
