# Plantilla de reporte académico

Esta es la estructura típica de un capítulo de resultados de tesis de maestría o de una nota técnica de respuesta. Es **flexible**: adapta secciones según la pregunta. Si es una nota corta de respuesta a un punto del jurado, no necesitas todas las secciones.

## Estructura recomendada para un capítulo de resultados

### 1. Introducción del capítulo (1-2 páginas)
- Pregunta de investigación específica del capítulo.
- Brevísima motivación.
- Anuncio de los hallazgos principales (un párrafo).
- Hoja de ruta del capítulo.

### 2. Datos (1-2 páginas)
- Fuente: ENPH 2016-2017 (o la versión correspondiente), DANE.
- Unidad de análisis: hogar / persona / hogar-categoría.
- N muestral y N expandido.
- Construcción de la variable dependiente (anualización, agregación).
- Tabla 1: Estadísticas descriptivas ponderadas de las variables clave (media, desviación, mín, máx).
- Mención al factor de expansión y a los errores estándar usados.

### 3. Estrategia empírica (1-3 páginas)
- Especificación del modelo principal (ecuación numerada).
- Justificación de la forma funcional (lineal vs. log, controles incluidos).
- Justificación de los métodos complementarios (k-means, etc.).
- Supuestos identificantes.
- Pruebas de robustez planeadas.

### 4. Resultados (3-6 páginas)
- Tabla principal de regresión.
- Interpretación cuantitativa de los coeficientes (en magnitudes, no solo signo).
- Gráfico(s) que muestren la relación clave (predicciones, efectos marginales).
- Resultado del clustering (si aplica): tabla de caracterización por cluster + gráfico de silhouette.

### 5. Robustez (1-2 páginas)
- Tabla con especificaciones alternativas en columnas.
- Comentario sobre cuáles coeficientes son estables y cuáles no.

### 6. Discusión (1-2 páginas)
- Comparación con literatura previa (citar 3-5 estudios relevantes).
- Limitaciones reconocidas.
- Implicaciones de política o prácticas.

### 7. Conclusiones del capítulo (½ página)
- Recapitulación breve de hallazgos.

---

## Formato de tablas

Las tablas de regresión académicas siguen una convención:

```
                          (1)        (2)        (3)
                       Modelo 1   Modelo 2   Modelo 3
log(ingreso)            0.823***   0.812***   0.798***
                       (0.012)    (0.013)    (0.014)
edad jefe               0.005**    0.004**    0.004*
                       (0.002)    (0.002)    (0.002)
educación jefe          0.018***              0.015***
                       (0.003)               (0.003)
...
Constante               1.234***   1.456***   1.345***
                       (0.234)    (0.245)    (0.256)
N                       87,234     87,234     87,234
N expandido         14,521,000 14,521,000 14,521,000
R²                       0.412      0.398      0.421
Errores estándar entre paréntesis. *** p<0.01, ** p<0.05, * p<0.10
Errores robustos a heterocedasticidad (HC3).
```

Notas mínimas a pie de tabla:
- Qué son los paréntesis.
- Tipo de errores estándar.
- Significancia.
- N expandido si aplica.

---

## Formato de gráficos

- DPI ≥ 150, idealmente 300.
- Texto legible (≥10 pt cuando se imprime).
- Ejes etiquetados con unidades (pesos, millones de pesos, log de pesos, etc.).
- Sin colores demasiado saturados; en escala de grises o paleta accesible.
- Cada gráfico debe tener título numerado ("Figura 1: ...") y nota al pie con la fuente y la muestra.

Ejemplo en `matplotlib`:
```python
import matplotlib.pyplot as plt
plt.style.use('seaborn-v0_8-whitegrid')

fig, ax = plt.subplots(figsize=(8, 5), dpi=200)
ax.scatter(df['log_ingreso'], df['log_gasto'], alpha=0.1, s=10, color='gray')
ax.set_xlabel('Log del ingreso anual del hogar (pesos de 2017)')
ax.set_ylabel('Log del gasto anual del hogar (pesos de 2017)')
ax.set_title('Figura 1: Relación entre ingreso y gasto del hogar')
fig.text(0.5, -0.05,
         'Fuente: cálculos propios con base en ENPH 2016-2017, DANE.\n'
         'Muestra: hogares con ingreso y gasto positivos. Ponderado por factor de expansión.',
         ha='center', fontsize=8)
fig.savefig('figura1.png', dpi=300, bbox_inches='tight')
```

---

## Cómo escribir la interpretación

**Mal**: "El coeficiente del ingreso es 0.823 y es significativo."

**Bien**: "Un aumento del 1% en el ingreso del hogar se asocia con un aumento del 0.82% en el gasto, en promedio, manteniendo constantes las demás variables (Tabla 2, columna 1). Este coeficiente es estadísticamente significativo al 1% y económicamente relevante: corresponde a una elasticidad-ingreso del gasto inferior a la unidad, consistente con la ley de Engel para el gasto agregado."

Las interpretaciones deben:
- Traducir coeficientes a magnitudes interpretables (porcentajes, pesos, desviaciones estándar).
- Mencionar significancia estadística sin que sea el centro de la frase.
- Conectar con teoría o literatura previa cuando sea posible.

---

## Citas

Usa formato APA o el que pida la universidad. Algunas referencias frecuentes para tesis sobre gasto:

- Engel, E. (1857). Die Productions- und Consumtionsverhältnisse des Königreichs Sachsen.
- Deaton, A., & Muellbauer, J. (1980). Economics and Consumer Behavior.
- DANE. (2018). Encuesta Nacional de Presupuestos de los Hogares 2016-2017: Boletín técnico.
- Banks, J., Blundell, R., & Lewbel, A. (1997). Quadratic Engel Curves and Consumer Demand.

---

## Idioma y registro

- Español académico, tercera persona o impersonal ("se estima", "se observa").
- Evitar "demuestra" (no se demuestra causalidad con datos observacionales) — usar "sugiere", "se asocia", "es consistente con".
- Evitar adjetivos calificativos vagos ("muy", "bastante"). Usar magnitudes específicas.
- Tiempos verbales consistentes: presente para describir lo que se hace, pasado para resultados específicos.
