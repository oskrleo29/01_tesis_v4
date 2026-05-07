# ==========================================================
# app.py
# Interfaz Streamlit — Estimador de Gasto Personal
# Versión 3.0 — Modelo híbrido (residuos WLS + clasificador)
# ==========================================================

import streamlit as st
import pandas as pd

from pipeline import predict, SMMLV_2025
from persistence import guardar_resultado

# ----------------------------------------------------------
# Configuración general
# ----------------------------------------------------------
st.set_page_config(
    page_title="Estimador de Gasto Personal",
    page_icon="💳",
    layout="centered",
)

st.title("Estimador de Gasto Personal y Perfil de Consumo")
st.markdown("""
Esta herramienta estima el **gasto personal mensual** de un solicitante
de crédito a partir de sus características socioeconómicas y lo clasifica
en un **perfil de comportamiento financiero** mediante un modelo híbrido:
regresión WLS + segmentación comportamental + clasificador de producción.

> Todas las variables de entrada están disponibles en el momento de la
> solicitud de crédito. **No se requiere el gasto observado del solicitante.**
""")

# ----------------------------------------------------------
# Formulario de entrada
# ----------------------------------------------------------
st.header("Características del solicitante")

with st.form("form_solicitante"):

    id_sol = st.text_input(
        "Identificación del solicitante",
        placeholder="Número de documento"
    )

    col1, col2 = st.columns(2)

    with col1:
        ingreso = st.number_input(
            "Ingreso mensual declarado (COP)",
            min_value=float(SMMLV_2025),
            step=50_000.0,
            format="%.0f",
            help=f"Mínimo: 1 SMMLV = ${SMMLV_2025:,.0f}",
        )
        estrato = st.selectbox(
            "Estrato socioeconómico",
            ["1", "2", "3", "4", "5", "6"]
        )
        ciudad = st.selectbox("Ciudad", sorted([
            "ARMENIA", "ARAUCA", "BARRANCABERMEJA", "BARRANQUILLA",
            "BOGOTÁ", "BUCARAMANGA", "BUENAVENTURA", "CALI",
            "CARTAGENA", "CÚCUTA", "FLORENCIA", "IBAGUÉ",
            "MANIZALES", "MEDELLÍN", "MONTERÍA", "NEIVA",
            "PASTO", "PEREIRA", "POPAYÁN", "QUIBDÓ",
            "RIONEGRO", "RIOHACHA", "SANTA MARTA", "SINCELEJO",
            "SOLEDAD", "TUNJA", "VALLEDUPAR", "VILLAVICENCIO",
            "YOPAL", "YUMBO",
        ]))
        edad = st.number_input("Edad", min_value=18, max_value=80, step=1)
        sexo = st.selectbox("Sexo", ["Hombre", "Mujer"])
        estado_civil = st.selectbox("Estado civil", [
            "Soltero(a)", "Casado(a)", "Pareja < 2 años",
            "Pareja ≥ 2 años", "Separado/Divorciado", "Viudo(a)",
        ])

    with col2:
        nivel_educativo = st.selectbox("Nivel educativo", [
            "Ninguno", "Basica Primaria", "Basica Secundaria",
            "Bachiller", "Tecnico Tecnólogo", "Universitaria", "Postgrado",
        ])
        actividad = st.selectbox(
            "Actividad principal",
            ["Empleado", "Independiente", "Pensionado"]
        )
        antiguedad = st.number_input(
            "Antigüedad en la actividad (meses)",
            min_value=0, max_value=600, step=1
        )
        aportantes = st.number_input(
            "Número de aportantes del hogar",
            min_value=1, max_value=9, step=1
        )
        tipo_vivienda = st.selectbox("Tipo de vivienda", [
            "Arriendo", "Propia En Pago", "Propia Pagada",
            "Tenencia No Formal", "Otros",
        ])

    submitted = st.form_submit_button("Estimar gasto y perfil", type="primary")

# ----------------------------------------------------------
# Ejecución del modelo
# ----------------------------------------------------------
if submitted:
    payload = {
        "id_solicitante"       : id_sol,
        "ingreso_mensual_total": ingreso,
        "estrato"              : estrato,
        "ciudad"               : ciudad,
        "edad"                 : edad,
        "sexo"                 : sexo,
        "estado_civil"         : estado_civil,
        "nivel_educativo"      : nivel_educativo,
        "actividad_principal"  : actividad,
        "antiguedad_actividad" : antiguedad,
        "aportantes_hogar"     : aportantes,
        "tipo_vivienda"        : tipo_vivienda,
    }

    try:
        resultado = predict(payload)
        guardar_resultado(payload, resultado)

        st.success("Estimación completada correctamente")

        # --------------------------------------------------
        # Métricas principales
        # --------------------------------------------------
        st.subheader("Resultados del modelo")

        c1, c2, c3 = st.columns(3)
        c1.metric("Ingreso mensual",
                  f"${resultado['ingreso']:,.0f}")
        c2.metric("Gasto personal estimado",
                  f"${resultado['gasto_estimado']:,.0f}")
        c3.metric("Ratio gasto / ingreso",
                  f"{resultado['ratio_estimado']*100:.1f}%")

        c4, c5, c6 = st.columns(3)
        c4.metric("Segmento",
                  f"Clúster {resultado['cluster_ord']}")
        c5.metric("Percentil en el segmento",
                  resultado['percentil'])
        c6.metric("Nivel de riesgo",
                  resultado['riesgo_nivel'])

        # --------------------------------------------------
        # Señal de alta presión financiera (modelo híbrido)
        # --------------------------------------------------
        proba_c3 = resultado.get("proba_c3", 0.0)
        senal    = resultado.get("senal_alta_presion", False)
        umbral   = resultado.get("umbral_c3", 0.50)

        st.subheader("Señal de alta presión financiera")
        if senal:
            st.error(
                f"⚠ **Alta presión financiera detectada** "
                f"(P(C3) = {proba_c3:.1%} ≥ umbral {umbral:.0%})\n\n"
                "El clasificador detecta un perfil de sobregasto relativo. "
                "Se recomienda validación adicional antes de otorgar crédito."
            )
        elif proba_c3 >= 0.40:
            st.warning(
                f"🔶 **Zona gris** (P(C3) = {proba_c3:.1%})\n\n"
                "El perfil muestra señales moderadas de presión financiera. "
                "Considerar solicitar información adicional."
            )
        else:
            st.success(
                f"✓ **Sin señal de alta presión** "
                f"(P(C3) = {proba_c3:.1%} < umbral {umbral:.0%})"
            )

        # Detalle de probabilidades por segmento (expandible)
        with st.expander("Ver probabilidades por segmento"):
            st.caption(
                "El clasificador asigna una probabilidad a cada segmento. "
                "P(C3) es la probabilidad de alta presión financiera."
            )
            st.write(f"P(C3) — Alta presión: **{proba_c3:.1%}**")
            resid = resultado.get("residuo_mediano_segmento")
            if resid is not None:
                st.write(
                    f"Residuo mediano del segmento: **{resid:+.3f}** "
                    f"({'gasta más de lo esperado' if resid > 0 else 'gasta menos de lo esperado'})"
                )

        # --------------------------------------------------
        # Perfil de consumo
        # --------------------------------------------------
        st.subheader("Perfil de consumo")
        st.markdown(f"**{resultado['perfil_nombre']}**")
        st.write(resultado['perfil_descripcion'])
        st.caption(
            f"Este perfil representa el {resultado['perfil_part_pct']}% "
            f"de la población objetivo. Ratio observado P50: "
            f"{resultado['perfil_ratio_ref']*100:.1f}%"
        )

        # --------------------------------------------------
        # Semáforo de riesgo
        # --------------------------------------------------
        st.subheader("Evaluación de riesgo financiero")
        color = resultado['riesgo_color']
        if color == "verde":
            st.success(f"**Riesgo {resultado['riesgo_nivel']}**")
        elif color == "amarillo":
            st.warning(f"**Riesgo {resultado['riesgo_nivel']}**")
        else:
            st.error(f"**Riesgo {resultado['riesgo_nivel']}**")
        st.write(resultado['riesgo_descripcion'])

        # --------------------------------------------------
        # Tabla de percentiles del segmento
        # --------------------------------------------------
        st.subheader("Distribución del ratio en el segmento")
        tabla = resultado['tabla_percentiles']
        if tabla:
            df_t = pd.DataFrame({
                "Percentil"            : ["P25", "P50", "P75", "P90"],
                "Ratio gasto/ingreso"  : [
                    f"{tabla['p25']*100:.1f}%",
                    f"{tabla['p50']*100:.1f}%",
                    f"{tabla['p75']*100:.1f}%",
                    f"{tabla['p90']*100:.1f}%",
                ],
                "Interpretación": [
                    "25% del segmento tiene ratio menor",
                    "Valor típico (mediana) del segmento",
                    "75% del segmento tiene ratio menor",
                    "90% del segmento tiene ratio menor",
                ]
            })
            st.dataframe(df_t, use_container_width=True, hide_index=True)

            ratio_sol  = resultado['ratio_estimado'] * 100
            p50_seg    = tabla['p50'] * 100
            diferencia = ratio_sol - p50_seg
            st.caption(
                f"El ratio del solicitante ({ratio_sol:.1f}%) es "
                f"{'superior' if diferencia > 0 else 'inferior'} a la "
                f"mediana de su segmento ({p50_seg:.1f}%) en "
                f"{abs(diferencia):.1f} puntos porcentuales."
            )

        # --------------------------------------------------
        # Nota metodológica
        # --------------------------------------------------
        st.divider()
        st.caption(
            "Modelo híbrido calibrado con microdatos ENPH 2016-2017 indexados a "
            f"diciembre de 2025. SMMLV 2025 = ${resultado['SMMLV_2025']:,.0f}. "
            "El gasto se estima mediante regresión WLS ponderada por FEX_C. "
            "La segmentación comportamental usa K-Means con residuos WLS (k=4). "
            "La asignación en producción usa un clasificador logístico multinomial "
            f"(balanced accuracy CV = 0.7915). Umbral de alta presión P(C3) ≥ {umbral:.0%}. "
            "Los resultados son referenciales y complementan el análisis crediticio institucional."
        )

    except Exception as e:
        st.error("Error durante la estimación.")
        st.exception(e)
