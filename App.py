"""
Dashboard interactivo — Dengue en Argentina (2018-2025)

Ejecutar con: streamlit run app.py

Autora: Fabiana Grisel Gonzalez
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import seaborn as sns
import streamlit as st
from pathlib import Path

# ===========================================================
# CONFIGURACION DE PAGINA
# ===========================================================

st.set_page_config(
    page_title="Dengue Argentina - EDA",
    page_icon="🦟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ===========================================================
# ESTILOS
# ===========================================================

COLOR_DENGUE = "#E63946"
COLOR_ZIKA = "#457B9D"
COLOR_ACCENT = "#F4A261"
PALETTE_PROV = ["#E63946", "#F4A261", "#2A9D8F", "#264653", "#E9C46A"]


# ===========================================================
# CARGA DE DATOS
# ===========================================================

@st.cache_data
def cargar_datos():
    """Carga el dataset limpio. Intenta processed primero, luego raw."""
    processed = Path("data/processed/dengue_limpio.csv")
    raw_dir = Path("data/raw")

    if processed.exists():
        df = pd.read_csv(processed)
    else:
        archivos_raw = list(raw_dir.glob("*.csv"))
        if not archivos_raw:
            st.error("No se encontraron archivos CSV en data/processed/ ni data/raw/")
            st.stop()
        df = pd.read_csv(archivos_raw[0], encoding="latin-1")

    return df


df = cargar_datos()

COL_CANTIDAD = "cantidad_casos"
COL_SEMANA = "semanas_epidemiologicas"
COL_ANIO = "ano"


# ===========================================================
# SIDEBAR — FILTROS
# ===========================================================

st.sidebar.image(
    "https://img.shields.io/badge/🦟_Dengue-Argentina-E63946?style=for-the-badge",
    use_container_width=True,
)
st.sidebar.title("Filtros")

# Filtro de anios
anios_disponibles = sorted(df[COL_ANIO].unique())
anios_seleccionados = st.sidebar.multiselect(
    "Anio(s)",
    options=anios_disponibles,
    default=anios_disponibles,
)

# Filtro de provincias
provincias_disponibles = sorted(df["provincia_nombre"].unique())
provincias_seleccionadas = st.sidebar.multiselect(
    "Provincia(s)",
    options=provincias_disponibles,
    default=provincias_disponibles,
)

# Filtro de evento
eventos_disponibles = sorted(df["evento_nombre"].unique())
evento_seleccionado = st.sidebar.multiselect(
    "Evento",
    options=eventos_disponibles,
    default=eventos_disponibles,
)

# Aplicar filtros
mask = (
    df[COL_ANIO].isin(anios_seleccionados)
    & df["provincia_nombre"].isin(provincias_seleccionadas)
    & df["evento_nombre"].isin(evento_seleccionado)
)
df_filtrado = df[mask]

# Info en sidebar
st.sidebar.markdown("---")
st.sidebar.metric("Registros filtrados", f"{len(df_filtrado):,}")
st.sidebar.metric("Total de casos", f"{df_filtrado[COL_CANTIDAD].sum():,.0f}")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "**Fuente:** [Ministerio de Salud](https://datos.salud.gob.ar/dataset/vigilancia-de-dengue-y-zika)"
)
st.sidebar.markdown(
    "**Autora:** [Fabiana Grisel Gonzalez](https://linkedin.com/in/fabiana-grisel-gonzalez)"
)


# ===========================================================
# HEADER
# ===========================================================

st.title("🦟 Dengue en Argentina")
st.markdown("**Analisis Exploratorio de Datos (2018-2025)** — Dashboard interactivo")
st.markdown("---")


# ===========================================================
# KPIs
# ===========================================================

total_casos = df_filtrado[COL_CANTIDAD].sum()
total_provincias = df_filtrado["provincia_nombre"].nunique()
total_departamentos = df_filtrado["departamento_nombre"].nunique()
anio_pico = (
    df_filtrado.groupby(COL_ANIO)[COL_CANTIDAD].sum().idxmax()
    if len(df_filtrado) > 0
    else "N/A"
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de casos", f"{total_casos:,.0f}")
col2.metric("Provincias afectadas", total_provincias)
col3.metric("Departamentos", total_departamentos)
col4.metric("Anio con mas casos", anio_pico)

st.markdown("---")


# ===========================================================
# FILA 1: EVOLUCION ANUAL + PROVINCIAS
# ===========================================================

col_left, col_right = st.columns(2)

# --- Evolucion anual ---
with col_left:
    st.subheader("Evolucion anual de casos")

    casos_anio = df_filtrado.groupby(COL_ANIO)[COL_CANTIDAD].sum()

    if len(casos_anio) > 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        colores = [
            COLOR_DENGUE if v == casos_anio.max() else COLOR_ZIKA
            for v in casos_anio.values
        ]
        ax.bar(casos_anio.index, casos_anio.values, color=colores, edgecolor="white")

        for i, v in enumerate(casos_anio.values):
            ax.text(
                casos_anio.index[i],
                v + casos_anio.max() * 0.02,
                f"{v:,.0f}",
                ha="center",
                fontsize=9,
                fontweight="bold",
            )

        ax.set_xlabel("Anio")
        ax.set_ylabel("Casos confirmados")
        ax.yaxis.set_major_formatter(
            ticker.FuncFormatter(lambda x, _: f"{x:,.0f}")
        )
        ax.set_xticks(casos_anio.index)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("No hay datos para los filtros seleccionados.")


# --- Top provincias ---
with col_right:
    st.subheader("Casos por provincia")

    df_geo = df_filtrado[df_filtrado["provincia_nombre"] != "DESCONOCIDA"]
    casos_prov = (
        df_geo.groupby("provincia_nombre")[COL_CANTIDAD]
        .sum()
        .sort_values(ascending=True)
    )

    if len(casos_prov) > 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        colores = sns.color_palette("YlOrRd", len(casos_prov))
        ax.barh(casos_prov.index, casos_prov.values, color=colores)
        ax.set_xlabel("Casos confirmados")

        for i, v in enumerate(casos_prov.values):
            ax.text(
                v + casos_prov.max() * 0.01,
                i,
                f"{v:,.0f}",
                va="center",
                fontsize=9,
            )

        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("No hay datos para los filtros seleccionados.")


st.markdown("---")


# ===========================================================
# FILA 2: ESTACIONALIDAD + EDAD
# ===========================================================

col_left2, col_right2 = st.columns(2)

# --- Estacionalidad ---
with col_left2:
    st.subheader("Estacionalidad (semana epidemiologica)")

    if len(df_filtrado) > 0:
        estacional = df_filtrado.pivot_table(
            index=COL_SEMANA,
            columns=COL_ANIO,
            values=COL_CANTIDAD,
            aggfunc="sum",
            fill_value=0,
        )

        fig, ax = plt.subplots(figsize=(8, 4))
        anio_max = estacional.sum().idxmax() if len(estacional.columns) > 0 else None

        for col in estacional.columns:
            alpha = 1.0 if col == anio_max else 0.35
            lw = 2.5 if col == anio_max else 1
            ax.plot(
                estacional.index,
                estacional[col],
                label=str(col),
                alpha=alpha,
                linewidth=lw,
            )

        ax.axvspan(1, 22, alpha=0.08, color="red", label="Temporada alta")
        ax.set_xlabel("Semana epidemiologica")
        ax.set_ylabel("Casos")
        ax.legend(title="Anio", bbox_to_anchor=(1.05, 1), loc="upper left", fontsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("No hay datos para los filtros seleccionados.")


# --- Grupos de edad ---
with col_right2:
    st.subheader("Distribucion por grupo de edad")

    casos_edad = (
        df_filtrado.groupby("grupo_edad_desc")[COL_CANTIDAD]
        .sum()
        .sort_values(ascending=True)
    )

    if len(casos_edad) > 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        colores = sns.color_palette("viridis", len(casos_edad))
        ax.barh(casos_edad.index, casos_edad.values, color=colores)
        ax.set_xlabel("Casos confirmados")

        max_idx = len(casos_edad) - 1
        ax.get_children()[max_idx].set_color(COLOR_DENGUE)
        ax.get_children()[max_idx].set_edgecolor("black")

        for i, v in enumerate(casos_edad.values):
            ax.text(
                v + casos_edad.max() * 0.01,
                i,
                f"{v:,.0f}",
                va="center",
                fontsize=8,
            )

        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="y", labelsize=8)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("No hay datos para los filtros seleccionados.")


st.markdown("---")


# ===========================================================
# FILA 3: HEATMAP GEOGRAFICO
# ===========================================================

st.subheader("Mapa de calor: Provincia x Anio")

df_geo = df_filtrado[df_filtrado["provincia_nombre"] != "DESCONOCIDA"]

if len(df_geo) > 0:
    pivot_geo = df_geo.pivot_table(
        index="provincia_nombre",
        columns=COL_ANIO,
        values=COL_CANTIDAD,
        aggfunc="sum",
        fill_value=0,
    )

    pivot_geo["total"] = pivot_geo.sum(axis=1)
    pivot_geo = pivot_geo.sort_values("total", ascending=False).drop(columns="total")

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(
        pivot_geo,
        cmap="YlOrRd",
        linewidths=0.5,
        linecolor="white",
        annot=True,
        fmt=".0f",
        ax=ax,
        cbar_kws={"label": "Casos confirmados", "shrink": 0.8},
    )
    ax.set_xlabel("Anio")
    ax.set_ylabel("")
    ax.tick_params(axis="y", rotation=0)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
else:
    st.info("No hay datos para los filtros seleccionados.")


st.markdown("---")


# ===========================================================
# FILA 4: DENGUE vs ZIKA + TOP DEPARTAMENTOS
# ===========================================================

col_left3, col_right3 = st.columns(2)

# --- Dengue vs Zika ---
with col_left3:
    st.subheader("Dengue vs. Zika")

    eventos = df_filtrado.groupby("evento_nombre")[COL_CANTIDAD].sum()

    if len(eventos) > 0:
        fig, ax = plt.subplots(figsize=(6, 4))
        colores_pie = [COLOR_DENGUE, COLOR_ZIKA][: len(eventos)]
        eventos.plot(
            kind="pie",
            autopct="%1.1f%%",
            colors=colores_pie,
            startangle=90,
            ax=ax,
            textprops={"fontsize": 11},
        )
        ax.set_ylabel("")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("No hay datos para los filtros seleccionados.")


# --- Top departamentos ---
with col_right3:
    st.subheader("Top 10 departamentos")

    top_deptos = (
        df_filtrado.groupby(["provincia_nombre", "departamento_nombre"])[COL_CANTIDAD]
        .sum()
        .nlargest(10)
        .sort_values(ascending=True)
    )

    if len(top_deptos) > 0:
        fig, ax = plt.subplots(figsize=(8, 4))
        labels = [f"{depto} ({prov})" for prov, depto in top_deptos.index]
        ax.barh(labels, top_deptos.values, color=sns.color_palette("OrRd_r", 10))
        ax.set_xlabel("Casos confirmados")

        for i, v in enumerate(top_deptos.values):
            ax.text(
                v + top_deptos.max() * 0.01,
                i,
                f"{v:,.0f}",
                va="center",
                fontsize=9,
            )

        ax.spines[["top", "right"]].set_visible(False)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("No hay datos para los filtros seleccionados.")


st.markdown("---")


# ===========================================================
# FOOTER
# ===========================================================

st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 20px;'>
        <small>
            Dengue Argentina EDA — Datos abiertos del Ministerio de Salud (CC BY 4.0)<br>
            Desarrollado por <a href='https://linkedin.com/in/fabiana-grisel-gonzalez'>Fabiana Grisel Gonzalez</a>
            | <a href='https://github.com/Grisel86/dengue-argentina-eda'>GitHub</a>
        </small>
    </div>
    """,
    unsafe_allow_html=True,
)