"""Ejecuta las pruebas preliminares de la etapa "Probar" de Design Thinking.

1. Precisión del intérprete conversacional sobre el corpus de 60 mensajes.
2. Precisión del pronóstico (backtest rodante a 28 días vs. método ingenuo).
3. Piloto simulado de 90 días en 30 tiendas: gestión empírica vs. TenderIA,
   y análisis de la contribución de cada funcionalidad (palancas).
4. Proyección financiera y análisis de escenarios.

Uso:  python ejecutar_pruebas_preliminares.py
Salidas en ./resultados (CSV, JSON y Excel) para el informe y las diapositivas.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from tenderia.asistente import InterpreteMensajes
from tenderia.corpus_prueba import evaluar
from tenderia.datos import CATALOGO, CATALOGO_POR_SKU, generar_historial, serie_por_sku
from tenderia.finanzas import analisis_escenarios, economia_unitaria, exportar_excel, proyectar
from tenderia.pronostico import PronosticadorDemanda
from tenderia.simulacion import analisis_palancas, correr_piloto, resumen_piloto

SALIDA = Path(__file__).parent / "resultados"


def main() -> None:
    SALIDA.mkdir(exist_ok=True)
    resumen: dict = {}

    # 1. Intérprete conversacional
    r = evaluar(InterpreteMensajes(CATALOGO_POR_SKU))
    resumen["interprete"] = {"mensajes": r["n"], "exactitud_intencion": r["exactitud_intencion"],
                             "exactitud_completa": r["exactitud_completa"],
                             "fallos": [f[0] for f in r["fallos"]]}
    print(f"[1] Intérprete: intención {r['exactitud_intencion']:.1%} | "
          f"intención + productos + cantidades {r['exactitud_completa']:.1%} (n={r['n']})")

    # 2. Pronóstico
    filas = []
    for semilla in (4, 5, 6):
        hist = generar_historial(dias=150, semilla=semilla)
        for p in CATALOGO:
            bt = PronosticadorDemanda.backtest(serie_por_sku(hist, p.sku), dias_prueba=28)
            filas.append({"semilla": semilla, "sku": p.sku, "perecedero": p.perecedero,
                          "wape_modelo": bt.wape_modelo, "wape_ingenuo": bt.wape_ingenuo})
    bt = pd.DataFrame(filas)
    bt.to_csv(SALIDA / "backtest_pronostico.csv", index=False)
    wm, wi = bt["wape_modelo"].mean(), bt["wape_ingenuo"].mean()
    resumen["pronostico"] = {"wape_modelo": wm, "wape_ingenuo": wi, "mejora_pct": (1 - wm / wi) * 100,
                             "sku_donde_mejora_pct": float((bt["wape_modelo"] < bt["wape_ingenuo"]).mean() * 100)}
    print(f"[2] Pronóstico: WAPE modelo {wm:.1%} vs. ingenuo {wi:.1%} "
          f"(mejora {(1 - wm / wi) * 100:.1f} %)")

    # 3. Piloto simulado
    t0 = time.time()
    piloto = correr_piloto(n_tiendas=30, dias_eval=90)
    piloto.to_csv(SALIDA / "piloto_simulado_detalle.csv", index=False)
    res = resumen_piloto(piloto)
    res.to_csv(SALIDA / "piloto_simulado_resumen.csv")
    e, t = res["empirico"], res["tenderia"]
    pares = piloto.pivot(index="tienda", columns="escenario", values="merma_pct_perecederos")
    resumen["piloto"] = {
        "tiendas": 30, "dias": 90,
        "merma_empirico": e["merma_pct_perecederos"], "merma_tenderia": t["merma_pct_perecederos"],
        "reduccion_merma_pct": (1 - t["merma_pct_perecederos"] / e["merma_pct_perecederos"]) * 100,
        "servicio_empirico": e["nivel_servicio"], "servicio_tenderia": t["nivel_servicio"],
        "ventas_perdidas_empirico": e["ventas_perdidas_u"], "ventas_perdidas_tenderia": t["ventas_perdidas_u"],
        "reduccion_ventas_perdidas_pct": (1 - t["ventas_perdidas_u"] / e["ventas_perdidas_u"]) * 100,
        "costo_merma_empirico": e["costo_merma"], "costo_merma_tenderia": t["costo_merma"],
        "margen_empirico": e["margen_neto_merma"], "margen_tenderia": t["margen_neto_merma"],
        "aumento_margen_pct": (t["margen_neto_merma"] / e["margen_neto_merma"] - 1) * 100,
        "inventario_empirico": e["inventario_promedio_costo"], "inventario_tenderia": t["inventario_promedio_costo"],
        "tiendas_con_menor_merma": int((pares["tenderia"] < pares["empirico"]).sum()),
        "kg_vencidos_empirico": e["kg_vencidos"], "kg_vencidos_tenderia": t["kg_vencidos"],
        "kg_salvados_tienda_anio": (e["kg_vencidos"] - t["kg_vencidos"]) * 365 / 90,
        "ahorro_merma_tienda_anio": (e["costo_merma"] - t["costo_merma"]) * 365 / 90,
    }
    p = resumen["piloto"]
    print(f"[3] Piloto ({time.time() - t0:.0f} s): merma perecederos {p['merma_empirico']:.2%} -> "
          f"{p['merma_tenderia']:.2%} (-{p['reduccion_merma_pct']:.0f} %); nivel de servicio "
          f"{p['servicio_empirico']:.1%} -> {p['servicio_tenderia']:.1%}; margen neto "
          f"+{p['aumento_margen_pct']:.1f} %; inventario {p['inventario_empirico']:,.0f} -> "
          f"{p['inventario_tenderia']:,.0f}")

    # 3b. Contribución de cada funcionalidad (análisis por palanca)
    pal = analisis_palancas(n_tiendas=12)
    pal.to_csv(SALIDA / "analisis_palancas.csv")
    resumen["palancas"] = pal.reset_index().to_dict(orient="records")
    print("[3b] Palancas (merma perecederos):",
          {k: f"{v:.2%}" for k, v in pal["merma_pct_perecederos"].items()})

    # 4. Finanzas
    fin = proyectar()
    exportar_excel(fin, str(SALIDA / "proyeccion_financiera_TenderIA.xlsx"))
    esc = analisis_escenarios()
    esc.to_csv(SALIDA / "escenarios_financieros.csv")
    resumen["finanzas"] = {
        "inversion_inicial": fin.inversion_inicial, "necesidad_financiacion": fin.necesidad_financiacion,
        "mes_equilibrio": fin.mes_equilibrio, "mes_recuperacion": fin.mes_recuperacion,
        "vpn": fin.vpn, "vpn_sin_vt": fin.vpn_sin_vt, "tir": fin.tir,
        "anual": fin.anual.reset_index().to_dict(orient="records"),
        "unitaria": economia_unitaria(),
        "escenarios": esc.reset_index().to_dict(orient="records"),
    }
    print(f"[4] Finanzas: necesidad {fin.necesidad_financiacion:,.0f}; equilibrio mes {fin.mes_equilibrio}; "
          f"VPN {fin.vpn:,.0f}; TIR {fin.tir:.1%}")

    def _json(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        raise TypeError(type(o))

    (SALIDA / "resumen_resultados.json").write_text(
        json.dumps(resumen, indent=2, ensure_ascii=False, default=_json), encoding="utf-8")
    print(f"Resultados guardados en {SALIDA}")


if __name__ == "__main__":
    main()
