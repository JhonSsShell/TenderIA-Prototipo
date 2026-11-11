"""Entidades del dominio de TenderIA."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class MedioPago(str, Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    FIADO = "fiado"


@dataclass(frozen=True)
class Producto:
    """Referencia del catálogo de la tienda."""

    sku: str
    nombre: str
    categoria: str
    precio_venta: int          # COP por unidad
    costo: int                 # COP por unidad
    perecedero: bool
    vida_util_dias: int        # días desde que ingresa hasta que vence
    lead_time_dias: int        # días que tarda el proveedor en entregar
    demanda_base: float        # unidades/día de una tienda típica
    alias: tuple[str, ...] = ()
    perfil: str = "general"    # perfil de estacionalidad semanal
    multiplo_compra: int = 1   # el proveedor vende por paca/canasta/cubeta
    dias_pedido: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6)  # días de visita del proveedor (0=lunes)

    def dias_hasta_proximo_pedido(self, dia_semana: int) -> int:
        """Periodo de revisión R: días hasta la siguiente oportunidad de pedido."""
        for k in range(1, 8):
            if (dia_semana + k) % 7 in self.dias_pedido:
                return k
        return 7

    @property
    def margen_unitario(self) -> int:
        return self.precio_venta - self.costo

    @property
    def margen_pct(self) -> float:
        return self.margen_unitario / self.precio_venta


@dataclass
class Lote:
    """Unidades de un producto que ingresaron el mismo día."""

    sku: str
    cantidad: int
    fecha_ingreso: date
    fecha_vencimiento: date

    def dias_para_vencer(self, hoy: date) -> int:
        return (self.fecha_vencimiento - hoy).days


@dataclass(frozen=True)
class Venta:
    fecha: date
    sku: str
    cantidad: int
    precio_unitario: int
    medio_pago: MedioPago = MedioPago.EFECTIVO

    @property
    def total(self) -> int:
        return self.cantidad * self.precio_unitario


@dataclass
class Tienda:
    """Tienda de barrio usuaria de TenderIA."""

    id: str
    nombre: str
    propietario: str
    ciudad: str
    plan: str = "Básico"       # Básico (gratuito) | Pro
    ventas: list[Venta] = field(default_factory=list)
