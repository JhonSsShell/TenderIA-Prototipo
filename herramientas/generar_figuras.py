"""Genera todas las figuras del informe y la presentación (UML, negocio y finanzas).

Uso:  python herramientas/generar_figuras.py
Salida: ../imagenes/*.png  (carpeta Actividad4_TenderIA/imagenes)
Requiere haber ejecutado antes:  python ejecutar_pruebas_preliminares.py
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from tenderia.finanzas import proyectar  # noqa: E402

SALIDA = RAIZ.parent / "imagenes"
SALIDA.mkdir(exist_ok=True)
RES = json.loads((RAIZ / "resultados" / "resumen_resultados.json").read_text(encoding="utf-8"))

# Paleta validada (scripts/validate_palette.js: PASS en modo claro)
VERDE, AMBAR, AZUL, LADRILLO = "#0F7B5F", "#C27C0E", "#2F5DA8", "#B5473A"
TINTA, TINTA2, GRIS, REJILLA = "#1B2B26", "#4A5A55", "#8A9893", "#E3E8E6"
T_VERDE, T_AMBAR, T_AZUL, T_LADRILLO, T_GRIS = "#E6F2EE", "#F8EEDC", "#E6EDF7", "#F6E5E2", "#F3F5F4"
FONDO = "#FFFFFF"

plt.rcParams.update({
    "font.family": "Arial", "font.size": 10, "text.color": TINTA, "axes.labelcolor": TINTA2,
    "axes.edgecolor": GRIS, "xtick.color": TINTA2, "ytick.color": TINTA2, "axes.titleweight": "bold",
    "axes.titlesize": 12, "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
})


# =============================================================== utilidades
def lienzo(ancho, alto, w_in, h_in):
    fig, ax = plt.subplots(figsize=(w_in, h_in))
    ax.set_xlim(0, ancho)
    ax.set_ylim(0, alto)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def guardar(fig, nombre):
    ruta = SALIDA / nombre
    fig.savefig(ruta, dpi=220, bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("  ✓", ruta.name)


def envolver(texto, ancho):
    return "\n".join(textwrap.fill(p, ancho) if p else "" for p in texto.split("\n"))


def caja(ax, x, y, w, h, texto="", fc=T_GRIS, ec=GRIS, fs=9, bold=False, color=TINTA, radio=0.08,
         ha="center", va="center", lw=1.1, ancho_txt=None, ls="-", z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={radio}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=z))
    if texto:
        if ancho_txt:
            texto = envolver(texto, ancho_txt)
        tx = x + w / 2 if ha == "center" else x + 0.12
        ty = y + h / 2 if va == "center" else y + h - 0.12
        ax.text(tx, ty, texto, ha=ha, va=va, fontsize=fs, fontweight="bold" if bold else "normal",
                color=color, zorder=z + 1, linespacing=1.25)


def flecha(ax, x1, y1, x2, y2, color=TINTA2, ls="-", lw=1.2, estilo="-|>", texto=None, fs=8,
           desp=(0, 0.12), rad=0.0, z=1, ms=12):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=estilo, color=color, lw=lw,
                                 linestyle=ls, mutation_scale=ms, connectionstyle=f"arc3,rad={rad}",
                                 zorder=z, shrinkA=0, shrinkB=0))
    if texto:
        ax.text((x1 + x2) / 2 + desp[0], (y1 + y2) / 2 + desp[1], texto, ha="center", va="bottom",
                fontsize=fs, color=color, zorder=z + 2,
                bbox=dict(boxstyle="round,pad=0.15", fc=FONDO, ec="none", alpha=0.9))


def actor(ax, x, y, nombre, s=1.0, ancho=14):
    ax.add_patch(Circle((x, y + 0.62 * s), 0.14 * s, fc=FONDO, ec=TINTA, lw=1.4, zorder=3))
    ax.plot([x, x], [y + 0.48 * s, y + 0.12 * s], color=TINTA, lw=1.4, zorder=3)
    ax.plot([x - 0.22 * s, x + 0.22 * s], [y + 0.36 * s, y + 0.36 * s], color=TINTA, lw=1.4, zorder=3)
    ax.plot([x, x - 0.18 * s], [y + 0.12 * s, y - 0.18 * s], color=TINTA, lw=1.4, zorder=3)
    ax.plot([x, x + 0.18 * s], [y + 0.12 * s, y - 0.18 * s], color=TINTA, lw=1.4, zorder=3)
    ax.text(x, y - 0.3 * s, envolver(nombre, ancho), ha="center", va="top", fontsize=8.5, fontweight="bold")


def titulo_fig(ax, x, y, texto, fs=12):
    ax.text(x, y, texto, ha="left", va="top", fontsize=fs, fontweight="bold", color=TINTA)


# ======================================================= 1. metodología
def fig_metodologia():
    fig, ax = lienzo(16, 6.0, 9.4, 3.53)
    etapas = [("1. Empatizar", "Investigación secundaria,\nproto-personas y\nmapa de empatía", T_VERDE),
              ("2. Definir", "Punto de vista y\npregunta “¿Cómo\npodríamos…?”", T_VERDE),
              ("3. Idear", "Lluvia de ideas,\nSCAMPER y matriz\nimpacto-esfuerzo", T_AMBAR),
              ("4. Prototipar", "MVP en Python:\nasistente, pronóstico,\nalertas y puntaje", T_AMBAR),
              ("5. Probar", "Pruebas unitarias,\ncorpus conversacional\ny piloto simulado", T_AZUL)]
    x0, w, gap = 0.2, 3.0, 0.15
    for i, (t, d, c) in enumerate(etapas):
        x = x0 + i * (w + gap)
        pts = [(x, 2.75), (x + w - 0.35, 2.75), (x + w, 4.0), (x + w - 0.35, 5.25), (x, 5.25), (x + 0.35, 4.0)]
        if i == 0:
            pts[5] = (x, 4.0)
        ax.add_patch(Polygon(pts, closed=True, fc=c, ec=GRIS, lw=1.0))
        ax.text(x + w / 2 + 0.05, 4.82, t, ha="center", va="center", fontsize=9.5, fontweight="bold")
        ax.text(x + w / 2 + 0.05, 3.62, d, ha="center", va="center", fontsize=7.6, color=TINTA2, linespacing=1.25)
    ax.text(0.2, 5.95, "Design Thinking: comprender el problema y diseñar la solución correcta", fontsize=10,
            fontweight="bold", va="top")
    ax.text(0.2, 2.35, "Lean Startup: construir · medir · aprender (Ries, 2011)", fontsize=10, fontweight="bold",
            va="top")
    caja(ax, 0.9, 0.35, 3.9, 1.2, "Construir\nMVP mínimo y medible", T_GRIS, GRIS, fs=8.2)
    caja(ax, 6.05, 0.35, 3.9, 1.2, "Medir\nmerma, servicio, retención\ny disposición a pagar", T_GRIS, GRIS, fs=8.0)
    caja(ax, 11.2, 0.35, 3.9, 1.2, "Aprender\npivotar o perseverar\nsegún métricas", T_GRIS, GRIS, fs=8.2)
    flecha(ax, 4.85, 0.95, 6.0, 0.95, color=VERDE, lw=1.8)
    flecha(ax, 10.0, 0.95, 11.15, 0.95, color=VERDE, lw=1.8)
    ruta(ax, [(15.1, 0.95), (15.65, 0.95), (15.65, 0.12), (2.85, 0.12), (2.85, 0.35)], color=VERDE, ls="--",
         lw=1.3)
    ax.text(9.0, 0.17, "nuevo ciclo con lo aprendido", fontsize=7.4, color=VERDE, ha="center", va="bottom",
            bbox=dict(boxstyle="round,pad=0.1", fc=FONDO, ec="none"))
    guardar(fig, "fig01_metodologia.png")


# ================================================ 2. mercado TAM/SAM/SOM
def fig_mercado():
    fig, ax = lienzo(12, 7, 7.6, 4.43)
    ax.add_patch(Circle((3.6, 3.5), 3.3, fc=T_VERDE, ec=VERDE, lw=1.3))
    ax.add_patch(Circle((3.6, 2.55), 2.3, fc="#C6E3D9", ec=VERDE, lw=1.3))
    ax.add_patch(Circle((3.6, 1.5), 1.25, fc=VERDE, ec=VERDE, lw=1.3))
    ax.text(3.6, 6.25, "TAM", ha="center", fontsize=13, fontweight="bold", color=VERDE)
    ax.text(3.6, 4.35, "SAM", ha="center", fontsize=13, fontweight="bold", color=VERDE)
    ax.text(3.6, 1.65, "SOM", ha="center", fontsize=13, fontweight="bold", color="white")
    ax.text(3.6, 1.15, "año 5", ha="center", fontsize=9, color="white")
    textos = [
        (6.6, "TAM · 453.750 tiendas de barrio en Colombia",
         "≈ COP 162.800 millones/año a precio Pro (COP 358.800/año)\nFuente: NielsenIQ citado en La República (2025)"),
        (4.3, "SAM · ≈ 204.000 tiendas urbanas digitalizables",
         "Supuesto: 45 % ubicadas en las 5 principales áreas\nmetropolitanas, con smartphone y WhatsApp\n≈ COP 73.300 millones/año"),
        (1.9, "SOM · 34.000 tiendas activas en 2031",
         "16,7 % del SAM; 10.600 en plan Pro\nIngresos proyectados: COP 6.238 millones (2031)"),
    ]
    for y, t, d in textos:
        ax.plot([6.1, 7.05], [y - 0.05, y - 0.05], color=GRIS, lw=1)
        ax.text(7.15, y + 0.15, t, fontsize=10, fontweight="bold", va="bottom")
        ax.text(7.15, y + 0.05, d, fontsize=8.6, color=TINTA2, va="top", linespacing=1.3)
    guardar(fig, "fig02_mercado_tam_sam_som.png")


# =========================================== 3. mapa de posicionamiento
def fig_competencia():
    fig, ax = plt.subplots(figsize=(7.4, 4.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axhline(5, color=REJILLA, lw=1.2, zorder=0)
    ax.axvline(5, color=REJILLA, lw=1.2, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("Inteligencia predictiva  →\n(de registrar datos a recomendar decisiones)", fontsize=9.5)
    ax.set_ylabel("Facilidad de adopción para el tendero  →\n(canal conocido, sin app nueva ni hardware)", fontsize=9.5)
    jugadores = [
        ("Cuaderno y memoria\ndel tendero", 0.9, 8.6, GRIS),
        ("Apps de registro y\nfiado (p. ej., Treinta)", 3.0, 6.5, AZUL),
        ("Pagos y datáfonos\n(p. ej., Bold)", 2.2, 4.6, AZUL),
        ("Abastecimiento B2B\n(p. ej., Chiper)", 4.3, 5.7, AZUL),
        ("POS y facturación\n(p. ej., Siigo, Alegra)", 4.0, 2.4, AZUL),
        ("ERP y analítica de\ngrandes cadenas", 8.3, 1.4, AZUL),
        ("TenderIA", 8.0, 8.5, VERDE),
    ]
    for nombre, x, y, c in jugadores:
        tam = 420 if nombre == "TenderIA" else 160
        ax.scatter(x, y, s=tam, color=c, zorder=3, edgecolor="white", linewidth=2)
        dx = 0.35
        ax.text(x + dx, y, nombre, va="center", fontsize=9.5 if nombre == "TenderIA" else 8.6,
                fontweight="bold" if nombre == "TenderIA" else "normal", color=TINTA)
    ax.add_patch(FancyBboxPatch((6.1, 6.9), 3.7, 2.9, boxstyle="round,pad=0,rounding_size=0.25",
                                fc=T_VERDE, ec="none", zorder=0))
    ax.text(6.25, 9.62, "Espacio vacío: predictivo + conversacional", fontsize=8.3, color=VERDE,
            fontweight="bold", va="top")
    ax.text(9.95, 0.2, "Posicionamiento cualitativo elaborado por el autor", ha="right", fontsize=7.8, color=GRIS)
    guardar(fig, "fig03_mapa_competitivo.png")


# ================================================ 4. mapa de empatía
def fig_empatia():
    fig, ax = lienzo(16, 8.7, 9.6, 5.22)
    ancho = 50
    cuad = [
        ("¿Qué piensa y siente?", 0.2, 5.75, [
            "“Trabajo 14 horas y no sé si gané plata.”", "Miedo a quedarse sin producto cuando llega el cliente.",
            "Le duele botar leche y pan vencidos.", "Desconfía de los bancos; teme al “gota a gota”."], T_VERDE),
        ("¿Qué ve?", 9.5, 5.75, [
            "Tiendas de descuento (D1, Ara, Isimo) en su cuadra.", "Clientes que pagan con Nequi o Daviplata.",
            "Preventistas con “la promoción del mes”.", "Vecinos que fían y no pagan a tiempo."], T_AZUL),
        ("¿Qué dice y hace?", 0.2, 2.85, [
            "Anota fiados en un cuaderno; cuadra caja de memoria.", "Pide “lo mismo de siempre” al distribuidor.",
            "Usa WhatsApp todo el día con proveedores y clientes.", "Rechaza apps “complicadas” que piden tiempo."],
         T_AMBAR),
        ("¿Qué oye?", 9.5, 2.85, [
            "“Las tiendas de barrio se están quebrando.”", "Hijos que le dicen “digitalícese, mamá”.",
            "Proveedores que suben precios cada mes.", "Ofertas de crédito rápido sin requisitos."], T_LADRILLO),
    ]
    for t, x, y, items, c in cuad:
        caja(ax, x, y, 6.3, 2.8, "", c, "none", radio=0.15)
        ax.text(x + 0.2, y + 2.62, t, fontsize=9.5, fontweight="bold", va="top")
        ax.text(x + 0.2, y + 2.12, viñetas(items, ancho), fontsize=7.9, va="top", color=TINTA, linespacing=1.35)
    ax.add_patch(Circle((8.0, 6.35), 1.05, fc=FONDO, ec=VERDE, lw=2.0, zorder=2))
    actor(ax, 8.0, 5.95, "", s=1.05)
    ax.text(8.0, 4.95, "Doña Marta\n52 años · tendera\nKennedy, Bogotá", ha="center", va="top", fontsize=8.2,
            fontweight="bold", zorder=6, linespacing=1.3)
    ax.text(8.0, 3.6, "Proto-persona\n(investigación\nsecundaria)", ha="center", va="top", fontsize=7.2,
            color=TINTA2, zorder=6, linespacing=1.25)
    caja(ax, 0.2, 0.1, 7.65, 2.6, "", "#FBEAEA", "none", radio=0.15)
    ax.text(0.4, 2.52, "Esfuerzos (dolores)", fontsize=9.5, fontweight="bold", va="top", color=LADRILLO)
    ax.text(0.4, 2.02, viñetas(["Merma de perecederos y agotados en fin de semana",
                                "Capital atrapado en inventario que no rota",
                                "Crédito caro e informal; sin tiempo ni datos para decidir"], 58),
            fontsize=7.9, va="top", linespacing=1.35)
    caja(ax, 8.15, 0.1, 7.65, 2.6, "", T_VERDE, "none", radio=0.15)
    ax.text(8.35, 2.52, "Resultados esperados (ganancias)", fontsize=9.5, fontweight="bold", va="top", color=VERDE)
    ax.text(8.35, 2.02, viñetas(["Saber cuánto gana cada día y pedir lo justo",
                                 "Vender antes de que el producto se venza",
                                 "Acceder a crédito formal y competir con el hard discount"], 58),
            fontsize=7.9, va="top", linespacing=1.35)
    guardar(fig, "fig04_mapa_empatia.png")


# ========================================= 5. matriz impacto-esfuerzo
def fig_ideas():
    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ideas = [
        ("A", "Registro de ventas por chat/voz en WhatsApp", 3.0, 8.6, True),
        ("B", "Pedido sugerido con pronóstico", 5.0, 8.9, True),
        ("C", "Alerta de vencimiento + descuento", 2.6, 7.6, True),
        ("D", "Puntaje alternativo de crédito", 5.6, 7.9, True),
        ("E", "Marketplace de proveedores", 7.4, 6.6, False),
        ("F", "Datáfono propio / billetera", 9.0, 5.2, False),
        ("G", "App móvil nativa con escáner", 7.8, 4.0, False),
        ("H", "Cuadre de caja y fiados", 2.0, 6.0, True),
        ("I", "Kiosco IoT con sensores en neveras", 9.3, 3.4, False),
        ("J", "Insights B2B para marcas", 6.2, 6.9, False),
    ]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axvline(5, color=REJILLA, lw=1.2, zorder=0)
    ax.axhline(5, color=REJILLA, lw=1.2, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("Esfuerzo de desarrollo y adopción  →", fontsize=9.5)
    ax.set_ylabel("Impacto en el problema del tendero  →", fontsize=9.5)
    for et, x, y in [("Ganancias rápidas", 0.2, 9.8), ("Apuestas estratégicas", 5.2, 9.8),
                     ("Complementos", 0.2, 0.25), ("Descartar por ahora", 5.2, 0.25)]:
        ax.text(x, y, et, fontsize=9, color=GRIS, fontweight="bold", va="top" if y > 5 else "bottom")
    for letra, nombre, x, y, sel in ideas:
        c = VERDE if sel else GRIS
        ax.scatter(x, y, s=330, color=c, zorder=3, edgecolor="white", linewidth=1.5)
        ax.text(x, y, letra, ha="center", va="center", color="white", fontsize=9, fontweight="bold", zorder=4)
    leyenda = "\n".join(f"{l}  {n}" for l, n, *_ in ideas)
    ax.text(10.3, 9.9, leyenda, fontsize=8.4, va="top", linespacing=1.6)
    ax.scatter([], [], s=80, color=VERDE, label="Incluida en el MVP")
    ax.scatter([], [], s=80, color=GRIS, label="Fase posterior o descartada")
    ax.legend(loc="lower left", bbox_to_anchor=(1.02, 0.0), frameon=False, fontsize=8.4)
    guardar(fig, "fig05_matriz_ideas.png")


# ============================================ 6. UML casos de uso
def fig_casos_uso():
    fig, ax = lienzo(16, 10, 9.0, 5.63)
    caja(ax, 2.9, 0.25, 9.6, 9.45, "", "#FAFCFB", TINTA2, radio=0.12, lw=1.3, z=0)
    ax.text(3.1, 9.5, "Sistema TenderIA", fontsize=11, fontweight="bold", va="top")
    actor(ax, 1.25, 4.9, "Tendero(a)", s=1.4)
    externos = [("Empresa de consumo\nmasivo (B2B)", 14.6, 7.4), ("Proveedor /\ndistribuidor aliado", 14.6, 4.45),
                ("Entidad aliada de\nmicrocrédito", 14.6, 1.35)]
    for n, x, y in externos:
        actor(ax, x, y, n, s=1.3, ancho=22)

    def uc(x, y, t, w=3.5, h=0.78):
        ax.add_patch(Ellipse((x, y), w, h, fc=T_VERDE, ec=VERDE, lw=1.2, zorder=2))
        ax.text(x, y, t, ha="center", va="center", fontsize=8.4, zorder=3, linespacing=1.15)
        return x, y, w, h

    izq = [uc(5.25, 8.55, "Registrar venta\n(texto o nota de voz)"), uc(5.25, 7.45, "Registrar entrada\nde mercancía"),
           uc(5.25, 6.35, "Consultar existencias"), uc(5.25, 5.25, "Recibir pedido sugerido"),
           uc(5.25, 4.15, "Recibir alerta de\nvencimiento"), uc(5.25, 3.05, "Consultar resumen\ny fiados del día"),
           uc(5.25, 1.6, "Autorizar y consultar\npuntaje de crédito")]
    nlu = uc(9.9, 8.0, "Interpretar mensaje\n(NLU)")
    b2b = uc(9.9, 6.6, "Consultar tablero\nde insights")
    envio = uc(9.9, 5.25, "Enviar pedido\nal proveedor")
    desc = uc(9.9, 3.9, "Aplicar descuento\nsugerido")
    cred = uc(9.9, 1.6, "Solicitar\nmicrocrédito")
    for x, y, w, h in izq:
        ax.plot([1.6, x - w / 2], [5.55, y], color=TINTA2, lw=0.9, zorder=1)
    # include / extend
    flecha(ax, 7.0, 8.45, 8.15, 8.1, ls="--", estilo="->", texto="«include»", fs=7.5, desp=(0, 0.02))
    flecha(ax, 7.0, 7.5, 8.15, 7.9, ls="--", estilo="->", texto="«include»", fs=7.5, desp=(0, -0.32))
    flecha(ax, 8.15, 5.25, 7.0, 5.25, ls="--", estilo="->", texto="«extend»", fs=7.5)
    flecha(ax, 8.15, 3.95, 7.0, 4.1, ls="--", estilo="->", texto="«extend»", fs=7.5)
    flecha(ax, 8.15, 1.6, 7.0, 1.6, ls="--", estilo="->", texto="«include»", fs=7.5)
    for (x, y, w, h), (_, ax_x, ax_y) in [(b2b, externos[0]), (envio, externos[1]), (cred, externos[2])]:
        ax.plot([x + w / 2, ax_x - 0.35], [y, ax_y + 0.45], color=TINTA2, lw=0.9)
    guardar(fig, "fig07_uml_casos_uso.png")


# ============================================= 7. UML componentes
def componente(ax, x, y, w, h, nombre, detalle="", fc=T_VERDE, ec=VERDE, fs=9):
    caja(ax, x, y, w, h, "", fc, ec, radio=0.06)
    ax.add_patch(Rectangle((x + w - 0.42, y + h - 0.38), 0.26, 0.26, fc=FONDO, ec=ec, lw=0.9, zorder=4))
    ax.add_patch(Rectangle((x + w - 0.48, y + h - 0.2), 0.12, 0.05, fc=FONDO, ec=ec, lw=0.8, zorder=5))
    ax.add_patch(Rectangle((x + w - 0.48, y + h - 0.32), 0.12, 0.05, fc=FONDO, ec=ec, lw=0.8, zorder=5))
    ax.text(x + 0.15, y + h - 0.16, "«component»", fontsize=6.8, color=TINTA2, va="top", zorder=4)
    ax.text(x + 0.15, y + h - 0.42, nombre, fontsize=fs, fontweight="bold", va="top", zorder=4)
    if detalle:
        ax.text(x + 0.15, y + h - 0.78, detalle, fontsize=7.6, color=TINTA2, va="top", zorder=4, linespacing=1.25)


def ruta(ax, puntos, color=TINTA2, ls="-", lw=1.2, texto=None, fs=7.5, i_texto=0, desp=(0, 0.1)):
    """Conector ortogonal: polilínea con punta de flecha en el último tramo."""
    for (x1, y1), (x2, y2) in zip(puntos[:-2], puntos[1:-1]):
        ax.plot([x1, x2], [y1, y2], color=color, ls=ls, lw=lw, zorder=1)
    flecha(ax, *puntos[-2], *puntos[-1], color=color, ls=ls, lw=lw)
    if texto:
        (x1, y1), (x2, y2) = puntos[i_texto], puntos[i_texto + 1]
        ax.text((x1 + x2) / 2 + desp[0], (y1 + y2) / 2 + desp[1], texto, ha="center", va="bottom", fontsize=fs,
                color=color, zorder=5, bbox=dict(boxstyle="round,pad=0.12", fc=FONDO, ec="none", alpha=0.9))


def fig_componentes():
    fig, ax = lienzo(18, 10, 10.2, 5.67)
    for x, w, t in [(0.15, 3.55, "Canales"), (4.05, 9.25, "Núcleo de TenderIA (Python)"),
                    (13.65, 4.2, "Datos e integraciones")]:
        caja(ax, x, 0.15, w, 9.7, "", "#FAFCFB", REJILLA, radio=0.12, z=0)
        ax.text(x + 0.2, 9.68, t, fontsize=9.5, fontweight="bold", va="top")
    am = dict(fc=T_AMBAR, ec=AMBAR)
    az = dict(fc=T_AZUL, ec=AZUL)
    componente(ax, 0.35, 6.6, 3.15, 1.85, "WhatsApp", "App del tendero:\ntexto y voz", **am)
    componente(ax, 0.35, 3.95, 3.15, 1.85, "Panel del tendero", "Web opcional\n(Streamlit)", **am)
    componente(ax, 0.35, 1.0, 3.15, 1.85, "Portal B2B", "Tableros para\nmarcas", **am)
    # fila 1
    componente(ax, 4.3, 7.0, 2.85, 1.85, "API / Webhook", "Eventos de\nWhatsApp")
    componente(ax, 7.4, 7.0, 2.85, 1.85, "Orquestador", "Asistente\nTenderIA")
    componente(ax, 10.5, 7.0, 2.6, 1.85, "Intérprete NLU", "Reglas + LLM")
    # fila 2
    componente(ax, 4.3, 4.2, 2.85, 1.85, "Inventario", "Lotes y FEFO")
    componente(ax, 7.4, 4.2, 2.85, 1.85, "Pronóstico", "Estacionalidad\nsemanal")
    componente(ax, 10.5, 4.2, 2.6, 1.85, "Reabasteci-\nmiento", "\nPedido sugerido")
    # fila 3
    componente(ax, 4.3, 1.4, 2.85, 1.85, "Insights B2B", "Anonimización")
    componente(ax, 7.4, 1.4, 2.85, 1.85, "Alertas", "Vencimiento y\ndescuento")
    componente(ax, 10.5, 1.4, 2.6, 1.85, "Puntaje de\ncrédito", "\nConsentimiento")
    # datos e integraciones
    componente(ax, 13.85, 7.25, 3.8, 1.55, "Proveedor de LLM", "", **az)
    componente(ax, 13.85, 5.45, 3.8, 1.55, "Base transaccional", "PostgreSQL", **az)
    componente(ax, 13.85, 3.65, 3.8, 1.55, "API proveedores", "Pedidos", **az)
    componente(ax, 13.85, 1.85, 3.8, 1.55, "API aliados crédito", "Finanzas abiertas", **az)
    componente(ax, 13.85, 0.3, 3.8, 1.3, "Almacén analítico", "", **az)
    # conexiones
    flecha(ax, 3.5, 7.5, 4.3, 7.5)
    flecha(ax, 7.15, 7.9, 7.4, 7.9)
    flecha(ax, 10.25, 7.9, 10.5, 7.9)
    flecha(ax, 13.1, 8.0, 13.85, 8.0, ls="--")
    flecha(ax, 3.5, 4.9, 4.3, 7.15, texto="consultas", fs=7, desp=(-0.05, 0.1))
    flecha(ax, 8.0, 7.0, 6.2, 6.05)
    flecha(ax, 8.8, 7.0, 8.8, 6.05)
    flecha(ax, 9.6, 7.0, 11.4, 6.05)
    flecha(ax, 10.25, 5.1, 10.5, 5.1)
    flecha(ax, 8.8, 4.2, 8.8, 3.25)
    flecha(ax, 6.2, 4.2, 7.9, 3.25)
    flecha(ax, 13.1, 4.45, 13.85, 4.45)
    flecha(ax, 13.1, 2.6, 13.85, 2.6)
    flecha(ax, 4.3, 2.2, 3.5, 2.2)
    flecha(ax, 13.3, 6.25, 13.85, 6.25)
    ax.text(13.25, 6.42, "persiste", fontsize=7, ha="right", va="bottom", color=TINTA2)
    ruta(ax, [(13.85, 0.95), (5.7, 0.95), (5.7, 1.4)], texto="datos agregados", fs=7, i_texto=0)
    guardar(fig, "fig08_uml_componentes.png")


# ================================================= 8. UML clases
def clase(ax, x, y_sup, w, nombre, atributos, metodos, fc=T_VERDE, ec=VERDE, fs=7.8, estereotipo=None):
    lh = 0.27
    h_n = 0.62 if estereotipo else 0.45
    h_a = lh * max(len(atributos), 1) + 0.14
    h_m = lh * max(len(metodos), 1) + 0.14 if metodos is not None else 0
    h = h_n + h_a + h_m
    y = y_sup - h
    ax.add_patch(Rectangle((x, y), w, h, fc=FONDO, ec=ec, lw=1.2, zorder=2))
    ax.add_patch(Rectangle((x, y_sup - h_n), w, h_n, fc=fc, ec=ec, lw=1.2, zorder=2))
    if estereotipo:
        ax.text(x + w / 2, y_sup - 0.17, estereotipo, ha="center", va="center", fontsize=6.8, color=TINTA2, zorder=3)
    ax.text(x + w / 2, y_sup - h_n + 0.22, nombre, ha="center", va="center", fontsize=8.8, fontweight="bold", zorder=3)
    for i, a in enumerate(atributos):
        ax.text(x + 0.1, y_sup - h_n - 0.08 - lh * (i + 0.5), a, fontsize=fs, va="center", zorder=3, family="Consolas")
    if metodos is not None:
        ym = y_sup - h_n - h_a
        ax.plot([x, x + w], [ym, ym], color=ec, lw=1.0, zorder=3)
        for i, m in enumerate(metodos):
            ax.text(x + 0.1, ym - 0.08 - lh * (i + 0.5), m, fontsize=fs, va="center", zorder=3, family="Consolas")
    return {"x": x, "y": y, "w": w, "h": h, "cx": x + w / 2, "cy": y + h / 2, "top": y_sup}


def rel(ax, p1, p2, tipo="asoc", texto="", m1="", m2="", rad=0.0, desp=(0, 0.1)):
    estilos = {"asoc": ("-", "-"), "dep": ("--", "->"), "comp": ("-", "-"), "agreg": ("-", "-"), "nav": ("-", "->")}
    ls, est = estilos[tipo]
    flecha(ax, *p1, *p2, ls=ls, estilo=est, texto=texto or None, fs=7.2, rad=rad, desp=desp, lw=1.0)
    (x1, y1), (x2, y2) = p1, p2
    ang = np.arctan2(y2 - y1, x2 - x1)
    if tipo in ("comp", "agreg"):
        d = 0.22
        pts = [(x1, y1), (x1 + d * np.cos(ang + 0.5), y1 + d * np.sin(ang + 0.5)),
               (x1 + 2 * d * np.cos(ang) * 0.9, y1 + 2 * d * np.sin(ang) * 0.9),
               (x1 + d * np.cos(ang - 0.5), y1 + d * np.sin(ang - 0.5))]
        ax.add_patch(Polygon(pts, closed=True, fc=TINTA2 if tipo == "comp" else FONDO, ec=TINTA2, lw=1.0, zorder=4))
    # multiplicidades: junto al extremo, del lado de la línea y desplazadas en perpendicular
    for (px, py), m, sentido in (((x1, y1), m1, 1), ((x2, y2), m2, -1)):
        if m:
            ux, uy = np.cos(ang) * sentido, np.sin(ang) * sentido
            lx, ly = px + 0.45 * ux - 0.22 * uy, py + 0.45 * uy + 0.22 * ux
            ax.text(lx, ly, m, fontsize=7.2, color=TINTA2, ha="center", va="center", zorder=5)


def fig_clases():
    fig, ax = lienzo(19, 12.4, 10.6, 6.92)
    asis = clase(ax, 6.6, 12.2, 5.2, "AsistenteTenderIA",
                 ["- hoy: date", "- ventas_hoy: list[Venta]"],
                 ["+ responder(mensaje): str", "+ demanda_diaria(): dict", "+ modelo(sku)"])
    nlu = clase(ax, 0.2, 12.2, 5.1, "InterpreteMensajes",
                ["- alias: dict[str, str]"],
                ["+ interpretar(texto)", "+ detectar_intencion(t)", "+ extraer_items(t): dict"])
    ped = clase(ax, 13.3, 12.2, 5.5, "PedidoSugerido", ["- cantidad · costo_estimado"], None, fc=T_AZUL, ec=AZUL)
    ale = clase(ax, 13.3, 10.85, 5.5, "AlertaVencimiento", ["- descuento_pct · precio"], None,
                fc=T_AZUL, ec=AZUL)
    pun = clase(ax, 13.3, 9.5, 5.5, "PuntajeCredito", ["- puntaje · banda · monto"], None, fc=T_AZUL, ec=AZUL)
    pro = clase(ax, 13.3, 7.85, 5.5, "PronosticadorDemanda",
                ["- alpha: float", "- indices_semana", "- nivel, sigma: float"],
                ["+ ajustar(serie)", "+ predecir(h): Series"])
    inv = clase(ax, 6.6, 8.6, 5.2, "Inventario",
                ["- politica: FEFO|LIFO|MIXTA", "- fraccion_fefo: float"],
                ["+ registrar_compra(sku, q)", "+ registrar_venta(sku, q)", "+ retirar_vencidos(hoy)"])
    tienda = clase(ax, 0.2, 8.6, 5.1, "Tienda",
                   ["- id, nombre: str", "- propietario: str", "- ciudad: str", "- plan: str"], [])
    lote = clase(ax, 6.6, 4.55, 5.2, "Lote",
                 ["- cantidad: int", "- fecha_ingreso: date", "- fecha_vencimiento"],
                 ["+ dias_para_vencer(hoy)"])
    prod = clase(ax, 13.3, 4.55, 5.5, "Producto",
                 ["- sku, nombre: str", "- precio_venta, costo", "- perecedero: bool",
                  "- vida_util_dias: int", "- multiplo_compra: int"],
                 ["+ margen_unitario(): int"])
    venta = clase(ax, 0.2, 4.55, 5.1, "Venta",
                  ["- fecha: date", "- cantidad: int", "- precio_unitario", "- medio_pago"],
                  ["+ total(): int"])
    medio = clase(ax, 0.2, 1.3, 5.1, "MedioPago", ["EFECTIVO · TRANSFER. · FIADO"], None,
                  fc=T_AMBAR, ec=AMBAR, estereotipo="«enumeration»")
    rel(ax, (asis["x"], 11.45), (nlu["x"] + nlu["w"], 11.45), "comp", m2="1")
    rel(ax, (asis["x"] + asis["w"], 11.6), (ped["x"], 11.6), "dep", texto="«crea»", desp=(0, 0.04))
    rel(ax, (asis["x"] + asis["w"], 10.3), (ale["x"], 10.3), "dep", texto="«crea»", desp=(0, 0.04))
    rel(ax, (asis["x"] + asis["w"] - 0.3, asis["y"]), (pun["x"], pun["cy"]), "dep", texto="«crea»",
        desp=(0.3, -0.02))
    rel(ax, (asis["x"] + asis["w"] - 1.1, asis["y"]), (pro["x"], pro["top"] - 0.6), "comp", m2="1..*")
    rel(ax, (asis["cx"] - 0.6, asis["y"]), (inv["cx"] - 0.6, inv["top"]), "comp", m2="1")
    rel(ax, (inv["cx"], inv["y"]), (lote["cx"], lote["top"]), "comp", m2="0..*")
    rel(ax, (lote["x"] + lote["w"], 3.4), (prod["x"], 3.4), "nav", m2="1")
    rel(ax, (tienda["x"] + tienda["w"], 7.6), (inv["x"], 7.6), "asoc", m1="1", m2="1")
    rel(ax, (tienda["cx"], tienda["y"]), (venta["cx"], venta["top"]), "comp", m2="0..*")
    rel(ax, (venta["cx"], venta["y"]), (medio["cx"], medio["top"]), "nav")
    ruta(ax, [(venta["x"] + venta["w"], venta["y"] + 0.2), (5.9, venta["y"] + 0.2), (5.9, 1.75),
              (prod["cx"], 1.75), (prod["cx"], prod["y"])], lw=1.0, texto="se refiere a", fs=7.2, i_texto=2,
         desp=(0, 0.03))
    ax.text(prod["cx"] + 0.25, prod["y"] - 0.3, "1", fontsize=7.2, color=TINTA2)
    guardar(fig, "fig09_uml_clases.png")


# =============================================== 9. UML secuencia
def fig_secuencia():
    fig, ax = lienzo(18, 11.6, 9.9, 6.38)
    part = [("Tendero(a)", 1.0, True), (":WhatsApp\nCloud API", 3.8, False), (":Asistente\nTenderIA", 6.8, False),
            (":Interprete\nMensajes", 9.6, False), (":Inventario", 12.0, False), (":Pronosticador\nDemanda", 14.3, False),
            (":Motor de\nalertas", 16.6, False)]
    top, base = 10.6, 0.3
    for nombre, x, es_actor in part:
        if es_actor:
            actor(ax, x, top - 0.25, "", s=0.9)
            ax.text(x, top + 0.75, nombre, ha="center", fontsize=8.5, fontweight="bold")
        else:
            caja(ax, x - 1.05, top - 0.15, 2.1, 0.9, nombre, T_VERDE, VERDE, fs=8, bold=True, radio=0.05)
        ax.plot([x, x], [top - 0.5 if es_actor else top - 0.15, base], color=GRIS, lw=1, ls=(0, (4, 3)), zorder=0)
    T, W, A, I, INV, P, AL = 1.0, 3.8, 6.8, 9.6, 12.0, 14.3, 16.6
    for x, y1, y2 in [(W, 9.55, 0.95), (A, 9.0, 1.45), (I, 8.25, 7.55), (INV, 6.35, 5.4), (P, 4.55, 3.95),
                      (AL, 2.9, 2.3)]:
        ax.add_patch(Rectangle((x - 0.1, y2), 0.2, y1 - y2, fc=FONDO, ec=TINTA2, lw=1, zorder=2))

    def msg(x1, x2, y, t, ret=False, num=None):
        flecha(ax, x1 + (0.1 if x2 > x1 else -0.1), y, x2 + (-0.1 if x2 > x1 else 0.1), y,
               ls="--" if ret else "-", estilo="->" if ret else "-|>", color=TINTA2 if ret else TINTA, lw=1.1, z=3)
        etiqueta = f"{num}. {t}" if num else t
        ax.text((x1 + x2) / 2, y + 0.1, etiqueta, ha="center", va="bottom", fontsize=7.8,
                color=TINTA2 if ret else TINTA, zorder=4,
                bbox=dict(boxstyle="round,pad=0.1", fc=FONDO, ec="none", alpha=0.95))

    msg(T, W, 9.6, "“vendí 3 leches y 2 panes”", num=1)
    msg(W, A, 9.05, "webhook(mensaje)", num=2)
    msg(A, I, 8.25, "interpretar(texto)", num=3)
    msg(I, A, 7.6, "Interpretacion(venta, ítems)", ret=True)
    caja(ax, 5.9, 5.15, 7.1, 2.05, "", "none", AMBAR, radio=0.02, lw=1.1, z=1)
    ax.add_patch(Polygon([(5.9, 7.2), (7.2, 7.2), (7.2, 7.0), (7.0, 6.82), (5.9, 6.82)], fc=T_AMBAR, ec=AMBAR, zorder=2))
    ax.text(6.0, 7.01, "loop", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(7.35, 7.01, "[por cada producto]", fontsize=7.6, va="center", color=TINTA2)
    msg(A, INV, 6.3, "registrar_venta(sku, cantidad)", num=4)
    msg(INV, A, 5.45, "unidades vendidas (FEFO)", ret=True)
    msg(A, P, 4.5, "predecir(horizonte=1)", num=5)
    msg(P, A, 4.0, "demanda esperada", ret=True)
    caja(ax, 5.9, 2.0, 11.6, 1.7, "", "none", AZUL, radio=0.02, lw=1.1, z=1)
    ax.add_patch(Polygon([(5.9, 3.7), (6.9, 3.7), (6.9, 3.5), (6.7, 3.32), (5.9, 3.32)], fc=T_AZUL, ec=AZUL, zorder=2))
    ax.text(6.0, 3.51, "opt", fontsize=7.8, fontweight="bold", va="center", zorder=3)
    ax.text(7.05, 3.51, "[hay lotes próximos a vencer]", fontsize=7.6, va="center", color=TINTA2)
    msg(A, AL, 2.85, "generar_alertas(inventario, hoy)", num=6)
    msg(AL, A, 2.3, "alertas + descuento sugerido", ret=True)
    msg(A, W, 1.55, "respuesta", num=7)
    msg(W, T, 1.0, "confirmación", num=8)
    guardar(fig, "fig10_uml_secuencia.png")


# =============================================== 10. UML despliegue
def nodo(ax, x, y, w, h, nombre, estereotipo, fc=T_GRIS, ec=TINTA2):
    d = 0.3
    ax.add_patch(Polygon([(x, y + h), (x + d, y + h + d), (x + w + d, y + h + d), (x + w, y + h)], fc=fc, ec=ec, lw=1.1))
    ax.add_patch(Polygon([(x + w, y), (x + w + d, y + d), (x + w + d, y + h + d), (x + w, y + h)], fc=fc, ec=ec, lw=1.1))
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=1.1))
    ax.text(x + 0.15, y + h - 0.15, estereotipo, fontsize=7, color=TINTA2, va="top")
    ax.text(x + 0.15, y + h - 0.45, nombre, fontsize=9, fontweight="bold", va="top")


def artefacto(ax, x, y, w, h, t, fc=FONDO, ec=VERDE):
    caja(ax, x, y, w, h, "", fc, ec, radio=0.03, z=3)
    ax.text(x + 0.12, y + h - 0.12, "«artifact»", fontsize=6.6, color=TINTA2, va="top", zorder=4)
    ax.text(x + 0.12, y + h - 0.38, t, fontsize=7.9, va="top", zorder=4, linespacing=1.2)


def fig_despliegue():
    fig, ax = lienzo(18, 9.6, 9.8, 5.23)
    nodo(ax, 0.3, 5.6, 3.4, 2.6, "Smartphone\ndel tendero", "«device»", T_AMBAR, AMBAR)
    artefacto(ax, 0.55, 5.85, 2.9, 0.8, "WhatsApp (app)", ec=AMBAR)
    nodo(ax, 0.3, 1.0, 3.4, 2.6, "Navegador web", "«device»", T_AMBAR, AMBAR)
    artefacto(ax, 0.55, 1.15, 2.9, 1.3, "Portal B2B /\npanel del tendero", ec=AMBAR)
    nodo(ax, 4.6, 5.6, 3.3, 2.6, "Meta WhatsApp\nCloud API", "«servicio externo»", T_AZUL, AZUL)
    nodo(ax, 8.8, 0.5, 5.6, 8.2, "Nube pública (PaaS)", "«execution environment»", T_VERDE, VERDE)
    artefacto(ax, 9.1, 6.0, 5.0, 1.15, "api_webhook (FastAPI)\ncontenedor autoescalable")
    artefacto(ax, 9.1, 4.45, 5.0, 1.15, "tenderia (núcleo Python):\nasistente, inventario, pronóstico")
    artefacto(ax, 9.1, 2.9, 5.0, 1.15, "worker programado:\nalertas 6 a. m. y pedidos")
    artefacto(ax, 9.1, 0.8, 2.35, 1.55, "PostgreSQL\n(cifrado en\nreposo)", ec=AZUL)
    artefacto(ax, 11.75, 0.8, 2.35, 1.55, "Almacén\nanalítico\n(anonimizado)", ec=AZUL)
    nodo(ax, 15.2, 6.0, 2.5, 2.1, "Proveedor\nde LLM", "«servicio externo»", T_AZUL, AZUL)
    nodo(ax, 15.2, 3.2, 2.5, 2.1, "Aliados de\ncrédito", "«servicio externo»", T_AZUL, AZUL)
    nodo(ax, 15.2, 0.5, 2.5, 2.1, "Proveedores\naliados", "«servicio externo»", T_AZUL, AZUL)
    flecha(ax, 3.7, 6.4, 4.6, 6.4, estilo="<|-|>", texto="HTTPS", fs=7, desp=(0, -0.42))
    flecha(ax, 7.9, 5.9, 8.8, 5.9, estilo="<|-|>", texto="webhook", fs=7, desp=(0, -0.42))
    flecha(ax, 3.7, 2.3, 8.8, 2.3, estilo="<|-|>", texto="HTTPS (TLS 1.3)", fs=7.2)
    flecha(ax, 14.4, 7.0, 15.2, 7.0, estilo="<|-|>", texto="API", fs=7.2)
    flecha(ax, 14.4, 4.2, 15.2, 4.2, estilo="<|-|>", texto="API", fs=7.2)
    flecha(ax, 14.4, 1.5, 15.2, 1.5, estilo="<|-|>", texto="API", fs=7.2)
    guardar(fig, "fig11_uml_despliegue.png")


# ============================================ 11. resultados del piloto
def fig_piloto():
    pal = RES["palancas"]
    pil = RES["piloto"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.6, 3.7), gridspec_kw={"width_ratios": [1.15, 1]})
    nombres = [p["configuracion"] for p in pal][::-1]
    valores = [p["merma_pct_perecederos"] * 100 for p in pal][::-1]
    colores = [VERDE if n == "TenderIA completo" else (GRIS if "Empírico" in n else "#7FB5A5") for n in nombres]
    barras = a1.barh(nombres, valores, color=colores, height=0.6)
    for b, v in zip(barras, valores):
        a1.text(v + 0.05, b.get_y() + b.get_height() / 2, f"{v:.2f} %".replace(".", ","), va="center", fontsize=9)
    a1.set_title("Merma de perecederos por configuración", loc="left")
    a1.set_xlabel("% de unidades perecederas vencidas")
    a1.set_xlim(0, max(valores) * 1.25)
    a1.grid(axis="x", color=REJILLA)
    a1.set_axisbelow(True)
    for s in ("top", "right", "left"):
        a1.spines[s].set_visible(False)
    a1.tick_params(axis="y", length=0)
    kpis = [
        ("Merma de perecederos", -pil["reduccion_merma_pct"], True),
        ("Costo de la merma", (pil["costo_merma_tenderia"] / pil["costo_merma_empirico"] - 1) * 100, True),
        ("Ventas perdidas por agotado", -pil["reduccion_ventas_perdidas_pct"], True),
        ("Margen neto de merma", pil["aumento_margen_pct"], True),
        ("Inventario promedio", (pil["inventario_tenderia"] / pil["inventario_empirico"] - 1) * 100, False),
    ][::-1]
    etiquetas = [k[0] for k in kpis]
    vals = [k[1] for k in kpis]
    cols = [VERDE if k[2] else AMBAR for k in kpis]
    b2 = a2.barh(etiquetas, vals, color=cols, height=0.6)
    for b, v in zip(b2, vals):
        dentro = v < 0
        a2.text(v + 2 if dentro else v + 1.5, b.get_y() + b.get_height() / 2, f"{v:+.1f} %".replace(".", ","),
                va="center", ha="left", fontsize=9, color="white" if dentro else TINTA,
                fontweight="bold" if dentro else "normal")
    a2.axvline(0, color=TINTA2, lw=1)
    a2.set_xlim(-100, 45)
    a2.set_title("TenderIA vs. gestión empírica (cambio %)", loc="left")
    a2.grid(axis="x", color=REJILLA)
    a2.set_axisbelow(True)
    for s in ("top", "right", "left"):
        a2.spines[s].set_visible(False)
    a2.tick_params(axis="y", length=0)
    a2.set_xlabel("Cambio % (verde = favorable; ámbar = costo a gestionar)")
    fig.text(0.01, -0.03, "Fuente: simulación de 30 tiendas sintéticas durante 90 días (12 tiendas en el análisis "
             "por palanca), elaborada con el prototipo.", fontsize=8, color=GRIS)
    fig.tight_layout()
    guardar(fig, "fig12_resultados_piloto.png")


# ============================================ 12. Business Model Canvas
def viñetas(items, ancho):
    return "\n".join(textwrap.fill(i, ancho, initial_indent="• ", subsequent_indent="   ") for i in items)


def fig_canvas():
    fig, ax = lienzo(20, 13.6, 12.6, 8.57)
    W = 20 / 5
    A = 30  # caracteres por línea en columnas angostas
    bloques = [
        ("Socios clave", 0, 4.6, W, 9.0, T_AZUL, viñetas([
            "Meta y proveedor BSP de WhatsApp Business", "Nube y proveedor de modelos de lenguaje",
            "Distribuidores y empresas de consumo masivo", "Microfinancieras y fintech vigiladas",
            "Fenalco y asociaciones de tenderos", "Bancos de alimentos", "Programas públicos de inclusión financiera"], A)),
        ("Actividades clave", W, 9.1, W, 4.5, T_AZUL, viñetas([
            "Mejora continua de modelos de IA", "Adquisición y onboarding en campo",
            "Alianzas y analítica B2B", "Seguridad y protección de datos"], A)),
        ("Recursos clave", W, 4.6, W, 4.5, T_AZUL, viñetas([
            "Motor de IA: NLU, pronóstico, puntaje", "Datos transaccionales (activo creciente)",
            "Equipo técnico y red de agentes", "Marca de confianza en el barrio"], A)),
        ("Propuesta de valor", 2 * W, 4.6, W, 9.0, T_VERDE,
         textwrap.fill("Tendero: “vende más, bota menos y accede a crédito justo, sin aprender una app nueva”.", A)
         + "\n" + viñetas(["Registro por chat o voz en WhatsApp", "Pedido sugerido y cuadre de caja",
                           "Alertas de vencimiento con descuento", "Historial que se convierte en puntaje"], A)
         + "\n\n" + textwrap.fill("Marcas: sell-out del canal tradicional casi en tiempo real.", A)
         + "\n\n" + textwrap.fill("Crédito: señales verificables de micronegocios sin historial.", A)),
        ("Relación con clientes", 3 * W, 9.1, W, 4.5, T_AMBAR, viñetas([
            "Asistencia automatizada 24/7", "Onboarding presencial de 15 min",
            "Comunidad y retos “merma cero”", "Cuenta dedicada para clientes B2B"], A)),
        ("Canales", 3 * W, 4.6, W, 4.5, T_AMBAR, viñetas([
            "WhatsApp (canal principal)", "Agentes de campo por barrio", "Preventistas de distribuidores",
            "Referidos tendero a tendero", "Portal web B2B"], A)),
        ("Segmentos de clientes", 4 * W, 4.6, W, 9.0, T_AMBAR,
         "Plataforma multilateral:\n\n" + viñetas([
             "Tenderos urbanos (estratos 1-3) con smartphone y WhatsApp: usuarios y pagadores",
             "Empresas de consumo masivo y distribuidores (insights B2B)",
             "Microfinancieras y fintech (originación de crédito)"], A)),
        ("Estructura de costos", 0, 1.75, 10, 2.85, T_GRIS, viñetas([
            "Nómina técnica y comercial (≈ 65 % del costo total)",
            "WhatsApp, nube e IA: ≈ COP 1.200 por tienda activa al mes",
            "Adquisición en campo: ≈ COP 15.000 por tienda dada de alta",
            "Marketing, administración y cumplimiento legal"], 80)),
        ("Fuentes de ingresos", 10, 1.75, 10, 2.85, T_VERDE, viñetas([
            "Freemium: plan Básico gratis; plan Pro COP 29.900/mes",
            "Comisión del 3 % por microcrédito desembolsado (la paga el aliado)",
            "Insights B2B: COP 6 millones/mes por contrato",
            "Comisión del 1,2 % sobre pedidos a proveedores aliados"], 80)),
        ("Impacto social y ambiental (capa de sostenibilidad)", 0, 0, 20, 1.75, "#DDEFE8",
         "Menos alimento desperdiciado (ODS 12.3) · inclusión financiera y alternativa al “gota a gota” (ODS 8.10) · "
         "fortalecimiento del comercio de barrio (ODS 8 y 10)\n· datos personales tratados con consentimiento "
         "(Ley 1581 de 2012)"),
    ]
    for t, x, y, w, h, c, d in bloques:
        caja(ax, x + 0.05, y + 0.05, w - 0.1, h - 0.1, "", c, "white", radio=0.1, lw=2)
        ax.text(x + 0.25, y + h - 0.25, t, fontsize=10, fontweight="bold", va="top")
        ax.text(x + 0.25, y + h - 0.8 if h > 2 else y + h - 0.68, d, fontsize=8.4, va="top", linespacing=1.38,
                color=TINTA)
    guardar(fig, "fig13_business_model_canvas.png")


# ===================================== 13. propuesta de valor (lienzo)
def fig_propuesta_valor():
    fig, ax = lienzo(16, 8.2, 9.6, 4.92)
    # cuadrado (producto) y círculo (cliente)
    ax.add_patch(Rectangle((0.3, 0.4), 7.2, 7.2, fc=FONDO, ec=VERDE, lw=1.6))
    ax.plot([0.3, 7.5], [4.0, 4.0], color=VERDE, lw=1.2)
    ax.plot([3.9, 3.9], [0.4, 7.6], color=VERDE, lw=1.2)
    ax.add_patch(Circle((12.0, 4.0), 3.6, fc=FONDO, ec=AMBAR, lw=1.6))
    ax.plot([8.4, 15.6], [4.0, 4.0], color=AMBAR, lw=1.2)
    ax.text(3.9, 7.95, "Mapa de valor (TenderIA)", ha="center", fontsize=11, fontweight="bold", color=VERDE)
    ax.text(12.0, 7.95, "Perfil del cliente (tendero)", ha="center", fontsize=11, fontweight="bold", color=AMBAR)
    zonas = [
        (0.5, 7.4, "Creadores de alegrías", "Saber la ganancia\ndel día · puntaje que\nabre crédito formal ·\ndescuentos que\nrecuperan dinero"),
        (4.1, 7.4, "Productos y servicios", "Asistente en\nWhatsApp · pedido\nsugerido · alertas ·\ncuadre y fiados ·\npuntaje de crédito"),
        (0.5, 3.8, "Aliviadores de\nfrustraciones", "Registro por voz en\n10 segundos · pedir\nlo justo · rotación\nFEFO guiada"),
        (4.1, 3.8, "", ""),
    ]
    for x, y, t, d in zonas:
        if t:
            ax.text(x, y, t, fontsize=9.2, fontweight="bold", va="top")
            ax.text(x, y - (0.95 if "\n" in t else 0.5), d, fontsize=8.6, va="top", linespacing=1.35, color=TINTA2)
    ax.text(5.7, 2.2, "Sin app nueva,\nsin hardware,\nen su idioma", ha="center", fontsize=9, color=VERDE,
            fontweight="bold", va="center", linespacing=1.4)
    ax.text(10.7, 6.75, "Alegrías", fontsize=9.2, fontweight="bold")
    ax.text(10.1, 6.3, "Más margen · menos estrés ·\ncompetir con el hard\ndiscount · crédito sin\n“gota a gota”",
            fontsize=8.6, va="top", color=TINTA2, linespacing=1.35)
    ax.text(13.35, 4.15, "Trabajos", fontsize=9.2, fontweight="bold", va="bottom")
    ax.text(13.35, 3.75, "Surtir · vender ·\ncobrar fiados ·\ncuadrar caja", fontsize=8.6, va="top",
            color=TINTA2, linespacing=1.35)
    ax.text(9.6, 3.6, "Frustraciones", fontsize=9.2, fontweight="bold", va="top")
    ax.text(9.6, 3.15, "Producto vencido ·\nagotados el sábado ·\nsin datos para decidir ·\ncrédito caro",
            fontsize=8.6, va="top", color=TINTA2, linespacing=1.35)
    flecha(ax, 7.6, 4.0, 8.35, 4.0, color=TINTA, lw=2, estilo="<|-|>", texto="encaje", fs=8.5)
    guardar(fig, "fig06_lienzo_propuesta_valor.png")


# ============================================ 14. finanzas
def _fmt_millones(v):
    return f"{v:,.0f}".replace(",", ".")


def fig_finanzas():
    fin = proyectar()
    a = fin.anual
    anios = [str(x) for x in a.index]
    flujos = [("Suscripción Pro", "ing_suscripcion", VERDE), ("Comisión por crédito", "ing_credito", AMBAR),
              ("Insights B2B", "ing_b2b", AZUL), ("Pedidos a proveedores", "ing_pedidos", LADRILLO)]
    fig, ax = plt.subplots(figsize=(8.0, 4.1))
    base = np.zeros(len(a))
    x = np.arange(len(a))
    for nombre, col, c in flujos:
        v = a[col].to_numpy() / 1e6
        ax.bar(x, v, bottom=base, color=c, width=0.58, label=nombre, edgecolor="white", linewidth=1.5)
        base += v
    for i, tot in enumerate(base):
        ax.text(i, tot + 90, _fmt_millones(tot), ha="center", fontsize=9, fontweight="bold")
    costos = a["costos"].to_numpy() / 1e6
    ax.plot(x, costos, color=TINTA, lw=2, marker="o", ms=7, label="Costos operativos totales", zorder=5)
    for i, c in enumerate(costos):
        ax.text(i + 0.33, c, _fmt_millones(c), fontsize=8.4, color=TINTA2, va="center")
    ax.set_xticks(x, anios)
    ax.set_ylabel("Millones de COP")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: _fmt_millones(v)))
    ax.grid(axis="y", color=REJILLA)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Ingresos por fuente vs. costos operativos (escenario base)", loc="left")
    ax.legend(frameon=False, fontsize=8.6, loc="upper left", ncol=1)
    ax.set_ylim(0, base.max() * 1.12)
    guardar(fig, "fig14_proyeccion_ingresos_costos.png")

    m = fin.mensual
    fig, ax = plt.subplots(figsize=(8.0, 3.5))
    caja_m = m["caja_acumulada"].to_numpy() / 1e6
    meses = m["mes"].to_numpy()
    ax.fill_between(meses, caja_m, 0, where=caja_m < 0, color=T_LADRILLO, step=None)
    ax.fill_between(meses, caja_m, 0, where=caja_m >= 0, color=T_VERDE)
    ax.plot(meses, caja_m, color=TINTA, lw=2)
    ax.axhline(0, color=TINTA2, lw=1)
    i_min = int(np.argmin(caja_m))
    ax.scatter([meses[i_min]], [caja_m[i_min]], color=LADRILLO, s=60, zorder=5)
    ax.annotate(f"Necesidad máxima de caja:\nCOP {_fmt_millones(-caja_m[i_min])} millones (mes {meses[i_min]})",
                (meses[i_min], caja_m[i_min]), xytext=(2, 350), fontsize=8.6,
                arrowprops=dict(arrowstyle="-", color=TINTA2))
    eq = fin.mes_equilibrio
    ax.axvline(eq, color=AMBAR, lw=1.3, ls="--")
    ax.text(eq - 0.6, 1050, f"EBITDA positivo\ndesde el mes {eq}", fontsize=8.6, color=TINTA, ha="right")
    rec = fin.mes_recuperacion
    ax.axvline(rec, color=VERDE, lw=1.3, ls="--")
    ax.text(rec + 0.8, -900, f"Recuperación de la\ninversión: mes {rec}", fontsize=8.6, color=TINTA)
    ax.set_xticks([1, 12, 24, 36, 48, 60], ["Ene-27", "Dic-27", "Dic-28", "Dic-29", "Dic-30", "Dic-31"])
    ax.set_ylabel("Millones de COP")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: _fmt_millones(v)))
    ax.grid(axis="y", color=REJILLA)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.set_title("Caja acumulada mensual (incluye inversión inicial e impuestos)", loc="left")
    ax.set_xlim(0, 61)
    guardar(fig, "fig15_caja_acumulada.png")


# ============================================ 15. journey map
def fig_journey():
    fig, ax = lienzo(18, 8.6, 10.4, 4.97)
    etapas = ["5:30 a. m.\nAbre y recibe\npan y leche", "7:00 a. m.\nVentas de\ndesayuno", "11:00 a. m.\nVisita del\npreventista",
              "3:00 p. m.\nFiados y\nreposición", "9:30 p. m.\nCierre de caja\ny vencidos"]
    emocion = [0.2, 0.6, -0.5, -0.2, -0.8]
    dolores = ["No sabe cuánto\npedir: “lo de\nsiempre”", "Agotados de leche\ny huevos en hora\npico", "Compra por\npromoción, no\npor rotación",
               "Fiados anotados\nen cuaderno;\ncobro difícil", "Bota producto\nvencido; no sabe\nsi ganó"]
    oport = ["Pedido sugerido\npor WhatsApp", "Alerta de stock\nbajo a tiempo", "Pedido con datos\nenviado al\nproveedor",
             "Registro de fiado\npor voz y\nrecordatorio", "Resumen diario y\nalerta con\ndescuento"]
    x0, dx = 2.3, 3.15
    ax.text(0.1, 7.75, "Momento", fontsize=9, fontweight="bold", color=TINTA2)
    ax.text(0.1, 5.6, "Emoción", fontsize=9, fontweight="bold", color=TINTA2)
    ax.text(0.1, 3.3, "Dolor", fontsize=9, fontweight="bold", color=LADRILLO)
    ax.text(0.1, 1.2, "Oportunidad\nTenderIA", fontsize=9, fontweight="bold", color=VERDE)
    xs = [x0 + i * dx + dx / 2 for i in range(5)]
    for i, (e, d, o) in enumerate(zip(etapas, dolores, oport)):
        x = x0 + i * dx
        caja(ax, x + 0.08, 6.9, dx - 0.16, 1.5, e, T_GRIS, "none", fs=8.6)
        caja(ax, x + 0.08, 2.45, dx - 0.16, 1.55, d, T_LADRILLO, "none", fs=8.4)
        caja(ax, x + 0.08, 0.3, dx - 0.16, 1.8, o, T_VERDE, "none", fs=8.4)
    ys = [5.4 + 0.9 * e for e in emocion]
    ax.plot(xs, ys, color=TINTA, lw=2, zorder=3)
    for x, y, e in zip(xs, ys, emocion):
        ax.scatter([x], [y], s=90, color=VERDE if e > 0 else LADRILLO, zorder=4, edgecolor="white", lw=1.5)
    ax.plot([x0, x0 + 5 * dx], [5.4, 5.4], color=REJILLA, lw=1, zorder=1)
    guardar(fig, "fig16_customer_journey.png")


if __name__ == "__main__":
    print("Generando figuras en", SALIDA)
    for f in (fig_metodologia, fig_mercado, fig_competencia, fig_empatia, fig_ideas, fig_propuesta_valor,
              fig_casos_uso, fig_componentes, fig_clases, fig_secuencia, fig_despliegue, fig_piloto,
              fig_canvas, fig_finanzas, fig_journey):
        f()
