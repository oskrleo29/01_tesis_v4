# Métodos estadísticos para el análisis del gasto

Este archivo es una caja de herramientas para profundizar el análisis más allá de regresión lineal múltiple + k-means. Cada método incluye cuándo usarlo, cómo justificarlo ante un jurado, código de referencia en Python, y diagnósticos clave.

## Tabla de contenidos
1. Regresión lineal y log-lineal robusta
2. Diagnósticos esenciales
3. Manejo del gasto censurado: Tobit y Heckman
4. Sistemas de demanda: AIDS y QUAIDS
5. Regresión cuantílica
6. Modelos jerárquicos / multinivel
7. K-means con justificación rigurosa
8. Comparación con métodos de machine learning (random forest, gradient boosting)
9. Pruebas de robustez

---

## 1. Regresión lineal y log-lineal robusta

### Cuándo usarla
Para un primer modelo predictivo o explicativo del gasto en función de características socioeconómicas. Es el "caballo de batalla" y el jurado esperará que esté bien hecha.

### Forma funcional
- **Lineal**: `gasto = β₀ + β₁·ingreso + β₂·educ + ...` — interpretación en pesos.
- **Log-lineal**: `log(gasto) = β₀ + β₁·log(ingreso) + ...` — interpretación en elasticidades; útil cuando el gasto es muy asimétrico.
- **Semi-log**: `log(gasto) = β₀ + β₁·educ + ...` — interpretación en porcentajes (un año adicional de educación → β₁·100% más de gasto).

Justificación de log: el gasto típicamente tiene distribución log-normal, con cola larga a la derecha. Tomar log estabiliza la varianza y hace que los residuos sean aproximadamente normales.

### Código

```python
import statsmodels.api as sm
import statsmodels.formula.api as smf
import numpy as np

# Variable dependiente en log
df['log_gasto'] = np.log(df['gasto_anual'].clip(lower=1))  # clip evita log(0)

formula = (
    'log_gasto ~ log(ingreso_total) + edad_jefe + I(edad_jefe**2) '
    '+ educacion_jefe + tam_hogar + C(estrato) + C(region) + C(clase)'
)

# WLS con factor de expansión y errores robustos
modelo = smf.wls(formula, data=df, weights=df['fex_c']).fit(cov_type='HC3')
print(modelo.summary())
```

### Errores estándar
Para defender ante un jurado, **siempre** usa errores robustos:
- `cov_type='HC3'`: robusto a heterocedasticidad (default recomendado).
- `cov_type='cluster', cov_kwds={'groups': df['upm']}`: si hay clusterización por unidades primarias de muestreo.

---

## 2. Diagnósticos esenciales

Antes de presentar resultados al jurado, ejecuta estos diagnósticos:

### Multicolinealidad: VIF
```python
from statsmodels.stats.outliers_influence import variance_inflation_factor
import pandas as pd

X = modelo.model.exog
vif = pd.DataFrame({
    'variable': modelo.model.exog_names,
    'vif': [variance_inflation_factor(X, i) for i in range(X.shape[1])]
})
print(vif)
```
Regla: VIF > 10 sugiere multicolinealidad problemática. VIF > 5 amerita atención.

### Heterocedasticidad: Breusch-Pagan
```python
from statsmodels.stats.diagnostic import het_breuschpagan
bp = het_breuschpagan(modelo.resid, modelo.model.exog)
print(f'BP test: estadístico={bp[0]:.3f}, p-valor={bp[1]:.4f}')
```

### Especificación: Ramsey RESET
```python
from statsmodels.stats.diagnostic import linear_reset
reset = linear_reset(modelo, power=2, use_f=True)
print(reset)
```
Si el p-valor es bajo, considera términos cuadráticos o forma funcional log.

### Normalidad de residuos: Jarque-Bera
```python
from statsmodels.stats.stattools import jarque_bera
jb = jarque_bera(modelo.resid)
print(f'Jarque-Bera: estadístico={jb[0]:.3f}, p-valor={jb[1]:.4f}')
```
Con N grande (típico ENPH), JB casi siempre rechaza, pero el TLC garantiza inferencia válida si la muestra es grande.

### Influencia / outliers
```python
infl = modelo.get_influence()
cooks = infl.cooks_distance[0]
import numpy as np
umbral = 4 / len(df)
outliers = np.where(cooks > umbral)[0]
print(f'{len(outliers)} observaciones con Cook > {umbral:.5f}')
```

---

## 3. Manejo del gasto censurado: Tobit y Heckman

### Por qué importa
Muchas categorías de gasto tienen una fracción no trivial de hogares con valor cero (no consumen tabaco, no pagan educación si no tienen niños, no van a restaurantes, etc.). OLS sobre esos datos da estimaciones sesgadas.

### Tobit (cuando el cero es genuino, no falta de reporte)
```python
# statsmodels no incluye Tobit directamente; usar `linearmodels` o implementar a mano
# Alternativa: usar `py-tobit` o transformar y modelar Pr(gasto>0) y E[gasto|gasto>0] por separado
```

### Heckman dos etapas (selección)
Ideal cuando hay autoselección (un hogar decide primero si consume y luego cuánto consume).

Etapa 1 (probit): probabilidad de consumir.
```python
from statsmodels.discrete.discrete_model import Probit
df['consume'] = (df['gasto_categoria'] > 0).astype(int)
probit = Probit(df['consume'], sm.add_constant(df[Xvars])).fit()
df['imr'] = stats.norm.pdf(probit.fittedvalues) / stats.norm.cdf(probit.fittedvalues)
```

Etapa 2 (OLS con IMR como regresor adicional, solo en consumidores):
```python
sub = df[df['consume'] == 1]
modelo2 = smf.ols('log_gasto ~ ' + ' + '.join(Xvars) + ' + imr', data=sub).fit(cov_type='HC3')
```

Si el coeficiente de IMR es significativo, hay sesgo de selección y Heckman corrige.

---

## 4. Sistemas de demanda: AIDS y QUAIDS

### Cuándo
Cuando se quiere estimar elasticidades-ingreso y elasticidades-precio entre categorías de consumo. Es el método de referencia en economía aplicada a presupuestos familiares (Deaton & Muellbauer, 1980; Banks, Blundell & Lewbel, 1997).

### Idea
El sistema modela los **shares** del gasto en cada categoría como función del log del precio relativo, log del gasto total, y características del hogar. QUAIDS (Quadratic AIDS) añade término cuadrático en log del gasto, permitiendo elasticidades-ingreso variables.

### Implementación práctica
- Python no tiene una librería madura para AIDS. Las opciones son:
  - Implementar las restricciones de Slutsky a mano con `scipy.optimize`.
  - Usar `R` con paquete `micEconAids` y llamarlo desde Python con `rpy2`.
  - Usar Stata con paquete `quaids` y exportar resultados.
- Para una tesis de maestría, lo más defendible es usar `R`/`Stata` en este punto y traer los resultados al reporte.

### Estructura mínima
Para 12 grandes categorías COICOP, los shares deben sumar 1; se estima un sistema SUR con restricciones de homogeneidad y simetría, y se omite una ecuación para evitar singularidad.

---

## 5. Regresión cuantílica

### Cuándo
Cuando interesa caracterizar cómo cambian los determinantes del gasto a lo largo de la distribución. Por ejemplo: el ingreso puede tener un efecto distinto en hogares de bajo gasto vs. alto gasto.

### Código
```python
import statsmodels.formula.api as smf

modelos_q = {}
for q in [0.1, 0.25, 0.5, 0.75, 0.9]:
    modelos_q[q] = smf.quantreg(formula, df).fit(q=q)

# Tabla comparativa
import pandas as pd
coef = pd.DataFrame({q: m.params for q, m in modelos_q.items()})
print(coef)
```

Reportar coeficientes para varios cuantiles permite mostrar heterogeneidad que la regresión de la media oculta.

---

## 6. Modelos jerárquicos / multinivel

### Cuándo
Cuando hay estructura anidada (hogar dentro de municipio, dentro de departamento, etc.) y se sospecha que efectos varían por nivel.

### Código
```python
import statsmodels.formula.api as smf

modelo_ml = smf.mixedlm(
    'log_gasto ~ log_ingreso + edad_jefe + educacion_jefe + tam_hogar',
    data=df,
    groups=df['depto'],
    re_formula='~log_ingreso'  # pendiente aleatoria por departamento
).fit()
print(modelo_ml.summary())
```

ICC (correlación intraclase) ayuda a justificar el modelo: si > 0.05, hay variabilidad relevante a nivel de departamento.

---

## 7. K-means con justificación rigurosa

### Pasos para defender k-means ante un jurado

#### 1. Escala las variables
```python
from sklearn.preprocessing import StandardScaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[features])
```

#### 2. Elige K con múltiples criterios
```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import numpy as np

inercia, sil, ch = [], [], []
for k in range(2, 11):
    km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(X_scaled)
    inercia.append(km.inertia_)
    sil.append(silhouette_score(X_scaled, km.labels_))
    ch.append(calinski_harabasz_score(X_scaled, km.labels_))
```
Reporta los tres y justifica K con base en el balance, no solo el codo.

#### 3. Valida estabilidad
Corre k-means con 10 semillas distintas y mide ARI (Adjusted Rand Index) entre asignaciones. Si ARI promedio > 0.7, el clustering es estable.

```python
from sklearn.metrics import adjusted_rand_score

labels_ref = KMeans(n_clusters=K, n_init=20, random_state=42).fit_predict(X_scaled)
aris = []
for s in range(1, 11):
    labels_s = KMeans(n_clusters=K, n_init=20, random_state=s).fit_predict(X_scaled)
    aris.append(adjusted_rand_score(labels_ref, labels_s))
print(f'ARI promedio: {np.mean(aris):.3f}')
```

#### 4. Caracteriza los clusters
Tabula medias ponderadas (con factor de expansión) de las variables originales por cluster y dale un nombre interpretable a cada uno.

#### 5. Considera alternativas
- **K-medians o K-prototypes**: más robusto a outliers.
- **Clustering jerárquico**: produce dendrograma, útil para discutir jerarquía.
- **DBSCAN o HDBSCAN**: si hay clusters de forma irregular.
- **Gaussian Mixture Models**: si quieres clusters probabilísticos.

Mencionar al menos una alternativa en el reporte muestra al jurado que se evaluaron opciones.

---

## 8. Comparación con machine learning

Para reforzar el análisis, comparar la regresión lineal con métodos no paramétricos:

```python
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import cross_val_score

modelos_ml = {
    'OLS': modelo,  # de statsmodels, evaluado con R² out-of-sample manualmente
    'RF': RandomForestRegressor(n_estimators=200, random_state=42),
    'GBM': GradientBoostingRegressor(random_state=42),
}

for nombre, m in modelos_ml.items():
    if nombre == 'OLS': continue
    scores = cross_val_score(m, X, y, cv=5, scoring='neg_root_mean_squared_error')
    print(f'{nombre}: RMSE={-scores.mean():.0f} ± {scores.std():.0f}')
```

Si RF/GBM mejora poco sobre OLS, la regresión es defendible. Si mejora mucho, vale la pena explorar interacciones o no linealidades.

Reportar la importancia de variables del random forest también ayuda a triangular qué características pesan más en el gasto.

---

## 9. Pruebas de robustez

Toda tesis debería incluir una sección de robustez. Incluye al menos dos de las siguientes:

- **Subsamples**: estimar el modelo principal en hogares urbanos vs. rurales, por región, por estrato.
- **Especificaciones alternativas**: añadir/quitar controles, usar gasto per cápita en vez de gasto total, log en vez de niveles.
- **Manejo de outliers**: estimar con y sin winsorizar al 1% y al 99%.
- **Variables instrumentales**: si hay endogeneidad sospechada (ej: ingreso → gasto, pero gasto → percepción de ingreso reportado).
- **Comparación con ENPH de otra ronda** (si hay dos años disponibles): chequear estabilidad temporal.

Presenta los resultados en una sola tabla con columnas para cada especificación; el jurado lo va a apreciar.

---

## Referencias bibliográficas útiles

- Deaton, A., & Muellbauer, J. (1980). *Economics and Consumer Behavior*. Cambridge University Press.
- Banks, J., Blundell, R., & Lewbel, A. (1997). Quadratic Engel Curves and Consumer Demand. *Review of Economics and Statistics*, 79(4), 527-539.
- Cameron, A. C., & Trivedi, P. K. (2005). *Microeconometrics: Methods and Applications*. Cambridge University Press.
- Wooldridge, J. M. (2010). *Econometric Analysis of Cross Section and Panel Data*. MIT Press.
- DANE (2018). *Boletín técnico ENPH 2016-2017*. Bogotá.
- Hastie, T., Tibshirani, R., & Friedman, J. (2009). *The Elements of Statistical Learning*. Springer.
