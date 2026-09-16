"""Deterministic query mapping for the hackathon demo."""

import re
from collections.abc import Iterable

from app.models import DetectedEvent

VEHICLE_LABELS = frozenset({"bicycle", "car", "motorcycle", "bus", "truck"})
QUERY_LABELS = {
    "person": frozenset({"person"}),
    "people": frozenset({"person"}),
    "someone": frozenset({"person"}),
    "car": frozenset({"car"}),
    "cars": frozenset({"car"}),
    "vehicle": VEHICLE_LABELS,
    "vehicles": VEHICLE_LABELS,
    "bicycle": frozenset({"bicycle"}),
    "motorcycle": frozenset({"motorcycle"}),
    "bus": frozenset({"bus"}),
    "truck": frozenset({"truck"}),
}


class EventSearchService:
    """Map supported query terms to object labels without inventing matches."""

    def search(self, query: str, events: Iterable[DetectedEvent]) -> list[DetectedEvent]:
        labels = self.labels_for_query(query)
        if not labels:
            return []
        return sorted(
            (event for event in events if event.label.lower() in labels),
            key=lambda event: (event.timestamp_seconds, -event.confidence),
        )

    @staticmethod
    def labels_for_query(query: str) -> frozenset[str]:
        words = set(re.findall(r"[a-z]+", query.lower()))
        labels: set[str] = set()
        for word in words:
            labels.update(QUERY_LABELS.get(word, ()))
        return frozenset(labels)
