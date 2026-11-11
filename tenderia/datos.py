"""Catálogo base y generador de historiales de venta sintéticos.

Los datos son sintéticos (no provienen de tiendas reales). Se construyen con
patrones documentados del canal tradicional: picos de fin de semana, efecto
quincena (días de pago) y alta variabilidad diaria (proceso de Poisson).
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from .modelos import Producto

# Índices de estacionalidad semanal (lunes=0 ... domingo=6)
PERFILES_SEMANA: dict[str, list[float]] = {
    "general": [0.90, 0.90, 0.95, 1.00, 1.12, 1.25, 0.98],
    "bebidas": [0.70, 0.70, 0.80, 0.90, 1.30, 1.70, 1.40],
    "desayuno": [1.05, 1.00, 1.00, 1.00, 1.00, 1.05, 1.20],
}

FACTOR_QUINCENA = 1.15  # días 15-17 y 30-2: mayor liquidez de los hogares


TODOS = (0, 1, 2, 3, 4, 5, 6)
LUN_SAB = (0, 1, 2, 3, 4, 5)


def _p(sku, nombre, cat, pv, costo, per, vida, lead, base, alias, perfil="general", multiplo=1, dias=TODOS):
    return Producto(sku, nombre, cat, pv, costo, per, vida, lead, base, tuple(alias), perfil, multiplo, dias)


# Precios de referencia COP 2026 (aproximados, con fines de simulación).
# multiplo = unidad de compra al proveedor; dias = días de visita/compra (0 = lunes).
CATALOGO: list[Producto] = [
    # Perecederos
    _p("LEC01", "Leche entera 1 L", "Lácteos", 4800, 4000, True, 7, 1, 14, ["leche", "leches"], "desayuno", 6, LUN_SAB),
    _p("PAN01", "Pan tajado 500 g", "Panadería", 6500, 5300, True, 6, 1, 5, ["pan", "panes", "pan tajado"], "desayuno", 5, TODOS),
    _p("HUE01", "Huevo AA (unidad)", "Huevos", 600, 470, True, 21, 1, 60, ["huevo", "huevos"], "desayuno", 30, (0, 2, 4)),
    _p("ARE01", "Arepas x5", "Panadería", 3500, 2700, True, 8, 1, 6, ["arepa", "arepas"], "desayuno", 5, TODOS),
    _p("QUE01", "Queso campesino 250 g", "Lácteos", 6000, 4700, True, 10, 1, 4, ["queso", "quesos"], "desayuno", 4, LUN_SAB),
    _p("YOG01", "Yogur 200 g", "Lácteos", 2800, 2100, True, 15, 1, 6, ["yogur", "yogurt", "yogures", "kumis"], "general", 6, LUN_SAB),
    _p("TOM01", "Tomate (libra)", "Fruver", 2600, 1800, True, 6, 1, 8, ["tomate", "tomates"], "general", 10, (1, 4)),
    _p("PAP01", "Papa pastusa (libra)", "Fruver", 1500, 1000, True, 20, 1, 10, ["papa", "papas"], "general", 25, (1, 4)),
    _p("PLA01", "Plátano (unidad)", "Fruver", 1200, 800, True, 8, 1, 12, ["platano", "plátano", "platanos", "plátanos"], "general", 10, (1, 4)),
    _p("SAL01", "Salchichón 250 g", "Carnes frías", 5200, 4100, True, 25, 2, 3, ["salchichon", "salchichón"], "general", 6, (2,)),
    # No perecederos
    _p("ARR01", "Arroz 500 g", "Granos", 2600, 2100, False, 365, 2, 12, ["arroz"], "general", 25, (1,)),
    _p("ACE01", "Aceite 1 L", "Abarrotes", 11500, 9600, False, 365, 2, 3, ["aceite", "aceites"], "general", 12, (1,)),
    _p("AZU01", "Azúcar 1 kg", "Abarrotes", 4600, 3800, False, 365, 2, 4, ["azucar", "azúcar"], "general", 10, (1,)),
    _p("PNL01", "Panela 500 g", "Abarrotes", 3200, 2500, False, 180, 2, 4, ["panela", "panelas"], "general", 12, (1,)),
    _p("CAF01", "Café molido 250 g", "Abarrotes", 9800, 8000, False, 365, 2, 2, ["cafe", "café", "tinto"], "general", 12, (1,)),
    _p("GAS01", "Gaseosa 1,5 L", "Bebidas", 5500, 4300, False, 180, 1, 10, ["gaseosa", "gaseosas", "cocacola", "coca"], "bebidas", 6, (0, 3)),
    _p("CER01", "Cerveza lata 330 ml", "Bebidas", 3200, 2500, False, 180, 1, 18, ["cerveza", "cervezas", "pola", "polas"], "bebidas", 24, (0, 3)),
    _p("AGU01", "Agua 600 ml", "Bebidas", 1800, 1100, False, 365, 1, 8, ["agua", "aguas", "botella de agua"], "bebidas", 24, (0, 3)),
    _p("GAL01", "Galletas paquete", "Pasabocas", 2000, 1500, False, 180, 2, 7, ["galleta", "galletas"], "general", 12, (1,)),
    _p("ATU01", "Atún lata 160 g", "Enlatados", 7200, 5900, False, 720, 2, 2, ["atun", "atún"], "general", 12, (1,)),
    _p("JAB01", "Jabón en barra", "Aseo", 3000, 2300, False, 720, 2, 2, ["jabon", "jabón", "jabones"], "general", 6, (1,)),
    _p("PHG01", "Papel higiénico x4", "Aseo", 7500, 6100, False, 720, 2, 2, ["papel", "papel higienico", "papel higiénico"], "general", 12, (1,)),
    _p("FRI01", "Fríjol 500 g", "Granos", 5500, 4500, False, 365, 2, 2, ["frijol", "fríjol", "frijoles", "fríjoles"], "general", 12, (1,)),
    _p("PAS01", "Pasta 250 g", "Granos", 1900, 1450, False, 365, 2, 5, ["pasta", "pastas", "espagueti", "espaguetis"], "general", 12, (1,)),
]

CATALOGO_POR_SKU: dict[str, Producto] = {p.sku: p for p in CATALOGO}


def es_quincena(d: date) -> bool:
    return d.day in (15, 16, 17, 30, 31, 1, 2)


def demanda_esperada(producto: Producto, d: date, escala: float = 1.0, tendencia_diaria: float = 0.0,
                     dia_indice: int = 0) -> float:
    """Demanda media esperada de un producto en una fecha dada."""
    estacional = PERFILES_SEMANA[producto.perfil][d.weekday()]
    quincena = FACTOR_QUINCENA if es_quincena(d) else 1.0
    tendencia = 1.0 + tendencia_diaria * dia_indice
    return producto.demanda_base * escala * estacional * quincena * tendencia


K_TRAFICO = 16.0   # choque diario común (clima, eventos): CV ~ 25 %
K_PRODUCTO = 12.0  # sobredispersión propia de cada producto (binomial negativa)


def choque_trafico(rng: np.random.Generator) -> float:
    return float(rng.gamma(K_TRAFICO, 1 / K_TRAFICO))


def muestrear_demanda(rng: np.random.Generator, mu: float) -> int:
    """Demanda con sobredispersión (mezcla gamma-Poisson = binomial negativa)."""
    if mu <= 0:
        return 0
    return int(rng.poisson(rng.gamma(K_PRODUCTO, mu / K_PRODUCTO)))


def generar_historial(dias: int = 180, inicio: date | None = None, escala: float = 1.0,
                      semilla: int = 7, tendencia_diaria: float = 0.0005,
                      catalogo: list[Producto] | None = None) -> pd.DataFrame:
    """Genera ventas diarias sintéticas (demanda no censurada) por SKU.

    Devuelve un DataFrame con columnas: fecha, sku, unidades, precio, ingreso.
    """
    catalogo = catalogo or CATALOGO
    rng = np.random.default_rng(semilla)
    inicio = inicio or date(2026, 1, 1)
    filas = []
    for i in range(dias):
        d = inicio + timedelta(days=i)
        choque = choque_trafico(rng)
        for p in catalogo:
            mu = demanda_esperada(p, d, escala, tendencia_diaria, i) * choque
            unidades = muestrear_demanda(rng, mu)
            filas.append((pd.Timestamp(d), p.sku, unidades, p.precio_venta, unidades * p.precio_venta))
    return pd.DataFrame(filas, columns=["fecha", "sku", "unidades", "precio", "ingreso"])


def serie_por_sku(historial: pd.DataFrame, sku: str) -> pd.Series:
    s = historial[historial["sku"] == sku].set_index("fecha")["unidades"].sort_index()
    s.index = pd.DatetimeIndex(s.index)
    return s.asfreq("D", fill_value=0)
