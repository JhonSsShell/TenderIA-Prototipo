"""Alertas de vencimiento y descuento dinámico para perecederos."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .inventario import Inventario


@dataclass
class AlertaVencimiento:
    sku: str
    producto: str
    unidades: int
    dias_para_vencer: int
    venta_esperada: float
    descuento_pct: int
    precio_sugerido: int
    mensaje: str


def descuento_sugerido(dias: int, exceso_ratio: float) -> int:
    """Descuento escalonado: más cerca del vencimiento y más exceso, mayor descuento."""
    if exceso_ratio <= 0:
        return 0
    base = {1: 30, 2: 20, 3: 10}.get(dias, 0)
    if exceso_ratio > 0.5:
        base += 10
    return min(base, 40)


def generar_alertas(inventario: Inventario, hoy: date, demanda_diaria: dict[str, float],
                    horizonte_dias: int = 3) -> list[AlertaVencimiento]:
    alertas = []
    for lote in sorted(inventario.lotes_por_vencer(hoy, horizonte_dias), key=lambda l: l.fecha_vencimiento):
        p = inventario.catalogo[lote.sku]
        dias = lote.dias_para_vencer(hoy)
        venta_esperada = demanda_diaria.get(lote.sku, 0.0) * dias
        exceso = lote.cantidad - venta_esperada
        ratio = exceso / lote.cantidad if lote.cantidad else 0
        desc = descuento_sugerido(dias, ratio)
        if desc == 0:
            continue
        precio = int(round(p.precio_venta * (1 - desc / 100), -2))
        msg = (f"{p.nombre}: {lote.cantidad} u. vencen en {dias} día(s). "
               f"Se esperan vender {venta_esperada:.0f}. Sugerencia: {desc}% de descuento "
               f"(${precio:,} c/u) y ubicar al frente del exhibidor.").replace(",", ".")
        alertas.append(AlertaVencimiento(p.sku, p.nombre, lote.cantidad, dias, round(venta_esperada, 1),
                                         desc, precio, msg))
    return alertas
