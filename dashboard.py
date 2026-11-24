"""Dashboard de aproximaciones a la Tierra con datos de NASA Asteroids NeoWs."""
import json
import os
from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import requests
import streamlit as st

FEED = "https://api.nasa.gov/neo/rest/v1/feed"
ARCHIVO = Path(__file__).with_name("respuesta.json")
NUMERICAS = ["Diámetro máximo (km)", "Velocidad (km/h)", "Distancia (km)"]
COLUMNAS = ["Asteroide", "Fecha", *NUMERICAS, "Clasificación"]
PERIODO = (date(2026, 10, 1), date(2026, 11, 7))
GRUPOS = ["No clasificado como peligroso", "Potencialmente peligroso"]
COLOR = alt.Color(
    "Clasificación:N",
    scale=alt.Scale(domain=GRUPOS, range=["#51d6c8", "#ffb46b"]),
    legend=None,
)


def transformar(registros):
    """Convierte cada aproximación del feed en una fila de la tabla."""
    filas = []
    for fecha_feed, asteroide in registros:
        peligro = asteroide.get("is_potentially_hazardous_asteroid")
        diametro = asteroide.get("estimated_diameter", {}).get("kilometers", {})
        for evento in asteroide.get("close_approach_data", []):
            fecha = evento.get("close_approach_date")
            if fecha_feed is not None and fecha != fecha_feed:
                continue
            filas.append({
                "Asteroide": asteroide.get("name"),
                "Fecha": fecha,
                "Diámetro máximo (km)": diametro.get("estimated_diameter_max"),
                "Velocidad (km/h)": evento.get("relative_velocity", {}).get("kilometers_per_hour"),
                "Distancia (km)": evento.get("miss_distance", {}).get("kilometers"),
                "Clasificación": {False: GRUPOS[0], True: GRUPOS[1]}.get(peligro),
            })

    tabla = pd.DataFrame(filas, columns=COLUMNAS)
    tabla["Fecha"] = pd.to_datetime(tabla["Fecha"], errors="coerce")
    for columna in NUMERICAS:
        tabla[columna] = pd.to_numeric(tabla[columna], errors="coerce")
    return tabla.dropna().sort_values(["Fecha", "Distancia (km)"])


@st.cache_data
def cargar_evaluacion():
    datos = json.loads(ARCHIVO.read_text(encoding="utf-8"))
    return transformar((None, asteroide) for asteroide in datos)


def clave_nasa():
    try:
        return st.secrets.get("NASA_API_KEY") or os.getenv("NASA_API_KEY") or "DEMO_KEY"
    except FileNotFoundError:
        return os.getenv("NASA_API_KEY") or "DEMO_KEY"


@st.cache_data(ttl=900, show_spinner=False)
def consultar_nasa(inicio, fin, clave):
    try:
        respuesta = requests.get(
            FEED,
            params={"start_date": inicio, "end_date": fin, "api_key": clave},
            timeout=15,
        )
    except requests.RequestException:
        raise ValueError("No se pudo conectar con NASA. Intenta de nuevo.") from None

    if respuesta.status_code == 429:
        raise ValueError("NASA alcanzó el límite de consultas. Intenta más tarde o configura NASA_API_KEY.")
    if respuesta.status_code in (401, 403):
        raise ValueError("NASA rechazó la clave. Revisa NASA_API_KEY en la configuración de la app.")
    if not respuesta.ok:
        raise ValueError(f"El servicio de NASA respondió con HTTP {respuesta.status_code}.")

    try:
        grupos = respuesta.json()["near_earth_objects"]
        return transformar(
            (fecha, asteroide)
            for fecha, asteroides in grupos.items()
            for asteroide in asteroides
        )
    except (KeyError, TypeError, AttributeError, ValueError):
        raise ValueError("NASA devolvió datos en un formato inesperado.") from None


def mostrar_graficas(tabla, periodo):
    st.header("Análisis de aproximaciones")
    primera, segunda = st.columns(2)
    with primera:
        st.subheader("Aproximaciones por día")
        fechas = pd.date_range(pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1]))
        diario = tabla.groupby("Fecha").size().reindex(fechas, fill_value=0)
        diario = diario.rename("Aproximaciones").rename_axis("Fecha").reset_index()
        grafica = alt.Chart(diario).mark_line(point=True, color="#51d6c8").encode(
            x=alt.X("Fecha:T", title="Fecha", axis=alt.Axis(format="%d/%m", tickCount=8)),
            y=alt.Y("Aproximaciones:Q", axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("Fecha:T", format="%d/%m/%Y"), "Aproximaciones:Q"],
        )
        st.altair_chart(grafica.properties(height=245), width="stretch")

    with segunda:
        st.subheader("Distribución de tamaños")
        grafica = alt.Chart(tabla).mark_bar(color="#7b9cf9", cornerRadiusTopLeft=3,
                                            cornerRadiusTopRight=3).encode(
            x=alt.X("Diámetro máximo (km):Q", bin=alt.Bin(maxbins=22)),
            y=alt.Y("count()", title="Aproximaciones", axis=alt.Axis(tickMinStep=1)),
            tooltip=[alt.Tooltip("Diámetro máximo (km):Q", bin=True),
                     alt.Tooltip("count()", title="Aproximaciones")],
        )
        st.altair_chart(grafica.properties(height=245), width="stretch")

    tercera, cuarta = st.columns(2)
    with tercera:
        st.subheader("Velocidad promedio por clasificación")
        promedios = tabla.groupby("Clasificación", as_index=False)["Velocidad (km/h)"].mean()
        grafica = alt.Chart(promedios).mark_bar(cornerRadiusEnd=4).encode(
            x=alt.X("Velocidad (km/h):Q", title="Promedio (km/h)"),
            y=alt.Y("Clasificación:N", title=None, sort=GRUPOS,
                    axis=alt.Axis(labelLimit=165)),
            color=COLOR,
            tooltip=["Clasificación:N", alt.Tooltip("Velocidad (km/h):Q", format=",.0f")],
        )
        st.altair_chart(grafica.properties(height=245), width="stretch")

    with cuarta:
        st.subheader("Tamaño frente a velocidad")
        grafica = alt.Chart(tabla).mark_circle(size=57, opacity=0.75).encode(
            x="Diámetro máximo (km):Q",
            y="Velocidad (km/h):Q",
            color=COLOR,
            tooltip=["Asteroide:N", "Clasificación:N",
                     alt.Tooltip("Diámetro máximo (km):Q", format=".4f"),
                     alt.Tooltip("Velocidad (km/h):Q", format=",.0f")],
        )
        st.caption("Turquesa · No clasificado como peligroso     |     Naranja · Potencialmente peligroso")
        st.altair_chart(grafica.properties(height=245), width="stretch")


st.set_page_config(page_title="Asteroides cerca de la Tierra", layout="wide")
st.markdown("""
<style>
.block-container {max-width: 1320px; padding-top: 3rem;}
[data-testid="stMetric"] {
    background: #142139;
    border: 1px solid #2a3b59;
    border-radius: 14px;
    padding: 14px 17px;
}
</style>
""", unsafe_allow_html=True)
st.title("Asteroides cerca de la Tierra")
st.caption("NASA / JPL · Asteroids NeoWs")

with st.sidebar:
    st.header("Filtros")
    origen = st.radio("Origen de los datos", ["Datos de la evaluación", "Consultar API NASA"])
    if origen == "Consultar API NASA":
        with st.form("consulta"):
            intervalo = st.date_input("Fechas de consulta", (date(2026, 11, 1), PERIODO[1]))
            st.caption("Elige hasta siete días consecutivos.")
            consultar = st.form_submit_button("Consultar NASA", type="primary")
    else:
        intervalo = st.date_input("Fechas de aproximación", PERIODO,
                                  min_value=PERIODO[0], max_value=PERIODO[1])
    seleccion = st.selectbox("Clasificación NASA", ["Todas", *GRUPOS])

if origen == "Consultar API NASA":
    if consultar:
        if len(intervalo) != 2 or not 0 <= (intervalo[1] - intervalo[0]).days <= 6:
            st.warning("Selecciona un intervalo de uno a siete días.")
        else:
            try:
                with st.spinner("Consultando NASA Asteroids NeoWs..."):
                    tabla_api = consultar_nasa(*intervalo, clave_nasa())
                st.session_state["resultado_api"] = (intervalo, tabla_api)
            except ValueError as error:
                st.warning(str(error))
    if "resultado_api" not in st.session_state:
        st.info("Selecciona las fechas y pulsa **Consultar NASA**.")
        st.stop()
    periodo, tabla = st.session_state["resultado_api"]
    fuente = "Consulta a la API NASA"
else:
    if len(intervalo) != 2:
        st.info("Selecciona la fecha de inicio y la fecha final.")
        st.stop()
    periodo = intervalo
    tabla = cargar_evaluacion()
    tabla = tabla[tabla["Fecha"].between(pd.Timestamp(periodo[0]), pd.Timestamp(periodo[1]))]
    fuente = "Datos guardados de la evaluación"

st.caption(f"{fuente} · {periodo[0]:%d/%m/%Y} al {periodo[1]:%d/%m/%Y}")
if seleccion != "Todas":
    tabla = tabla[tabla["Clasificación"].eq(seleccion)]
if tabla.empty:
    st.info("No hay aproximaciones para los filtros seleccionados.")
    st.stop()

total, riesgo, cercana, rapida = st.columns(4)
total.metric("Aproximaciones", f"{len(tabla):,}")
riesgo.metric("Potencialmente peligrosas", f"{tabla['Clasificación'].eq(GRUPOS[1]).sum():,}")
cercana.metric("Distancia mínima", f"{tabla['Distancia (km)'].min():,.0f} km")
rapida.metric("Velocidad máxima", f"{tabla['Velocidad (km/h)'].max():,.0f} km/h")

mostrar_graficas(tabla, periodo)
st.header("Detalle de aproximaciones")
st.dataframe(tabla, hide_index=True, width="stretch",
             column_config={"Fecha": st.column_config.DateColumn(format="DD/MM/YYYY")})
st.download_button("Descargar CSV filtrado", tabla.to_csv(index=False).encode("utf-8-sig"),
                   file_name="aproximaciones_nasa.csv", mime="text/csv")
