"""Tests for Event and Subscription types."""

from mu_dsu.events.types import CRITICAL, HIGH, LOW, NORMAL, Event, EventPriority, Subscription


class TestEventPriority:
    def test_ordering(self):
        assert CRITICAL > HIGH > NORMAL > LOW

    def test_custom_priority(self):
        p = EventPriority(60)
        assert p > NORMAL
        assert p < HIGH


class TestEvent:
    def test_creation_defaults(self):
        e = Event(type="test.event", source="test")
        assert e.type == "test.event"
        assert e.source == "test"
        assert e.payload == {}
        assert e.priority == NORMAL
        assert e.id  # non-empty

    def test_unique_ids(self):
        e1 = Event(type="a", source="s")
        e2 = Event(type="a", source="s")
        assert e1.id != e2.id

    def test_custom_payload(self):
        e = Event(type="x", source="s", payload={"key": "value"})
        assert e.payload["key"] == "value"


class TestSubscription:
    def test_creation_defaults(self):
        s = Subscription(event_pattern="test.*", adaptation_script="redo;")
        assert s.event_pattern == "test.*"
        assert s.active is True
        assert s.filter is None

    def test_with_filter(self):
        f = lambda e: e.payload.get("path") == "/tmp"
        s = Subscription(event_pattern="file.*", adaptation_script="redo;", filter=f)
        assert s.filter is not None
