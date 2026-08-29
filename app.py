import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ============================================================
# Configuración de página y paleta (negro/blanco/gris/naranja)
# ============================================================
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
ALTURA_CHICA = 300

st.markdown(
    """
    <style>
    hr, div[data-testid="stDivider"] { border-color: #F97316 !important; }
    .stTabs [aria-selected="true"] { color: #F97316 !important; }
    .stTabs [data-baseweb="tab-border"] { background-color: #F97316 !important; }
    div[data-testid="stMetric"] {
        border: 1px solid #F97316; border-radius: 6px; padding: 8px 10px;
    }
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }
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
        titulo_kwargs["x"] = 0.5
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
    d["kpis"] = pd.read_csv("data/kpis_resumen.csv").iloc[0]
    d["tabla"] = pd.read_csv("data/tabla_clientes.csv")
    d["concentracion"] = pd.read_csv("data/concentracion_linea.csv")
    d["estado_credito"] = pd.read_csv("data/estado_credito.csv")
    d["mora"] = pd.read_csv("data/mora_distribucion.csv")
    d["composicion"] = pd.read_csv("data/composicion_cuota.csv", parse_dates=["Mes"])
    d["cobros_vs_credito"] = pd.read_csv("data/cobros_vs_credito.csv", parse_dates=["Mes"])
    d["proyeccion"] = pd.read_csv("data/proyeccion_cuotas.csv", parse_dates=["Mes"])
    return d


datos = cargar_datos()
kpis = datos["kpis"]

tabla = datos["tabla"].copy()
for col in ["Saldo", "Saldo vencido", "Creditos activos", "Cuotas impagas", "Días de atraso (máx.)"]:
    if col in tabla.columns:
        tabla[col] = tabla[col].fillna(0)
        if col in ["Saldo", "Saldo vencido"]:
            tabla[col] = tabla[col].round(0).astype(int)

st.title("Tablero de gestión crediticia — Masori")

tab_intro, tab_monitoreo, tab_tabla, tab_definiciones = st.tabs(
    ["Introducción", "Monitoreo de cartera", "Tabla operativa", "Definiciones"]
)

with tab_intro:
    st.header("Descripción")
    st.markdown(
        """
        **Masori** es una fintech prendaria que opera en Neuquén y Río Negro, como Proveedor No
        Financiero de Crédito (PNFC) supervisado por el BCRA. Su cartera incluye créditos prendarios
        (vehículos), créditos personales y descuento de cheques.
        """
    )
    st.header("Objetivo del tablero")
    st.markdown(
        """
        - Monitorear el estado general de la cartera crediticia.
        - Visualizar la composición y evolución de las cuotas.
        - Identificar concentración de riesgo y niveles de mora.
        - Contar con una vista operativa filtrable por cliente.
        """
    )
    st.caption("Período de análisis: septiembre 2025 – septiembre 2026.")

with tab_monitoreo:
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Tasa de aprobación", f"{kpis['tasa_aprobacion_pct']:.1f}%")
    k2.metric("Cobrado / Otorgado", f"{kpis['tasa_cobrado_sobre_otorgado_pct']:.1f}%")
    k3.metric("% de cartera en mora", f"{kpis['pct_en_mora']:.1f}%")
    k4.metric("Total otorgado", formato_ars(kpis["total_otorgado"]))
    k5.metric("Total cobrado", formato_ars(kpis["total_cobrado"]))
    k6.metric("Pendiente de cobro", formato_ars(kpis["monto_pendiente_cobro"]))

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        fig = go.Figure(go.Pie(
            labels=datos["concentracion"]["Linea de crédito"], values=datos["concentracion"]["monto_pct"],
            marker=dict(colors=PALETA_CATEGORICA),
            hovertemplate="<b>%{label}</b><br>%{value:.1f}% del monto<extra></extra>",
        ))
        tema_oscuro(fig, title=dict(text="Cartera por línea de crédito"), height=ALTURA_CHICA, showlegend=True)
        st.plotly_chart(fig, width="stretch")

    with col2:
        ec = datos["estado_credito"].sort_values("monto")
        colores_estado = {
            "Acreditado": BLANCO, "Pagado": GRIS, "Refinanciado": NARANJA,
            "Pre-cancelado": GRIS_CLARO, "Borrador": NARANJA_CLARO, "Rechazado": NARANJA_OSCURO,
        }
        fig = go.Figure(go.Bar(
            x=ec["monto"], y=ec["Estado"], orientation="h",
            marker_color=[colores_estado.get(e, GRIS) for e in ec["Estado"]],
            customdata=ec["cantidad"],
            hovertemplate="<b>%{y}</b><br>Monto: %{x:,.0f}<br>Cantidad: %{customdata}<extra></extra>",
        ))
        tema_oscuro(fig, title=dict(text="Créditos por estado"), height=ALTURA_CHICA, xaxis=dict(title="Monto"))
        st.plotly_chart(fig, width="stretch")

    with col3:
        m = datos["mora"].sort_values("monto")
        colores_mora = {
            "Normal": BLANCO, "Mora temprana": NARANJA_CLARO, "Mora media": NARANJA,
            "Mora tardia": NARANJA_OSCURO, "Incobrable": "#7C2D12", "Mora preventiva": GRIS,
        }
        fig = go.Figure(go.Bar(
            x=m["monto"], y=m["Estado de mora"], orientation="h",
            marker_color=[colores_mora.get(e, GRIS) for e in m["Estado de mora"]],
            customdata=m["cantidad"],
            hovertemplate="<b>%{y}</b><br>Saldo: %{x:,.0f}<br>Cantidad: %{customdata} cuotas<extra></extra>",
        ))
        tema_oscuro(fig, title=dict(text="Cuotas por estado de mora"), height=ALTURA_CHICA, xaxis=dict(title="Saldo"))
        st.plotly_chart(fig, width="stretch")

    col4, col5 = st.columns(2)

    with col4:
        colores_comp = {"Capital": BLANCO, "Interés": NARANJA, "Cargo": GRIS, "Impuesto": NARANJA_CLARO}
        fig = go.Figure(data=[
            go.Bar(name=c, x=datos["composicion"]["Mes"], y=datos["composicion"][c], marker_color=colores_comp[c])
            for c in ["Capital", "Interés", "Cargo", "Impuesto"]
        ])
        tema_oscuro(fig, barmode="stack", title=dict(text="Composición mensual del cronograma de cuotas"),
                    height=ALTURA_CHICA, xaxis=dict(title="Mes"), yaxis=dict(title="Monto", tickformat=",.0f"))
        st.plotly_chart(fig, width="stretch")

    with col5:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=datos["cobros_vs_credito"]["Mes"], y=datos["cobros_vs_credito"]["Cobrado"],
                                  name="Cobrado", mode="lines+markers",
                                  line=dict(width=2, color=NARANJA, dash="dash"), marker=dict(size=6, color=NARANJA)))
        fig.add_trace(go.Scatter(x=datos["cobros_vs_credito"]["Mes"], y=datos["cobros_vs_credito"]["Credito_otorgado"],
                                  name="Crédito otorgado", mode="lines+markers",
                                  line=dict(width=2, color=BLANCO, dash="dot"), marker=dict(size=6, color=BLANCO)))
        fig.add_trace(go.Scatter(x=datos["proyeccion"]["Mes"], y=datos["proyeccion"]["Monto_programado"],
                                  name="Cuotas programadas (proyección)", mode="lines",
                                  line=dict(width=2, color=GRIS, dash="dashdot")))
        tema_oscuro(fig, title=dict(text="Cobros confirmados vs. Crédito otorgado (con proyección)"),
                    height=ALTURA_CHICA + 90,
                    xaxis=dict(title="Mes", rangeslider=dict(visible=True, thickness=0.08), type="date"),
                    yaxis=dict(title="Monto", tickformat=",.0f"))
        st.plotly_chart(fig, width="stretch")

with tab_tabla:
    col1, col2 = st.columns(2)
    with col1:
        estado_sel = st.selectbox("Estado del crédito", ["Todos"] + sorted(tabla["Estado"].dropna().unique().tolist()))
    with col2:
        impagas_sel = st.selectbox("¿Tiene cuotas impagas?", ["Todos", "Sí", "No"])

    tabla_filtrada = tabla.copy()
    if estado_sel != "Todos":
        tabla_filtrada = tabla_filtrada[tabla_filtrada["Estado"] == estado_sel]
    if impagas_sel != "Todos":
        tabla_filtrada = tabla_filtrada[tabla_filtrada["Tiene cuotas impagas"] == impagas_sel]

    st.dataframe(
        tabla_filtrada.rename(columns={"Cliente_id": "Cliente", "Estado": "Estado del crédito"}),
        width="stretch", hide_index=True,
        column_config={
            "Saldo": st.column_config.NumberColumn(format="$ %d"),
            "Saldo vencido": st.column_config.NumberColumn(format="$ %d"),
        },
    )

with tab_definiciones:
    st.markdown(
        """
        **Fuente de datos:** planillas de gestión de Masori (Contacto, Crédito, Cuotas, Cobros),
        anonimizadas antes de su publicación.

        **Variables:**
        - **Cliente:** identificador anonimizado del cliente (no es el nombre real).
        - **Estado del crédito:** Acreditado, Pagado, Refinanciado, Pre-cancelado, Borrador o Rechazado.
        - **Saldo:** capital pendiente de pago del cliente.
        - **Saldo vencido:** porción del saldo que ya venció sin pagarse.
        - **Cuotas impagas:** cantidad de cuotas vencidas sin pago registrado.
        - **Días de atraso (máx.):** mayor cantidad de días de atraso entre las cuotas impagas del cliente.
        - **Tasa de aprobación:** % de solicitudes de crédito aprobadas sobre el total resuelto.
        - **Cobrado / Otorgado:** % del monto total otorgado que ya fue efectivamente cobrado.
        - **% de cartera en mora:** % del saldo de cuotas que no está en estado "Normal".
        """
    )
