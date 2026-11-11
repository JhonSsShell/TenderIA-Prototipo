"""TenderIA: asistente inteligente para tiendas de barrio.

Prototipo académico (Actividad 4 - Gestión de Innovación y Emprendimiento).
Módulos principales:

- modelos:        entidades del dominio (Producto, Lote, Venta, Tienda).
- datos:          catálogo base y generador de historiales de venta sintéticos.
- inventario:     control de existencias por lotes con rotación FEFO.
- pronostico:     pronóstico de demanda con estacionalidad semanal.
- reabastecimiento: pedido sugerido con stock de seguridad y tope por vida útil.
- alertas:        alertas de vencimiento y descuentos dinámicos.
- credito:        puntaje alternativo de crédito a partir del historial.
- asistente:      intérprete conversacional (simula el canal WhatsApp).
- simulacion:     piloto simulado: gestión empírica vs. TenderIA.
- finanzas:       proyección financiera básica a tres años.
"""

__version__ = "0.1.0"
