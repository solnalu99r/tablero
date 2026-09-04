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
