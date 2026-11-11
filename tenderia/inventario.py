"""Control de inventario por lotes.

TenderIA rota los productos con la regla FEFO (First Expired, First Out): se
vende primero lo que vence primero. La gestión empírica suele comportarse como
LIFO en perecederos, porque el cliente elige el producto más fresco y el
tendero acomoda la mercancía nueva adelante.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

import numpy as np

from .modelos import Lote, Producto


class Inventario:
    """Existencias por lotes.

    politica: "FEFO" (vende primero lo que vence primero), "LIFO" (vende lo más
    reciente) o "MIXTA", en la que cada unidad sale por FEFO con probabilidad
    `fraccion_fefo` (el cliente a veces escoge el producto más fresco).
    """

    def __init__(self, catalogo: dict[str, Producto], politica: str = "FEFO",
                 fraccion_fefo: float = 1.0, semilla: int | None = None):
        if politica not in ("FEFO", "LIFO", "MIXTA"):
            raise ValueError("La política debe ser FEFO, LIFO o MIXTA")
        self.catalogo = catalogo
        self.politica = politica
        self.fraccion_fefo = fraccion_fefo
        self._rng = np.random.default_rng(semilla)
        self._lotes: dict[str, list[Lote]] = defaultdict(list)

    # ------------------------------------------------------------------ entradas
    def registrar_compra(self, sku: str, cantidad: int, fecha: date) -> Lote:
        if cantidad <= 0:
            raise ValueError("La cantidad comprada debe ser positiva")
        producto = self.catalogo[sku]
        lote = Lote(sku, cantidad, fecha, fecha + timedelta(days=producto.vida_util_dias))
        self._lotes[sku].append(lote)
        self._lotes[sku].sort(key=lambda l: l.fecha_vencimiento)
        return lote

    # ------------------------------------------------------------------- salidas
    def registrar_venta(self, sku: str, cantidad: int, lote_prioritario: Lote | None = None) -> int:
        """Descarga unidades vendidas. Devuelve las unidades efectivamente vendidas."""
        pendientes = cantidad
        lotes = self._lotes[sku]
        if lote_prioritario is not None and lote_prioritario in lotes:
            usar = min(pendientes, lote_prioritario.cantidad)
            lote_prioritario.cantidad -= usar
            pendientes -= usar
        if self.politica == "MIXTA" and pendientes > 0:
            por_fefo = int(self._rng.binomial(pendientes, self.fraccion_fefo))
            pendientes = self._descargar(lotes, por_fefo, fefo=True) + (pendientes - por_fefo)
            pendientes = self._descargar(lotes, pendientes, fefo=False)
        else:
            pendientes = self._descargar(lotes, pendientes, fefo=self.politica == "FEFO")
        self._lotes[sku] = [l for l in lotes if l.cantidad > 0]
        return cantidad - pendientes

    @staticmethod
    def _descargar(lotes: list[Lote], cantidad: int, fefo: bool) -> int:
        """Descuenta unidades de los lotes en el orden indicado; devuelve lo no atendido."""
        for lote in (lotes if fefo else reversed(lotes)):
            if cantidad == 0:
                break
            usar = min(cantidad, lote.cantidad)
            lote.cantidad -= usar
            cantidad -= usar
        return cantidad

    def retirar_vencidos(self, hoy: date) -> dict[str, int]:
        """Retira lotes vencidos y devuelve las unidades perdidas por SKU (merma)."""
        merma: dict[str, int] = {}
        for sku, lotes in self._lotes.items():
            vencidas = sum(l.cantidad for l in lotes if l.fecha_vencimiento <= hoy)
            if vencidas:
                merma[sku] = vencidas
                self._lotes[sku] = [l for l in lotes if l.fecha_vencimiento > hoy]
        return merma

    # ----------------------------------------------------------------- consultas
    def stock(self, sku: str) -> int:
        return sum(l.cantidad for l in self._lotes[sku])

    def lotes(self, sku: str) -> list[Lote]:
        return list(self._lotes[sku])

    def lotes_por_vencer(self, hoy: date, dias: int = 2) -> list[Lote]:
        return [l for lotes in self._lotes.values() for l in lotes
                if 0 < l.dias_para_vencer(hoy) <= dias and l.cantidad > 0]

    def valor_a_costo(self) -> int:
        return sum(self.catalogo[sku].costo * self.stock(sku) for sku in self._lotes)

    def resumen(self) -> list[dict]:
        return [
            {"sku": sku, "producto": p.nombre, "stock": self.stock(sku),
             "valor_costo": p.costo * self.stock(sku)}
            for sku, p in self.catalogo.items()
        ]
