"""Piloto simulado: gestión empírica vs. gestión asistida por TenderIA.

Diseño del experimento (in silico):
- N tiendas sintéticas heterogéneas (escala de demanda log-normal).
- 28 días de calentamiento + D días de evaluación, revisión diaria de pedidos.
- Misma demanda (misma semilla) para ambos escenarios: solo cambia la gestión.

Escenario EMPÍRICO (línea base, prácticas habituales del canal tradicional):
- Pide "lo de siempre" el día que pasa el proveedor: promedio de ventas de
  los últimos 7 días x (L + R), con sobrecompra de perecederos (sesgo 1,25)
  para "no quedarse sin", redondeado hacia arriba a la paca/canasta.
- Rotación mixta: la mitad de las unidades sale por FEFO y la otra mitad por
  LIFO (el cliente escoge el producto más fresco).
- Sin alertas de vencimiento ni descuentos.

Escenario TENDERIA:
- Pedido sugerido con pronóstico estacional + stock de seguridad + tope por
  vida útil (ver reabastecimiento.py). Adherencia parcial: el tendero sigue la
  sugerencia el 70 % de las veces; el resto pide "lo de siempre".
- Rotación guiada (75 % de las unidades por FEFO) y alerta con descuento del
  25 % al lote que vence mañana: ese lote se vende primero con descuento
  (canibaliza venta a precio lleno) y atrae una demanda adicional del 10 %.

Los resultados dependen de estos supuestos y deben validarse en campo.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .datos import CATALOGO, CATALOGO_POR_SKU, choque_trafico, demanda_esperada, muestrear_demanda
from .inventario import Inventario
from .pronostico import PronosticadorDemanda
from .reabastecimiento import calcular_pedido

SESGO_SOBRECOMPRA = 1.25
DESCUENTO_ALERTA = 0.25
ELASTICIDAD_DESCUENTO = 0.10  # demanda incremental por el descuento (fracción de la demanda base)
ADHERENCIA = 0.70             # el tendero acepta la sugerencia de pedido 7 de cada 10 veces
FEFO_EMPIRICO = 0.50          # mitad de las unidades salen por FEFO (el cliente escoge lo fresco)
FEFO_TENDERIA = 0.75          # la alerta de rotación mejora el acomodo, pero no es perfecta

PALANCAS = ("pedido", "rotacion", "descuento")

# Peso aproximado por unidad de venta (kg), para expresar la merma en alimento perdido
PESO_KG = {"LEC01": 1.03, "PAN01": 0.50, "HUE01": 0.06, "ARE01": 0.40, "QUE01": 0.25,
           "YOG01": 0.20, "TOM01": 0.50, "PAP01": 0.50, "PLA01": 0.30, "SAL01": 0.25}


@dataclass
class Metricas:
    unidades_demandadas: int = 0
    unidades_vendidas: int = 0
    unidades_vencidas: int = 0
    unidades_vendidas_perecederas: int = 0
    unidades_demandadas_perecederas: int = 0
    unidades_compradas_perecederas: int = 0
    ingresos: float = 0.0
    costo_ventas: float = 0.0
    costo_merma: float = 0.0
    inventario_promedio_costo: float = 0.0
    kg_vencidos: float = 0.0
    dias: int = 0

    @property
    def merma_pct_perecederos(self) -> float:
        base = self.unidades_vendidas_perecederas + self.unidades_vencidas
        return self.unidades_vencidas / base if base else 0.0

    @property
    def nivel_servicio(self) -> float:
        return self.unidades_vendidas / self.unidades_demandadas if self.unidades_demandadas else 0.0

    @property
    def ventas_perdidas(self) -> int:
        return self.unidades_demandadas - self.unidades_vendidas

    @property
    def margen_neto_merma(self) -> float:
        return self.ingresos - self.costo_ventas - self.costo_merma


def _simular_tienda(escenario: str, escala: float, semilla: int, inicio: date,
                    dias_eval: int, calentamiento: int = 28,
                    palancas: tuple[str, ...] | None = None) -> Metricas:
    """palancas: funcionalidades de TenderIA activas (por defecto todas en 'tenderia')."""
    if palancas is None:
        palancas = PALANCAS if escenario == "tenderia" else ()
    rng = np.random.default_rng(semilla)               # demanda: idéntica en ambos escenarios
    rng_desc = np.random.default_rng(semilla + 10_000)  # respuesta al descuento (solo TenderIA)
    inv = Inventario(CATALOGO_POR_SKU, "MIXTA", semilla=semilla + 20_000,
                     fraccion_fefo=FEFO_TENDERIA if "rotacion" in palancas else FEFO_EMPIRICO)
    historia: dict[str, list[int]] = {p.sku: [] for p in CATALOGO}
    fechas: list[pd.Timestamp] = []
    transito: dict[str, list[tuple[date, int]]] = {p.sku: [] for p in CATALOGO}
    m = Metricas()
    total_dias = calentamiento + dias_eval

    # inventario inicial: 3 días de demanda base
    for p in CATALOGO:
        inv.registrar_compra(p.sku, math.ceil(p.demanda_base * escala * 3), inicio - timedelta(days=1))

    for i in range(total_dias):
        hoy = inicio + timedelta(days=i)
        evaluando = i >= calentamiento
        fechas.append(pd.Timestamp(hoy))
        # 1) llegan pedidos
        for p in CATALOGO:
            llegan = [q for (f, q) in transito[p.sku] if f == hoy]
            transito[p.sku] = [(f, q) for (f, q) in transito[p.sku] if f != hoy]
            for q in llegan:
                if q > 0:
                    inv.registrar_compra(p.sku, q, hoy)
                    if evaluando and p.perecedero:
                        m.unidades_compradas_perecederas += q
        # 2) ventas del día (choque de tráfico común + sobredispersión por producto)
        choque = choque_trafico(rng)
        for p in CATALOGO:
            demanda = muestrear_demanda(rng, demanda_esperada(p, hoy, escala, 0.0005, i) * choque)
            lote_desc = None
            if "descuento" in palancas and p.perecedero:
                por_vencer = [l for l in inv.lotes(p.sku) if l.dias_para_vencer(hoy) == 1]
                lote_desc = por_vencer[0] if por_vencer else None
            if lote_desc is None:
                vendidas = inv.registrar_venta(p.sku, demanda)
                extra_vendidas, ingreso = 0, vendidas * p.precio_venta
            else:
                # alerta + descuento: el lote que vence mañana se exhibe al frente con
                # descuento; canibaliza parte de la venta normal y atrae demanda adicional
                en_lote = lote_desc.cantidad
                vendidas = inv.registrar_venta(p.sku, demanda, lote_prioritario=lote_desc)
                con_descuento = min(en_lote, vendidas)
                incremental = int(rng_desc.poisson(p.demanda_base * escala * ELASTICIDAD_DESCUENTO))
                extra_vendidas = 0
                if lote_desc.cantidad > 0 and incremental > 0:
                    extra_vendidas = inv.registrar_venta(p.sku, min(incremental, lote_desc.cantidad),
                                                         lote_prioritario=lote_desc)
                precio_desc = p.precio_venta * (1 - DESCUENTO_ALERTA)
                ingreso = ((vendidas - con_descuento) * p.precio_venta
                           + (con_descuento + extra_vendidas) * precio_desc)
            historia[p.sku].append(vendidas)
            if evaluando:
                m.unidades_demandadas += demanda + extra_vendidas
                m.unidades_vendidas += vendidas + extra_vendidas
                m.ingresos += ingreso
                m.costo_ventas += (vendidas + extra_vendidas) * p.costo
                if p.perecedero:
                    m.unidades_demandadas_perecederas += demanda + extra_vendidas
                    m.unidades_vendidas_perecederas += vendidas + extra_vendidas
        # 3) cierre: retiro de vencidos
        merma = inv.retirar_vencidos(hoy + timedelta(days=1))
        if evaluando:
            for sku, q in merma.items():
                m.unidades_vencidas += q
                m.kg_vencidos += q * PESO_KG.get(sku, 0.5)
                m.costo_merma += q * CATALOGO_POR_SKU[sku].costo
            m.inventario_promedio_costo += inv.valor_a_costo()
            m.dias += 1
        # 4) decisión de pedido (solo en días de visita del proveedor)
        for p in CATALOGO:
            if hoy.weekday() not in p.dias_pedido:
                continue
            en_transito = sum(q for _, q in transito[p.sku])
            stock = inv.stock(p.sku)
            revision = p.dias_hasta_proximo_pedido(hoy.weekday())
            cobertura = p.lead_time_dias + revision
            sigue_sugerencia = rng_desc.random() < ADHERENCIA
            if "pedido" not in palancas or len(historia[p.sku]) < 14 or not sigue_sugerencia:
                prom = np.mean(historia[p.sku][-7:]) if historia[p.sku] else p.demanda_base * escala
                sesgo = SESGO_SOBRECOMPRA if p.perecedero else 1.10
                neto = prom * cobertura * sesgo - stock - en_transito
                cantidad = 0 if neto <= 0 else math.ceil(neto / p.multiplo_compra) * p.multiplo_compra
            else:
                serie = pd.Series(historia[p.sku], index=pd.DatetimeIndex(fechas))
                modelo = PronosticadorDemanda().ajustar(serie.iloc[-84:])
                horizonte = max(p.vida_util_dias, cobertura)
                dem = list(modelo.predecir(horizonte, hoy + timedelta(days=1)))
                cantidad = calcular_pedido(p, stock, en_transito, dem, modelo.sigma, revision).cantidad
            if cantidad > 0:
                transito[p.sku].append((hoy + timedelta(days=p.lead_time_dias), cantidad))
    m.inventario_promedio_costo /= max(m.dias, 1)
    return m


def correr_piloto(n_tiendas: int = 30, dias_eval: int = 90, semilla: int = 2026,
                  inicio: date = date(2026, 3, 2)) -> pd.DataFrame:
    rng = np.random.default_rng(semilla)
    escalas = np.clip(rng.lognormal(0.0, 0.35, n_tiendas), 0.5, 2.2)
    filas = []
    for t, escala in enumerate(escalas):
        for escenario in ("empirico", "tenderia"):
            m = _simular_tienda(escenario, float(escala), semilla + t, inicio, dias_eval)
            filas.append({
                "tienda": f"T{t + 1:02d}", "escenario": escenario, "escala": round(float(escala), 2),
                "merma_pct_perecederos": m.merma_pct_perecederos,
                "nivel_servicio": m.nivel_servicio,
                "ventas_perdidas_u": m.ventas_perdidas,
                "unidades_vencidas": m.unidades_vencidas, "kg_vencidos": m.kg_vencidos,
                "ingresos": m.ingresos, "costo_merma": m.costo_merma,
                "margen_neto_merma": m.margen_neto_merma,
                "inventario_promedio_costo": m.inventario_promedio_costo,
            })
    return pd.DataFrame(filas)


def resumen_piloto(df: pd.DataFrame) -> pd.DataFrame:
    agg = df.groupby("escenario").agg(
        merma_pct_perecederos=("merma_pct_perecederos", "mean"),
        nivel_servicio=("nivel_servicio", "mean"),
        ventas_perdidas_u=("ventas_perdidas_u", "mean"),
        unidades_vencidas=("unidades_vencidas", "mean"),
        kg_vencidos=("kg_vencidos", "mean"),
        costo_merma=("costo_merma", "mean"),
        ingresos=("ingresos", "mean"),
        margen_neto_merma=("margen_neto_merma", "mean"),
        inventario_promedio_costo=("inventario_promedio_costo", "mean"),
    )
    return agg.T


def analisis_palancas(n_tiendas: int = 12, dias_eval: int = 90, semilla: int = 2026,
                      inicio: date = date(2026, 3, 2)) -> pd.DataFrame:
    """Contribución de cada funcionalidad a la reducción de merma (análisis por palanca)."""
    rng = np.random.default_rng(semilla)
    escalas = np.clip(rng.lognormal(0.0, 0.35, n_tiendas), 0.5, 2.2)
    configuraciones = {
        "Empírico (línea base)": (),
        "Solo pedido sugerido": ("pedido",),
        "Solo rotación FEFO guiada": ("rotacion",),
        "Solo alerta + descuento": ("descuento",),
        "TenderIA completo": PALANCAS,
    }
    filas = []
    for nombre, palancas in configuraciones.items():
        ms = [_simular_tienda("tenderia" if palancas else "empirico", float(e), semilla + t, inicio,
                              dias_eval, palancas=palancas) for t, e in enumerate(escalas)]
        filas.append({"configuracion": nombre,
                      "merma_pct_perecederos": float(np.mean([m.merma_pct_perecederos for m in ms])),
                      "nivel_servicio": float(np.mean([m.nivel_servicio for m in ms])),
                      "margen_neto_merma": float(np.mean([m.margen_neto_merma for m in ms])),
                      "inventario_promedio_costo": float(np.mean([m.inventario_promedio_costo for m in ms]))})
    return pd.DataFrame(filas).set_index("configuracion")
