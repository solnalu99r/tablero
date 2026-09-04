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
    ["Resumen general", "Monitoreo de cartera", "Tabla operativa", "Documentación"]
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
        de mora, composición de la cuota y otorgamiento frente al horizonte de vencimientos. Todos los
        gráficos y tarjetas responden al rango de fechas seleccionado arriba a la derecha. En "Tabla
        operativa" se puede consultar el detalle por cliente, filtrable por estado y por cuotas impagas.
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
    fechas_disponibles = pd.concat([
        datos["credito_detalle"]["Fecha"],
        datos["cuotas_detalle"]["Fecha de vencimiento"],
        datos["cobros_detalle"]["Fecha de cobro"],
    ]).dropna()
    fecha_min, fecha_max = fechas_disponibles.min().date(), fechas_disponibles.max().date()

    col_titulo, col_slider = st.columns([3, 2])
    with col_slider:
        fecha_desde, fecha_hasta = st.slider(
            "Rango de fechas",
            min_value=fecha_min, max_value=fecha_max,
            value=(fecha_min, fecha_max), format="MMM YYYY",
        )
    fecha_desde, fecha_hasta = pd.Timestamp(fecha_desde), pd.Timestamp(fecha_hasta)

    # --- filtrado del detalle segun el rango elegido ---
    credito_f = datos["credito_detalle"][
        (datos["credito_detalle"]["Fecha"] >= fecha_desde) & (datos["credito_detalle"]["Fecha"] <= fecha_hasta)
    ]
    cuotas_f = datos["cuotas_detalle"][
        (datos["cuotas_detalle"]["Fecha de vencimiento"] >= fecha_desde) & (datos["cuotas_detalle"]["Fecha de vencimiento"] <= fecha_hasta)
    ]
    cobros_f = datos["cobros_detalle"][
        (datos["cobros_detalle"]["Fecha de cobro"] >= fecha_desde) & (datos["cobros_detalle"]["Fecha de cobro"] <= fecha_hasta)
    ]

    # --- KPIs recalculados sobre el rango filtrado ---
    resueltos_f = credito_f[credito_f["Estado"] != "Borrador"]
    aprobados_f = resueltos_f[resueltos_f["Estado"].isin(ESTADOS_OTORGADOS)]
    tasa_aprobacion_f = len(aprobados_f) / len(resueltos_f) * 100 if len(resueltos_f) else 0

    monto_cuotas_f = cuotas_f["Cuota - Monto"].sum()
    total_cobrado_f = cobros_f[cobros_f["Estado"] == "Confirmado"]["Monto a cobrar"].sum()
    tasa_cobranza_f = total_cobrado_f / monto_cuotas_f * 100 if monto_cuotas_f else 0
    monto_pendiente_f = monto_cuotas_f - total_cobrado_f

    mora_saldo_f = cuotas_f.groupby("Estado de mora")["Cuota - Saldo"].sum()
    pct_en_mora_f = (mora_saldo_f[mora_saldo_f.index != "Normal"].sum() / mora_saldo_f.sum() * 100) if mora_saldo_f.sum() else 0

    k1, k2, k3, k4, k5, k6 = st.columns([1, 1, 1, 1.5, 1.5, 1.5])
    k1.metric("Tasa de aprobación", f"{tasa_aprobacion_f:.1f}%")
    k2.metric("Tasa de cobranza", f"{tasa_cobranza_f:.1f}%")
    k3.metric("% de cartera en mora", f"{pct_en_mora_f:.1f}%")
    k4.metric("Monto de cuotas", formato_ars(monto_cuotas_f))
    k5.metric("Total cobrado", formato_ars(total_cobrado_f))
    k6.metric("Pendiente de cobro", formato_ars(monto_pendiente_f))

    #st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        concentracion_f = credito_f.groupby("Linea de crédito").agg(
            monto=("Monto", "sum"), cantidad=("Monto", "count")
        ).reset_index().sort_values("monto", ascending=False)
        fig = go.Figure(go.Pie(
            labels=concentracion_f["Linea de crédito"], values=concentracion_f["monto"],
            marker=dict(colors=PALETA_CATEGORICA, line=dict(color=FONDO, width=2)),
            customdata=concentracion_f[["monto", "cantidad"]],
            opacity=0.75,
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
        estado_f = credito_f.groupby("Estado").agg(
            monto=("Monto", "sum"), cantidad=("Monto", "count")
        ).reset_index().sort_values("monto")
        colores_estado = {
            "Acreditado": BLANCO, "Pagado": GRIS, "Refinanciado": NARANJA,
            "Pre-cancelado": GRIS_CLARO, "Borrador": NARANJA_CLARO, "Rechazado": NARANJA_OSCURO,
        }
        fig = go.Figure(go.Bar(
            x=estado_f["monto"], y=estado_f["Estado"], orientation="h",
            marker=dict(color=[colores_estado.get(e, GRIS) for e in estado_f["Estado"]], opacity=0.75, line=dict(width=0)),
            customdata=estado_f["cantidad"],
            hovertemplate="<b>%{y}</b><br>Monto: %{x:,.0f}<br>Cantidad: %{customdata} créditos<extra></extra>",
        ))
        tema_oscuro(fig, title=dict(text="Créditos por estado: monto y cantidad"), height=ALTURA_CHICA, xaxis=dict(title="Monto"))
        st.plotly_chart(fig, width="stretch")

    with col3:
        mora_f = cuotas_f.groupby("Estado de mora").agg(
            monto=("Cuota - Saldo", "sum"), cantidad=("Cuota - Saldo", "count")
        ).reset_index().sort_values("monto")
        colores_mora = {
            "Normal": BLANCO, "Mora temprana": NARANJA_CLARO, "Mora media": NARANJA,
            "Mora tardia": NARANJA_OSCURO, "Incobrable": "#7C2D12", "Mora preventiva": GRIS,
        }
        fig = go.Figure(go.Bar(
            x=mora_f["monto"], y=mora_f["Estado de mora"], orientation="h",
            marker=dict(color=[colores_mora.get(e, GRIS) for e in mora_f["Estado de mora"]], opacity=0.75, line=dict(width=0)),
            customdata=mora_f["cantidad"],
            hovertemplate="<b>%{y}</b><br>Saldo: %{x:,.0f}<br>Cantidad: %{customdata} cuotas<extra></extra>",
        ))
        tema_oscuro(fig, title=dict(text="Cuotas por estado de mora: saldo y cantidad"), height=ALTURA_CHICA, xaxis=dict(title="Saldo"))
        st.plotly_chart(fig, width="stretch")

    col4, col5 = st.columns(2)

    with col4:
        comp_total = cuotas_f[["Capital", "Interés", "Cargo", "Impuesto"]].sum()
        total_facturado = comp_total.sum()

        etiquetas_comp = ["Capital", "+ Interés", "+ Cargo", "+ Impuesto", "Total facturado"]
        valores_comp = [comp_total["Capital"], comp_total["Interés"], comp_total["Cargo"], comp_total["Impuesto"], total_facturado]
        colores_comp_barras = [GRIS_CLARO, NARANJA, GRIS_OSCURO, NARANJA_CLARO, BLANCO]
        bases_comp = [0, comp_total["Capital"], comp_total["Capital"] + comp_total["Interés"],
                      comp_total["Capital"] + comp_total["Interés"] + comp_total["Cargo"], 0]

        fig = go.Figure(go.Bar(
            x=etiquetas_comp, y=valores_comp, base=bases_comp,
            marker=dict(color=colores_comp_barras, opacity=0.75, line=dict(width=0)),
            hovertemplate="%{x}: " + "%{y:,.0f}<extra></extra>",
        ))
        tema_oscuro(fig, height=260,
            title=dict(text="Composición de cuota: de Capital a Total"),
            yaxis=dict(title="Monto", tickformat=",.0f"),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")

    with col5:
        def hex_a_rgba(color_hex, alpha):
            color_hex = color_hex.lstrip("#")
            r, g, b = int(color_hex[0:2], 16), int(color_hex[2:4], 16), int(color_hex[4:6], 16)
            return f"rgba({r},{g},{b},{alpha})"

        NEON_CALIDO = ["#FF4500", "#E63946", "#FF7F50", "#FF9E00"]
        NEON_FRIO   = ["#00E5FF", "#FFFFFF", "#D1D5DB", "#6B7280"]

        evolucion_wide = datos["evolucion_credito"].pivot(index="Mes", columns="Linea de crédito", values="Monto").fillna(0)
        horizonte_wide = datos["horizonte_2029"].pivot(index="Mes", columns="Linea de crédito", values="Monto").fillna(0)
        evolucion_wide = evolucion_wide[(evolucion_wide.index >= fecha_desde) & (evolucion_wide.index <= fecha_hasta)]
        horizonte_wide = horizonte_wide[(horizonte_wide.index >= fecha_desde) & (horizonte_wide.index <= fecha_hasta)]

        fig = go.Figure()

        def agregar_serie(x, y, color, stackgroup):
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines", stackgroup=stackgroup, showlegend=False,
                line=dict(width=2, color=color), fillcolor=hex_a_rgba(color, 0.35),
                hovertemplate="%{x|%b-%Y}: %{y:,.0f}<extra></extra>",
            ))

        colores_otorgado = {}
        for i, linea in enumerate(evolucion_wide.columns):
            color = NEON_CALIDO[i % len(NEON_CALIDO)]
            colores_otorgado[linea] = color
            agregar_serie(evolucion_wide.index, evolucion_wide[linea], color, "otorgado")

        colores_vencimiento = {}
        for i, linea in enumerate(horizonte_wide.columns):
            color = NEON_FRIO[i % len(NEON_FRIO)]
            colores_vencimiento[linea] = color
            agregar_serie(horizonte_wide.index, horizonte_wide[linea], color, "vencimientos")

        fecha_corte = evolucion_wide.index.max() if len(evolucion_wide) else fecha_hasta
        fig.add_shape(
            type="line", xref="x", yref="paper",
            x0=fecha_corte, x1=fecha_corte, y0=0, y1=1,
            line=dict(color=BLANCO, dash="dash"),
        )

        tema_oscuro(fig, height=260,
            title=dict(text="Otorgamiento vs. horizonte de vencimientos"),
            xaxis=dict(title="Mes", tickformat="%b-%Y"),
            yaxis=dict(title="Monto", tickformat=",.0f"),
            showlegend=False,
        )
        st.plotly_chart(fig, width="stretch")

        filas_tabla = max(len(colores_vencimiento), len(colores_otorgado))
        items_venc = list(colores_vencimiento.items())
        items_otor = list(colores_otorgado.items())

        filas_html = ""
        for i in range(filas_tabla):
            venc = f'<span style="color:{items_venc[i][1]}">⬤</span> {items_venc[i][0]}' if i < len(items_venc) else ""
            otor = f'<span style="color:{items_otor[i][1]}">⬤</span> {items_otor[i][0]}' if i < len(items_otor) else ""
            filas_html += f"<tr><td style='padding:2px 8px;'>{venc}</td><td style='padding:2px 8px;'>{otor}</td></tr>"

        st.markdown(
            f"""
            <table style="width:100%; font-size:13px; color:{BLANCO};">
                <tr><th style="text-align:left; padding:2px 8px;">Vencimiento</th><th style="text-align:left; padding:2px 8px;">Otorgado</th></tr>
                {filas_html}
            </table>
            """,
            unsafe_allow_html=True,
        )

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
    st.markdown('<h2 style="font-size:22px; margin-top:0; margin-bottom:0.2rem;">Indicadores clave de performance</h2>', unsafe_allow_html=True)

    indicadores = [
        {
            "nombre": "Tasa de aprobación",
            "descripcion": "Refleja el porcentaje de solicitudes de crédito aprobadas en relación con el total de solicitudes resueltas en el período seleccionado.",
            "calculo": "(Cantidad de créditos en Acreditado, Pagado, Refinanciado o Pre-cancelado / Cantidad de solicitudes resueltas, excluye Borrador) * 100.",
        },
        {
            "nombre": "Tasa de cobranza",
            "descripcion": "Indica qué proporción del monto total de cuotas (capital, interés, cargo e impuesto) ya fue efectivamente cobrada.",
            "calculo": "(Monto cobrado en cobros Confirmado / Monto total de cuotas) * 100.",
        },
        {
            "nombre": "% de cartera en mora",
            "descripcion": "Mide la proporción del saldo de cuotas que se encuentra en cualquier estado de mora, respecto del saldo total de cuotas.",
            "calculo": "(Saldo de cuotas en estados de mora distintos de Normal / Saldo total de cuotas) * 100.",
        },
    ]

    fila1 = st.columns(2)
    fila2 = st.columns(2)
    posiciones = fila1 + fila2

    for pos, ind in zip(posiciones, indicadores):
        with pos:
            with st.container(border=True):
                st.markdown(f"**{ind['nombre']}**")
                st.markdown(f"**Descripción:** {ind['descripcion']}")
                st.markdown(f"**Cálculo:** {ind['calculo']}")

    st.markdown('<h2 style="font-size:22px; margin-top:0; margin-bottom:0.2rem;">Fuente de datos y variables</h2>', unsafe_allow_html=True)
    st.markdown(
        """
        **Variables de la tabla operativa:**
        - **Cliente:** identificador anonimizado del cliente (no es el nombre real).
        - **Estado del crédito:** Acreditado, Pagado, Refinanciado, Pre-cancelado, Borrador o Rechazado.
        - **Saldo:** capital pendiente de pago del cliente.
        - **Saldo vencido:** porción del saldo que ya venció sin pagarse.
        - **Cuotas impagas:** cantidad de cuotas vencidas sin pago registrado.
        - **Días de atraso (máx.):** mayor cantidad de días de atraso entre las cuotas impagas del cliente.
        """
    )
