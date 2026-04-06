"""
utils.py — Funciones reutilizables para el proyecto Dengue Argentina EDA.

Autor: Fabiana Grisel González
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


# ===========================================================
# CONFIGURACIÓN GLOBAL
# ===========================================================

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"

# Estilo de gráficos
PLOT_STYLE = "seaborn-v0_8-whitegrid"
PALETTE = "viridis"
FIG_SIZE = (12, 6)


def configurar_graficos():
    """Aplica configuración global de estilo para los gráficos."""
    plt.style.use(PLOT_STYLE)
    sns.set_palette(PALETTE)
    plt.rcParams["figure.figsize"] = FIG_SIZE
    plt.rcParams["figure.dpi"] = 100
    plt.rcParams["savefig.dpi"] = 150
    plt.rcParams["font.size"] = 11
    plt.rcParams["axes.titlesize"] = 14
    plt.rcParams["axes.labelsize"] = 12
    print("✅ Configuración de gráficos aplicada.")


# ===========================================================
# CARGA DE DATOS
# ===========================================================

def cargar_csv(nombre_archivo: str, encoding: str = "utf-8", sep: str = ",") -> pd.DataFrame:
    """
    Carga un archivo CSV desde data/raw/.

    Parameters
    ----------
    nombre_archivo : str
        Nombre del archivo (ej: 'dengue_2024.csv').
    encoding : str
        Codificación del archivo. Probar 'latin-1' si 'utf-8' falla.
    sep : str
        Separador de columnas.

    Returns
    -------
    pd.DataFrame
    """
    ruta = DATA_RAW / nombre_archivo
    if not ruta.exists():
        raise FileNotFoundError(f"❌ No se encontró el archivo: {ruta}")

    df = pd.read_csv(ruta, encoding=encoding, sep=sep)
    print(f"✅ Archivo cargado: {nombre_archivo}")
    print(f"   Filas: {df.shape[0]:,} | Columnas: {df.shape[1]}")
    return df


# ===========================================================
# INSPECCIÓN Y CALIDAD DE DATOS (enfoque QA)
# ===========================================================

def reporte_calidad(df: pd.DataFrame) -> pd.DataFrame:
    """
    Genera un reporte de calidad del DataFrame.

    Devuelve un DataFrame con: tipo de dato, cantidad de nulls,
    porcentaje de nulls, valores únicos y duplicados.
    """
    reporte = pd.DataFrame({
        "tipo": df.dtypes,
        "nulls": df.isnull().sum(),
        "nulls_%": (df.isnull().sum() / len(df) * 100).round(2),
        "unicos": df.nunique(),
        "ejemplo": df.iloc[0] if len(df) > 0 else None
    })

    duplicados = df.duplicated().sum()
    total = len(df)

    print("=" * 60)
    print("📋 REPORTE DE CALIDAD DE DATOS")
    print("=" * 60)
    print(f"   Total de registros: {total:,}")
    print(f"   Total de columnas:  {df.shape[1]}")
    print(f"   Filas duplicadas:   {duplicados:,} ({duplicados/total*100:.2f}%)")
    print(f"   Columnas con nulls: {(df.isnull().sum() > 0).sum()}")
    print("=" * 60)

    return reporte


def detectar_outliers_iqr(serie: pd.Series, factor: float = 1.5) -> pd.Series:
    """
    Detecta outliers usando el método IQR.

    Parameters
    ----------
    serie : pd.Series
        Serie numérica a analizar.
    factor : float
        Multiplicador del IQR (default 1.5).

    Returns
    -------
    pd.Series
        Máscara booleana indicando outliers (True = outlier).
    """
    Q1 = serie.quantile(0.25)
    Q3 = serie.quantile(0.75)
    IQR = Q3 - Q1
    limite_inferior = Q1 - factor * IQR
    limite_superior = Q3 + factor * IQR

    outliers = (serie < limite_inferior) | (serie > limite_superior)
    print(f"   Outliers detectados: {outliers.sum():,} de {len(serie):,} "
          f"({outliers.sum()/len(serie)*100:.2f}%)")
    return outliers


# ===========================================================
# VISUALIZACIONES
# ===========================================================

def guardar_figura(fig, nombre: str, formato: str = "png"):
    """
    Guarda una figura en outputs/figures/.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
    nombre : str
        Nombre del archivo sin extensión.
    formato : str
        Formato de imagen (png, svg, pdf).
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    ruta = FIGURES_DIR / f"{nombre}.{formato}"
    fig.savefig(ruta, bbox_inches="tight", facecolor="white")
    print(f"💾 Figura guardada: {ruta}")


def plot_evolucion_temporal(df: pd.DataFrame, col_fecha: str, col_casos: str,
                            titulo: str = "Evolución temporal de casos",
                            guardar: bool = False):
    """
    Gráfico de línea de evolución temporal.

    Parameters
    ----------
    df : pd.DataFrame
    col_fecha : str
        Nombre de la columna de fecha.
    col_casos : str
        Nombre de la columna con cantidad de casos.
    titulo : str
    guardar : bool
        Si True, guarda la figura en outputs/figures/.
    """
    fig, ax = plt.subplots(figsize=FIG_SIZE)
    ax.plot(df[col_fecha], df[col_casos], linewidth=2, color="#E63946")
    ax.set_title(titulo, fontweight="bold")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Cantidad de casos")
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    if guardar:
        guardar_figura(fig, "evolucion_temporal")

    plt.show()


def plot_casos_por_jurisdiccion(df: pd.DataFrame, col_jurisdiccion: str,
                                 col_casos: str, top_n: int = 10,
                                 guardar: bool = False):
    """
    Barplot horizontal de casos por jurisdicción (top N).

    Parameters
    ----------
    df : pd.DataFrame
    col_jurisdiccion : str
    col_casos : str
    top_n : int
    guardar : bool
    """
    datos = (df.groupby(col_jurisdiccion)[col_casos]
               .sum()
               .nlargest(top_n)
               .sort_values())

    fig, ax = plt.subplots(figsize=(10, 6))
    datos.plot(kind="barh", ax=ax, color=sns.color_palette(PALETTE, top_n))
    ax.set_title(f"Top {top_n} jurisdicciones por cantidad de casos",
                 fontweight="bold")
    ax.set_xlabel("Total de casos confirmados")
    ax.set_ylabel("")
    plt.tight_layout()

    if guardar:
        guardar_figura(fig, "casos_por_jurisdiccion")

    plt.show()
