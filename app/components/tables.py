"""Table rendering and CSV download helpers."""

from __future__ import annotations

import pandas as pd
import streamlit as st


def recommendation_column_config() -> dict:
    """Label recommendation columns without changing frame or CSV schemas."""
    return {
        "track_name": st.column_config.TextColumn("Canción", width="medium"),
        "artists": st.column_config.TextColumn("Artista", width="medium"),
        "album_name": st.column_config.TextColumn("Álbum"),
        "genres": st.column_config.TextColumn("Géneros"),
        "similarity": st.column_config.NumberColumn(
            "Similitud",
            format="%.3f",
            help="Cercanía musical calculada por el recomendador; no es una probabilidad de gusto.",
        ),
        "duration": st.column_config.TextColumn("Duración", help="Minutos y segundos."),
        "popularity_median": st.column_config.NumberColumn(
            "Popularidad", format="%.0f", help="Popularidad registrada en el catálogo."
        ),
    }


def download_csv_button(
    frame: pd.DataFrame,
    filename: str,
    *,
    label: str = "Descargar CSV",
) -> None:
    """Render a CSV download button for ``frame``."""
    st.download_button(
        label=label,
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


def format_duration(ms_value: object) -> str:
    """Format a duration in milliseconds as ``m:ss``."""
    try:
        ms = float(ms_value)
    except (TypeError, ValueError):
        return str(ms_value)
    total_seconds = int(round(ms / 1000))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d}"


def result_display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a presentation-ready copy of a recommendation result.

    ``genres`` lists are joined into a readable string and durations are
    formatted; the original DataFrame is not modified.
    """
    rows = frame.copy()
    if "genres" in rows.columns:
        rows["genres"] = rows["genres"].apply(
            lambda value: ", ".join(value) if isinstance(value, (list, tuple)) else value
        )
    if "duration_ms" in rows.columns:
        rows["duration"] = rows["duration_ms"].map(format_duration)

    columns = [
        "track_name",
        "artists",
        "album_name",
        "genres",
        "similarity",
        "duration",
        "popularity_median",
    ]
    present = [column for column in columns if column in rows.columns]
    return rows[present]
