# Aplicación Streamlit

Resonance es el nombre visible de la aplicación, configurado en `configs/app.yaml`.

## Estructura

- `streamlit_app.py` — Router multipágina.
- `app/pages/` — Páginas individuales (home, recomendación por canción, recomendación por preferencias, laboratorio multietiqueta, laboratorio multiclase, auditoría de datos, metodología).
- `app/components/` — Componentes reutilizables (cards, charts, filters, tables, messages, resources).

## Presentación visual

- El tema compartido se configura en `.streamlit/config.toml`: colores, tipografía,
  jerarquía de títulos, bordes y esquinas de controles y tablas.
- Los fondos neutros y el texto oscuro priorizan la legibilidad. Los acentos
  verdes se reservan para superficies y gráficos, no para texto sobre blanco.
- Las tarjetas utilizan contenedores y métricas nativos con borde; no dependen
  de selectores CSS internos ni de fuentes externas.
- Los gráficos de `app/components/charts.py` conservan sus datos y orden,
  con relleno de acento y contornos oscuros.
- Los mensajes mantienen la semántica nativa de información, advertencia y error.

## Inicio y navegación

- Inicio es la página predeterminada y presenta «Recomendar por canción» como
  acción principal, con una guía breve de búsqueda, selección y recomendación.
- El recomendador por preferencias permanece accesible como alternativa.
- La navegación agrupa Inicio y ambos recomendadores en «Descubrir música».
  Auditoría, laboratorios y metodología se agrupan en «Explorar el proyecto»,
  también disponible como sección plegada en Inicio.
- Las siete páginas conservan sus rutas y funcionalidades. Las cifras del
  catálogo y los avisos sobre similitud y limitaciones permanecen visibles.

## Presentación de recomendaciones

- El recomendador por canción identifica la canción de referencia antes de los
  controles. Sus resultados conservan una tabla y muestran las diferencias por
  característica en secciones individuales identificadas por canción y artista.
- Las diferencias de características no se presentan como contribuciones
  individuales a la similitud. El recomendador por preferencias explica la
  distancia ponderada sin inventar un desglose que sus resultados no contienen.
- Los encabezados en español se aplican con configuración de columnas de Streamlit.
  Los nombres, valores, orden de filas y archivos CSV se conservan.
- La edición de valores, los pesos y las opciones avanzadas empiezan plegados.
  Sus controles siguen ejecutándose y conservan claves, valores y reinicio al
  cambiar de perfil inicial.
- La similitud no es una probabilidad de gusto. La afinidad de género y la
  diversidad pueden modificar el orden y se explican junto a los resultados.

## Reglas

- Streamlit no reentrena modelos durante una interacción.
- Artefactos ausentes producen un error claro, no entrenamiento silencioso.
- La aplicación no contiene lógica de producción; delega a `src/spotify_intelligence/`.
