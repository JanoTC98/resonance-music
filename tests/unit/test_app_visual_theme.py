"""Theme contrast and presentation-only component regressions."""

from __future__ import annotations

import importlib
import sys
import tomllib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

cards = importlib.import_module("app.components.cards")
charts = importlib.import_module("app.components.charts")

PALETTE = {"#beed80", "#59d999", "#31ada1", "#51647a", "#453c5c"}


def _contrast(first: str, second: str) -> float:
    def luminance(color: str) -> float:
        channels = [int(color[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
            for value in channels
        ]
        return sum(
            value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722), strict=True)
        )

    light, dark = sorted((luminance(first), luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def test_theme_uses_resonance_palette_and_readable_foregrounds() -> None:
    with (ROOT / ".streamlit/config.toml").open("rb") as file:
        theme = tomllib.load(file)["theme"]

    assert set(theme["chartCategoricalColors"]) == PALETTE
    assert theme["textColor"] == "#453c5c"
    assert theme["baseRadius"] == "0.75rem"
    assert theme["showWidgetBorder"] is True
    for background in (
        theme["backgroundColor"],
        theme["secondaryBackgroundColor"],
        theme["dataframeHeaderBackgroundColor"],
    ):
        assert _contrast(theme["textColor"], background) >= 4.5
    assert _contrast("#ffffff", theme["primaryColor"]) >= 4.5
    assert _contrast(theme["linkColor"], theme["backgroundColor"]) >= 4.5
    sidebar = theme["sidebar"]
    assert _contrast(sidebar["textColor"], sidebar["backgroundColor"]) >= 4.5


@pytest.mark.parametrize("kind", ["scores", "counts"])
def test_chart_palette_preserves_values_labels_and_orientation(kind: str) -> None:
    if kind == "scores":
        figure = charts.score_bars([("First", 0.8), ("Second", 0.3)])
        assert list(figure.data[0].x) == [0.8, 0.3]
        assert list(figure.data[0].y) == ["First", "Second"]
        assert figure.data[0].orientation == "h"
        assert figure.layout.yaxis.autorange == "reversed"
    else:
        figure = charts.audit_counts(["First", "Second"], [8, 3])
        assert list(figure.data[0].x) == ["First", "Second"]
        assert list(figure.data[0].y) == [8, 3]
    assert figure.data[0].marker.color == "#31ada1"
    assert figure.data[0].marker.line.color == "#51647a"
    assert figure.layout.font.color == "#453c5c"


def test_metric_cards_keep_labels_and_values(monkeypatch: pytest.MonkeyPatch) -> None:
    ui = MagicMock()
    columns = [MagicMock(), MagicMock()]
    ui.columns.return_value = columns
    monkeypatch.setattr(cards, "st", ui)

    cards.metric_row([("Tracks", 12), ("Genres", 3)])

    for column, label, value in zip(columns, ("Tracks", "Genres"), ("12", "3"), strict=True):
        column.metric.assert_called_once_with(label, value, border=True)


def test_seed_card_keeps_content_inside_native_container(monkeypatch: pytest.MonkeyPatch) -> None:
    ui = MagicMock()
    monkeypatch.setattr(cards, "st", ui)
    cards.seed_track_card(
        {
            "track_name": "Example",
            "artists": "Artist",
            "album_name": "Album",
            "duration_ms": 120000,
            "popularity_median": 50,
        }
    )
    ui.container.assert_called_once_with(border=True)
    ui.markdown.assert_called_once_with(
        "**Example** — Artist  \nÁlbum: Album · Duración: 2:00 · Popularidad: 50"
    )
