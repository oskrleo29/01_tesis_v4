# Estilo de redacción y formato de la tesis

Esta referencia consolida el estilo del documento `ANALISIS DEL GASTO DE LOS HOGARES_20250211_vrevisada.docx` para que cualquier nuevo capítulo, anexo o respuesta al jurado mantenga coherencia.

## Estructura general (CRISP-DM)

La tesis sigue las seis fases de CRISP-DM. Cuando agregues una sección, ubícala en la fase correcta:

1. **Comprensión del negocio** (Cap. 4) — objetivos, recursos, requisitos, restricciones.
2. **Comprensión de los datos** (Cap. 5) — fuente, estructura de cuadernillos ENPH, descriptivos.
3. **Preparación de los datos** (Cap. 6 y Anexo A) — construcción de variables, ajuste a 2025, ratios.
4. **Modelado** (Cap. 10) — regresión lineal múltiple WLS y comparaciones.
5. **Evaluación** (Cap. 12) — validez, limitaciones.
6. **Implementación** (Cap. 13 y Anexo G) — uso operativo para analistas de crédito.

Las fases 4-6 son donde típicamente se concentran las observaciones del jurado.

## Niveles de encabezado

El documento usa hasta `Heading 5`. La convención observada es:

- `Heading 1` — capítulo principal (ej: "Fase de modelado").
- `Heading 2` — sección numerada con dos niveles (ej: "10.1 Especificación del modelo de regresión lineal múltiple").
- `Heading 3` — subsección con tres niveles (ej: "10.1.1 Forma funcional").
- `Heading 5` — sub-subsección dentro de modelado (ej: "10.3.1 Métricas de evaluación del modelo de regresión").

> Nota: el documento salta de Heading 3 a Heading 5 en algunos lugares. Es un patrón existente; al agregar contenido respeta el nivel ya usado en la sección.

Cuando generes un `.docx` nuevo:

```python
from docx import Document
doc = Document()
doc.add_heading('Capítulo X. Título', level=1)
doc.add_heading('X.1 Sección', level=2)
doc.add_heading('X.1.1 Subsección', level=3)
```

## Tono y registro

- Tercera persona o impersonal: "se estima", "se evidencia", "los resultados muestran".
- Evita primera persona ("yo estimé") y segunda ("usted observará").
- Verbos en presente para descripciones metodológicas, en pasado para resultados puntuales.
- Cita decisiones técnicas con autores: Deaton & Muellbauer (1980), Engel (1857), Banks et al. (1997), Wooldridge (2010), Cameron & Trivedi (2005).
- Reconoce limitaciones explícitamente; el jurado lo valora.

## Formato de tablas

Las tablas de la tesis incluyen, según observación del documento:

1. **Tablas de regresión**: variable dependiente arriba, coeficientes en el cuerpo, error estándar entre paréntesis, asteriscos de significancia, N muestral y N expandido al pie, R² ajustado, RMSE.

2. **Tablas de cluster**: una fila por cluster (0 a 3, ordenados por ingreso mediano), columnas con media, mediana, percentiles del gasto y del ingreso, N muestral, N expandido (FEX_C sumado), participación porcentual expandida.

3. **Tablas descriptivas**: presentar siempre dos planos paralelos — muestral y poblacional (expandido por FEX_C).

Plantilla mínima de tabla en `python-docx`:

```python
table = doc.add_table(rows=1, cols=4)
table.style = 'Light Grid Accent 1'
hdr = table.rows[0].cells
hdr[0].text = 'Variable'
hdr[1].text = 'Coeficiente'
hdr[2].text = 'Error estándar'
hdr[3].text = 'p-valor'
# ...
# Notas al pie de tabla:
nota = doc.add_paragraph()
nota.add_run(
    'Nota: errores estándar robustos a heterocedasticidad (HC3). '
    '*** p<0.01, ** p<0.05, * p<0.10. '
    'N muestral = 87,234. N expandido = 14,521,000.'
).italic = True
```

## Formato de figuras

- Insertadas con DPI ≥ 200 (300 ideal para impresión).
- Eje Y con unidades explícitas (logaritmo, pesos de 2025, porcentaje).
- Título numerado: "Figura X: descripción concisa".
- Nota al pie: fuente (`Cálculos propios con base en ENPH 2016-2017, DANE`) y muestra (`Población objetivo: trabajadores con ingreso reportado, ponderado por FEX_C`).
- Paleta sobria; evita combinaciones rojo-verde para accesibilidad.

## Convenciones específicas de esta tesis

### Naming de variables
- Sufijo `_AL_2025` para variables monetarias ajustadas: `INGRESOS_AL_2025`, `GASTOS_AL_2025`.
- Prefijo `log_` para transformaciones logarítmicas: `log_ingresos_2025`, `log_gastos_2025`, `log_ratio_ingreso`.
- Sufijo `_w` para variantes ponderadas (WLS / K-Means): `cluster_w`, `residuo_log_gasto_w`, `model_lin_w`, `kmeans_w`, `RATIO_TABLE_W`, `RESIDUO_ESPERADO_W`.
- Sufijo `_ord` para versiones ordenadas: `cluster_ord_w` (ordenado por ingreso mediano).
- Variables homologadas con sufijo `_homo` o agrupadas con `_agrup`/`_agrupado`.

### Anexos
La tesis tiene anexos A-G:
- **Anexo A** — Preparación y transformación de datos.
- **Anexo B** — Regresión lineal estimada con coeficientes.
- **Anexo C** — Coeficiente estimado y variación aproximada del gasto personal.
- **Anexo D** — Comportamiento de los residuales por variable.
- **Anexo E** — Composición de las variables por clúster.
- **Anexo F** — Diferencia entre coeficientes OLS, Ridge y Lasso.
- **Anexo G** — Implementación y uso operativo de los resultados.

Para agregar un nuevo anexo, sigue la letra que sigue (H, I, J...).

### Tablas de ratio y residuos esperados
La tesis tiene dos tablas centrales para el uso operativo:

- `RATIO_TABLE_W` — percentiles (p25, p50, p75, p90) del ratio gasto/ingreso por cluster ordenado.
- `RESIDUO_ESPERADO_W` — residuo log esperado por (cluster_ord_w, percentil_w).
- `RESIDUO_INICIAL_GRUPO_W` — residuo medio por combinación de (actividad_ppal, tipo_vivienda_agrup, Grupo_Aportantes, flag_pensionado, Estrato, nivel_educ_agrupado).

Estos diccionarios se serializan en `artefactos_modelo.pkl` junto con los modelos. Cualquier nuevo análisis debe respetar y, si lo modifica, actualizar también el `.pkl`.

## Cómo redactar conclusiones de un capítulo

La tesis cierra cada capítulo con un párrafo o dos que:
1. Recapitulan los hallazgos cuantitativos principales en magnitudes.
2. Conectan con la pregunta de investigación.
3. Anticipan el siguiente capítulo.

Ejemplo del estilo:
> "El modelo WLS ponderado por FEX_C reproduce la elasticidad-ingreso esperada (β_log_ingreso = 0.78, p<0.01), consistente con la ley de Engel para gasto agregado. La inclusión del estrato y la actividad principal mejora el R² ajustado de 0.41 a 0.52, evidencia de que el contexto socioeconómico aporta señal por encima del ingreso. La heterogeneidad residual motiva la siguiente fase de segmentación no supervisada (Capítulo 11)."

## Citas y bibliografía

El documento usa formato APA. Citas en texto: `(Autor, año)` o `Autor (año)`. Referencias frecuentes:

- DANE (2018). *Encuesta Nacional de Presupuestos de los Hogares 2016-2017: Boletín técnico*. Bogotá.
- Deaton, A., & Muellbauer, J. (1980). *Economics and Consumer Behavior*. Cambridge University Press.
- Banks, J., Blundell, R., & Lewbel, A. (1997). Quadratic Engel Curves and Consumer Demand. *Review of Economics and Statistics*, 79(4), 527-539.
- Wooldridge, J. M. (2010). *Econometric Analysis of Cross Section and Panel Data* (2ª ed.). MIT Press.
- Cameron, A. C., & Trivedi, P. K. (2005). *Microeconometrics: Methods and Applications*. Cambridge University Press.
- Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning* (2ª ed.). Springer.
- Chapman, P., et al. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*.

Para autores colombianos (gasto, desigualdad), considera citar trabajos de Núñez, Sánchez, Lasso, Galvis, Bonilla; el jurado puede pedirlo.
