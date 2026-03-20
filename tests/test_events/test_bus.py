"""Tests for EventBus."""

from mu_dsu.events.bus import EventBus
from mu_dsu.events.types import Event, Subscription


class TestEventBus:
    def test_subscribe_and_match_exact(self):
        bus = EventBus()
        sub = Subscription(event_pattern="file.changed", adaptation_script="redo;")
        bus.subscribe(sub)
        matched = bus.match(Event(type="file.changed", source="test"))
        assert len(matched) == 1
        assert matched[0] is sub

    def test_glob_pattern(self):
        bus = EventBus()
        sub = Subscription(event_pattern="file.*", adaptation_script="redo;")
        bus.subscribe(sub)
        assert len(bus.match(Event(type="file.changed", source="s"))) == 1
        assert len(bus.match(Event(type="file.deleted", source="s"))) == 1
        assert len(bus.match(Event(type="timer.tick", source="s"))) == 0

    def test_no_match(self):
        bus = EventBus()
        bus.subscribe(Subscription(event_pattern="x", adaptation_script=""))
        assert bus.match(Event(type="y", source="s")) == []

    def test_multiple_subscriptions(self):
        bus = EventBus()
        s1 = Subscription(event_pattern="e", adaptation_script="a", priority=1)
        s2 = Subscription(event_pattern="e", adaptation_script="b", priority=2)
        bus.subscribe(s1)
        bus.subscribe(s2)
        matched = bus.match(Event(type="e", source="s"))
        assert len(matched) == 2
        # Higher priority first
        assert matched[0] is s2
        assert matched[1] is s1

    def test_unsubscribe(self):
        bus = EventBus()
        sub = Subscription(event_pattern="e", adaptation_script="a")
        sub_id = bus.subscribe(sub)
        assert bus.unsubscribe(sub_id) is True
        assert bus.match(Event(type="e", source="s")) == []
        assert bus.unsubscribe("nonexistent") is False

    def test_filter(self):
        bus = EventBus()
        sub = Subscription(
            event_pattern="file.*",
            adaptation_script="a",
            filter=lambda e: e.payload.get("path", "").endswith(".cfg"),
        )
        bus.subscribe(sub)
        assert len(bus.match(Event(type="file.changed", source="s", payload={"path": "x.cfg"}))) == 1
        assert len(bus.match(Event(type="file.changed", source="s", payload={"path": "x.py"}))) == 0

    def test_inactive_subscription(self):
        bus = EventBus()
        sub = Subscription(event_pattern="e", adaptation_script="a", active=False)
        bus.subscribe(sub)
        assert bus.match(Event(type="e", source="s")) == []

    def test_publish_records_history(self):
        bus = EventBus()
        bus.subscribe(Subscription(event_pattern="e", adaptation_script="a"))
        event = Event(type="e", source="s")
        bus.publish(event)
        assert len(bus.history) == 1
        assert bus.history[0] is event

    def test_publish_returns_matched(self):
        bus = EventBus()
        sub = Subscription(event_pattern="e", adaptation_script="a")
        bus.subscribe(sub)
        matched = bus.publish(Event(type="e", source="s"))
        assert len(matched) == 1
