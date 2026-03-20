"""Event and Subscription types for the μ-DSU event system."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True, order=True)
class EventPriority:
    """Comparable priority. Higher numeric value = processed first."""
    value: int = 50


# Predefined priority levels
CRITICAL = EventPriority(100)
HIGH = EventPriority(75)
NORMAL = EventPriority(50)
LOW = EventPriority(25)


@dataclass
class Event:
    """Typed event with metadata."""
    type: str
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = field(default_factory=lambda: NORMAL)
    timestamp: float = field(default_factory=time.monotonic)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


@dataclass
class Subscription:
    """Links an event pattern to a μDA adaptation script."""
    event_pattern: str
    adaptation_script: str
    micro_language: str = ""
    priority: int = 0
    filter: Callable[[Event], bool] | None = None
    context: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    active: bool = True
