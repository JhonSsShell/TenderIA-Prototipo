"""Proyección financiera básica de TenderIA (escenario base, cifras en COP).

Modelo mensual a 60 meses (2027-2031) resumido por año. Todas las cifras son
estimaciones de planeación construidas sobre los supuestos de SUPUESTOS; no
constituyen resultados reales. Los precios se expresan sin IVA.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

ANIO_INICIO = 2027
MESES = 60
SMMLV_2026 = 1_750_905          # Decreto 1469 de 2025
FACTOR_PRESTACIONAL = 1.52      # prestaciones sociales, seguridad social y parafiscales
TASA_IMPUESTO = 0.35            # impuesto de renta personas jurídicas (Colombia)
TASA_DESCUENTO = 0.30           # tasa de descuento anual exigida a un emprendimiento temprano

SUPUESTOS = {
    # --- adopción
    "nuevas_tiendas_mes": [150, 250, 350, 450, 550, 650, 700, 750, 800, 850, 900, 950],  # año 1
    "crecimiento_nuevas_anual": [1.45, 1.25, 1.10, 1.05],   # multiplicador de altas años 2-5
    "churn_basico_mensual": 0.060,
    "churn_pro_mensual": 0.030,
    "conversion_pro_altas": 0.12,       # altas que pasan a Pro tras 30 días de prueba
    "upgrade_mensual_basico": 0.010,    # usuarios básicos que se pasan a Pro cada mes
    # --- precios e ingresos
    "precio_pro_mensual": 29_900,
    "incremento_precio_anual": 0.05,
    "creditos_por_cada_100_activas_mes": 0.6,
    "ticket_promedio_credito": 2_500_000,
    "comision_credito": 0.03,
    "contratos_b2b_fin_de_anio": [2, 5, 9, 12, 14],
    "inicio_b2b_mes": 10,
    "tarifa_b2b_mensual": 6_000_000,
    "inicio_pedidos_mes": 13,
    "participacion_pedidos": [0.0, 0.08, 0.12, 0.15, 0.17],
    "gmv_pedidos_tienda_mes": 900_000,
    "take_rate_pedidos": 0.012,
    # --- costos variables
    "costo_tecnologico_por_activa_mes": 1_200,   # WhatsApp API + modelos de IA + nube
    "pasarela_pago_pct": 0.035,
    "cac_por_alta": 15_000,                      # comisión de agente, material POP, promoción
    # --- costos fijos (mensuales por año)
    "infraestructura_fija": [2_500_000, 4_000_000, 6_000_000, 7_000_000, 8_000_000],
    "marketing_fijo": [3_000_000, 6_000_000, 9_000_000, 10_000_000, 11_000_000],
    "administracion": [4_000_000, 6_000_000, 8_000_000, 9_000_000, 10_000_000],
    "incremento_salarial_anual": 0.06,
}

# Rol, salario mensual año 1 (COP), {año: (personas, mes de inicio dentro del año)}
EQUIPO = [
    ("CEO / Producto (fundador)", 6_000_000, {1: (1, 1), 2: (1, 1), 3: (1, 1), 4: (1, 1), 5: (1, 1)}),
    ("CTO / Desarrollo", 8_000_000, {1: (1, 1), 2: (1, 1), 3: (1, 1), 4: (1, 1), 5: (1, 1)}),
    ("Desarrollador(a) backend e IA", 7_000_000, {1: (1, 1), 2: (2, 1), 3: (3, 1), 4: (3, 1), 5: (4, 1)}),
    ("Científico(a) de datos", 7_500_000, {1: (1, 4), 2: (1, 1), 3: (2, 1), 4: (2, 1), 5: (2, 1)}),
    ("Diseñador(a) UX conversacional", 6_000_000, {2: (1, 1), 3: (1, 1), 4: (1, 1), 5: (1, 1)}),
    ("Líder comercial y alianzas", 5_500_000, {1: (1, 1), 2: (1, 1), 3: (1, 1), 4: (1, 1), 5: (1, 1)}),
    ("Ejecutivo(a) B2B (insights)", 6_500_000, {2: (1, 1), 3: (1, 1), 4: (2, 1), 5: (2, 1)}),
    ("Agentes de campo", 2_000_000, {1: (2, 2), 2: (5, 1), 3: (7, 1), 4: (7, 1), 5: (7, 1)}),
    ("Éxito del cliente / soporte", 2_500_000, {1: (1, 6), 2: (2, 1), 3: (3, 1), 4: (4, 1), 5: (4, 1)}),
]

INVERSION_INICIAL = {
    "Desarrollo del MVP y diseño UX": 30_000_000,
    "Equipos de cómputo (5)": 22_000_000,
    "Protección de datos y asesoría legal": 8_000_000,
    "Constitución S.A.S. y registro de marca": 4_000_000,
}
VIDA_UTIL_EQUIPOS_MESES = 36


CRECIMIENTO_PERPETUO = 0.04    # crecimiento de largo plazo para el valor terminal


@dataclass
class ResultadoFinanciero:
    mensual: pd.DataFrame
    anual: pd.DataFrame
    inversion_inicial: int
    necesidad_financiacion: int
    mes_equilibrio: int | None        # primer mes desde el cual el EBITDA es siempre positivo
    mes_recuperacion: int | None      # mes en que la caja acumulada vuelve a ser positiva
    vpn_sin_vt: float                 # VPN de los 5 años, sin valor terminal
    vpn: float                        # VPN con valor terminal (Gordon)
    tir: float | None                 # TIR con valor terminal
    valor_terminal: float


def economia_unitaria(s: dict | None = None) -> dict:
    """Indicadores por tienda Pro (año 1)."""
    s = {**SUPUESTOS, **(s or {})}
    precio = s["precio_pro_mensual"]
    margen = precio - s["costo_tecnologico_por_activa_mes"] - precio * s["pasarela_pago_pct"]
    cac_pro = s["cac_por_alta"] / s["conversion_pro_altas"]   # conservador: ignora upgrades
    ltv = margen / s["churn_pro_mensual"]
    return {"precio": precio, "margen_contribucion": margen, "margen_pct": margen / precio,
            "cac_por_tienda_pro": cac_pro, "ltv": ltv, "ltv_cac": ltv / cac_pro,
            "meses_recuperar_cac": cac_pro / margen,
            "vida_media_meses": 1 / s["churn_pro_mensual"]}


def _costo_equipo(anio: int, mes_del_anio: int) -> tuple[float, int]:
    inc = (1 + SUPUESTOS["incremento_salarial_anual"]) ** (anio - 1)
    total, personas = 0.0, 0
    for _, salario, plan in EQUIPO:
        n, inicio = plan.get(anio, (0, 1))
        if n and mes_del_anio >= inicio:
            total += n * salario * inc * FACTOR_PRESTACIONAL
            personas += n
    return total, personas


def _tir(flujos: list[float]) -> float | None:
    """TIR anual por bisección (None si no hay cambio de signo)."""
    def vpn(r):
        return sum(f / (1 + r) ** t for t, f in enumerate(flujos))
    bajo, alto = -0.99, 10.0
    if vpn(bajo) * vpn(alto) > 0:
        return None
    for _ in range(200):
        medio = (bajo + alto) / 2
        if vpn(bajo) * vpn(medio) <= 0:
            alto = medio
        else:
            bajo = medio
    return (bajo + alto) / 2


def proyectar(s: dict | None = None) -> ResultadoFinanciero:
    s = {**SUPUESTOS, **(s or {})}
    filas = []
    basicas, pro = 0.0, 0.0
    altas_anio1 = s["nuevas_tiendas_mes"]
    for t in range(1, MESES + 1):
        anio = (t - 1) // 12 + 1
        mes = (t - 1) % 12 + 1
        # altas del mes
        if anio == 1:
            altas = altas_anio1[mes - 1]
        else:
            factor = np.prod(s["crecimiento_nuevas_anual"][: anio - 1])
            altas = altas_anio1[-1] * factor
        # dinámica de usuarios
        nuevas_pro = altas * s["conversion_pro_altas"] + basicas * s["upgrade_mensual_basico"]
        basicas = basicas * (1 - s["churn_basico_mensual"]) + altas - nuevas_pro
        pro = pro * (1 - s["churn_pro_mensual"]) + nuevas_pro
        activas = basicas + pro
        # ingresos
        precio = s["precio_pro_mensual"] * (1 + s["incremento_precio_anual"]) ** (anio - 1)
        ing_suscripcion = pro * precio
        creditos = activas * s["creditos_por_cada_100_activas_mes"] / 100
        ing_credito = creditos * s["ticket_promedio_credito"] * s["comision_credito"]
        if t >= s["inicio_b2b_mes"]:
            meta = s["contratos_b2b_fin_de_anio"][anio - 1]
            previo = s["contratos_b2b_fin_de_anio"][anio - 2] if anio > 1 else 0
            contratos = round(previo + (meta - previo) * mes / 12)
        else:
            contratos = 0
        ing_b2b = contratos * s["tarifa_b2b_mensual"] * (1 + s["incremento_precio_anual"]) ** (anio - 1)
        part = s["participacion_pedidos"][anio - 1] if t >= s["inicio_pedidos_mes"] else 0.0
        ing_pedidos = activas * part * s["gmv_pedidos_tienda_mes"] * s["take_rate_pedidos"]
        ingresos = ing_suscripcion + ing_credito + ing_b2b + ing_pedidos
        # costos
        nomina, personas = _costo_equipo(anio, mes)
        c_tec = activas * s["costo_tecnologico_por_activa_mes"] + s["infraestructura_fija"][anio - 1]
        c_pasarela = ing_suscripcion * s["pasarela_pago_pct"]
        c_cac = altas * s["cac_por_alta"]
        c_mkt = s["marketing_fijo"][anio - 1]
        c_admin = s["administracion"][anio - 1]
        costos = nomina + c_tec + c_pasarela + c_cac + c_mkt + c_admin
        ebitda = ingresos - costos
        depreciacion = (INVERSION_INICIAL["Equipos de cómputo (5)"] / VIDA_UTIL_EQUIPOS_MESES
                        if t <= VIDA_UTIL_EQUIPOS_MESES else 0.0)
        filas.append({
            "mes": t, "anio": ANIO_INICIO + anio - 1, "altas": altas, "tiendas_activas": activas,
            "tiendas_pro": pro, "contratos_b2b": contratos, "personas_equipo": personas,
            "ing_suscripcion": ing_suscripcion, "ing_credito": ing_credito, "ing_b2b": ing_b2b,
            "ing_pedidos": ing_pedidos, "ingresos": ingresos,
            "c_nomina": nomina, "c_tecnologia": c_tec, "c_pasarela": c_pasarela, "c_adquisicion": c_cac,
            "c_marketing": c_mkt, "c_administracion": c_admin, "costos": costos,
            "ebitda": ebitda, "depreciacion": depreciacion,
        })
    m = pd.DataFrame(filas)

    # resumen anual con impuesto de renta y compensación de pérdidas
    a = m.groupby("anio").agg({
        "altas": "sum", "tiendas_activas": "last", "tiendas_pro": "last", "contratos_b2b": "last",
        "personas_equipo": "last", "ing_suscripcion": "sum", "ing_credito": "sum", "ing_b2b": "sum",
        "ing_pedidos": "sum", "ingresos": "sum", "c_nomina": "sum", "c_tecnologia": "sum",
        "c_pasarela": "sum", "c_adquisicion": "sum", "c_marketing": "sum", "c_administracion": "sum",
        "costos": "sum", "ebitda": "sum", "depreciacion": "sum",
    })
    perdidas = 0.0
    impuestos = []
    for _, fila in a.iterrows():
        base = fila["ebitda"] - fila["depreciacion"]
        if base < 0:
            perdidas += -base
            impuestos.append(0.0)
        else:
            compensa = min(perdidas, base)
            perdidas -= compensa
            impuestos.append((base - compensa) * TASA_IMPUESTO)
    a["impuesto_renta"] = impuestos
    a["utilidad_neta"] = a["ebitda"] - a["depreciacion"] - a["impuesto_renta"]
    a["flujo_caja_libre"] = a["ebitda"] - a["impuesto_renta"]
    a["margen_ebitda"] = a["ebitda"] / a["ingresos"]

    inversion = sum(INVERSION_INICIAL.values())
    # caja acumulada mensual (impuesto provisionado mes a mes vía anticipos y retenciones)
    imp_mes = np.zeros(MESES)
    for i, imp in enumerate(impuestos):
        imp_mes[i * 12:(i + 1) * 12] = imp / 12
    caja = -inversion + np.cumsum(m["ebitda"].to_numpy() - imp_mes)
    m["caja_acumulada"] = caja
    necesidad = int(round(-caja.min(), -6)) if caja.min() < 0 else 0
    positivos = m.index[m["ebitda"] > 0].tolist()
    mes_eq = None
    for idx in positivos:
        if (m.loc[idx:, "ebitda"] > 0).all():
            mes_eq = int(m.loc[idx, "mes"])
            break
    mes_rec = None
    for idx in range(len(caja)):
        if caja[idx] > 0 and (caja[idx:] > 0).all():
            mes_rec = idx + 1
            break
    flujos = [-inversion] + a["flujo_caja_libre"].tolist()
    vpn_sin_vt = sum(f / (1 + TASA_DESCUENTO) ** k for k, f in enumerate(flujos))
    vt = flujos[-1] * (1 + CRECIMIENTO_PERPETUO) / (TASA_DESCUENTO - CRECIMIENTO_PERPETUO)
    flujos_vt = flujos[:-1] + [flujos[-1] + vt]
    vpn = sum(f / (1 + TASA_DESCUENTO) ** k for k, f in enumerate(flujos_vt))
    return ResultadoFinanciero(m, a, inversion, necesidad, mes_eq, mes_rec, vpn_sin_vt, vpn,
                               _tir(flujos_vt), vt)


ESCENARIOS = {
    "Pesimista": {"conversion_pro_altas": 0.08, "churn_pro_mensual": 0.045, "upgrade_mensual_basico": 0.006,
                  "contratos_b2b_fin_de_anio": [1, 3, 6, 8, 10]},
    "Base": {},
    "Optimista": {"conversion_pro_altas": 0.15, "churn_pro_mensual": 0.025, "upgrade_mensual_basico": 0.012,
                  "contratos_b2b_fin_de_anio": [3, 7, 12, 15, 18]},
}


def analisis_escenarios() -> pd.DataFrame:
    filas = []
    for nombre, cambios in ESCENARIOS.items():
        r = proyectar(cambios)
        filas.append({
            "escenario": nombre,
            "ingresos_2029": r.anual.loc[2029, "ingresos"], "ingresos_2031": r.anual.loc[2031, "ingresos"],
            "ebitda_2031": r.anual.loc[2031, "ebitda"], "necesidad_financiacion": r.necesidad_financiacion,
            "mes_equilibrio": r.mes_equilibrio, "vpn": r.vpn, "tir": r.tir,
        })
    return pd.DataFrame(filas).set_index("escenario")


def exportar_excel(resultado: ResultadoFinanciero, ruta: str) -> None:
    with pd.ExcelWriter(ruta) as w:
        pd.DataFrame([{"supuesto": k, "valor": str(v)} for k, v in SUPUESTOS.items()]).to_excel(
            w, sheet_name="Supuestos", index=False)
        resultado.anual.to_excel(w, sheet_name="Resumen anual")
        resultado.mensual.to_excel(w, sheet_name="Proyeccion mensual", index=False)
        pd.DataFrame([{"rol": r, "salario_mensual_anio1": s, "plan": str(p)} for r, s, p in EQUIPO]).to_excel(
            w, sheet_name="Equipo", index=False)
        pd.DataFrame(list(INVERSION_INICIAL.items()), columns=["concepto", "valor"]).to_excel(
            w, sheet_name="Inversion inicial", index=False)


if __name__ == "__main__":
    r = proyectar()
    pd.set_option("display.width", 200)
    print((r.anual[["tiendas_activas", "tiendas_pro", "ingresos", "costos", "ebitda", "margen_ebitda",
                    "utilidad_neta", "personas_equipo"]] / [1, 1, 1e6, 1e6, 1e6, 1, 1e6, 1]).round(2))
    print("Inversión inicial:", r.inversion_inicial, "Necesidad de financiación:", r.necesidad_financiacion)
    print("Mes de equilibrio EBITDA:", r.mes_equilibrio, "Mes de recuperación de caja:", r.mes_recuperacion)
    print("VPN sin VT:", round(r.vpn_sin_vt / 1e6, 1), "M | VPN con VT:", round(r.vpn / 1e6, 1),
          "M | TIR:", None if r.tir is None else round(r.tir * 100, 1), "%")
    print({k: round(v, 2) for k, v in economia_unitaria().items()})
