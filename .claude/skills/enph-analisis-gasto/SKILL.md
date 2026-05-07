---
name: enph-analisis-gasto
description: 'Asistente para la tesis de maestría de Paola sobre estimación del gasto personal usando microdatos ENPH 2016-2017 del DANE, metodología CRISP-DM, modelo WLS ponderado por FEX_C y K-Means ponderado para evaluación de capacidad de pago crediticia. Activa este skill SIEMPRE que se mencione tesis, jurado, ENPH, DANE, gasto personal, FEX_C, factor de expansión, WLS, regresión ponderada, K-Means ponderado, Ridge, Lasso, RATIO_TABLE, residuo_log_gasto, cluster_ord_w, df_temp_a, CRISP-DM, analista de crédito, capacidad de pago, microdatos, cuadernillos, log_ingresos_2025, log_gastos_2025, percentil_w. También actívalo al trabajar en Proyecto_gasto_personal_2026_tesis.ipynb o ANALISIS DEL GASTO DE LOS HOGARES_*.docx, o cuando la usuaria mencione su notebook, su tesis, su modelo de gasto, los clusters, o la respuesta al jurado. Salida típica - reporte docx para jurado, código Python (pandas, statsmodels, sklearn, joblib), tabulados ponderados.'
---

# Análisis del gasto personal con microdatos ENPH (tesis Paola)

Este skill está diseñado a la medida de la tesis de maestría de Paola Velandia (Universidad Central): **"Estimación del gasto personal como variable principal para la evaluación de capacidad de pago"**. La tesis usa microdatos de la ENPH 2016-2017 del DANE, sigue la metodología **CRISP-DM**, y termina en un artefacto operativo (`.pkl`) que un analista de crédito puede consumir.

> **Contexto crítico**: la usuaria está respondiendo a revisiones del jurado evaluador. Toda recomendación, código y reporte que produzcas debe poder defenderse técnicamente.

## Cuándo activarse

Activa este skill siempre que:

- Se mencione la ENPH, microdatos del DANE, FEX_C, o cuadernillos.
- Se trabaje sobre los archivos `Proyecto_gasto_personal_2026_tesis.ipynb` o `ANALISIS DEL GASTO DE LOS HOGARES_*.docx`.
- Se pida estimar gasto personal, segmentar perfiles socioeconómicos, calcular ratios gasto/ingreso, o producir tablas/anexos de tesis.
- La usuaria mencione respuesta al jurado, robustez, justificación de K, comparación de modelos (OLS/WLS/Ridge/Lasso), o validación.

## Lo que la usuaria ya tiene

Antes de proponer nada, ten presente que el notebook ya contiene un pipeline completo:

| Sección del notebook | Contenido | Variable/objeto principal |
|---|---|---|
| 1. Carga de microdatos | Lectura desde repositorio externo (gdown), descompresión, lectura por cuadernillos | `dataframes` (dict), `ViviendaHog`, `CaracteristicasGP`, `GdUrbano`, etc. |
| 2. Limpieza y construcción | Construcción del público objetivo (trabajadores), homologación de actividades CIIU, nivel educativo, ingresos | `publico_objetivo`, `publico_objetivo_5`, `homologa_ciiu`, `homologa_nivel_academico` |
| 3. Universo de análisis | Integración de cuadernillos de gasto, indexación, ajuste a 2025 | `gastos_objetivo_final`, `df_temp_a` |
| 4. Modelo de regresión | WLS ponderado por FEX_C (modelo principal), comparación con Ridge/Lasso | `model_lin_w`, `preprocess`, `X_train/X_test`, `y_train/y_test`, `fex_c_norm` |
| 5. Segmentación | K-Means ponderado por FEX_C, K=4, comparación con K-Means original | `kmeans_w`, `cluster_ord_w`, `X_cluster`, `preprocess_cluster` |
| 6. Artefactos de producción | Tabla de ratios y residuos esperados, exportación a `.pkl` | `RATIO_TABLE_W`, `RESIDUO_ESPERADO_W`, `RESIDUO_INICIAL_GRUPO_W`, `artefactos` |
| 7. Simulación | Uso operativo del modelo para un caso de analista de crédito | `artefactos_modelo.pkl` |

**Variables clave que ya existen en `df_temp_a`** (úsalas con estos nombres exactos):

- Identificación: `DIRECTORIO`, `ORDEN`, `Id_Person`
- Sociodemográficas: `Sexo_`, `Edad`, `Estado_Civil`, `nivel_educ_agrupado`, `actividad_ppal`, `Grupo_Aportantes`, `flag_pensionado`
- Hogar/territorio: `Estrato`, `REGION`, `DOMINIO`, `PersonasHogar`, `tipo_vivienda_agrup`
- Económicas: `INGRESOS_AL_2025`, `GASTOS_AL_2025`, `log_ingresos_2025`, `log_gastos_2025`, `log_ratio_ingreso`, `gasto_pct_ingreso_w`
- Diseño muestral: `FEX_C`, `fex_c_norm`
- Modelado: `log_gasto_pred_w`, `residuo_log_gasto_w`, `residuo_log_gasto`, `cluster`, `cluster_w`, `cluster_ord_w`, `percentil_w`

**Estructura del docx de la tesis** (también está en el directorio):

1. Introducción · 2. Objetivos · 3. Antecedentes · 4. Comprensión del negocio (CRISP-DM) · 5. Comprensión de los datos · 6. Preparación · 10. Fase de modelado (regresión) · 11. Segmentación · 12. Evaluación · 13. Implementación · 14. Discusión · 15. Conclusiones · Anexos A-G.

## Filosofía de trabajo

1. **Respeta el vocabulario que la usuaria ya tiene.** Si ella escribe `df_temp_a`, no cambies a `df` o `data`. Si su variable es `log_gastos_2025`, no la renombres a `log_gasto`. La consistencia con su notebook ahorra tiempo y reduce errores.

2. **Modelo principal = WLS, no OLS.** OLS sin ponderar fue removido del notebook a propósito. Cualquier nuevo análisis debe usar `sample_weight=fex_c_norm` (o equivalente) para que sea representativo de la población de trabajadores colombianos.

3. **K-Means ponderado, K=4 ya validado.** No empieces de cero la justificación de K; el codo y silhouette ya están en el notebook (celdas 134-136). Si el jurado pide más, agrega Calinski-Harabasz, Davies-Bouldin, o estabilidad por bootstrap.

4. **Marco CRISP-DM.** El reporte y los argumentos al jurado se organizan en las seis fases CRISP-DM. No introduzcas un marco distinto sin avisar.

5. **El producto final es operativo.** Cada decisión técnica debe poder traducirse a algo que un analista de crédito pueda usar (un ratio, un percentil, un residuo esperado). No prefieras modelos "elegantes" que no se pueden serializar a `.pkl`.

6. **Diseño muestral complejo.** ENPH tiene estratos y UPM. Para errores estándar, prefiere `cov_type='HC3'` como mínimo; si el jurado pide más, considera bootstrap por replicación o errores con cluster por dominio.

## Flujo de trabajo recomendado

Cuando la usuaria pida algo concreto, sigue estos pasos:

### 1. Identifica si es nueva análisis o revisión de jurado

- **Análisis nuevo**: ¿qué pregunta? ¿qué sub-sección de la tesis aporta?
- **Revisión de jurado**: ¿qué observación específica? Lee `references/respuesta_jurado.md` antes de redactar.

### 2. Carga el contexto necesario

Para responder bien, casi siempre vas a querer:
- Leer `references/estructura_enph.md` (módulos y llaves de unión).
- Leer `references/metodos_avanzados.md` (técnicas que el jurado puede pedir).
- Mirar las celdas del notebook que ya tocan el tema.

### 3. Genera código que se pegue al estilo de Paola

Patrones que usa:
- `import statsmodels.api as sm` y `import statsmodels.formula.api as smf`.
- `from sklearn.pipeline import Pipeline` con `ColumnTransformer`.
- `from sklearn.cluster import KMeans` con `n_init=30`, `random_state=CLUSTER_SEED`.
- Modelos en sklearn con `sample_weight=w_train` para WLS.
- Pesos normalizados como `fex_c_norm = fex_c_raw / fex_c_raw.mean()`.
- Encabezados de celda en mayúscula con líneas de `=`.

### 4. Para reportes, usa la plantilla CRISP-DM

Lee `references/plantilla_reporte.md` para la estructura. Si es respuesta al jurado, usa el formato de `references/respuesta_jurado.md`.

### 5. Para el .docx, replica el estilo de la tesis

Lee `references/estilo_tesis.md` para el estilo específico (Heading 1/2/3, tablas con N muestral y N expandido, anexos numerados con letras).

## Qué hay en cada referencia

- **`references/estructura_enph.md`** — módulos de la ENPH (cuadernillos), llaves de unión, factor de expansión `FEX_C`, anualización del gasto, advertencias comunes con el dato de Paola.
- **`references/metodos_avanzados.md`** — más allá de WLS y K-Means: regresión cuantílica, Tobit/Heckman para gasto censurado, GLM Gamma, modelos jerárquicos, comparación con random forest/gradient boosting, sistemas de demanda AIDS/QUAIDS. Lee solo la sección que aplica.
- **`references/respuesta_jurado.md`** — cómo estructurar respuesta a observaciones del jurado punto por punto.
- **`references/estilo_tesis.md`** — estilo de redacción, formato de tablas y figuras, manejo de Anexos A-G coherente con el documento existente.

## Qué hay en cada script

- **`scripts/cargar_enph.py`** — utilidades genéricas para cargar cuadernillos de la ENPH (uso si necesitas reproducir desde cero o explicarle a alguien más cómo se cargan).
- **`scripts/analisis_ponderado.py`** — funciones de tabulados ponderados por `FEX_C` (medias, medianas, percentiles, cuantiles), validación de representatividad, comparación muestral vs poblacional. Pegado al estilo del notebook.
- **`scripts/generar_reporte.py`** — generador de `.docx` con `python-docx` siguiendo el estilo de la tesis: tabla de regresión con coeficientes/SE/asteriscos, tabla de clusters con N muestral y expandido, gráficos insertados a 300 DPI, secciones con Heading 1/2/3, anexos.

## Reglas de oro específicas para esta tesis

1. **Nunca uses OLS sin ponderar como modelo principal.** Si lo necesitas para comparar, etiquétalo claramente como "modelo no ponderado (referencia)". El modelo principal es WLS con `FEX_C` normalizado.

2. **Reporta siempre N muestral y N expandido**, en cada tabla. Esto es clave para defender ante el jurado que se cuidó el diseño muestral.

3. **El target es `log_gastos_2025`, no `GASTOS_AL_2025`.** Cualquier nuevo modelo trabaja en log; al final se exponencia para reportar pesos.

4. **El ratio se construye en niveles, no en logs:** `gasto_pct_ingreso_w = exp(log_gastos_2025) / exp(log_ingresos_2025)`. No promedies ratios en log y luego exponencies.

5. **Los cuatro clusters están ordenados por ingreso mediano.** El "cluster 0" tiene el menor, el "cluster 3" el mayor (`cluster_ord_w`). Mantén este orden en cualquier tabla nueva.

6. **Si el jurado pide alternativas a K-Means**, considera:
   - Clustering jerárquico aglomerativo (linkage Ward).
   - Gaussian Mixture Models con BIC para selección.
   - K-Prototypes (mezcla numérico/categórico) — relevante porque hay variables categóricas.
   - HDBSCAN (no requiere K).

7. **Para Ridge y Lasso**, ya hay base en el Anexo F. Si se pide profundizar, mantén la misma X (preprocesada con `preprocess`) y usa `RidgeCV`/`LassoCV` con CV ponderada por FEX_C. Reporta α óptimo y comparación de coeficientes.

8. **Decisiones a poner siempre por escrito**: por qué log y no Box-Cox/Yeo-Johnson (ya está justificado en celda 95-99 — usa esa justificación), por qué WLS y no OLS, por qué K=4, por qué se ordenan los clusters por ingreso mediano.

9. **El uso operativo es para analistas de crédito.** Cualquier propuesta debe terminar diciendo cómo afecta al uso final: el analista ingresa características de una persona, recibe un gasto estimado y un percentil del ratio.

10. **No reescribas variables que ya existen.** Si necesitas un nuevo agregado, derívalo de las que están; no inventes paralelas.

## Errores comunes a evitar

- Olvidar pasar `sample_weight=fex_c_norm` en sklearn → modelo no ponderado por accidente.
- Calcular silhouette sobre toda la muestra (lento y poco distinto) → usar muestreo proporcional al peso, como en celda 136.
- Reportar coeficientes de WLS con errores estándar de OLS → usa `cov_type='HC3'` si vas con `statsmodels.WLS`.
- Comparar pesos entre 2017 y 2025 sin deflactar/inflar → la usuaria ya hizo el ajuste con la columna `_AL_2025`; respétalo.
- Modificar el público objetivo sin avisar → cambia el N y rompe trazabilidad con la tesis.
