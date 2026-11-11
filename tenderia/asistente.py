"""Asistente conversacional de TenderIA (simulación del canal WhatsApp).

El tendero escribe como habla ("vendí 3 leches y media docena de huevos") y el
asistente interpreta la intención, extrae productos y cantidades, actualiza el
inventario y responde. El intérprete es determinista (reglas + coincidencia
aproximada), lo que lo hace auditable y barato; en producción se complementa
con un modelo de lenguaje para los mensajes que las reglas no resuelven.
"""
from __future__ import annotations

import difflib
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

import pandas as pd

from .alertas import generar_alertas
from .credito import calcular_puntaje
from .datos import serie_por_sku
from .inventario import Inventario
from .modelos import MedioPago, Producto, Venta
from .pronostico import PronosticadorDemanda
from .reabastecimiento import calcular_pedido

NUMEROS = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
    "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12, "trece": 13,
    "catorce": 14, "quince": 15, "dieciseis": 16, "veinte": 20, "veinticuatro": 24,
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "par": 2,
}
MULTIPLICADORES = {"docena": 12, "docenas": 12, "cubeta": 30, "cubetas": 30, "canasta": 30,
                   "canastas": 30, "paca": 12, "pacas": 12, "sixpack": 6}

INTENCIONES: list[tuple[str, tuple[str, ...]]] = [
    ("credito", ("credito", "prestamo", "puntaje", "plata prestada", "financiar")),
    ("vencimientos", ("vence", "vencer", "vencen", "caduca", "por vencerse", "por vencer", "se me dana", "se me danan")),
    ("pedido", ("que pido", "que compro", "pedido", "que debo pedir", "que me falta", "surtir", "que encargo")),
    ("resumen", ("como me fue", "resumen", "cuanto vendi", "ventas de hoy", "cierre de caja", "cuadre")),
    ("stock", ("cuanto me queda", "cuanto queda", "cuanto hay", "cuantos me quedan", "cuantas me quedan",
               "me queda", "quedan", "inventario de", "hay de", "tengo de")),
    ("compra", ("compre", "llego", "llegaron", "recibi", "entraron", "me trajeron", "surti", "ingreso", "ingresaron")),
    ("venta", ("vendi", "venta", "se llevaron", "se llevo", "despache", "fie", "fiado", "fiados", "vendimos")),
    ("ayuda", ("ayuda", "hola", "menu", "buenas", "que puedes hacer", "opciones")),
]

PALABRAS_VACIAS = {
    "de", "del", "la", "el", "los", "las", "unos", "unas", "hoy", "a", "en", "me", "se", "y", "con",
    "mas", "al", "que", "por", "para", "fiado", "fiados", "ayer", "otra", "otro", "otras", "otros",
    "vendi", "vendimos", "venta", "llevaron", "llevo", "compre", "llego", "llegaron", "recibi",
    "entraron", "trajeron", "surti", "ingreso", "ingresaron", "despache", "fie", "media", "medio",
    "unidades", "unidad", "u", "paquetes", "paquete", "bolsas", "bolsa", "libras", "libra", "lb",
    "proveedor", "senora", "senor", "vecina", "vecino", "cliente", "don", "dona", "le", "les",
    "acabo", "acabe", "tambien", "pues", "ya", "manana", "tarde", "noche", "nos",
}


def normalizar(texto: str) -> str:
    texto = re.sub(r"[,;\n]+", " y ", texto.lower()).replace("ñ", "n")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


@dataclass
class Interpretacion:
    intencion: str
    items: dict[str, int] = field(default_factory=dict)
    fiado: bool = False
    texto_normalizado: str = ""


class InterpreteMensajes:
    def __init__(self, catalogo: dict[str, Producto]):
        self.catalogo = catalogo
        self.alias: dict[str, str] = {}
        for sku, p in catalogo.items():
            for a in p.alias + (p.nombre,):
                self.alias[normalizar(a)] = sku

    # -------------------------------------------------------------- intención
    def detectar_intencion(self, t: str) -> str:
        for intencion, claves in INTENCIONES:
            if any(re.search(rf"\b{re.escape(c)}\b", t) for c in claves):
                return intencion
        return "desconocida"

    # ---------------------------------------------------------- productos
    def buscar_producto(self, frase: str) -> str | None:
        frase = frase.strip()
        if not frase:
            return None
        if frase in self.alias:
            return self.alias[frase]
        tokens = [t for t in frase.split() if t not in PALABRAS_VACIAS and t not in NUMEROS]
        # bigramas primero ("papel higienico"), luego palabras sueltas
        for n in (2, 1):
            for i in range(len(tokens) - n + 1):
                cand = " ".join(tokens[i:i + n])
                if cand in self.alias:
                    return self.alias[cand]
                for singular in self._singulares(cand):
                    if singular in self.alias:
                        return self.alias[singular]
        for tok in tokens:
            if len(tok) < 3:
                continue
            parecido = difflib.get_close_matches(tok, self.alias.keys(), n=1, cutoff=0.8)
            if parecido:
                return self.alias[parecido[0]]
        return None

    @staticmethod
    def _singulares(palabra: str) -> list[str]:
        """Formas singulares candidatas: arroces->arroz, panes->pan, leches->leche."""
        formas = []
        if palabra.endswith("ces"):
            formas.append(palabra[:-3] + "z")
        if palabra.endswith("es"):
            formas.append(palabra[:-2])
        if palabra.endswith("s"):
            formas.append(palabra[:-1])
        return formas

    @staticmethod
    def _cantidad(tokens: list[str]) -> int | None:
        cantidad = None
        for i, tok in enumerate(tokens):
            if tok.isdigit():
                cantidad = int(tok)
            elif tok in NUMEROS and cantidad is None:
                cantidad = NUMEROS[tok]
            if tok in MULTIPLICADORES:
                base = MULTIPLICADORES[tok]
                previo = tokens[i - 1] if i > 0 else ""
                if previo == "media":
                    return base // 2
                return (cantidad or 1) * base
        return cantidad

    def extraer_items(self, t: str) -> dict[str, int]:
        items: dict[str, int] = {}
        segmentos = []
        for parte in re.split(r"\b(?:y|con|mas|tambien)\b", t):
            # "2 gaseosas 1 agua": un nuevo número abre un nuevo segmento
            segmentos.extend(re.split(r"\s(?=\d)", parte))
        for seg in segmentos:
            tokens = seg.split()
            if not tokens:
                continue
            sku = self.buscar_producto(seg)
            if sku is None:
                continue
            cantidad = self._cantidad(tokens) or 1
            items[sku] = items.get(sku, 0) + cantidad
        return items

    def interpretar(self, texto: str) -> Interpretacion:
        t = normalizar(texto)
        intencion = self.detectar_intencion(t)
        items = self.extraer_items(t) if intencion in ("venta", "compra", "stock") else {}
        if intencion == "desconocida":
            # "3 leches y 2 panes" sin verbo: se asume venta si hay productos
            posibles = self.extraer_items(t)
            if posibles:
                intencion, items = "venta", posibles
        fiado = bool(re.search(r"\b(fiado|fiados|fie)\b", t))
        return Interpretacion(intencion, items, fiado, t)


def _cop(valor: float) -> str:
    return "$" + f"{int(round(valor)):,}".replace(",", ".")


class AsistenteTenderIA:
    """Orquesta inventario, pronóstico, alertas y puntaje detrás del chat."""

    def __init__(self, catalogo: dict[str, Producto], inventario: Inventario,
                 historial: pd.DataFrame, hoy: date):
        self.catalogo = catalogo
        self.inventario = inventario
        self.historial = historial
        self.hoy = hoy
        self.interprete = InterpreteMensajes(catalogo)
        self.ventas_hoy: list[Venta] = []
        self._modelos: dict[str, PronosticadorDemanda] = {}

    # ------------------------------------------------------------ pronósticos
    def modelo(self, sku: str) -> PronosticadorDemanda:
        if sku not in self._modelos:
            self._modelos[sku] = PronosticadorDemanda().ajustar(serie_por_sku(self.historial, sku))
        return self._modelos[sku]

    def demanda_diaria(self) -> dict[str, float]:
        return {sku: float(self.modelo(sku).predecir(1, self.hoy).iloc[0]) for sku in self.catalogo}

    # --------------------------------------------------------------- acciones
    def responder(self, mensaje: str) -> str:
        it = self.interprete.interpretar(mensaje)
        manejador = getattr(self, f"_r_{it.intencion}", self._r_desconocida)
        return manejador(it)

    def _r_venta(self, it: Interpretacion) -> str:
        if not it.items:
            return "No identifiqué los productos. Ejemplo: 'vendí 3 leches y 2 panes'."
        lineas, total = [], 0
        for sku, cant in it.items.items():
            p = self.catalogo[sku]
            vendidas = self.inventario.registrar_venta(sku, cant)
            medio = MedioPago.FIADO if it.fiado else MedioPago.EFECTIVO
            if vendidas:
                self.ventas_hoy.append(Venta(self.hoy, sku, vendidas, p.precio_venta, medio))
            total += vendidas * p.precio_venta
            aviso = "" if vendidas == cant else f" (solo había {vendidas})"
            lineas.append(f"- {vendidas} x {p.nombre} = {_cop(vendidas * p.precio_venta)}{aviso}")
        encabezado = "Venta registrada como FIADO:" if it.fiado else "Venta registrada:"
        return "\n".join([encabezado, *lineas, f"Total: {_cop(total)}"])

    def _r_compra(self, it: Interpretacion) -> str:
        if not it.items:
            return "¿Qué mercancía llegó? Ejemplo: 'llegaron 30 huevos y 12 leches'."
        lineas = []
        for sku, cant in it.items.items():
            lote = self.inventario.registrar_compra(sku, cant, self.hoy)
            p = self.catalogo[sku]
            venc = "" if not p.perecedero else f", vence {lote.fecha_vencimiento:%d/%m}"
            lineas.append(f"- {cant} x {p.nombre}{venc}")
        return "\n".join(["Entrada de mercancía registrada:", *lineas])

    def _r_stock(self, it: Interpretacion) -> str:
        if not it.items:
            return "¿De qué producto? Ejemplo: '¿cuánto arroz me queda?'."
        dd = self.demanda_diaria()
        lineas = []
        for sku in it.items:
            p, stock = self.catalogo[sku], self.inventario.stock(sku)
            dias = stock / dd[sku] if dd[sku] > 0 else float("inf")
            lineas.append(f"{p.nombre}: {stock} u. (alcanza para ~{dias:.1f} días)")
        return "\n".join(lineas)

    def _r_pedido(self, it: Interpretacion) -> str:
        pedidos = []
        for sku, p in self.catalogo.items():
            m = self.modelo(sku)
            revision = p.dias_hasta_proximo_pedido(self.hoy.weekday())
            dem = list(m.predecir(max(p.vida_util_dias, p.lead_time_dias + revision), self.hoy))
            ped = calcular_pedido(p, self.inventario.stock(sku), 0, dem, m.sigma, revision)
            if ped.cantidad > 0:
                pedidos.append(ped)
        if not pedidos:
            return "Tu inventario cubre la demanda esperada. No necesitas pedir hoy."
        pedidos.sort(key=lambda x: -x.costo_estimado)
        lineas = [f"- {x.cantidad} x {x.producto} ({_cop(x.costo_estimado)})" for x in pedidos[:8]]
        total = sum(x.costo_estimado for x in pedidos)
        return "\n".join(["Pedido sugerido para mañana:", *lineas,
                          f"Inversión estimada: {_cop(total)}. ¿Lo envío a tus proveedores aliados?"])

    def _r_vencimientos(self, it: Interpretacion) -> str:
        alertas = generar_alertas(self.inventario, self.hoy, self.demanda_diaria())
        if not alertas:
            return "No tienes productos en riesgo de vencerse en los próximos 3 días."
        return "\n".join(["Productos en riesgo de vencimiento:", *[f"- {a.mensaje}" for a in alertas]])

    def _r_resumen(self, it: Interpretacion) -> str:
        total = sum(v.total for v in self.ventas_hoy)
        fiado = sum(v.total for v in self.ventas_hoy if v.medio_pago == MedioPago.FIADO)
        margen = sum(v.cantidad * self.catalogo[v.sku].margen_unitario for v in self.ventas_hoy)
        return (f"Resumen de hoy: ventas {_cop(total)} en {len(self.ventas_hoy)} registros; "
                f"ganancia bruta {_cop(margen)}; fiado {_cop(fiado)}.")

    def _r_credito(self, it: Interpretacion) -> str:
        diario = self.historial.groupby("fecha")["ingreso"].sum()
        diario.index = pd.DatetimeIndex(diario.index)
        costo = (self.historial["unidades"] * self.historial["sku"].map(
            lambda s: self.catalogo[s].costo)).sum()
        margen = 1 - costo / max(self.historial["ingreso"].sum(), 1)
        r = calcular_puntaje(diario.tail(90), margen)
        return (f"Tu puntaje TenderIA es {r.puntaje} (banda {r.banda}). Con tu autorización, "
                f"podemos compartirlo con aliados de microcrédito. Monto de referencia: {_cop(r.monto_sugerido)}.")

    def _r_ayuda(self, it: Interpretacion) -> str:
        return ("Hola, soy TenderIA. Puedes escribirme o enviarme audios como:\n"
                "- 'vendí 3 leches y 2 panes' | 'fié 2 arroces a doña Rosa'\n"
                "- 'llegaron 30 huevos' | '¿cuánto arroz me queda?'\n"
                "- '¿qué pido mañana?' | '¿qué se me vence?' | '¿cómo me fue hoy?'")

    def _r_desconocida(self, it: Interpretacion) -> str:
        return "No te entendí. Escribe 'ayuda' para ver ejemplos."


def construir_demo(hoy: date | None = None, semilla: int = 11) -> AsistenteTenderIA:
    """Crea una tienda de demostración con 120 días de historia e inventario inicial."""
    from .datos import CATALOGO_POR_SKU, generar_historial

    hoy = hoy or date(2026, 11, 5)
    historial = generar_historial(dias=120, inicio=hoy - timedelta(days=120), semilla=semilla)
    inv = Inventario(CATALOGO_POR_SKU, "FEFO")
    for sku, p in CATALOGO_POR_SKU.items():
        # inventario inicial: dos lotes, uno de ellos cerca del vencimiento en perecederos
        inv.registrar_compra(sku, max(1, int(p.demanda_base * 2)), hoy - timedelta(days=1))
        if p.perecedero:
            # lote sobrecomprado que vence en 2 días: dispara alertas de descuento en la demo
            inv.registrar_compra(sku, max(2, int(p.demanda_base * 3)),
                                 hoy - timedelta(days=p.vida_util_dias - 2))
    return AsistenteTenderIA(CATALOGO_POR_SKU, inv, historial, hoy)
