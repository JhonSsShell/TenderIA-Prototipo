"""Pronóstico de demanda diaria por producto.

Modelo: suavizamiento exponencial simple sobre la serie desestacionalizada,
con índices multiplicativos de día de la semana y de quincena (Hyndman y
Athanasopoulos, 2021). Es liviano, explicable al tendero y funciona con pocas
semanas de historia, condición típica de una tienda que recién se digitaliza.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd

from .datos import es_quincena

DIAS_QUINCENA = (15, 16, 17, 30, 31, 1, 2)


@dataclass
class ResultadoBacktest:
    wape_modelo: float
    wape_ingenuo: float

    @property
    def mejora_pct(self) -> float:
        if self.wape_ingenuo == 0:
            return 0.0
        return (1 - self.wape_modelo / self.wape_ingenuo) * 100


class PronosticadorDemanda:
    def __init__(self, alpha: float = 0.10, semanas_estacionalidad: int = 12):
        self.alpha = alpha
        self.semanas = semanas_estacionalidad
        self.nivel: float = 0.0
        self.indices_semana = np.ones(7)
        self.indice_quincena = 1.0
        self.sigma: float = 0.0
        self.ultima_fecha: date | None = None

    # ------------------------------------------------------------------ ajuste
    def ajustar(self, serie: pd.Series) -> "PronosticadorDemanda":
        if len(serie) < 14:
            raise ValueError("Se requieren al menos 14 días de historia")
        y = serie.to_numpy(dtype=float)
        idx = pd.DatetimeIndex(serie.index)
        dia_sem = idx.day_of_week.to_numpy()
        quincena = np.isin(idx.day.to_numpy(), DIAS_QUINCENA)
        n = min(len(y), 7 * self.semanas)
        yv, dv, qv = y[-n:], dia_sem[-n:], quincena[-n:]
        # índice de quincena
        if qv.any() and (~qv).any():
            self.indice_quincena = float(np.clip(yv[qv].mean() / max(yv[~qv].mean(), 1e-9), 0.8, 1.5))
        # índices de día de la semana (sobre la serie sin efecto quincena)
        ajustada = yv / np.where(qv, self.indice_quincena, 1.0)
        media = max(ajustada.mean(), 1e-9)
        indices = np.array([ajustada[dv == d].mean() / media if (dv == d).any() else 1.0 for d in range(7)])
        self.indices_semana = np.where(np.isfinite(indices) & (indices > 0.05), indices, 1.0)
        # nivel por suavizamiento exponencial sobre la serie desestacionalizada
        factores = self.indices_semana[dia_sem] * np.where(quincena, self.indice_quincena, 1.0)
        y_des = y / factores
        nivel = y_des[0]
        errores = np.empty(len(y) - 1)
        for t in range(1, len(y)):
            errores[t - 1] = y[t] - nivel * factores[t]
            nivel = self.alpha * y_des[t] + (1 - self.alpha) * nivel
        self.nivel = float(nivel)
        self.sigma = float(np.std(errores[-56:])) if len(errores) else 0.0
        self.ultima_fecha = idx[-1].date()
        return self

    def _factor(self, d: date) -> float:
        return self.indices_semana[d.weekday()] * (self.indice_quincena if es_quincena(d) else 1.0)

    # --------------------------------------------------------------- pronóstico
    def predecir(self, horizonte: int, desde: date | None = None) -> pd.Series:
        desde = desde or (self.ultima_fecha + timedelta(days=1))
        fechas = [desde + timedelta(days=i) for i in range(horizonte)]
        valores = [max(self.nivel * self._factor(f), 0.0) for f in fechas]
        return pd.Series(valores, index=pd.DatetimeIndex(fechas), name="pronostico")

    # ----------------------------------------------------------------- backtest
    @staticmethod
    def backtest(serie: pd.Series, dias_prueba: int = 28, horizonte: int = 1) -> ResultadoBacktest:
        """Evaluación rodante a un día vs. el método ingenuo (promedio 7 días)."""
        reales, pred_modelo, pred_ingenuo = [], [], []
        for corte in range(len(serie) - dias_prueba, len(serie) - horizonte + 1):
            entrenamiento = serie.iloc[:corte]
            modelo = PronosticadorDemanda().ajustar(entrenamiento)
            p = modelo.predecir(horizonte).iloc[-1]
            reales.append(serie.iloc[corte + horizonte - 1])
            pred_modelo.append(p)
            pred_ingenuo.append(entrenamiento.iloc[-7:].mean())
        reales = np.array(reales, dtype=float)
        total = reales.sum() or 1e-9
        wape_m = np.abs(reales - np.array(pred_modelo)).sum() / total
        wape_i = np.abs(reales - np.array(pred_ingenuo)).sum() / total
        return ResultadoBacktest(float(wape_m), float(wape_i))
