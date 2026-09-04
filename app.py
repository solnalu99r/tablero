import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# Configuración de página y paleta (negro/blanco/gris/naranja)

st.set_page_config(page_title="Tablero de gestión crediticia - Masori", layout="wide")

FONDO = "#0D0D0D"
NEGRO = "#000000"
BLANCO = "#FFFFFF"
NARANJA = "#F97316"
NARANJA_CLARO = "#FDBA74"
NARANJA_OSCURO = "#C2410C"
GRIS = "#9CA3AF"
GRIS_CLARO = "#D1D5DB"
GRIS_OSCURO = "#6B7280"
PALETA_CATEGORICA = [BLANCO, NARANJA, GRIS, NARANJA_CLARO, GRIS_CLARO, NARANJA_OSCURO, GRIS_OSCURO]
PLANTILLA = "plotly_dark"
ALTURA_CHICA = 250
ESTADOS_OTORGADOS = ["Acreditado", "Pagado", "Refinanciado", "Pre-cancelado"]


st.markdown(
    """
    <style>
        hr, div[data-testid="stDivider"] { border-color: #F97316 !important; }
    .stTabs [data-baseweb="tab-list"] {
        display: flex;
        width: 100%;
        gap: 4px;
        background-color: #000000;
        border: 1px solid #F97316;
        border-radius: 6px;
        padding: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        justify-content: center;
        font-size: 18px;
        padding: 14px 44px;
        border-radius: 4px;
        background-color: #1A1A1A;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F97316 !important;
        color: #000000 !important;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab-border"] { display: none; }
    .stTabs [data-baseweb="tab-highlight"] { display: none; }
          div[data-testid="stMetric"] {
        border: 1px solid #F97316; border-radius: 6px; padding: 6px 8px;
    }
    div[data-testid="stPlotlyChart"] {
        border: 1px solid #F97316; border-radius: 6px; padding: 1px;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #F97316; border-radius: 6px;
    }
    label[data-testid="stWidgetLabel"] p { color: #F97316 !important; font-weight: 600; }
    .block-container { padding-top: 0.1rem; padding-bottom: 0.1rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.1rem; }
    h2 { margin-bottom: 0.0rem !important; margin-top: 0 !important; }
    .stTabs [data-baseweb="tab-panel"] { padding-top: 0 !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] { margin-bottom: 0 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


def formato_ars(x, decimales=0):
    if pd.isna(x):
        x = 0
    s = f"{x:,.{decimales}f}"
    return "$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


def tema_oscuro(fig, **kwargs):
    legend_kwargs = kwargs.pop("legend", {})
    legend_final = dict(bgcolor=FONDO, font=dict(color=BLANCO))
    legend_final.update(legend_kwargs)
    titulo_kwargs = kwargs.pop("title", None)
    if titulo_kwargs is not None and isinstance(titulo_kwargs, dict) and "x" not in titulo_kwargs:
        titulo_kwargs["x"] = 0.02
    fig.update_layout(
        template=PLANTILLA, plot_bgcolor=FONDO, paper_bgcolor=FONDO,
        font=dict(color=BLANCO, family="Arial", size=11), title_font=dict(color=BLANCO, family="Arial", size=14),
        legend=legend_final, separators=",.", margin=dict(l=40, r=20, t=40, b=30),
        **({"title": titulo_kwargs} if titulo_kwargs is not None else {}), **kwargs,
    )
    fig.update_xaxes(gridcolor="#2B2B2B", zerolinecolor="#2B2B2B", color=BLANCO)
    fig.update_yaxes(gridcolor="#2B2B2B", zerolinecolor="#2B2B2B", color=BLANCO)
    return fig


@st.cache_data
def cargar_datos():
    d = {}
    d["credito_detalle"] = pd.read_csv("data/credito_detalle.csv", parse_dates=["Fecha"])
    d["cuotas_detalle"] = pd.read_csv("data/cuotas_detalle.csv", parse_dates=["Fecha de vencimiento"])
    d["cobros_detalle"] = pd.read_csv("data/cobros_detalle.csv", parse_dates=["Fecha de cobro"])
    d["tabla"] = pd.read_csv("data/tabla_clientes.csv")
    d["evolucion_credito"] = pd.read_csv("data/evolucion_credito.csv", parse_dates=["Mes"])
    d["horizonte_2029"] = pd.read_csv("data/horizonte_2029.csv", parse_dates=["Mes"])
    return d


datos = cargar_datos()

tabla = datos["tabla"].copy()
for col in ["Saldo", "Saldo vencido", "Creditos activos", "Cuotas impagas", "Días de atraso (máx.)"]:
    if col in tabla.columns:
        tabla[col] = tabla[col].fillna(0)
        if col in ["Saldo", "Saldo vencido"]:
            tabla[col] =
