# TenderIA · Prototipo funcional (Python)

Prototipo académico de la Actividad 4 de *Gestión de la Innovación y Emprendimiento*.
TenderIA es un asistente con IA que funciona dentro de WhatsApp para que las tiendas de
barrio registren ventas conversando, reciban un pedido sugerido, eviten el vencimiento de
perecederos y construyan un historial útil para acceder a microcrédito.

> Todos los datos son **sintéticos**. Los resultados del piloto son una simulación que
> debe validarse con tenderos reales.

## Requisitos

- Python 3.10 o superior (probado con 3.12)
- Dependencias: `pip install -r requirements.txt`

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
```

```bash
python -m pytest -q
```

```bash
python ejecutar_pruebas_preliminares.py
```

```bash
streamlit run app.py
```

```bash
python herramientas/generar_figuras.py
```

1. `pytest` corre las 24 pruebas unitarias.
2. `ejecutar_pruebas_preliminares.py` produce la evidencia de la etapa **Probar** en
   `resultados/`: precisión del intérprete (60 mensajes), backtest del pronóstico, piloto
   simulado de 30 tiendas × 90 días, análisis por funcionalidad y proyección financiera
   (incluye `proyeccion_financiera_TenderIA.xlsx`).
3. `streamlit run app.py` abre la demostración (chat tipo WhatsApp, inventario, pronóstico,
   puntaje de crédito, piloto y finanzas) en `http://localhost:8501`.
4. `generar_figuras.py` regenera los diagramas UML y las gráficas en `../imagenes/`.

## Estructura

| Módulo | Qué hace |
|---|---|
| `tenderia/modelos.py` | Entidades: `Producto`, `Lote`, `Venta`, `Tienda`, `MedioPago` |
| `tenderia/datos.py` | Catálogo de 24 productos y generador de ventas sintéticas (fin de semana, quincena, sobredispersión) |
| `tenderia/inventario.py` | Inventario por lotes con rotación FEFO, LIFO o mixta |
| `tenderia/pronostico.py` | Suavizamiento exponencial con índices de día de la semana y quincena; backtest |
| `tenderia/reabastecimiento.py` | Pedido sugerido con stock de seguridad, múltiplo de compra y tope por vida útil |
| `tenderia/alertas.py` | Alertas de vencimiento con descuento escalonado |
| `tenderia/credito.py` | Puntaje alternativo 300–850 (regularidad, estabilidad, tendencia, margen, fiados) |
| `tenderia/asistente.py` | Intérprete de mensajes en español coloquial y orquestador del chat |
| `tenderia/corpus_prueba.py` | 60 mensajes de prueba para medir el intérprete |
| `tenderia/simulacion.py` | Piloto simulado: gestión empírica vs. TenderIA, y análisis por palanca |
| `tenderia/finanzas.py` | Proyección financiera mensual a 60 meses, economía unitaria y escenarios |
| `app.py` | Interfaz de demostración en Streamlit |
| `tests/test_tenderia.py` | Pruebas unitarias |

## Resultados de referencia (semilla fija)

- Intérprete: intención 100 %; intención + productos + cantidades 98,3 % (60 mensajes).
- Pronóstico: WAPE 51,2 % frente a 52,0 % del promedio de 7 días.
- Piloto simulado: merma de perecederos 2,89 % → 0,83 % (−71 %); nivel de servicio 98,3 % → 99,2 %;
  margen neto de merma +4,7 %; inventario promedio +14,6 %.
- Finanzas (escenario base): necesidad de financiación COP 1.611 millones; EBITDA positivo desde el
  mes 30; LTV/CAC 7,4.
