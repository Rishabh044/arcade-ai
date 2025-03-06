"""Discord Gateway API tools."""

from .subscribe_to_events import subscribe_to_events
from .unsubscribe_from_events import unsubscribe_from_events

__all__ = [
    "subscribe_to_events",
    "unsubscribe_from_events",
]
