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
ALTURA_CHICA = 350

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
        border: 1px solid #F97316; border-radius: 6px; padding: 4px;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #F97316; border-radius: 6px;
    }
    label[data-testid="stWidgetLabel"] p { color: #F97316 !important; font-weight: 600; }
    .block-container { padding-top: 0.8rem; padding-bottom: 0.2rem; }
    div[data-testid="stVerticalBlock"] { gap: 0.2rem; }
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

st.markdown(
    """
    <h1 style="text-align: center; margin-top: 2rem;">
        Tablero de gestión crediticia — Masori
    </h1>
    """,
    unsafe_allow_html=True,
)

tab_intro, tab_monitoreo, tab_tabla, tab_definiciones = st.tabs(
    ["Resumen general", "Monitoreo de cartera", "Tabla operativa", "Definiciones"]
)

with tab_intro:
    st.header("Objetivo")
    st.markdown(
        """
        El presente tablero tiene como objetivo monitorear el desempeño de la cartera de créditos de
        **Masori S.A.**, a través del seguimiento de indicadores clave de aprobación, cobranza y mora
        que permiten evaluar la eficiencia operativa y el estado general de la cartera.

        En la pestaña "Monitoreo de cartera" se presentan las tarjetas con los indicadores actuales,
        junto con gráficos de concentración por línea de crédito, estado de los créditos, distribución
        de mora, composición mensual de las cuotas y evolución de cobros frente al crédito otorgado.
        En "Tabla operativa" se puede consultar el detalle por cliente, filtrable por estado y por
        cuotas impagas.
        """
    )

    st.header("Origen de los datos")
    st.markdown(
        """
        Los datos provienen de cuatro exports del sistema de gestión de Masori:

        - **Contacto:** datos de los clientes (localidad, saldo, saldo vencido, cantidad de créditos activos).
        - **Crédito:** solicitudes de crédito (línea, monto, estado, usuario gestor).
        - **Cuotas:** detalle de cada cuota del cronograma (capital, interés, cargo, impuesto, estado de mora).
        - **Cobros:** pagos registrados sobre las cuotas.
        """
    )



    st.caption("Período de análisis: septiembre 2025 – septiembre 2026.")

with tab_monitoreo:
    k1, k2, k3, k4, k5, k6 = st.columns([1, 1, 1, 1.5, 1.5, 1.5])  # POSICION: los 6 numeros son el ancho relativo de cada tarjeta; cambia los primeros 4 para achicar o agrandar
    k1.metric("Tasa de aprobación", f"{kpis['tasa_aprobacion_pct']:.1f}%")
    k2.metric("Tasa de cobranza", f"{kpis['tasa_cobranza_pct']:.1f}%")
    k3.metric("% de cartera en mora", f"{kpis['pct_en_mora']:.1f}%")
    k4.metric("Monto de cuotas", formato_ars(kpis["monto_cuotas"]))
    k5.metric("Total cobrado", formato_ars(kpis["total_cobrado"]))
    k6.metric("Pendiente de cobro", formato_ars(kpis["monto_pendiente_cobro"]))
    
    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        fig = go.Figure(go.Pie(
            labels=datos["concentracion"]["Linea de crédito"], values=datos["concentracion"]["monto"],
            marker=dict(colors=PALETA_CATEGORICA, line=dict(color=FONDO, width=2)),
            customdata=datos["concentracion"][["monto", "cantidad"]],
            hovertemplate=(
                "<b>Línea de crédito:</b> %{label}<br>"
                "<b>Monto:</b> %{customdata[0]:,.0f}<br>"
                "<b>Cantidad de créditos:</b> %{customdata[1]}<br>"
                "<b>% del total:</b> %{percent}<extra></extra>"
            ),
        ))
        tema_oscuro(fig, title=dict(text="Cartera por línea de crédito (% del monto total)"),
                    height=ALTURA_CHICA, showlegend=True, legend_title_text="Línea de crédito")
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
            hovertemplate="<b>%{y}</b><br>Monto: %{x:,.0f}<br>Cantidad: %{customdata} créditos<extra></extra>",
        ))
        tema_oscuro(fig, title=dict(text="Créditos por estado: monto y cantidad"), height=ALTURA_CHICA, xaxis=dict(title="Monto"))
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
        tema_oscuro(fig, title=dict(text="Cuotas por estado de mora: saldo y cantidad"), height=ALTURA_CHICA, xaxis=dict(title="Saldo"))
        st.plotly_chart(fig, width="stretch")

    col4, col5 = st.columns(2)

    with col4:
        colores_comp = {"Capital": BLANCO, "Interés": NARANJA, "Cargo": GRIS, "Impuesto": NARANJA_CLARO}
        comp = datos["composicion"].copy()
        totales_mes = comp[["Capital", "Interés", "Cargo", "Impuesto"]].sum(axis=1)
        porcentuales = comp[["Capital", "Interés", "Cargo", "Impuesto"]].div(totales_mes.replace(0, pd.NA), axis=0).fillna(0) * 100
        UMBRAL = 5

        def etiquetas(col):
            p = porcentuales[col].values
            return [f"{v:.0f}%" if v >= UMBRAL else "" for v in p]

        MESES_ES = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
                    7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}
        etiquetas_mes = [f"{MESES_ES[m.month]}-{str(m.year)[2:]}" for m in comp["Mes"]]

        fig = go.Figure(data=[
            go.Bar(name=c, x=comp[c], y=comp["Mes"], orientation="h",
                   text=etiquetas(c), textposition="inside", insidetextanchor="middle",
                   marker_color=colores_comp[c],
                   hovertemplate=f"<b>{c}</b>: " + "%{x:,.0f}<extra></extra>")
            for c in ["Capital", "Interés", "Cargo", "Impuesto"]
        ])
        tema_oscuro(fig, barmode="stack", title=dict(text="Composición mensual del cronograma de cuotas"),
                    height=ALTURA_CHICA,
                    yaxis=dict(title="Mes", type="category", tickmode="array",
                               tickvals=list(comp["Mes"]), ticktext=etiquetas_mes, autorange="reversed"),
                    xaxis=dict(title="Monto", tickformat=",.0f"))
        st.plotly_chart(fig, width="stretch")

    with col5:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=datos["cobros_vs_credito"]["Mes"], y=datos["cobros_vs_credito"]["Cobrado"],
                                  name="Cobrado (confirmado)", mode="lines+markers",
                                  line=dict(width=2, color=NARANJA, dash="dash"), marker=dict(size=6, color=NARANJA),
                                  hovertemplate="<b>Mes:</b> %{x|%b-%Y}<br><b>Cobrado:</b> %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=datos["cobros_vs_credito"]["Mes"], y=datos["cobros_vs_credito"]["Credito_otorgado"],
                                  name="Crédito otorgado", mode="lines+markers",
                                  line=dict(width=2, color=BLANCO, dash="dot"), marker=dict(size=6, color=BLANCO),
                                  hovertemplate="<b>Mes:</b> %{x|%b-%Y}<br><b>Crédito otorgado:</b> %{y:,.0f}<extra></extra>"))
        fig.add_trace(go.Scatter(x=datos["proyeccion"]["Mes"], y=datos["proyeccion"]["Monto_programado"],
                                  name="Cuotas programadas (proyección)", mode="lines",
                                  line=dict(width=2, color=GRIS, dash="dashdot"),
                                  hovertemplate="<b>Mes:</b> %{x|%b-%Y}<br><b>Programado:</b> %{y:,.0f}<extra></extra>"))
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

    tabla_mostrar = tabla_filtrada.rename(columns={"Cliente_id": "Cliente", "Estado": "Estado del crédito"}).copy()
    tabla_mostrar["Saldo"] = tabla_mostrar["Saldo"].map(lambda v: formato_ars(v))
    tabla_mostrar["Saldo vencido"] = tabla_mostrar["Saldo vencido"].map(lambda v: formato_ars(v))

    st.dataframe(
        tabla_mostrar,
        width="stretch", hide_index=True,
        column_config={
            "Días de atraso (máx.)": st.column_config.ProgressColumn(
                format="%d días", min_value=0,
                max_value=int(tabla_filtrada["Días de atraso (máx.)"].max()) if len(tabla_filtrada) else 1,
            ),
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
