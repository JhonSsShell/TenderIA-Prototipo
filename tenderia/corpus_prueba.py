"""Corpus de mensajes de prueba para evaluar el intérprete conversacional.

Cada caso: (mensaje, intención esperada, ítems esperados {sku: cantidad}).
Los mensajes imitan la forma de escribir del tendero: sin tildes, con plurales
irregulares, cantidades en letras, docenas, errores de digitación y jerga.
"""

CASOS: list[tuple[str, str, dict[str, int]]] = [
    # --- ventas
    ("vendí 3 leches y 2 panes", "venta", {"LEC01": 3, "PAN01": 2}),
    ("vendi tres leches", "venta", {"LEC01": 3}),
    ("Vendí media docena de huevos", "venta", {"HUE01": 6}),
    ("se llevaron una docena de huevos y 2 arepas", "venta", {"HUE01": 12, "ARE01": 2}),
    ("vendí 6 polas", "venta", {"CER01": 6}),
    ("vendi 2 gaseosas, 1 agua y 3 galletas", "venta", {"GAS01": 2, "AGU01": 1, "GAL01": 3}),
    ("fié 2 arroces a doña Rosa", "venta", {"ARR01": 2}),
    ("venta de 1 aceite y 1 panela", "venta", {"ACE01": 1, "PNL01": 1}),
    ("vendí un queso y dos yogures", "venta", {"QUE01": 1, "YOG01": 2}),
    ("vendí 4 libras de papa", "venta", {"PAP01": 4}),
    ("vendí 5 platanos y 2 libras de tomate", "venta", {"PLA01": 5, "TOM01": 2}),
    ("se llevo un salchichon", "venta", {"SAL01": 1}),
    ("vendimos 10 cervezas", "venta", {"CER01": 10}),
    ("vendí 1 cafe y 2 azucar", "venta", {"CAF01": 1, "AZU01": 2}),
    ("vendí 2 atunes", "venta", {"ATU01": 2}),
    ("vendí un papel higienico", "venta", {"PHG01": 1}),
    ("vendí 3 jabones", "venta", {"JAB01": 3}),
    ("vendí 2 frijoles y 3 pastas", "venta", {"FRI01": 2, "PAS01": 3}),
    ("3 leches y 1 pan", "venta", {"LEC01": 3, "PAN01": 1}),
    ("vendi 2 lechez", "venta", {"LEC01": 2}),
    ("fiado: 1 leche y 1 pan a don Jorge", "venta", {"LEC01": 1, "PAN01": 1}),
    ("vendí 2 cocacolas", "venta", {"GAS01": 2}),
    ("despaché una cubeta de huevos", "venta", {"HUE01": 30}),
    ("vendí 2 kumis", "venta", {"YOG01": 2}),
    ("vendí 3 espaguetis", "venta", {"PAS01": 3}),
    # --- compras / entradas
    ("llegaron 30 huevos y 12 leches", "compra", {"HUE01": 30, "LEC01": 12}),
    ("compré 2 pacas de gaseosa", "compra", {"GAS01": 24}),
    ("recibí 20 panes", "compra", {"PAN01": 20}),
    ("me trajeron 10 quesos", "compra", {"QUE01": 10}),
    ("entraron 24 cervezas y 12 aguas", "compra", {"CER01": 24, "AGU01": 12}),
    ("llegó el proveedor con 15 arepas", "compra", {"ARE01": 15}),
    ("compre 10 libras de tomate", "compra", {"TOM01": 10}),
    ("surti 6 aceites", "compra", {"ACE01": 6}),
    ("ingresaron 40 platanos", "compra", {"PLA01": 40}),
    ("compré una canasta de cerveza", "compra", {"CER01": 30}),
    # --- consultas de existencias
    ("¿cuánto arroz me queda?", "stock", {"ARR01": 1}),
    ("cuantas leches me quedan", "stock", {"LEC01": 1}),
    ("cuanto hay de aceite", "stock", {"ACE01": 1}),
    ("tengo de huevos?", "stock", {"HUE01": 1}),
    ("cuantos panes quedan", "stock", {"PAN01": 1}),
    # --- pedido sugerido
    ("¿qué pido mañana?", "pedido", {}),
    ("hazme el pedido", "pedido", {}),
    ("que me falta para surtir", "pedido", {}),
    ("que compro para el fin de semana", "pedido", {}),
    # --- vencimientos
    ("¿qué se me vence?", "vencimientos", {}),
    ("que productos estan por vencer", "vencimientos", {}),
    ("que se me daña esta semana", "vencimientos", {}),
    # --- resumen
    ("¿cómo me fue hoy?", "resumen", {}),
    ("cuanto vendi hoy", "resumen", {}),
    ("hazme el cierre de caja", "resumen", {}),
    # --- crédito
    ("quiero un credito", "credito", {}),
    ("puedo pedir un prestamo?", "credito", {}),
    ("cual es mi puntaje", "credito", {}),
    # --- ayuda
    ("hola", "ayuda", {}),
    ("menu", "ayuda", {}),
    ("que puedes hacer", "ayuda", {}),
    # --- casos difíciles (se espera que algunos fallen y orienten la mejora)
    ("le vendí a la vecina lo de siempre", "venta", {}),
    ("vendí 2 bolsas de leche deslactosada", "venta", {"LEC01": 2}),
    ("vendí una gaseosa grande y unas papitas", "venta", {"GAS01": 1}),
    ("vendí 2 mantequillas", "venta", {}),
]


def evaluar(interprete) -> dict:
    """Devuelve exactitud de intención, exactitud de extracción y fallos."""
    ok_intencion, ok_completo, fallos = 0, 0, []
    for msg, intencion, items in CASOS:
        r = interprete.interpretar(msg)
        bien_int = r.intencion == intencion
        esperado = items if intencion in ("venta", "compra") else {k: 1 for k in items}
        obtenido = r.items if intencion in ("venta", "compra") else {k: 1 for k in r.items}
        bien_items = obtenido == esperado
        ok_intencion += bien_int
        ok_completo += bien_int and bien_items
        if not (bien_int and bien_items):
            fallos.append((msg, intencion, r.intencion, items, r.items))
    n = len(CASOS)
    return {"n": n, "exactitud_intencion": ok_intencion / n, "exactitud_completa": ok_completo / n,
            "fallos": fallos}
