# ==========================================================
# persistence.py
# Módulo de persistencia, auditoría y trazabilidad
# Versión 3.0 — Modelo híbrido
# Arquitectura: notebooks/02_app/
# ==========================================================

import os
import pandas as pd
from datetime import datetime

# El CSV de resultados se guarda en notebooks/02_app/
# junto a los demás archivos de la app.
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(BASE_DIR, "resultados_inferencia_v2.csv")
# Sufijo _v2 para no mezclar con los resultados de la app original


def guardar_resultado(payload: dict, resultado: dict):
    """
    Registra cada inferencia en CSV para auditoría y monitoreo.
    Incluye las nuevas columnas del modelo híbrido:
      - proba_c3            : probabilidad de alta presión financiera
      - senal_alta_presion  : True si P(C3) >= umbral
      - residuo_mediano_seg : residuo mediano del segmento asignado
    """
    try:
        registro = {
            # Identificación
            "timestamp"               : datetime.now().isoformat(),
            "version_modelo"          : "v3.0-hibrido-v2",
            "id_solicitante"          : payload.get("id_solicitante"),
            # Variables de entrada
            "ingreso_mensual_total"   : payload.get("ingreso_mensual_total"),
            "estrato"                 : payload.get("estrato"),
            "ciudad"                  : payload.get("ciudad"),
            "edad"                    : payload.get("edad"),
            "sexo"                    : payload.get("sexo"),
            "estado_civil"            : payload.get("estado_civil"),
            "nivel_educativo"         : payload.get("nivel_educativo"),
            "actividad_principal"     : payload.get("actividad_principal"),
            "antiguedad_actividad"    : payload.get("antiguedad_actividad"),
            "aportantes_hogar"        : payload.get("aportantes_hogar"),
            "tipo_vivienda"           : payload.get("tipo_vivienda"),
            # Resultados del modelo
            "gasto_estimado"          : resultado.get("gasto_estimado"),
            "ratio_estimado"          : resultado.get("ratio_estimado"),
            "cluster_ord"             : resultado.get("cluster_ord"),
            "percentil"               : resultado.get("percentil"),
            "proba_c3"                : resultado.get("proba_c3"),
            "senal_alta_presion"      : resultado.get("senal_alta_presion"),
            "residuo_mediano_segmento": resultado.get("residuo_mediano_segmento"),
            "riesgo_nivel"            : resultado.get("riesgo_nivel"),
            "perfil_nombre"           : resultado.get("perfil_nombre"),
        }

        df = pd.DataFrame([registro])

        if not os.path.exists(RESULTS_PATH):
            df.to_csv(RESULTS_PATH, index=False)
        else:
            df.to_csv(RESULTS_PATH, mode="a", header=False, index=False)

    except Exception as e:
        print(f"Advertencia: no se pudo guardar el resultado — {e}")
