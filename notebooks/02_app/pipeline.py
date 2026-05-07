# ==========================================================
# pipeline.py
# Motor de inferencia — Estimación del gasto personal
# Versión 3.0 — Modelo híbrido (residuos WLS + clasificador)
# Arquitectura: notebooks/02_app/
# ==========================================================
#
# Flujo de producción:
#   1. Recibe variables socioeconómicas verificables en originación
#   2. Estima log_gasto mediante modelo WLS
#   3. Calcula ratio_estimado = gasto_WLS / ingreso
#   4. Asigna segmento mediante clasificador logístico (sin residuo)
#   5. Entrega percentiles del ratio_obs del segmento + señal P(C3)
#
# IMPORTANTE: Este pipeline NO requiere el gasto observado
# del solicitante. Todas las variables de entrada están
# disponibles en el momento de la solicitud de crédito.
#
# NUM_VARS WLS (float): log_ingresos_2025, Edad,
#                       Aportantes_Hogar, log_inc_x_estrato
# CAT_VARS WLS:         Estrato (int64!), REGION, actividad_ppal, Sexo_,
#                       nivel_educ_agrupado, antiguedad_agrup,
#                       Grupo_Edad, EstadoCivil_hom,
#                       Grupo_Aportantes, tipo_vivienda_agrup,
#                       dominio_agrup, flag_pensionado
#
# NUM_CLF (float): log_ingresos_2025, log_gasto_pred_w,
#                  log_ratio_estimado, Estrato, Edad,
#                  Aportantes_Hogar
# CAT_CLF (str):   nivel_educ_agrupado, actividad_ppal,
#                  tipo_vivienda_agrup, Grupo_Edad,
#                  Grupo_Aportantes, REGION, flag_pensionado
# ==========================================================

import os
import joblib
import numpy as np
import pandas as pd

from business_rules import (
    CLUSTER_PROFILES,
    MAP_CIUDAD,
    MAP_ACTIVIDAD,
    MAP_NIVEL_EDUCATIVO,
    MAP_TIPO_VIVIENDA,
    MAP_ANTIGUEDAD,
    MAP_GRUPO_EDAD,
    MAP_GRUPO_APORTANTES,
    clasificar_riesgo,
)

# ----------------------------------------------------------
# 1. CONFIGURACIÓN DE RUTAS
# ----------------------------------------------------------
# Estructura esperada:
#   01_tesis_v4/
#   └── notebooks/
#       ├── artefactos_modelo_hibrido.pkl   ← generado por NB05
#       └── 02_app/
#           ├── pipeline.py                 ← este archivo
#           ├── app.py
#           ├── business_rules.py
#           └── persistence.py

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))   # notebooks/02_app/
NOTEBOOKS_DIR = os.path.dirname(BASE_DIR)                   # notebooks/

# El pkl lo genera NB05 en la carpeta notebooks/
ARTEFACTS_PATH = os.path.join(NOTEBOOKS_DIR, "artefactos_modelo_hibrido.pkl")

# Fallback: buscar también en el directorio de trabajo actual
if not os.path.exists(ARTEFACTS_PATH):
    ARTEFACTS_PATH = os.path.join(os.getcwd(), "artefactos_modelo_hibrido.pkl")

SMMLV_2025 = 1_300_000


# ----------------------------------------------------------
# 2. CARGA Y VALIDACIÓN DEL ARTEFACTO HÍBRIDO
# ----------------------------------------------------------
def _validar_artefactos(art):
    requeridos = {
        "model_wls",
        "clf_pipeline",
        "ratio_table_hibrido",
        "cluster_map_hibrido",
        "umbral_c3_optimo",
    }
    faltantes = requeridos - set(art.keys())
    if faltantes:
        raise ValueError(
            f"Artefacto incompleto. Faltan claves: {sorted(faltantes)}\n"
            f"Ruta buscada: {ARTEFACTS_PATH}\n"
            "Asegúrate de haber ejecutado NB05 (05_modelo_hibrido.ipynb) completamente."
        )
    for cluster_ord, tabla in art["ratio_table_hibrido"].items():
        for p in ["p25_obs", "p50_obs", "p75_obs", "p90_obs"]:
            if p not in tabla:
                raise ValueError(
                    f"Falta `{p}` en ratio_table_hibrido[{cluster_ord}]."
                )


if not os.path.exists(ARTEFACTS_PATH):
    raise FileNotFoundError(
        f"No se encontró el artefacto del modelo en:\n  {ARTEFACTS_PATH}\n"
        "Ejecuta NB05 desde el orquestador y vuelve a iniciar la app."
    )

artefactos   = joblib.load(ARTEFACTS_PATH)
_validar_artefactos(artefactos)

model_wls    = artefactos["model_wls"]
clf_pipeline = artefactos["clf_pipeline"]
RATIO_TABLE  = artefactos["ratio_table_hibrido"]
CLUSTER_MAP  = artefactos["cluster_map_hibrido"]
UMBRAL_C3    = artefactos["umbral_c3_optimo"]     # 0.50

# Features del modelo WLS — extraídas del pipeline entrenado
FEATURES = list(model_wls.feature_names_in_)


# ----------------------------------------------------------
# 3. FUNCIONES AUXILIARES
# ----------------------------------------------------------

def _map_rango(valor, mapping, nombre):
    for categoria, rango in mapping.items():
        if rango["min"] <= valor <= rango["max"]:
            return categoria
    raise ValueError(
        f"Valor fuera de dominio para '{nombre}': {valor}. "
        f"Rangos válidos: {list(mapping.keys())}"
    )


def _validar_input(payload):
    if float(payload["ingreso_mensual_total"]) < SMMLV_2025:
        raise ValueError(
            f"Ingreso inferior a 1 SMMLV (${SMMLV_2025:,.0f}). "
            "El modelo no es válido para este rango de ingreso."
        )
    edad = int(payload["edad"])
    if not (18 <= edad <= 80):
        raise ValueError(
            f"Edad {edad} fuera del rango permitido (18–80 años)."
        )


def _clasificar_percentil(ratio, cluster_ord):
    """Usa ratio_obs (comportamiento real del segmento)."""
    tabla = RATIO_TABLE.get(cluster_ord)
    if tabla is None:
        raise ValueError(
            f"No existe ratio_table para cluster_ord={cluster_ord}."
        )
    if ratio <= tabla["p25_obs"]: return "p25"
    if ratio <= tabla["p50_obs"]: return "p50"
    if ratio <= tabla["p75_obs"]: return "p75"
    if ratio <= tabla["p90_obs"]: return "p90"
    return "p100"


# ----------------------------------------------------------
# 4. DATAFRAME PARA EL MODELO WLS
# ----------------------------------------------------------

def _construir_df_regresion(payload):
    """
    Construye el DataFrame exacto que espera el modelo WLS.
    NUM_VARS: float  |  CAT_VARS: str
    Nota: Estrato y flag_pensionado son CAT_VARS en el WLS.
    """
    _validar_input(payload)

    ciudad = str(payload["ciudad"]).upper()
    if ciudad not in MAP_CIUDAD:
        raise ValueError(f"Ciudad fuera de dominio: '{ciudad}'")

    actividad  = payload["actividad_principal"]
    nivel_educ = payload["nivel_educativo"]
    tipo_viv   = payload["tipo_vivienda"]

    ciudad_info   = MAP_CIUDAD[ciudad]
    ingreso       = float(payload["ingreso_mensual_total"])
    log_ingreso   = np.log(ingreso)
    estrato       = int(payload["estrato"])
    es_pensionado = (actividad == "Pensionado")

    row = {
        # ── NUM_VARS (float) ─────────────────────────────
        "log_ingresos_2025"  : log_ingreso,
        "Edad"               : float(payload["edad"]),
        "Aportantes_Hogar"   : float(payload["aportantes_hogar"]),
        "log_inc_x_estrato"  : log_ingreso * estrato,

        # ── CAT_VARS ─────────────────────────────────────
        "Estrato"            : int(estrato),
        "REGION"             : ciudad_info["REGION"],
        "actividad_ppal"     : MAP_ACTIVIDAD[actividad],
        "Sexo_"              : payload["sexo"],
        "nivel_educ_agrupado": MAP_NIVEL_EDUCATIVO[nivel_educ],
        "antiguedad_agrup"   : _map_rango(
            int(payload["antiguedad_actividad"]),
            MAP_ANTIGUEDAD, "antiguedad_actividad"
        ),
        "Grupo_Edad"         : _map_rango(
            int(payload["edad"]), MAP_GRUPO_EDAD, "edad"
        ),
        "EstadoCivil_hom"    : payload["estado_civil"],
        "Grupo_Aportantes"   : _map_rango(
            int(payload["aportantes_hogar"]),
            MAP_GRUPO_APORTANTES, "aportantes_hogar"
        ),
        "tipo_vivienda_agrup": MAP_TIPO_VIVIENDA[tipo_viv],
        "dominio_agrup"      : ciudad_info["dominio_agrup"],
        "flag_pensionado"    : "es_pensionado" if es_pensionado else "no_es_pensionado",
    }

    df = pd.DataFrame([row])
    faltantes = [c for c in FEATURES if c not in df.columns]
    if faltantes:
        raise ValueError(
            f"Columnas faltantes para el modelo WLS: {faltantes}"
        )
    return df[FEATURES]


# ----------------------------------------------------------
# 5. DATAFRAME PARA EL CLASIFICADOR
# ----------------------------------------------------------

def _construir_df_clf(payload, log_gasto_pred, log_ratio_estimado):
    """
    Construye el DataFrame para clf_pipeline.
    NUM_CLF: float (incluye Estrato, Edad, Aportantes_Hogar)
    CAT_CLF: str   (incluye flag_pensionado)
    """
    ciudad        = str(payload["ciudad"]).upper()
    actividad     = payload["actividad_principal"]
    nivel_educ    = payload["nivel_educativo"]
    tipo_viv      = payload["tipo_vivienda"]
    ciudad_info   = MAP_CIUDAD[ciudad]
    estrato       = int(payload["estrato"])
    es_pensionado = (actividad == "Pensionado")

    row = {
        # ── NUM_CLF (float) ──────────────────────────────
        "log_ingresos_2025"  : float(np.log(float(payload["ingreso_mensual_total"]))),
        "log_gasto_pred_w"   : float(log_gasto_pred),
        "log_ratio_estimado" : float(log_ratio_estimado),
        "Estrato"            : float(estrato),
        "Edad"               : float(payload["edad"]),
        "Aportantes_Hogar"   : float(payload["aportantes_hogar"]),

        # ── CAT_CLF (str) ────────────────────────────────
        "nivel_educ_agrupado": MAP_NIVEL_EDUCATIVO[nivel_educ],
        "actividad_ppal"     : MAP_ACTIVIDAD[actividad],
        "tipo_vivienda_agrup": MAP_TIPO_VIVIENDA[tipo_viv],
        "Grupo_Edad"         : _map_rango(
            int(payload["edad"]), MAP_GRUPO_EDAD, "edad"
        ),
        "Grupo_Aportantes"   : _map_rango(
            int(payload["aportantes_hogar"]),
            MAP_GRUPO_APORTANTES, "aportantes_hogar"
        ),
        "REGION"             : ciudad_info["REGION"],
        "flag_pensionado"    : "es_pensionado" if es_pensionado else "no_es_pensionado",
    }
    return pd.DataFrame([row])


# ----------------------------------------------------------
# 6. FUNCIÓN PRINCIPAL DE INFERENCIA
# ----------------------------------------------------------

def predict(payload: dict) -> dict:
    """
    Ejecuta el flujo completo del modelo híbrido.

    Retorna dict con:
      - ingreso, gasto_estimado, ratio_estimado
      - cluster_ord (0–3), percentil, señal_alta_presion
      - proba_c3 (probabilidad de alta presión financiera)
      - perfil_nombre/descripcion/ratio_ref/part_pct
      - riesgo_nivel/color/descripcion
      - tabla_percentiles (p25_obs, p50_obs, p75_obs, p90_obs)
      - residuo_mediano_segmento
      - SMMLV_2025
    """

    # PASO 1: WLS → log_gasto
    df_reg         = _construir_df_regresion(payload)
    log_gasto_pred = float(model_wls.predict(df_reg)[0])
    gasto_estimado = float(np.exp(log_gasto_pred))
    ingreso        = float(payload["ingreso_mensual_total"])

    # PASO 2: ratio estimado
    ratio_estimado = gasto_estimado / ingreso
    if ratio_estimado <= 0:
        raise ValueError(
            f"Ratio inválido: gasto={gasto_estimado:.2f}, "
            f"ingreso={ingreso:.2f}"
        )
    log_ratio_estimado = float(np.log(ratio_estimado))

    # PASO 3: Clasificador → segmento (sin residuo)
    df_clf      = _construir_df_clf(payload, log_gasto_pred, log_ratio_estimado)
    cluster_ord = int(clf_pipeline.predict(df_clf)[0])
    probas      = clf_pipeline.predict_proba(df_clf)[0]
    proba_c3    = float(probas[3]) if len(probas) > 3 else 0.0

    # PASO 4: Señal de alta presión financiera
    senal_alta_presion = proba_c3 >= UMBRAL_C3

    # PASO 5: Percentil en el segmento (usando ratio_obs)
    percentil = _clasificar_percentil(ratio_estimado, cluster_ord)

    # PASO 6: Interpretación
    perfil    = CLUSTER_PROFILES.get(cluster_ord, {})
    riesgo    = clasificar_riesgo(percentil)
    tabla_seg = RATIO_TABLE.get(cluster_ord, {})

    tabla_percentiles = {
        "p25": tabla_seg.get("p25_obs", 0),
        "p50": tabla_seg.get("p50_obs", 0),
        "p75": tabla_seg.get("p75_obs", 0),
        "p90": tabla_seg.get("p90_obs", 0),
    }

    return {
        # Monetarios
        "ingreso"                  : ingreso,
        "gasto_estimado"           : gasto_estimado,
        "ratio_estimado"           : ratio_estimado,

        # Segmento
        "cluster_ord"              : cluster_ord,
        "percentil"                : percentil,
        "proba_c3"                 : proba_c3,
        "senal_alta_presion"       : senal_alta_presion,
        "umbral_c3"                : UMBRAL_C3,
        "residuo_mediano_segmento" : tabla_seg.get("residuo_mediano", None),

        # Perfil
        "perfil_nombre"            : perfil.get("nombre"),
        "perfil_descripcion"       : perfil.get("descripcion"),
        "perfil_ratio_ref"         : perfil.get("ratio_referencia"),
        "perfil_part_pct"          : perfil.get("participacion_pct"),

        # Riesgo
        "riesgo_nivel"             : riesgo["nivel"],
        "riesgo_color"             : riesgo["color"],
        "riesgo_descripcion"       : riesgo["descripcion"],

        # Tabla de referencia
        "tabla_percentiles"        : tabla_percentiles,

        # Metadatos
        "SMMLV_2025"               : SMMLV_2025,
    }
