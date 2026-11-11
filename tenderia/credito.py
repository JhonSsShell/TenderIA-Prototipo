"""Puntaje alternativo de crédito a partir del historial transaccional.

Uso ilustrativo: TenderIA no presta dinero. El puntaje se comparte, con
autorización expresa del tendero (Ley 1581 de 2012), con entidades aliadas de
microcrédito como señal complementaria a su propio análisis de riesgo.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

PESOS = {"regularidad": 0.30, "estabilidad": 0.25, "tendencia": 0.15, "margen": 0.15, "recaudo_fiado": 0.15}

BANDAS = [(750, "A"), (680, "B"), (600, "C"), (520, "D"), (0, "E")]
FACTOR_MONTO = {"A": 2.0, "B": 1.5, "C": 1.0, "D": 0.5, "E": 0.0}


@dataclass
class PuntajeCredito:
    puntaje: int
    banda: str
    componentes: dict[str, float]
    monto_sugerido: int
    explicacion: list[str]


def calcular_puntaje(ventas_diarias: pd.Series, margen_bruto_pct: float,
                     recaudo_fiado_pct: float = 0.9) -> PuntajeCredito:
    """ventas_diarias: ingresos diarios (COP) indexados por fecha; 0 = sin registro."""
    v = ventas_diarias.astype(float)
    regularidad = float((v > 0).mean())
    semanal = v.resample("W").sum()
    semanal = semanal[semanal > 0]
    cv = float(semanal.std() / semanal.mean()) if len(semanal) > 1 and semanal.mean() > 0 else 1.0
    estabilidad = float(np.clip(1 - cv, 0, 1))
    if len(semanal) >= 4:
        x = np.arange(len(semanal))
        pendiente = np.polyfit(x, semanal.values, 1)[0] / semanal.mean()
    else:
        pendiente = 0.0
    tendencia = float(np.clip((pendiente + 0.05) / 0.10, 0, 1))   # -5 %..+5 % semanal -> 0..1
    margen = float(np.clip(margen_bruto_pct / 0.30, 0, 1))
    recaudo = float(np.clip(recaudo_fiado_pct, 0, 1))
    comp = {"regularidad": regularidad, "estabilidad": estabilidad, "tendencia": tendencia,
            "margen": margen, "recaudo_fiado": recaudo}
    indice = sum(PESOS[k] * comp[k] for k in PESOS)
    puntaje = int(round(300 + 550 * indice))
    banda = next(b for limite, b in BANDAS if puntaje >= limite)
    utilidad_mensual = v.tail(30).sum() * margen_bruto_pct
    monto = int(round(utilidad_mensual * FACTOR_MONTO[banda], -4))
    explicacion = [
        f"Registra ventas el {regularidad:.0%} de los días",
        f"Variación semanal de ventas: {cv:.0%}",
        f"Tendencia semanal: {pendiente:+.1%}",
        f"Margen bruto estimado: {margen_bruto_pct:.0%}",
        f"Recaudo de fiados: {recaudo:.0%}",
    ]
    return PuntajeCredito(puntaje, banda, {k: round(c, 3) for k, c in comp.items()}, monto, explicacion)
