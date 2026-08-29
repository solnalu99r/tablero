import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

# ============================================================
# Configuración de página y paleta (misma que el notebook: negro/blanco/gris/naranja)
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


def formato_ars(x, decimales=0):
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
        font=dict(color=BLANCO, family="Arial"), title_font=dict(color=BLANCO, family="Arial"),
        legend=legend_final, separators=",.",
        **({"title": titulo_kwargs} if titulo_kwargs is not None else {}), **kwargs,
    )
    fig.update_xaxes(gridcolor="#2B2B2B", zerolinecolor="#2B2B2B", color=BLANCO)
    fig.update_yaxes(gridcolor="#2B2B2B", zerolinecolor="#2B2B2B", color=BLANCO)
    return fig


# ============================================================
# Carga de datos (cacheada: no se vuelve a leer en cada interacción)
# ============================================================
@st.cache_data
def cargar_datos():
    d = {}
    d["kpis"] = pd.read_csv("data/kpis_resumen.csv").iloc[0]
    d["tabla"] = pd.read_csv("data/tabla_clientes.csv")
    d["evolucion"] = pd.read_csv("data/evolucion_credito.csv", parse_dates=["Mes"])
    d["concentracion"] = pd.read_csv("data/concentracion_linea.csv")
    d["mora"] = pd.read_csv("data/mora_distribucion.csv")
    d["composicion"] = pd.read_csv("data/composicion_cuota.csv", parse_dates=["Mes"])
    d["cobros_vs_credito"] = pd.read_csv("data/cobros_vs_credito.csv", parse_dates=["Mes"])
    d["horizonte"] = pd.read_csv("data/horizonte_2029.csv", parse_dates=["Mes"])
    d["alertas"] = pd.read_csv("data/alertas_credito.csv")
    return d


datos = cargar_datos()
kpis = datos["kpis"]

# ============================================================
# Encabezado
# ============================================================
st.title("Tablero de gestión crediticia — Masori")
st.caption("Fintech prendaria de Vaca Muerta · Período de análisis: sep-2025 a sep-2026")

# ============================================================
# Resumen (pantalla principal — tarjetas de KPI, sin scroll)
# ============================================================
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Severidad de mora", f"{kpis['severidad_mora_pct']:.1f}%")
c2.metric("Tasa de aprobación", f"{kpis['tasa_aprobacion_pct']:.1f}%")
c3.metric("Tasa de cobranza", f"{kpis['tasa_cobranza_pct']:.1f}%")
c4.metric("Capital pendiente (prom.)", f"{kpis['ratio_pendiente_promedio']:.1f}%")
c5.metric("Tasa de refinanciación", f"{kpis['tasa_refinanciacion_pct']:.1f}%")

c6, c7, c8, c9 = st.columns(4)
c6.metric(f"Concentración top 1 ({kpis['concentracion_top1_nombre']})", f"{kpis['concentracion_top1_pct']:.1f}%")
c7.metric("Clientes con cuotas impagas", f"{int(kpis['clientes_con_cuotas_impagas'])}")
c8.metric("Última variación de caja", formato_ars(kpis["ultima_variacion_caja"]))
c9.metric("Créditos con alerta de dato", f"{int(kpis['creditos_con_alerta'])}",
          delta="Revisar" if kpis["creditos_con_alerta"] > 0 else "OK",
          delta_color="inverse" if kpis["creditos_con_alerta"] > 0 else "normal")

st.divider()

# ============================================================
# Pestañas de detalle
# ============================================================
tab_cartera, tab_mora, tab_cobranza, tab_tabla = st.tabs(
    ["📊 Cartera", "⚠️ Mora", "💰 Cobranza", "🗂️ Tabla operativa"]
)

# ---------- CARTERA ----------
with tab_cartera:
    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(datos["concentracion"], values="monto_pct", names="Linea de crédito",
                     color_discrete_sequence=PALETA_CATEGORICA)
        fig.update_traces(hovertemplate="<b>%{label}</b><br>%{value:.1f}% del monto<extra></extra>")
        tema_oscuro(fig, title=dict(text="Cartera por línea de crédito (% del monto)"), height=420)
        st.plotly_chart(fig, width="stretch")

    with col2:
        fig = go.Figure()
        for i, linea in enumerate(datos["evolucion"]["Linea de crédito"].unique()):
            sub = datos["evolucion"][datos["evolucion"]["Linea de crédito"] == linea]
            color = PALETA_CATEGORICA[i % len(PALETA_CATEGORICA)]
            fig.add_trace(go.Scatter(x=sub["Mes"], y=sub["Monto"], name=linea, mode="lines",
                                      stackgroup="cartera", line=dict(width=0.5, color=color), fillcolor=color))
        tema_oscuro(fig, title=dict(text="Origen mensual de crédito, por línea"), height=420,
                    xaxis=dict(title="Mes"), yaxis=dict(title="Monto", tickformat=",.0f"))
        st.plotly_chart(fig, width="stretch")

    fig = go.Figure()
    for i, linea in enumerate(datos["horizonte"]["Linea de crédito"].unique()):
        sub = datos["horizonte"][datos["horizonte"]["Linea de crédito"] == linea]
        color = PALETA_CATEGORICA[i % len(PALETA_CATEGORICA)]
        fig.add_trace(go.Scatter(x=sub["Mes"], y=sub["Monto"], name=linea, mode="lines",
                                  stackgroup="cuotas", line=dict(width=0.5, color=color), fillcolor=color))
    fecha_corte = pd.Timestamp("2026-09-30")
    fig.add_shape(type="line", xref="x", yref="paper", x0=fecha_corte, x1=fecha_corte, y0=0, y1=1,
                  line=dict(color=BLANCO, dash="dash"))
    fig.add_annotation(x=fecha_corte, y=1, xref="x", yref="paper", text="Fin período de análisis",
                        showarrow=False, yanchor="bottom", font=dict(color=BLANCO))
    tema_oscuro(fig, title=dict(text="Horizonte completo de vencimientos (hasta 2029)"), height=420,
                xaxis=dict(title="Mes"), yaxis=dict(title="Monto de cuotas", tickformat=",.0f"))
    st.plotly_chart(fig, width="stretch")

# ---------- MORA ----------
with tab_mora:
    col1, col2 = st.columns(2)
    colores_mora = {
        "Normal": BLANCO, "Mora temprana": NARANJA_CLARO, "Mora media": NARANJA,
        "Mora tardia": NARANJA_OSCURO, "Incobrable": "#7C2D12", "Mora preventiva": GRIS,
    }

    with col1:
        m = datos["mora"].sort_values("cantidad_pct")
        fig = go.Figure(go.Bar(
            x=m["cantidad_pct"], y=m["Estado de mora"], orientation="h",
            marker_color=[colores_mora.get(e, GRIS) for e in m["Estado de mora"]],
            text=[f"{v:.1f}%" for v in m["cantidad_pct"]], textposition="outside",
        ))
        tema_oscuro(fig, title=dict(text="Cuotas por estado de mora (% cantidad)"), height=420,
                    xaxis=dict(title="% de cuotas"))
        st.plotly_chart(fig, width="stretch")

    with col2:
        m2 = datos["mora"].sort_values("monto_pct")
        fig = go.Figure(go.Bar(
            x=m2["monto_pct"], y=m2["Estado de mora"], orientation="h",
            marker_color=[colores_mora.get(e, GRIS) for e in m2["Estado de mora"]],
            text=[f"{v:.1f}%" for v in m2["monto_pct"]], textposition="outside",
        ))
        tema_oscuro(fig, title=dict(text="Cuotas por estado de mora (% saldo)"), height=420,
                    xaxis=dict(title="% del saldo"))
        st.plotly_chart(fig, width="stretch")

    st.warning(
        f"⚠️ 'Mora preventiva' concentra {m2.set_index('Estado de mora').loc['Mora preventiva', 'monto_pct']:.1f}% "
        f"del saldo con apenas {m.set_index('Estado de mora').loc['Mora preventiva', 'cantidad_pct']:.1f}% de las cuotas "
        "— pocas cuotas, pero de mucho peso en plata."
    )

# ---------- COBRANZA ----------
with tab_cobranza:
    col1, col2 = st.columns(2)

    with col1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=datos["cobros_vs_credito"]["Mes"], y=datos["cobros_vs_credito"]["Cobrado"],
                                  name="Cobrado (confirmado)", mode="lines+markers",
                                  line=dict(width=2, color=NARANJA, dash="dash"), marker=dict(size=7, color=NARANJA)))
        fig.add_trace(go.Scatter(x=datos["cobros_vs_credito"]["Mes"], y=datos["cobros_vs_credito"]["Credito_otorgado"],
                                  name="Crédito otorgado", mode="lines+markers",
                                  line=dict(width=2, color=BLANCO, dash="dot"), marker=dict(size=7, color=BLANCO)))
        tema_oscuro(fig, title=dict(text="Cobros confirmados vs. Crédito otorgado"), height=420,
                    xaxis=dict(title="Mes"), yaxis=dict(title="Monto", tickformat=",.0f"))
        st.plotly_chart(fig, width="stretch")

    with col2:
        colores_comp = {"Capital": BLANCO, "Interés": NARANJA, "Cargo": GRIS, "Impuesto": NARANJA_CLARO}
        fig = go.Figure(data=[
            go.Bar(name=col, x=datos["composicion"]["Mes"], y=datos["composicion"][col], marker_color=colores_comp[col])
            for col in ["Capital", "Interés", "Cargo", "Impuesto"]
        ])
        tema_oscuro(fig, barmode="stack", title=dict(text="Composición mensual de la cuota"), height=420,
                    xaxis=dict(title="Mes"), yaxis=dict(title="Monto", tickformat=",.0f"))
        st.plotly_chart(fig, width="stretch")

# ---------- TABLA OPERATIVA ----------
with tab_tabla:
    st.markdown("Los encabezados de columna son clickeables para ordenar (nativo de Streamlit).")
    col1, col2 = st.columns(2)
    with col1:
        estado_sel = st.selectbox("Estado del crédito", ["Todos"] + sorted(datos["tabla"]["Estado"].dropna().unique().tolist()))
    with col2:
        impagas_sel = st.selectbox("¿Tiene cuotas impagas?", ["Todos", "Sí", "No"])

    tabla_filtrada = datos["tabla"].copy()
    if estado_sel != "Todos":
        tabla_filtrada = tabla_filtrada[tabla_filtrada["Estado"] == estado_sel]
    if impagas_sel != "Todos":
        tabla_filtrada = tabla_filtrada[tabla_filtrada["Tiene cuotas impagas"] == impagas_sel]

    st.dataframe(
        tabla_filtrada.rename(columns={"Cliente_id": "Cliente", "Estado": "Estado del crédito"}),
        width="stretch", hide_index=True,
    )

    if len(datos["alertas"]) > 0:
        st.markdown("### Créditos marcados para revisar (calidad de dato)")
        st.dataframe(datos["alertas"], width="stretch", hide_index=True)
