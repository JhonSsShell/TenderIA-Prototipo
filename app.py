"""Prototipo navegable de TenderIA (Streamlit).

Ejecutar:  streamlit run app.py
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from tenderia.alertas import generar_alertas
from tenderia.asistente import construir_demo
from tenderia.credito import calcular_puntaje
from tenderia.datos import serie_por_sku
from tenderia.finanzas import economia_unitaria, proyectar
from tenderia.reabastecimiento import calcular_pedido

RESULTADOS = Path(__file__).parent / "resultados" / "resumen_resultados.json"
HOY = date(2026, 11, 5)
VERDE = "#0F7B5F"

st.set_page_config(page_title="TenderIA - Prototipo", page_icon="🛒", layout="wide")
st.markdown(f"""
<style>
.burbuja-tendero {{background:#DCF8C6;border-radius:12px;padding:10px 14px;margin:6px 0 6px 18%;
                   white-space:pre-wrap;color:#1b1b1b;font-size:15px}}
.burbuja-bot {{background:#FFFFFF;border:1px solid #e5e5e5;border-radius:12px;padding:10px 14px;
               margin:6px 18% 6px 0;white-space:pre-wrap;color:#1b1b1b;font-size:15px}}
.chat {{background:#ECE5DD;border-radius:14px;padding:14px;}}
.etiqueta {{color:{VERDE};font-weight:700}}
</style>""", unsafe_allow_html=True)

CONVERSACION_INICIAL = ["hola", "vendí 3 leches y media docena de huevos", "fié 2 arroces a doña Rosa",
                        "¿qué se me vence?"]


def _cop(v: float) -> str:
    return "$" + f"{int(round(v)):,}".replace(",", ".")


if "asistente" not in st.session_state:
    a = construir_demo(HOY)
    st.session_state.asistente = a
    st.session_state.chat = [(m, a.responder(m)) for m in CONVERSACION_INICIAL]

a = st.session_state.asistente

with st.sidebar:
    st.markdown(f"## <span class='etiqueta'>TenderIA</span>", unsafe_allow_html=True)
    st.caption("Asistente con IA para tiendas de barrio")
    st.markdown("**Tienda:** Doña Marta - Kennedy, Bogotá  \n**Plan:** Pro (prueba)  \n"
                f"**Fecha:** {HOY:%d/%m/%Y}")
    if st.button("Reiniciar demostración"):
        del st.session_state["asistente"]
        st.rerun()
    st.divider()
    st.caption("Prototipo académico. Datos sintéticos. Actividad 4 - Gestión de Innovación y Emprendimiento.")

st.title("TenderIA · Prototipo funcional")
tab_chat, tab_inv, tab_pron, tab_cred, tab_pil, tab_fin = st.tabs(
    ["Asistente (WhatsApp)", "Inventario y vencimientos", "Pronóstico y pedido",
     "Puntaje de crédito", "Piloto simulado", "Finanzas"])

# ------------------------------------------------------------------ chat
with tab_chat:
    col_chat, col_info = st.columns([3, 2])
    with col_chat:
        html = "".join(f"<div class='burbuja-tendero'>{m}</div><div class='burbuja-bot'>{r}</div>"
                       for m, r in st.session_state.chat)
        st.markdown(f"<div class='chat'>{html}</div>", unsafe_allow_html=True)
        mensaje = st.chat_input("Escribe como lo harías en WhatsApp: 'vendí 2 panes', '¿qué pido mañana?'")
        if mensaje:
            st.session_state.chat.append((mensaje, a.responder(mensaje)))
            st.rerun()
    with col_info:
        st.subheader("Hoy en la tienda")
        total = sum(v.total for v in a.ventas_hoy)
        margen = sum(v.cantidad * a.catalogo[v.sku].margen_unitario for v in a.ventas_hoy)
        c1, c2 = st.columns(2)
        c1.metric("Ventas registradas", _cop(total))
        c2.metric("Ganancia bruta", _cop(margen))
        alertas = generar_alertas(a.inventario, a.hoy, a.demanda_diaria())
        c1.metric("Alertas de vencimiento", len(alertas))
        c2.metric("Valor del inventario", _cop(a.inventario.valor_a_costo()))
        st.info("Prueba: 'llegaron 30 huevos', '¿cuánto arroz me queda?', '¿qué pido mañana?', "
                "'¿cómo me fue hoy?', 'quiero un crédito'.")

# ------------------------------------------------------------- inventario
with tab_inv:
    st.subheader("Existencias por producto")
    dd = a.demanda_diaria()
    filas = []
    for sku, p in a.catalogo.items():
        stock = a.inventario.stock(sku)
        prox = min((l.fecha_vencimiento for l in a.inventario.lotes(sku)), default=None)
        filas.append({"Producto": p.nombre, "Categoría": p.categoria, "Existencias": stock,
                      "Días de cobertura": round(stock / dd[sku], 1) if dd[sku] else None,
                      "Próximo vencimiento": prox if p.perecedero else "-",
                      "Valor a costo": _cop(stock * p.costo)})
    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
    st.subheader("Alertas de vencimiento y descuento sugerido")
    alertas = generar_alertas(a.inventario, a.hoy, dd)
    if alertas:
        st.dataframe(pd.DataFrame([{"Producto": x.producto, "Unidades": x.unidades,
                                    "Vence en (días)": x.dias_para_vencer, "Venta esperada": x.venta_esperada,
                                    "Descuento": f"{x.descuento_pct} %", "Precio sugerido": _cop(x.precio_sugerido)}
                                   for x in alertas]), use_container_width=True, hide_index=True)
    else:
        st.success("Sin productos en riesgo en los próximos 3 días.")

# ------------------------------------------------------------- pronóstico
with tab_pron:
    nombres = {p.nombre: sku for sku, p in a.catalogo.items()}
    elegido = st.selectbox("Producto", list(nombres), index=list(nombres).index("Cerveza lata 330 ml"))
    sku = nombres[elegido]
    p = a.catalogo[sku]
    serie = serie_por_sku(a.historial, sku).tail(56)
    modelo = a.modelo(sku)
    pron = modelo.predecir(14, a.hoy)
    graf = pd.DataFrame({"Ventas reales": serie, "Pronóstico": pron})
    st.line_chart(graf, color=["#9AA5B1", VERDE])
    revision = p.dias_hasta_proximo_pedido(a.hoy.weekday())
    ped = calcular_pedido(p, a.inventario.stock(sku), 0,
                          list(modelo.predecir(max(p.vida_util_dias, p.lead_time_dias + revision), a.hoy)),
                          modelo.sigma, revision)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Existencias", ped.existencias)
    c2.metric("Demanda en cobertura", ped.demanda_cobertura)
    c3.metric("Stock de seguridad", ped.stock_seguridad)
    c4.metric("Pedido sugerido", f"{ped.cantidad} u.", _cop(ped.costo_estimado))
    st.caption(ped.motivo)

# ---------------------------------------------------------------- crédito
with tab_cred:
    diario = a.historial.groupby("fecha")["ingreso"].sum()
    diario.index = pd.DatetimeIndex(diario.index)
    costo = (a.historial["unidades"] * a.historial["sku"].map(lambda s: a.catalogo[s].costo)).sum()
    margen = 1 - costo / a.historial["ingreso"].sum()
    r = calcular_puntaje(diario.tail(90), margen)
    c1, c2, c3 = st.columns(3)
    c1.metric("Puntaje TenderIA", r.puntaje)
    c2.metric("Banda de riesgo", r.banda)
    c3.metric("Monto de referencia", _cop(r.monto_sugerido))
    st.progress((r.puntaje - 300) / 550)
    st.bar_chart(pd.Series(r.componentes, name="Componente (0-1)"), color=VERDE)
    for e in r.explicacion:
        st.write("• " + e)
    st.caption("El puntaje solo se comparte con aliados de microcrédito con autorización expresa del "
               "tendero (Ley 1581 de 2012).")

# ---------------------------------------------------------------- piloto
with tab_pil:
    if RESULTADOS.exists():
        res = json.loads(RESULTADOS.read_text(encoding="utf-8"))
        pil = res["piloto"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Merma perecederos", f"{pil['merma_tenderia']:.2%}",
                  f"{-pil['reduccion_merma_pct']:.0f} % vs. empírico", delta_color="inverse")
        c2.metric("Nivel de servicio", f"{pil['servicio_tenderia']:.1%}",
                  f"{(pil['servicio_tenderia'] - pil['servicio_empirico']) * 100:+.1f} pp")
        c3.metric("Margen neto de merma (90 días)", _cop(pil["margen_tenderia"]),
                  f"+{pil['aumento_margen_pct']:.1f} %")
        c4.metric("Inventario promedio", _cop(pil["inventario_tenderia"]),
                  f"{(pil['inventario_tenderia'] / pil['inventario_empirico'] - 1) * 100:+.0f} %",
                  delta_color="inverse")
        st.dataframe(pd.DataFrame(res["palancas"]).set_index("configuracion"), use_container_width=True)
        st.caption("Simulación de 30 tiendas sintéticas durante 90 días. Resultados sujetos a validación en campo.")
    else:
        st.warning("Ejecuta primero: python ejecutar_pruebas_preliminares.py")

# ---------------------------------------------------------------- finanzas
with tab_fin:
    fin = proyectar()
    anual = fin.anual[["tiendas_activas", "tiendas_pro", "ingresos", "costos", "ebitda"]].copy()
    st.bar_chart(anual[["ingresos", "costos"]] / 1e6, stack=False, color=[VERDE, "#E0A458"])
    anual["tiendas_activas"] = anual["tiendas_activas"].round(0)
    anual["tiendas_pro"] = anual["tiendas_pro"].round(0)
    for c in ("ingresos", "costos", "ebitda"):
        anual[c] = (anual[c] / 1e6).round(1)
    st.dataframe(anual.rename(columns={"ingresos": "Ingresos (M COP)", "costos": "Costos (M COP)",
                                       "ebitda": "EBITDA (M COP)"}), use_container_width=True)
    u = economia_unitaria()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Necesidad de financiación", _cop(fin.necesidad_financiacion))
    c2.metric("Equilibrio operativo", f"Mes {fin.mes_equilibrio}")
    c3.metric("LTV / CAC", f"{u['ltv_cac']:.1f}x")
    c4.metric("TIR (con valor terminal)", f"{fin.tir:.0%}")
