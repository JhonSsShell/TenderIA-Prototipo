"""Pruebas unitarias del prototipo TenderIA (ejecutar con: python -m pytest -q)."""
from datetime import date, timedelta

import pandas as pd
import pytest

from tenderia.alertas import descuento_sugerido, generar_alertas
from tenderia.asistente import InterpreteMensajes, construir_demo, normalizar
from tenderia.corpus_prueba import evaluar
from tenderia.credito import calcular_puntaje
from tenderia.datos import CATALOGO_POR_SKU, generar_historial, serie_por_sku
from tenderia.finanzas import economia_unitaria, proyectar
from tenderia.inventario import Inventario
from tenderia.pronostico import PronosticadorDemanda
from tenderia.reabastecimiento import calcular_pedido

HOY = date(2026, 11, 5)


# ----------------------------------------------------------------- inventario
def test_fefo_vende_primero_lo_que_vence_primero():
    inv = Inventario(CATALOGO_POR_SKU, "FEFO")
    viejo = inv.registrar_compra("LEC01", 5, HOY - timedelta(days=5))
    inv.registrar_compra("LEC01", 5, HOY)
    inv.registrar_venta("LEC01", 3)
    assert viejo.cantidad == 2
    assert inv.stock("LEC01") == 7


def test_lifo_vende_primero_lo_mas_reciente():
    inv = Inventario(CATALOGO_POR_SKU, "LIFO")
    viejo = inv.registrar_compra("LEC01", 5, HOY - timedelta(days=5))
    inv.registrar_compra("LEC01", 5, HOY)
    inv.registrar_venta("LEC01", 3)
    assert viejo.cantidad == 5


def test_venta_no_supera_existencias():
    inv = Inventario(CATALOGO_POR_SKU)
    inv.registrar_compra("PAN01", 2, HOY)
    assert inv.registrar_venta("PAN01", 5) == 2
    assert inv.stock("PAN01") == 0


def test_retiro_de_vencidos_cuenta_merma():
    inv = Inventario(CATALOGO_POR_SKU)
    inv.registrar_compra("PAN01", 4, HOY - timedelta(days=6))  # vida útil 6 días
    merma = inv.retirar_vencidos(HOY)
    assert merma == {"PAN01": 4}
    assert inv.stock("PAN01") == 0


def test_compra_invalida():
    with pytest.raises(ValueError):
        Inventario(CATALOGO_POR_SKU).registrar_compra("PAN01", 0, HOY)


# ----------------------------------------------------------------- pronóstico
def test_pronostico_no_es_peor_que_metodo_ingenuo():
    hist = generar_historial(dias=150, semilla=4)
    resultados = [PronosticadorDemanda.backtest(serie_por_sku(hist, sku), dias_prueba=28)
                  for sku in ("CER01", "GAS01", "LEC01", "HUE01", "PAN01", "QUE01", "ARR01")]
    wape_modelo = sum(r.wape_modelo for r in resultados) / len(resultados)
    wape_ingenuo = sum(r.wape_ingenuo for r in resultados) / len(resultados)
    assert wape_modelo <= wape_ingenuo


def test_pronostico_capta_fin_de_semana():
    hist = generar_historial(dias=120, semilla=5)
    m = PronosticadorDemanda().ajustar(serie_por_sku(hist, "CER01"))
    assert m.indices_semana[5] > m.indices_semana[1]  # sábado > martes


def test_pronostico_requiere_historia_minima():
    serie = pd.Series([1.0] * 10, index=pd.date_range("2026-01-01", periods=10))
    with pytest.raises(ValueError):
        PronosticadorDemanda().ajustar(serie)


# -------------------------------------------------------------- reabastecimiento
def test_pedido_respeta_multiplo_de_compra():
    p = CATALOGO_POR_SKU["ARR01"]  # paca de 25
    ped = calcular_pedido(p, existencias=3, en_transito=0, demanda_diaria=[12] * 10, sigma=3, revision_dias=5)
    assert ped.cantidad % 25 == 0 and ped.cantidad > 0


def test_pedido_perecedero_limitado_por_vida_util():
    p = CATALOGO_POR_SKU["PAN01"]  # vida útil 6 días
    ped = calcular_pedido(p, 0, 0, [5] * 10, sigma=50, revision_dias=1)
    assert ped.cantidad <= 0.9 * 5 * p.vida_util_dias + p.multiplo_compra


def test_sin_pedido_si_hay_existencias_suficientes():
    p = CATALOGO_POR_SKU["ACE01"]
    assert calcular_pedido(p, 500, 0, [3] * 10, sigma=1).cantidad == 0


# ------------------------------------------------------------------- alertas
def test_descuento_escalonado():
    assert descuento_sugerido(1, 0.6) > descuento_sugerido(3, 0.6)
    assert descuento_sugerido(1, 0.0) == 0
    assert descuento_sugerido(1, 0.9) <= 40


def test_alerta_para_lote_proximo_a_vencer():
    inv = Inventario(CATALOGO_POR_SKU)
    inv.registrar_compra("QUE01", 20, HOY - timedelta(days=9))  # vida útil 10 -> vence mañana
    alertas = generar_alertas(inv, HOY, {"QUE01": 4.0})
    assert alertas and alertas[0].sku == "QUE01" and alertas[0].descuento_pct > 0


# ------------------------------------------------------------------- crédito
def test_puntaje_en_rango_y_estabilidad_premiada():
    idx = pd.date_range("2026-08-01", periods=90)
    estable = pd.Series(500_000.0, index=idx)
    erratica = pd.Series([0.0 if i % 3 else 1_500_000.0 for i in range(90)], index=idx)
    p1, p2 = calcular_puntaje(estable, 0.22), calcular_puntaje(erratica, 0.22)
    assert 300 <= p2.puntaje < p1.puntaje <= 850


# ---------------------------------------------------------------- asistente
def test_normalizar_quita_tildes_y_signos():
    assert normalizar("¿Cuánto ARROZ me queda?") == "cuanto arroz me queda"


@pytest.mark.parametrize("mensaje, esperado", [
    ("vendí 3 leches y 2 panes", {"LEC01": 3, "PAN01": 2}),
    ("vendí media docena de huevos", {"HUE01": 6}),
    ("fié 2 arroces a doña Rosa", {"ARR01": 2}),
    ("vendi 2 gaseosas, 1 agua y 3 galletas", {"GAS01": 2, "AGU01": 1, "GAL01": 3}),
])
def test_extraccion_de_items(mensaje, esperado):
    assert InterpreteMensajes(CATALOGO_POR_SKU).interpretar(mensaje).items == esperado


def test_fiado_detectado():
    assert InterpreteMensajes(CATALOGO_POR_SKU).interpretar("fié 2 arroces a doña Rosa").fiado


def test_exactitud_minima_del_interprete():
    r = evaluar(InterpreteMensajes(CATALOGO_POR_SKU))
    assert r["exactitud_intencion"] >= 0.9
    assert r["exactitud_completa"] >= 0.85


def test_flujo_conversacional_completo():
    a = construir_demo(HOY)
    stock_antes = a.inventario.stock("LEC01")
    assert "Venta registrada" in a.responder("vendí 3 leches")
    assert a.inventario.stock("LEC01") == stock_antes - 3
    assert "Entrada de mercancía" in a.responder("llegaron 12 leches")
    assert "Pedido sugerido" in a.responder("¿qué pido mañana?") or "No necesitas" in a.responder("¿qué pido?")
    assert "puntaje" in a.responder("quiero un credito")


# ---------------------------------------------------------------- finanzas
def test_proyeccion_coherente():
    r = proyectar()
    assert len(r.mensual) == 60 and list(r.anual.index) == [2027, 2028, 2029, 2030, 2031]
    assert (r.anual["ingresos"].diff().dropna() > 0).all()
    assert r.necesidad_financiacion > 0 and r.mes_equilibrio is not None


def test_economia_unitaria_saludable():
    u = economia_unitaria()
    assert u["ltv_cac"] > 3 and u["meses_recuperar_cac"] < 12
