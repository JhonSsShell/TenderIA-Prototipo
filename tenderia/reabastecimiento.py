"""Pedido sugerido (política de revisión periódica con nivel objetivo).

Nivel objetivo S = demanda pronosticada en (L + R) + z * sigma * sqrt(L + R)
Pedido = max(0, S - existencias - pedidos en tránsito), redondeado a la unidad
de compra del proveedor (paca, canasta, cubeta).

Para perecederos se limita el pedido a lo que razonablemente se venderá antes
del vencimiento (tope por vida útil) y se redondea hacia abajo cuando no hay
riesgo de agotado: son las dos palancas principales contra la merma.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .modelos import Producto

Z_NIVEL_SERVICIO = {0.90: 1.28, 0.95: 1.645, 0.975: 1.96}


@dataclass
class PedidoSugerido:
    sku: str
    producto: str
    existencias: int
    demanda_cobertura: float
    stock_seguridad: float
    cantidad: int
    costo_estimado: int
    motivo: str


def calcular_pedido(producto: Producto, existencias: int, en_transito: int,
                    demanda_diaria: list[float], sigma: float,
                    revision_dias: int = 1, nivel_servicio: float = 0.95) -> PedidoSugerido:
    cobertura = producto.lead_time_dias + revision_dias
    demanda_cob = float(sum(demanda_diaria[:cobertura]))
    z = Z_NIVEL_SERVICIO.get(nivel_servicio, 1.645)
    ss = z * sigma * math.sqrt(cobertura)
    if producto.perecedero:
        # no más de lo vendible antes del vencimiento (con margen del 10 %)
        vendible = 0.9 * float(sum(demanda_diaria[:producto.vida_util_dias]))
        ss = min(ss, max(vendible - demanda_cob, 0.0))
    objetivo = demanda_cob + ss
    neto = objetivo - existencias - en_transito
    m = max(producto.multiplo_compra, 1)
    if neto <= 0:
        cantidad = 0
    elif producto.perecedero:
        abajo = math.floor(neto / m) * m
        cubre = abajo + existencias + en_transito >= demanda_cob
        cantidad = abajo if cubre else math.ceil(neto / m) * m
    else:
        cantidad = math.ceil(neto / m) * m
    motivo = "Cobertura de {:.0f} día(s) + seguridad {:.0f} u., múltiplo {}".format(cobertura, ss, m)
    if producto.perecedero:
        motivo += " (tope por vida útil)"
    return PedidoSugerido(producto.sku, producto.nombre, existencias, round(demanda_cob, 1),
                          round(ss, 1), cantidad, cantidad * producto.costo, motivo)
