"""Recommendation presentation preserves inputs, ordered data and CSV bytes."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
import streamlit as st
from pandas.testing import assert_frame_equal

from spotify_intelligence.recommenders.preference_based import PreferenceProfile
from spotify_intelligence.recommenders.track_based import RecommendationFilters

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

tables = importlib.import_module("app.components.tables")
filters = importlib.import_module("app.components.filters")


@pytest.fixture
def results() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "track_name": "Song A",
                "artists": "Artist A",
                "album_name": "Album A",
                "genres": ["rock", "pop"],
                "similarity": 0.8,
                "distance": 0.25,
                "duration_ms": 120000,
                "popularity_median": 40.0,
                "feature_differences": [{"feature": "energy", "absolute_difference": 0.12}],
            },
            {
                "track_name": "Song B",
                "artists": "Artist B",
                "album_name": "Album B",
                "genres": ["jazz"],
                "similarity": 0.5,
                "distance": 1.0,
                "duration_ms": 180000,
                "popularity_median": 50.0,
                "feature_differences": [{"feature": "tempo", "absolute_difference": 5.0}],
            },
        ],
        index=[4, 9],
    )


@pytest.fixture
def preset() -> dict:
    return {
        "label": "Example profile",
        "values": {
            "energy": 0.7,
            "danceability": 0.6,
            "valence": 0.5,
            "acousticness": 0.2,
            "instrumentalness": 0.1,
            "tempo": 120.0,
        },
        "weights": {
            "energy": 2,
            "danceability": 1,
            "valence": 1,
            "acousticness": 0,
            "instrumentalness": 0,
            "tempo": 1,
        },
    }


@pytest.mark.parametrize("kind", ["track", "preferences"])
@pytest.mark.parametrize("advanced", [False, True])
def test_recommendation_pages_preserve_data_and_csv(
    monkeypatch: pytest.MonkeyPatch, results: pd.DataFrame, preset: dict, kind: str, advanced: bool
) -> None:
    module_name = "recommend_by_track" if kind == "track" else "recommend_by_preferences"
    page = importlib.import_module(f"app.pages.{module_name}")
    ui = MagicMock()
    ui.column_config = st.column_config
    ui.slider.side_effect = lambda label, **kwargs: kwargs["value"]
    ui.button.return_value = True
    ui.toggle.return_value = advanced
    ui.checkbox.return_value = advanced
    monkeypatch.setattr(page, "st", ui)
    monkeypatch.setattr(tables, "st", ui)
    monkeypatch.setattr(page.messages, "info_note", MagicMock())

    config = {
        "track_recommender": {
            "retrieval": {"default_top_n": 5, "min_top_n": 5, "max_top_n": 20},
            "genre_affinity": {"enabled_default": False},
        },
        "preference_recommender": {"diversity": {"lambda_default": 0.85}},
    }
    monkeypatch.setattr(page.resources, "load_recommender_config", lambda: config)
    monkeypatch.setattr(page.resources, "load_genre_catalog", lambda: ["rock", "pop"])
    selected_filters = RecommendationFilters(
        explicit="non_explicit" if advanced else "all",
        genres=["rock"] if advanced else None,
        duration_enabled=advanced,
        duration_min_seconds=60,
        duration_max_seconds=600,
        different_artist=advanced if kind == "track" else False,
        popularity_min=40 if advanced else None,
    )
    monkeypatch.setattr(
        page.filters, "render_recommendation_filters", lambda *args, **kwargs: selected_filters
    )
    recommender = MagicMock()
    recommender.recommend.return_value = results
    recommender.out_of_distribution_status.return_value = {"status": "ok"}
    profile = PreferenceProfile.from_manual(preset["values"], preset["weights"])
    seed = pd.Series(
        {
            "recording_group_id": "seed",
            "track_name": "Seed",
            "artists": "Seed Artist",
            "audio_analysis_incomplete": False,
        }
    )
    if kind == "track":
        monkeypatch.setattr(page.resources, "load_tracks", lambda: pd.DataFrame())
        monkeypatch.setattr(page.resources, "load_track_recommender", lambda: recommender)
        monkeypatch.setattr(page.filters, "render_track_search", lambda *args, **kwargs: seed)
        seed_card = MagicMock()
        monkeypatch.setattr(page, "seed_track_card", seed_card)
        filename = "recomendaciones_por_cancion.csv"
    else:
        monkeypatch.setattr(page.resources, "load_presets_config", lambda: {"example": preset})
        monkeypatch.setattr(page.resources, "load_preference_recommender", lambda: recommender)
        monkeypatch.setattr(
            page.filters, "render_preference_profile", lambda *args, **kwargs: profile
        )
        filename = "recomendaciones_por_preferencias.csv"
    original = results.copy(deep=True)
    expected = tables.result_display_frame(results)

    page.render()

    assert_frame_equal(results, original)
    assert_frame_equal(ui.dataframe.call_args.args[0], expected)
    assert ui.dataframe.call_args.kwargs["hide_index"] is True
    column_config = ui.dataframe.call_args.kwargs["column_config"]
    assert [column_config[column]["label"] for column in expected.columns] == [
        "Canción",
        "Artista",
        "Álbum",
        "Géneros",
        "Similitud",
        "Duración",
        "Popularidad",
    ]
    ui.download_button.assert_called_once_with(
        label="Descargar CSV",
        data=expected.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )
    if kind == "track":
        seed_card.assert_called_once_with(seed)
        ui.subheader.assert_any_call("Tu canción de referencia")
        recommender.recommend.assert_called_once_with(
            "seed", top_n=5, filters=selected_filters, genre_affinity=advanced
        )
        ui.subheader.assert_any_call("Características comparadas")
        labels = [call.args[0] for call in ui.expander.call_args_list]
        assert "1. Song A — Artist A" in labels
        assert "2. Song B — Artist B" in labels
        assert "Explicaciones por característica" not in labels
        assert [call.args[0] for call in ui.code.call_args_list] == [
            "Energía: diferencia absoluta 0.120",
            "Tempo (BPM): diferencia absoluta 5.000",
        ]
        assert all(call.kwargs.get("wrap_lines") is True for call in ui.code.call_args_list)
    else:
        recommender.recommend.assert_called_once_with(
            profile,
            top_n=5,
            filters=selected_filters,
            diversity_enabled=advanced,
            lambda_=0.85,
        )
        assert any("distancia ponderada" in call.args[0] for call in ui.caption.call_args_list)


def test_preference_editors_start_collapsed_without_changing_profile(
    monkeypatch: pytest.MonkeyPatch, preset: dict
) -> None:
    ui = MagicMock()
    ui.session_state = {}
    ui.selectbox.side_effect = lambda label, *, options, index=0, **kwargs: options[index]
    ui.slider.side_effect = lambda label, **kwargs: kwargs["value"]
    monkeypatch.setattr(filters, "st", ui)

    profile = filters.render_preference_profile({"example": preset}, prefix="pref")

    assert profile.values == preset["values"]
    assert profile.weights == preset["weights"]
    assert len(ui.expander.call_args_list) == 2
    assert all(call.kwargs["expanded"] is False for call in ui.expander.call_args_list)
    keys = [call.kwargs["key"] for call in ui.selectbox.call_args_list]
    assert keys[0] == "pref_preset"
    assert "pref_weight_valence_1" in keys
    assert ui.session_state["pref_generation"] == 1
