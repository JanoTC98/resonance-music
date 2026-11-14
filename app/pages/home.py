"""Home page: a guided first recommendation and secondary project links."""

from __future__ import annotations

import streamlit as st

from app.components import resources
from app.components.cards import metric_row
from app.components.messages import info_note


def render() -> None:
    config = resources.load_app_config()["app"]
    title = str(config.get("title", "Resonance"))
    st.title(title)
    st.caption("Descubre música a partir de una canción o de tus preferencias.")

    st.subheader("Empieza con una canción")
    st.write(
        "Elige una canción de referencia y explora otras con características musicales similares."
    )
    if st.button("Recomendar por canción", type="primary", key="home_start_track"):
        st.switch_page("app/pages/recommend_by_track.py")

    st.markdown(
        """
1. Busca una canción por su título o artista.
2. Selecciona la coincidencia que buscas; puedes ajustar los filtros si lo necesitas.
3. Pulsa **Recomendar** para ver los resultados y sus explicaciones.
"""
    )
    st.page_link(
        "app/pages/recommend_by_preferences.py",
        label="Recomendar por preferencias",
        icon="🎛️",
    )

    st.subheader("El catálogo, de un vistazo")
    tracks = resources.load_tracks()
    recordings = resources.load_recordings()
    genres = resources.load_genre_catalog()

    metric_row(
        [
            ("Canciones únicas", f"{len(tracks):,}"),
            ("Grabaciones únicas", f"{len(recordings):,}"),
            ("Géneros", len(genres)),
        ]
    )

    with st.expander("Explorar el proyecto", expanded=False):
        st.caption(
            "Consulta la calidad de los datos, los laboratorios experimentales "
            "y las limitaciones del proyecto."
        )
        st.page_link("app/pages/data_audit.py", label="Auditoría y catálogo", icon="📊")
        st.page_link(
            "app/pages/multilabel_genre_lab.py", label="Laboratorio multietiqueta", icon="🏷️"
        )
        st.page_link(
            "app/pages/dominant_genre_lab.py",
            label="Laboratorio de género dominante",
            icon="🎼",
        )
        st.page_link("app/pages/methodology.py", label="Metodología y limitaciones", icon="📚")

    info_note(
        "Las similitudes y puntuaciones son medidas de distancia o de modelo; "
        "no representan probabilidades de gusto ni afiliación oficial con Spotify."
    )


if st.runtime.exists():
    render()
