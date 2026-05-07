# ==========================================================
# business_rules.py
# Reglas de negocio e interpretación económica del sistema
# Versión 3.0 — Modelo híbrido (residuos WLS + clasificador)
# ==========================================================

SMMLV_2025 = 1_300_000

# ----------------------------------------------------------
# Mapeo ciudad → dominio agrupado y región
# ----------------------------------------------------------
MAP_CIUDAD = {
    "BARRANQUILLA":    {"dominio_agrup": "a_Metro_principal",  "REGION": "ATLÁNTICA"},
    "CARTAGENA":       {"dominio_agrup": "c_Ciudad_intermedia","REGION": "ATLÁNTICA"},
    "MONTERÍA":        {"dominio_agrup": "c_Ciudad_intermedia","REGION": "ATLÁNTICA"},
    "SANTA MARTA":     {"dominio_agrup": "c_Ciudad_intermedia","REGION": "ATLÁNTICA"},
    "SINCELEJO":       {"dominio_agrup": "c_Ciudad_intermedia","REGION": "ATLÁNTICA"},
    "VALLEDUPAR":      {"dominio_agrup": "c_Ciudad_intermedia","REGION": "ATLÁNTICA"},
    "SOLEDAD":         {"dominio_agrup": "d_Periferia_urbana", "REGION": "ATLÁNTICA"},
    "RIOHACHA":        {"dominio_agrup": "e_Resto",            "REGION": "ATLÁNTICA"},
    "BOGOTÁ":          {"dominio_agrup": "a_Metro_principal",  "REGION": "BOGOTÁ"},
    "MEDELLÍN":        {"dominio_agrup": "a_Metro_principal",  "REGION": "CENTRAL"},
    "MANIZALES":       {"dominio_agrup": "b_Metro_regional",   "REGION": "CENTRAL"},
    "PEREIRA":         {"dominio_agrup": "b_Metro_regional",   "REGION": "CENTRAL"},
    "IBAGUÉ":          {"dominio_agrup": "c_Ciudad_intermedia","REGION": "CENTRAL"},
    "NEIVA":           {"dominio_agrup": "c_Ciudad_intermedia","REGION": "CENTRAL"},
    "RIONEGRO":        {"dominio_agrup": "d_Periferia_urbana", "REGION": "CENTRAL"},
    "ARMENIA":         {"dominio_agrup": "e_Resto",            "REGION": "CENTRAL"},
    "FLORENCIA":       {"dominio_agrup": "e_Resto",            "REGION": "CENTRAL"},
    "BUCARAMANGA":     {"dominio_agrup": "b_Metro_regional",   "REGION": "ORIENTAL"},
    "CÚCUTA":          {"dominio_agrup": "b_Metro_regional",   "REGION": "ORIENTAL"},
    "TUNJA":           {"dominio_agrup": "c_Ciudad_intermedia","REGION": "ORIENTAL"},
    "VILLAVICENCIO":   {"dominio_agrup": "c_Ciudad_intermedia","REGION": "ORIENTAL"},
    "BARRANCABERMEJA": {"dominio_agrup": "d_Periferia_urbana", "REGION": "ORIENTAL"},
    "CALI":            {"dominio_agrup": "a_Metro_principal",  "REGION": "PACÍFICA"},
    "YUMBO":           {"dominio_agrup": "d_Periferia_urbana", "REGION": "PACÍFICA"},
    "BUENAVENTURA":    {"dominio_agrup": "e_Resto",            "REGION": "PACÍFICA"},
    "PASTO":           {"dominio_agrup": "e_Resto",            "REGION": "PACÍFICA"},
    "POPAYÁN":         {"dominio_agrup": "e_Resto",            "REGION": "PACÍFICA"},
    "QUIBDÓ":          {"dominio_agrup": "e_Resto",            "REGION": "PACÍFICA"},
    "ARAUCA":          {"dominio_agrup": "e_Resto",            "REGION": "ORIENTAL"},
    "YOPAL":           {"dominio_agrup": "e_Resto",            "REGION": "ORIENTAL"},
}

# ----------------------------------------------------------
# Mapeo nivel educativo → categoría del modelo
# ----------------------------------------------------------
MAP_NIVEL_EDUCATIVO = {
    "Ninguno":           "a_Bajo",
    "Basica Primaria":   "a_Bajo",
    "Basica Secundaria": "b_Medio_bajo",
    "Bachiller":         "b_Medio_bajo",
    "Tecnico Tecnólogo": "c_Medio_alto",
    "Universitaria":     "d_Alto",
    "Postgrado":         "d_Alto",
}

# ----------------------------------------------------------
# Mapeo actividad principal
# ----------------------------------------------------------
MAP_ACTIVIDAD = {
    "Empleado":      "empleado",
    "Independiente": "independiente",
    "Pensionado":    "pensionado",
}

# ----------------------------------------------------------
# Mapeo tipo de vivienda
# ----------------------------------------------------------
MAP_TIPO_VIVIENDA = {
    "Arriendo":           "arriendo",
    "Propia En Pago":     "propia_en_pago",
    "Propia Pagada":      "propia_pagada",
    "Tenencia No Formal": "tenencia_no_formal",
    "Otros":              "otros",
}

# ----------------------------------------------------------
# Rangos de antigüedad (meses)
# ----------------------------------------------------------
MAP_ANTIGUEDAD = {
    "a_inserción_laboral_0_5":           {"min": 0,   "max": 5},
    "b_adaptacion_al_empleo_6_12":       {"min": 6,   "max": 12},
    "c_ingreso_predecible_13_36":        {"min": 13,  "max": 36},
    "d_trayectoria_estable_37_72":       {"min": 37,  "max": 72},
    "e_alta_estabilidad_73_120":         {"min": 73,  "max": 120},
    "f_trayectoria_excepcional_121_mas": {"min": 121, "max": 600},
    "g_desconoce":                       {"min": 997, "max": 999},
}

# ----------------------------------------------------------
# Rangos de edad
# ----------------------------------------------------------
MAP_GRUPO_EDAD = {
    "18-24": {"min": 18, "max": 24},
    "25-34": {"min": 25, "max": 34},
    "35-44": {"min": 35, "max": 44},
    "45-54": {"min": 45, "max": 54},
    "55-64": {"min": 55, "max": 64},
    "65+":   {"min": 65, "max": 80},
}

# ----------------------------------------------------------
# Rangos de aportantes del hogar
# ----------------------------------------------------------
MAP_GRUPO_APORTANTES = {
    "Hogares unipersonales": {"min": 1, "max": 1},
    "Hogares pequeños":      {"min": 2, "max": 2},
    "Hogares medianos":      {"min": 3, "max": 4},
    "Hogares grandes":       {"min": 5, "max": 9},
}

# ----------------------------------------------------------
# Perfiles por clúster — Modelo híbrido
#
# Clúster 0: Alto ingreso, gasto controlado  (residuo ≈ −0.01)
# Clúster 1: Bajo ingreso, ahorradores       (residuo ≈ −0.39)
# Clúster 2: Bajo ingreso, comportamiento típico (residuo ≈ −0.09)
# Clúster 3: Bajo ingreso, alta presión financiera (residuo ≈ +0.47)
# ----------------------------------------------------------
CLUSTER_PROFILES = {
    0: {
        "nombre": "Alto ingreso — Gasto controlado",
        "descripcion": (
            "Solicitantes con ingresos altos (mediana $4.9M) y gasto personal "
            "muy contenido respecto al perfil (residuo mediano −0.01, ratio P50 = 14%). "
            "Representan el 17.4% de la población objetivo. Presentan la mayor "
            "capacidad de endeudamiento y la menor presión financiera relativa."
        ),
        "ratio_referencia": 0.1441,
        "participacion_pct": 17.4,
    },
    1: {
        "nombre": "Bajo ingreso — Ahorradores",
        "descripcion": (
            "Solicitantes con ingresos bajos (mediana $1.5M) que gastan "
            "significativamente menos de lo que su perfil predice "
            "(residuo mediano −0.39, ratio P50 = 12%). Representan el 24.4% "
            "de la población objetivo. Su holgura real es mayor a la estimada "
            "por el modelo de regresión."
        ),
        "ratio_referencia": 0.1195,
        "participacion_pct": 24.4,
    },
    2: {
        "nombre": "Bajo ingreso — Comportamiento típico",
        "descripcion": (
            "Solicitantes con ingresos bajos (mediana $1.6M) cuyo gasto es "
            "consistente con su perfil socioeconómico (residuo mediano −0.09, "
            "ratio P50 = 30%). Representan el 31.3% de la población objetivo. "
            "La presión financiera proviene del nivel de ingreso, no de sobregasto."
        ),
        "ratio_referencia": 0.2964,
        "participacion_pct": 31.3,
    },
    3: {
        "nombre": "Bajo ingreso — Alta presión financiera",
        "descripcion": (
            "Solicitantes con ingresos bajos (mediana $1.5M) que gastan "
            "significativamente más de lo que su perfil predice "
            "(residuo mediano +0.47, ratio P50 = 34%). Representan el 26.9% "
            "de la población objetivo. Este es el segmento de mayor riesgo "
            "financiero relativo: destinan un tercio del ingreso al gasto personal."
        ),
        "ratio_referencia": 0.3372,
        "participacion_pct": 26.9,
    },
}

# ----------------------------------------------------------
# Semáforo de riesgo financiero
# ----------------------------------------------------------
def clasificar_riesgo(percentil: str) -> dict:
    """
    Traduce el percentil del ratio gasto/ingreso estimado
    a un nivel interpretable de riesgo financiero.
    Usa ratio_obs del segmento como referencia.
    """
    if percentil == "p25":
        return {
            "nivel": "Bajo",
            "color": "verde",
            "descripcion": (
                "El gasto estimado se ubica por debajo del percentil 25 "
                "de su segmento. Carga de gasto muy sostenible respecto al ingreso."
            ),
        }
    if percentil == "p50":
        return {
            "nivel": "Bajo-Medio",
            "color": "verde",
            "descripcion": (
                "El gasto estimado se ubica en la mediana de su segmento. "
                "Comportamiento de gasto típico del perfil. Carga manejable."
            ),
        }
    if percentil == "p75":
        return {
            "nivel": "Medio",
            "color": "amarillo",
            "descripcion": (
                "El gasto estimado supera el P75 del segmento. "
                "Presión financiera moderadamente alta. Se recomienda "
                "prudencia en el otorgamiento de crédito adicional."
            ),
        }
    if percentil == "p90":
        return {
            "nivel": "Alto",
            "color": "rojo",
            "descripcion": (
                "El gasto estimado supera el P90 del segmento. "
                "Presión financiera elevada respecto al perfil comparable. "
                "Se recomienda análisis adicional antes de otorgar crédito."
            ),
        }
    return {
        "nivel": "Muy Alto",
        "color": "rojo",
        "descripcion": (
            "El gasto estimado supera el P90 del segmento. "
            "Vulnerabilidad financiera significativa. Alta exposición "
            "ante nuevos compromisos de deuda."
        ),
    }
