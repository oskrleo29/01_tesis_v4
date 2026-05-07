# Estructura de los microdatos ENPH

La Encuesta Nacional de Presupuestos de los Hogares (ENPH) del DANE recopila información sobre los ingresos y los gastos de los hogares colombianos. Los microdatos se distribuyen en varios módulos relacionales que comparten llaves de unión.

> **Nota importante**: La ENPH 2016-2017 es la versión más reciente comparable. El DANE puede haber publicado actualizaciones; siempre verifica la versión exacta que la usuaria está usando, porque los nombres de variables pueden variar ligeramente entre rondas.

## Módulos típicos

| Módulo | Unidad | Contenido | Archivo típico |
|---|---|---|---|
| Vivienda y hogar | Hogar | Tipo de vivienda, servicios públicos, estrato, tenencia | `Datos de la vivienda y su hogar.csv` |
| Personas | Persona | Edad, sexo, parentesco, estado civil, educación, ocupación | `Características generales (Personas).csv` |
| Fuerza de trabajo | Persona | Ocupación, ingresos laborales, horas trabajadas | `Fuerza de trabajo.csv` |
| Otros ingresos | Persona/Hogar | Pensiones, transferencias, ingresos de capital | `Otros ingresos.csv` |
| Gastos diarios | Hogar | Alimentos, bebidas, gastos del día a día | `Gastos diarios de los hogares.csv` |
| Gastos personales | Persona | Vestuario, calzado, peluquería, etc. | `Gastos personales.csv` |
| Gastos del hogar | Hogar | Servicios públicos, vivienda, transporte, salud | `Gastos del hogar.csv` |
| Equipamiento | Hogar | Bienes durables, electrodomésticos | `Equipamiento del hogar.csv` |

## Llaves de unión

Las llaves más comunes son:

- `DIRECTORIO`: identifica la vivienda.
- `SECUENCIA_ENCUESTA` (a veces `SECUENCIA_P`): identifica el hogar dentro de la vivienda.
- `ORDEN`: identifica la persona dentro del hogar.

Para construir el dataset a nivel de hogar:
```python
hogar = vivienda.merge(
    personas.groupby(['DIRECTORIO', 'SECUENCIA_ENCUESTA']).agg(...).reset_index(),
    on=['DIRECTORIO', 'SECUENCIA_ENCUESTA'],
    how='left'
)
```

Verifica que el merge no genere duplicados y que el número de filas final sea consistente con el número de hogares de la encuesta.

## Variables clave

### Identificación y diseño muestral
- `DIRECTORIO`, `SECUENCIA_ENCUESTA`, `ORDEN` — llaves.
- `FEX_C` — factor de expansión calibrado del hogar (verifica el nombre exacto en el diccionario de la versión que la usuaria tenga; en algunas rondas es `FEX_HOGAR` o similar).
- `MES`, `PERIODO` — período de referencia.
- `REGION`, `DEPTO`, `CLASE` (urbano/rural).

### Características del hogar
- Estrato (`P3271` o similar — verificar).
- Tenencia de la vivienda.
- Tipo de vivienda.
- Servicios públicos disponibles.
- Número de cuartos.
- Cantidad de personas (`CANT_PERSONAS_HOGAR` o equivalente).

### Características del jefe de hogar (típicamente `P6051 == 1` o equivalente)
- Edad.
- Sexo.
- Nivel educativo (`P6210` o similar — años aprobados, último nivel alcanzado).
- Estado civil.
- Ocupación principal.
- Ingreso laboral.

### Gastos
La ENPH usa la clasificación COICOP (Clasificación del Consumo Individual por Finalidades). Las grandes categorías son:

| Código | Categoría |
|---|---|
| 01 | Alimentos y bebidas no alcohólicas |
| 02 | Bebidas alcohólicas, tabaco |
| 03 | Prendas de vestir y calzado |
| 04 | Alojamiento, agua, electricidad, gas y otros combustibles |
| 05 | Muebles, artículos para el hogar |
| 06 | Salud |
| 07 | Transporte |
| 08 | Comunicaciones |
| 09 | Recreación y cultura |
| 10 | Educación |
| 11 | Restaurantes y hoteles |
| 12 | Bienes y servicios diversos |

Cada gasto en los módulos tiene típicamente:
- `VALOR_PAGADO` o similar.
- `FRECUENCIA` (1=diario, 2=semanal, 3=mensual, 4=trimestral, 5=semestral, 6=anual — verificar codificación en el diccionario).

## Anualización del gasto

**Esta es la fuente más común de errores en análisis de la ENPH.** Cada categoría puede estar reportada en una frecuencia diferente. Para sumar entre categorías, anualiza primero:

```python
factor_anual = {
    1: 365,    # diario
    2: 52,     # semanal
    3: 12,     # mensual
    4: 4,      # trimestral
    5: 2,      # semestral
    6: 1,      # anual
}
df['gasto_anual'] = df['valor_pagado'] * df['frecuencia'].map(factor_anual)
```

Si necesitas el gasto mensual, divide entre 12. Para per cápita, divide entre el número de personas del hogar. Documenta siempre qué unidad estás reportando.

## Factores de expansión

Sin el factor de expansión, las estadísticas no son representativas de Colombia. La ENPH 2016-2017 expande a aproximadamente 14.5 millones de hogares.

Para un promedio ponderado:
```python
import numpy as np
def media_ponderada(x, w):
    return np.average(x, weights=w)

media_gasto = media_ponderada(df['gasto_anual'], df['fex_c'])
```

Para regresión con pesos en `statsmodels`:
```python
import statsmodels.api as sm
model = sm.WLS(y, X, weights=df['fex_c']).fit(cov_type='HC3')
```

> **Atención**: usar `cov_type='HC3'` o errores estándar robustos por cluster es importante para defender ante el jurado. La ENPH tiene un diseño muestral complejo y los errores OLS estándar subestiman la incertidumbre.

## Advertencias comunes

1. **Gastos con valor cero**: muchos hogares no consumen ciertas categorías (alcohol, educación si no hay niños, etc.). Esto genera gasto censurado y motiva modelos Tobit o Heckman si se modela cada categoría por separado.

2. **Outliers extremos**: hay hogares con gastos que parecen errores de captura. Antes de modelar, examina los percentiles 99 y 99.9 de cada categoría y decide cómo manejarlos.

3. **Encuestas reportadas a la unidad de la persona vs. del hogar**: los gastos personales se reportan por persona; los del hogar son colectivos. Para análisis a nivel de hogar, suma los personales por hogar antes de modelar.

4. **Inconsistencias entre módulos**: ocasionalmente un hogar aparece en un módulo pero no en otro. Decide a priori si vas a usar `inner` o `left` joins y reporta cuántos hogares quedan al final.

5. **Inflación**: si comparas con datos de otros años, deflactar usando el IPC del DANE. Una tesis no debe comparar pesos nominales entre años distintos sin deflactar.
