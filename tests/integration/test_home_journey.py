"""First-use guidance and navigation retain all existing destinations."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


@pytest.fixture
def home_ui(monkeypatch: pytest.MonkeyPatch) -> tuple:
    home = importlib.import_module("app.pages.home")
    ui = MagicMock()
    ui.button.return_value = False
    monkeypatch.setattr(home, "st", ui)
    monkeypatch.setattr(home.resources, "load_app_config", lambda: {"app": {"title": "Resonance"}})
    for loader in ("load_tracks", "load_recordings", "load_genre_catalog"):
        monkeypatch.setattr(home.resources, loader, lambda: [])
    metrics = MagicMock()
    note = MagicMock()
    monkeypatch.setattr(home, "metric_row", metrics)
    monkeypatch.setattr(home, "info_note", note)
    return home, ui, metrics, note


def test_home_guides_first_recommendation_and_keeps_secondary_pages(home_ui: tuple) -> None:
    home, ui, metrics, note = home_ui

    home.render()

    ui.button.assert_called_once_with(
        "Recomendar por canción", type="primary", key="home_start_track"
    )
    ui.switch_page.assert_not_called()
    guidance = "\n".join(call.args[0] for call in ui.markdown.call_args_list)
    for step in (
        "1. Busca una canción",
        "2. Selecciona la coincidencia",
        "3. Pulsa **Recomendar**",
    ):
        assert step in guidance
    ui.expander.assert_called_once_with("Explorar el proyecto", expanded=False)
    assert [call.args[0] for call in ui.page_link.call_args_list] == [
        "app/pages/recommend_by_preferences.py",
        "app/pages/data_audit.py",
        "app/pages/multilabel_genre_lab.py",
        "app/pages/dominant_genre_lab.py",
        "app/pages/methodology.py",
    ]
    assert ui.page_link.call_args_list[0].kwargs["label"] == "Recomendar por preferencias"
    metrics.assert_called_once_with(
        [("Canciones únicas", "0"), ("Grabaciones únicas", "0"), ("Géneros", 0)]
    )
    assert "no representan probabilidades de gusto" in note.call_args.args[0]


def test_home_primary_action_opens_existing_track_page(home_ui: tuple) -> None:
    home, ui, _, _ = home_ui
    ui.button.return_value = True

    home.render()

    ui.switch_page.assert_called_once_with("app/pages/recommend_by_track.py")


def test_navigation_prioritizes_recommenders_without_changing_page_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    router = importlib.import_module("streamlit_app")
    ui = MagicMock()
    ui.Page.side_effect = lambda page, **kwargs: page
    monkeypatch.setattr(router, "st", ui)
    monkeypatch.setattr(router, "load_yaml_config", lambda path: {"app": {"title": "Resonance"}})

    router.main()

    groups = ui.navigation.call_args.args[0]
    assert isinstance(groups, dict)
    assert list(groups) == ["Descubrir música", "Explorar el proyecto"]
    assert groups["Descubrir música"] == [
        "app/pages/home.py",
        "app/pages/recommend_by_track.py",
        "app/pages/recommend_by_preferences.py",
    ]
    assert groups["Explorar el proyecto"] == [
        "app/pages/data_audit.py",
        "app/pages/multilabel_genre_lab.py",
        "app/pages/dominant_genre_lab.py",
        "app/pages/methodology.py",
    ]
    assert ui.Page.call_count == 7
    assert ui.Page.call_args_list[0].kwargs["default"] is True
    ui.navigation.return_value.run.assert_called_once_with()
