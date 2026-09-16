from pathlib import Path

import pytest

from app.models import DetectedEvent
from app.search import EventSearchService


def event(label: str, timestamp: float, confidence: float = 0.8) -> DetectedEvent:
    return DetectedEvent(
        timestamp_seconds=timestamp,
        label=label,
        description=f"{label.title()} detected",
        confidence=confidence,
        thumbnail_path=str(Path("thumb.jpg")),
    )


@pytest.mark.parametrize(
    ("query", "expected_labels"),
    [
        ("Show me PEOPLE!", ["person"]),
        ("find the cars", ["car"]),
        ("show all vehicles", ["truck", "car"]),
        ("Did someone appear?", ["person"]),
    ],
)
def test_search_maps_supported_queries(query: str, expected_labels: list[str]) -> None:
    events = [event("car", 8), event("person", 2), event("truck", 5)]

    results = EventSearchService().search(query, events)

    assert [result.label for result in results] == expected_labels


@pytest.mark.parametrize("query", ["", "   ", "find a collision", "show red objects"])
def test_search_returns_empty_for_unsupported_query(query: str) -> None:
    assert EventSearchService().search(query, [event("car", 1)]) == []


def test_search_sorts_matches_by_timestamp_then_confidence() -> None:
    events = [event("car", 4, 0.5), event("truck", 2), event("car", 4, 0.9)]

    results = EventSearchService().search("vehicles", events)

    assert [(result.timestamp_seconds, result.confidence) for result in results] == [
        (2, 0.8),
        (4, 0.9),
        (4, 0.5),
    ]
