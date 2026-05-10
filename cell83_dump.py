import numpy as np
import pandas as pd

# ============================================================
# 🔹 ANÁLISIS COMPARATIVO: Con y Sin FEX_C
# ============================================================
def _fex_c_series(df, peso='FEX_C'):
    """Convierte FEX_C a float64 (maneja comas decimales)."""
    return pd.to_numeric(
        df[peso].astype(str).str.replace(',', '.', regex=False), errors='coerce'
    ).fillna(1.0)

def _mediana_w_arr(x_arr, w_arr):
    """Mediana ponderada (numpy arrays)."""
    x_ = np.array(x_arr, dtype=float)
    w_ = np.array(w_arr, dtype=float)
    mask = np.isfinite(x_) & np.isfinite(w_) & (w_ > 0)
    if mask.sum() == 0:
        return np.nan
    x_, w_ = x_[mask], w_[mask]
    idx = np.argsort(x_)
    cumw = w_[idx].cumsum() / w_[idx].sum()
    return float(x_[idx][(cumw >= 0.5).argmax()])

def _medianas_w_por_grupo(df, grupo_col, var_col, peso='FEX_C', orden=None):
    """Serie de medianas ponderadas por grupo."""
    fexc = _fex_c_series(df, peso)
    grupos = list(orden) if orden is not None else sorted(df[grupo_col].dropna().unique())
    result = {}
    for g in grupos:
        mask_g = df[grupo_col] == g
        x = pd.to_numeric(df.loc[mask_g, var_col], errors='coerce').values
        w = fexc[mask_g].values
        result[g] = _mediana_w_arr(x, w)
    return pd.Series(result)

def tabla_comparativa_fexc(df, grupo_col, var_col='ratio_gastos_2025', peso='FEX_C', orden=None):
    """
    Tabla comparativa SIN FEX_C vs CON FEX_C.
    Columnas: n_obs | n_expandido | mediana_sin_fex_% | mediana_con_fex_% | delta_pp
    """
    fexc = _fex_c_series(df, peso)
    grupos = list(orden) if orden is not None else sorted(df[grupo_col].dropna().unique())
    filas = []
    for g in grupos:
        mask_g = df[grupo_col] == g
        x = pd.to_numeric(df.loc[mask_g, var_col], errors='coerce')
        w = fexc[mask_g]
        m = x.notna() & w.notna()
        if m.sum() == 0:
            continue
        med_sin = float(x[m].median())
        med_con = _mediana_w_arr(x[m].values, w[m].values)
        filas.append({
            'grupo':               str(g),
            'n_obs':               int(m.sum()),
            'n_expandido':         int(w[m].sum()),
            'mediana_sin_fex_%':   round(med_sin * 100, 2),
            'mediana_con_fex_%':   round(med_con * 100, 2),
            'delta_pp':            round((med_con - med_sin) * 100, 2),
        })
    return pd.DataFrame(filas).set_index('grupo')

df_temp_=gastos_objetivo_final.copy()

df_temp_.columns

df_temp_['Sexo_'] = df_temp_['Sexo'].replace({1: 'Hombre', 2: 'Mujer'})
df_temp_['EstadoCivil_'] = df_temp_['Estado_Civil'].replace({'1':'No esta casado(a) y vive en pareja hace menos de dos años','2':'No esta casado(a) y vive en pareja hace dos años o más','3':'Esta viudo (a)','4':'Esta separado(a) o divorciado(a)', '5':'Esta soltero (a)','6':'Esta casado (a)'})
df_temp_['NivelAcademico_def'] = df_temp_['NivelAcademico_def'].replace({'3_ Bachiller': '3_Bachiller'})
df_temp_['ClaseVivienda_'] = df_temp_['Clase_Vivienda'].replace({1: 'Casa', 2: 'Apartamento', 3: 'Cuarto (s) en inquilinato', 4: 'Cuarto (s) en otro tipo de estructura', 5: 'Vivienda indígena', 6: 'Otra vivienda (carpa, vagón, embarcación, cueva, refugio natural, etc.)'})
df_temp_['TipoVivienda_'] = df_temp_['Tipo_Vivienda'].replace({1: 'Propia, totalmente pagada', 2: 'Propia, la están pagando', 3: 'En arriendo o subarriendo', 4: 'En usufructo', 5: 'Posesión sin titulo (Ocupante de hecho) ó propiedad colectiva', 6: 'Otra'})

df_temp_a = df_temp_[[
    'DIRECTORIO_x', 'Id_Person', 'Edad', 'Estrato', 'REGION', 'DOMINIO',
    'PERIODO', 'NivelAcademico_def', 'DESC_DIVISION', 'agrup_seccion',
    'Antigüedad_Actividad', 'ingreso_mensual_total', 'actividad_ppal',
    'Aportantes_Hogar', 'F01', 'F02', 'F03', 'F04',
    'F05', 'F06', 'F07', 'F08', 'F09', 'F10', 'F11', 'F12', 'GastoMes',
    'RatioGastos', 'ingreso_smmlv_', 'F01_2025', 'F02_2025', 'F03_2025',
    'F04_2025', 'F05_2025', 'F06_2025', 'F07_2025', 'F08_2025', 'F09_2025',
    'F10_2025', 'F11_2025', 'F12_2025', 'GASTOS_AL_2025',
    'INGRESOS_AL_2025', 'AÑO', 'SMMLV_2025_EQ', 'log_ingresos_2025',
    'log_gastos_2025', 'log_SMMLV_2025_EQ', 'log_ratio_ingreso',
    'Sexo_', 'EstadoCivil_', 'ClaseVivienda_','TipoVivienda_', 'FEX_C'
]].copy()

df_temp_a['Antigüedad_Actividad'] = (
    pd.to_numeric(df_temp_a['Antigüedad_Actividad'], errors='coerce')
    .astype('Int64')
)

df_temp_a['ratio_gastos_2025'] = (
    df_temp_a['GASTOS_AL_2025'] / df_temp_a['INGRESOS_AL_2025']
)

df_temp_a['INGRESOS_AL_2025'] = (
    df_temp_a['INGRESOS_AL_2025']
    .round(0)
    .astype('Int64')
)

df_temp_a['GASTOS_AL_2025'] = (
    df_temp_a['GASTOS_AL_2025']
    .round(0)
    .astype('Int64')
)

import pandas as pd
pd.options.display.float_format = lambda x: f"{x:.2f}".replace('.', ',')
tabla_educacion = (
    df_temp_a
    .groupby('NivelAcademico_def')
    .agg(
        n_obs=('INGRESOS_AL_2025', 'count'),
        ingreso_media=('INGRESOS_AL_2025', 'mean'),
        ingreso_mediana=('INGRESOS_AL_2025', 'median'),
        gasto_media=('GASTOS_AL_2025', 'mean'),
        gasto_mediana=('GASTOS_AL_2025', 'median'),
        ratio_medio=('ratio_gastos_2025', 'mean'),
        ratio_mediana=('ratio_gastos_2025', 'median')
    )
    .reset_index()
)


# Asegurar ratios como float (normalmente ya lo son)
cols_ratio = ['ratio_medio', 'ratio_mediana']
tabla_educacion[cols_ratio] = tabla_educacion[cols_ratio].astype(float)

df_temp_a.columns

df_temp_a['nivel_educ_agrupado'] = df_temp_a['NivelAcademico_def'].astype(str)

# Reglas de agrupación
df_temp_a.loc[
    df_temp_a['NivelAcademico_def'].isin([
        '1_Basica_Primaria',
        '7_Ninguno'
    ]),
    'nivel_educ_agrupado'
] = 'a_Bajo'

df_temp_a.loc[
    df_temp_a['NivelAcademico_def'].isin([
        '2_Basica_Secundaria',
        '3_Bachiller'
    ]),
    'nivel_educ_agrupado'
] = 'b_Medio_bajo'

df_temp_a.loc[
    df_temp_a['NivelAcademico_def'].isin([
        '4_tecnico_tecnólogo'
    ]),
    'nivel_educ_agrupado'
] = 'c_Medio_alto'

df_temp_a.loc[
    df_temp_a['NivelAcademico_def'].isin([
        '5_Universitaria',
        '6_Postgrado'
    ]),
    'nivel_educ_agrupado'
] = 'd_Alto'

# Excluir "No informa"
df_temp_a = df_temp_a[df_temp_a['NivelAcademico_def'] != '8_No_Informa']

tabla_educ_agr = (
    df_temp_a
    .groupby('nivel_educ_agrupado')
    .agg(
        n_obs=('INGRESOS_AL_2025', 'count'),
        ingreso_mediana=('INGRESOS_AL_2025', 'median'),
        gasto_mediana=('GASTOS_AL_2025', 'median'),
        ratio_mediana=('ratio_gastos_2025', 'median')
    )
    .reset_index()
)

tabla_educ_agr

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --------------------------------------------------
# Definir orden alfabético de los niveles
# --------------------------------------------------
orden_alfabetico = sorted(df_temp_a['NivelAcademico_def'].dropna().unique())

# Calcular medianas (sin FEX_C) y ponderadas (con FEX_C)
medianas_gasto = (
    df_temp_a
    .groupby('NivelAcademico_def')['ratio_gastos_2025']
    .median()
    .reindex(orden_alfabetico)
)
medianas_gasto_w = _medianas_w_por_grupo(
    df_temp_a, 'NivelAcademico_def', 'ratio_gastos_2025', orden=orden_alfabetico
)

sns.set_style("whitegrid")

plt.figure(figsize=(12, 7))

ax = sns.boxplot(
    x='NivelAcademico_def',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    order=orden_alfabetico,   # 🔹 orden alfabético
    ax=plt.gca()
)

# Eje Y en porcentaje con 2 decimales
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda y, _: f'{y*100:.2f}%')
)

# Anotar medianas (cerca de la línea)
for i, nivel in enumerate(orden_alfabetico):
    valor   = medianas_gasto[nivel]
    valor_w = medianas_gasto_w.get(nivel, np.nan)
    ax.text(i, valor + (valor * 0.005),
            f'\u25cb {valor*100:.2f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='white')
    if not np.isnan(valor_w):
        ax.text(i, valor_w - abs(valor_w) * 0.05,
                f'\u25c6 {valor_w*100:.2f}%',
                ha='center', va='top', fontsize=11, fontweight='bold', color='orange')

from matplotlib.patches import Patch as _Patch
ax.legend(handles=[
    _Patch(facecolor='white', edgecolor='gray', label='\u25cb Sin FEX_C (muestra)'),
    _Patch(facecolor='orange', label='\u25c6 Con FEX_C (pob. estimada)')],
    loc='upper right', fontsize=9)

plt.title('Distribución del ratio gasto personal por Nivel Académico\n'
          '(\u25cb mediana muestral  |  \u25c6 mediana ponderada FEX_C)', fontsize=13)
plt.xlabel('Nivel Académico', fontsize=12)
plt.ylabel('Gasto / Ingreso (%)', fontsize=12)

plt.xticks(rotation=0, ha='center', fontsize=11)
plt.yticks(fontsize=11)

plt.tight_layout()
plt.show()

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --------------------------------------------------
# Definir orden alfabético de la actividad principal
# --------------------------------------------------
orden_alfabetico = sorted(df_temp_a['actividad_ppal'].dropna().unique())

# Calcular medianas (sin FEX_C) y ponderadas (con FEX_C)
medianas_gasto = (
    df_temp_a
    .groupby('actividad_ppal')['ratio_gastos_2025']
    .median()
    .reindex(orden_alfabetico)
)
medianas_gasto_w = _medianas_w_por_grupo(
    df_temp_a, 'actividad_ppal', 'ratio_gastos_2025', orden=orden_alfabetico
)

sns.set_style("whitegrid")

plt.figure(figsize=(12, 7))

ax = sns.boxplot(
    x='actividad_ppal',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    order=orden_alfabetico,   # 🔹 orden alfabético
    ax=plt.gca()
)

# Eje Y en porcentaje con 2 decimales
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda y, _: f'{y*100:.2f}%')
)

# Anotar medianas (cerca de la línea)
for i, actividad in enumerate(orden_alfabetico):
    valor   = medianas_gasto[actividad]
    valor_w = medianas_gasto_w.get(actividad, np.nan)
    ax.text(i, valor + (valor * 0.005),
            f'\u25cb {valor*100:.2f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='white')
    if not np.isnan(valor_w):
        ax.text(i, valor_w - abs(valor_w) * 0.05,
                f'\u25c6 {valor_w*100:.2f}%',
                ha='center', va='top', fontsize=11, fontweight='bold', color='orange')

ax.legend(handles=[
    _Patch(facecolor='white', edgecolor='gray', label='\u25cb Sin FEX_C (muestra)'),
    _Patch(facecolor='orange', label='\u25c6 Con FEX_C (pob. estimada)')],
    loc='upper right', fontsize=9)
plt.title('Distribución del ratio gasto personal por Actividad Principal\n'
          '(\u25cb mediana muestral  |  \u25c6 mediana ponderada FEX_C)', fontsize=13)
plt.xlabel('Actividad Principal', fontsize=12)
plt.ylabel('Gasto / Ingreso (%)', fontsize=12)

plt.xticks(rotation=0, ha='center', fontsize=11)
plt.yticks(fontsize=11)

plt.tight_layout()
plt.show()

import plotly.express as px

fig = px.scatter(
    df_temp_a,
    x='log_ingresos_2025',
    y='log_gastos_2025',
    color='actividad_ppal', # Usa 'color' para diferenciar por actividad principal
    opacity=0.3,
    title='Relación ingreso–gasto por actividad principal (Interactivo)',

    labels={
        'log_ingresos_2025': 'log(Ingreso 2025)',
        'log_gastos_2025': 'log(Gasto 2025)',
        'actividad_ppal': 'Actividad Principal'
    }
)

fig.update_layout(showlegend=True) # Asegura que la leyenda sea visible para la interactividad
fig.show()

import pandas as pd
import numpy as np

df_temp_a['Antigüedad_Actividad'] = pd.to_numeric(
    df_temp_a['Antigüedad_Actividad'],
    errors='coerce'
)

# 1️⃣ Convertir Antigüedad_Actividad de object a numérico
df_temp_a['Antigüedad_Actividad'] = pd.to_numeric(
    df_temp_a['Antigüedad_Actividad'],
    errors='coerce'
)

# 2️⃣ Definir condiciones (boolean numpy, sin NA)
condiciones = [
    df_temp_a['Antigüedad_Actividad'].isin([998, 999]).fillna(False).to_numpy(),
    df_temp_a['Antigüedad_Actividad'].between(0, 5).fillna(False).to_numpy(),
    df_temp_a['Antigüedad_Actividad'].between(6, 12).fillna(False).to_numpy(),
    df_temp_a['Antigüedad_Actividad'].between(13, 36).fillna(False).to_numpy(),
    df_temp_a['Antigüedad_Actividad'].between(37, 72).fillna(False).to_numpy(),
    df_temp_a['Antigüedad_Actividad'].between(73, 120).fillna(False).to_numpy(),
    (df_temp_a['Antigüedad_Actividad'] >= 121).fillna(False).to_numpy()
]

# 3️⃣ Valores (labels consistentes)
valores = [
    'g_desconoce',
    'a_inserción_laboral_0_5',
    'b_adaptacion_al_empleo_6_12',
    'c_ingreso_predecible_13_36',
    'd_trayectoria_estable_37_72',
    'e_alta_estabilidad_73_120',
    'f_trayectoria_excepcional_121_mas'
]

# 4️⃣ Crear variable agrupada
df_temp_a['antiguedad_agrup'] = np.select(
    condiciones,
    valores,
    default=None
)

# 5️⃣ Reemplazar NA restantes por 'g_desconoce'
df_temp_a['antiguedad_agrup'] = df_temp_a['antiguedad_agrup'].fillna('g_desconoce')

# 6️⃣ Convertir a categórica ordenada
orden = [
    'a_inserción_laboral_0_5',
    'b_adaptacion_al_empleo_6_12',
    'c_ingreso_predecible_13_36',
    'd_trayectoria_estable_37_72',
    'e_alta_estabilidad_73_120',
    'f_trayectoria_excepcional_121_mas',
    'g_desconoce'
]

df_temp_a['antiguedad_agrup'] = pd.Categorical(
    df_temp_a['antiguedad_agrup'],
    categories=orden,
    ordered=True
)

(
    df_temp_a
    .loc[df_temp_a['antiguedad_agrup'] == 'g_desconoce']
    .groupby('actividad_ppal')
    .agg(n_obs=('actividad_ppal', 'count'))
    .sort_values('n_obs', ascending=False)
)

import seaborn as sns
import matplotlib.pyplot as plt

# Calcular medianas
medianas_gasto = (
    df_temp_a
    .groupby('antiguedad_agrup')['GASTOS_AL_2025']
    .median()
)

sns.set_style("whitegrid")

plt.figure(figsize=(12, 7))

ax = sns.boxplot(
    x='antiguedad_agrup',
    y='GASTOS_AL_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    ax=plt.gca()
)

# Anotar las medianas
for i, antiguedad in enumerate(medianas_gasto.index):
    valor = medianas_gasto[antiguedad]
    ax.text(
        i, valor + (df_temp_a['GASTOS_AL_2025'].max() * 0.01), # Ajustar la posición vertical
        f'{valor:,.0f}'.replace(',', 'X').replace('.', ',').replace('X', '.'), # Formato de miles
        ha='center',
        va='bottom',
        fontsize=10,
        color='white'
    )

plt.title('Distribución del gasto personal por antigüedad en la actividad', fontsize=16)
plt.xlabel('Antigüedad en la actividad', fontsize=12)
plt.ylabel('Gasto personal (pesos)', fontsize=12)
plt.xticks(rotation=45, ha='right', fontsize=10)
plt.yticks(fontsize=10)
plt.tight_layout()
plt.show()

import pandas as pd

# Define age bins and labels
bins = [18, 25, 35, 45, 55, 65, 100]
labels = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']

# Create 'Grupo_Edad' column
df_temp_a['Grupo_Edad'] = pd.cut(df_temp_a['Edad'], bins=bins, labels=labels, right=False)

# Display value counts of the new column
print("Distribución de individuos por grupo de edad:")
print(df_temp_a['Grupo_Edad'].value_counts().sort_index())

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# Calcular medianas (sin FEX_C) y ponderadas (con FEX_C)
medianas_gasto = (
    df_temp_a
    .groupby('Grupo_Edad')['ratio_gastos_2025']
    .median()
)
medianas_gasto_w = _medianas_w_por_grupo(
    df_temp_a, 'Grupo_Edad', 'ratio_gastos_2025',
    orden=medianas_gasto.index.tolist()
)

sns.set_style("whitegrid")

plt.figure(figsize=(12, 7))

ax = sns.boxplot(
    x='Grupo_Edad',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    ax=plt.gca()
)

# Eje Y en porcentaje con 2 decimales
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda y, _: f'{y*100:.2f}%')
)

# Anotar medianas sin FEX_C (blanco) y con FEX_C (naranja)
for i, grupo_edad in enumerate(medianas_gasto.index):
    valor   = medianas_gasto[grupo_edad]
    valor_w = medianas_gasto_w.get(grupo_edad, np.nan)
    ax.text(i, valor + (df_temp_a['ratio_gastos_2025'].max() * 0.01),
            f'\u25cb {valor*100:.2f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='white')
    if not np.isnan(valor_w):
        ax.text(i, valor_w - (df_temp_a['ratio_gastos_2025'].max() * 0.02),
                f'\u25c6 {valor_w*100:.2f}%',
                ha='center', va='top', fontsize=11, fontweight='bold', color='orange')

ax.legend(handles=[
    _Patch(facecolor='white', edgecolor='gray', label='\u25cb Sin FEX_C (muestra)'),
    _Patch(facecolor='orange', label='\u25c6 Con FEX_C (pob. estimada)')],
    loc='upper right', fontsize=9)
plt.title('Distribución del ratio gasto personal por Edad\n'
          '(\u25cb mediana muestral  |  \u25c6 mediana ponderada FEX_C)', fontsize=13)
plt.xlabel('Rango edad', fontsize=12)
plt.ylabel('Gasto / Ingreso (%)', fontsize=12)

plt.xticks(rotation=0, ha='center', fontsize=11)
plt.yticks(fontsize=11)

plt.tight_layout()
plt.show()

import seaborn as sns
import matplotlib

print("seaborn:", sns.__version__)
print("matplotlib:", matplotlib.__version__)

df_temp_a.columns

df_temp_a['EstadoCivil_'].unique()

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --------------------------------------------------
# Homologación de etiquetas (más cortas)
# --------------------------------------------------
estado_civil_map = {
    'No esta casado(a) y vive en pareja hace menos de dos años': 'Pareja < 2 años',
    'No esta casado(a) y vive en pareja hace dos años o más': 'Pareja ≥ 2 años',
    'Esta viudo (a)': 'Viudo(a)',
    'Esta separado(a) o divorciado(a)': 'Separado/Divorciado',
    'Esta soltero (a)': 'Soltero(a)',
    'Esta casado (a)': 'Casado(a)'
}

# Crear variable homologada
df_temp_a['EstadoCivil_hom'] = df_temp_a['EstadoCivil_'].map(estado_civil_map)

# Orden explícito según tu codificación a–f
estado_civil_labels = [
    'Pareja < 2 años',
    'Pareja ≥ 2 años',
    'Viudo(a)',
    'Separado/Divorciado',
    'Soltero(a)',
    'Casado(a)'
]

# Calcular medianas (sin FEX_C) y ponderadas (con FEX_C)
medianas_gasto = (
    df_temp_a
    .groupby('EstadoCivil_hom')['ratio_gastos_2025']
    .median()
    .reindex(estado_civil_labels)
)
medianas_gasto_w = _medianas_w_por_grupo(
    df_temp_a, 'EstadoCivil_hom', 'ratio_gastos_2025', orden=estado_civil_labels
)

sns.set_style("whitegrid")

plt.figure(figsize=(13, 7))

ax = sns.boxplot(
    x='EstadoCivil_hom',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    order=estado_civil_labels,
    ax=plt.gca()
)

# Eje Y en porcentaje con 2 decimales
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda y, _: f'{y*100:.2f}%')
)

# Anotar medianas sin FEX_C (blanco) y con FEX_C (naranja)
for i, estado in enumerate(estado_civil_labels):
    valor   = medianas_gasto[estado]
    valor_w = medianas_gasto_w.get(estado, np.nan)
    ax.text(i, valor + (valor * 0.005),
            f'\u25cb {valor*100:.2f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='white')
    if not np.isnan(valor_w):
        ax.text(i, valor_w - abs(valor_w) * 0.05,
                f'\u25c6 {valor_w*100:.2f}%',
                ha='center', va='top', fontsize=11, fontweight='bold', color='orange')

ax.legend(handles=[
    _Patch(facecolor='white', edgecolor='gray', label='\u25cb Sin FEX_C (muestra)'),
    _Patch(facecolor='orange', label='\u25c6 Con FEX_C (pob. estimada)')],
    loc='upper right', fontsize=9)
plt.title('Distribución del ratio gasto personal por Estado Civil\n'
          '(\u25cb mediana muestral  |  \u25c6 mediana ponderada FEX_C)', fontsize=13)
plt.xlabel('Estado Civil', fontsize=12)
plt.ylabel('Gasto / Ingreso (%)', fontsize=12)

plt.xticks(rotation=0, ha='center', fontsize=11)
plt.yticks(fontsize=11)

plt.tight_layout()
plt.show()

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --------------------------------------------------
# Agrupación y homologación de Aportantes_Hogar
# --------------------------------------------------
bins_aportantes = [1, 2, 3, 5, df_temp_a['Aportantes_Hogar'].max() + 1]
labels_aportantes = [
    'Hogares unipersonales',  # 1 aportante
    'Hogares pequeños',       # 2 aportantes
    'Hogares medianos',       # 3-4 aportantes
    'Hogares grandes'         # 5 o más aportantes
]

df_temp_a['Grupo_Aportantes'] = pd.cut(
    df_temp_a['Aportantes_Hogar'],
    bins=bins_aportantes,
    labels=labels_aportantes,
    right=False,
    include_lowest=True
)

# Calcular medianas (sin FEX_C) y ponderadas (con FEX_C)
medianas_gasto = (
    df_temp_a
    .groupby('Grupo_Aportantes')['ratio_gastos_2025']
    .median()
    .reindex(labels_aportantes)
)
medianas_gasto_w = _medianas_w_por_grupo(
    df_temp_a, 'Grupo_Aportantes', 'ratio_gastos_2025', orden=labels_aportantes
)

sns.set_style("whitegrid")

plt.figure(figsize=(12, 7))

ax = sns.boxplot(
    x='Grupo_Aportantes',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    order=labels_aportantes,   # 🔹 orden conceptual
    ax=plt.gca()
)

# Eje Y en porcentaje con 2 decimales
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda y, _: f'{y*100:.2f}%')
)

# Anotar medianas sin FEX_C (blanco) y con FEX_C (naranja)
for i, grupo in enumerate(labels_aportantes):
    valor   = medianas_gasto[grupo]
    valor_w = medianas_gasto_w.get(grupo, np.nan)
    ax.text(i, valor + (valor * 0.005),
            f'\u25cb {valor*100:.2f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='white')
    if not np.isnan(valor_w):
        ax.text(i, valor_w - abs(valor_w) * 0.05,
                f'\u25c6 {valor_w*100:.2f}%',
                ha='center', va='top', fontsize=11, fontweight='bold', color='orange')

ax.legend(handles=[
    _Patch(facecolor='white', edgecolor='gray', label='\u25cb Sin FEX_C (muestra)'),
    _Patch(facecolor='orange', label='\u25c6 Con FEX_C (pob. estimada)')],
    loc='upper right', fontsize=9)
plt.title('Distribución del ratio gasto personal por Aportantes del Hogar\n'
          '(\u25cb mediana muestral  |  \u25c6 mediana ponderada FEX_C)', fontsize=13)
plt.xlabel('Tipo de hogar según aportantes', fontsize=12)
plt.ylabel('Gasto / Ingreso (%)', fontsize=12)

plt.xticks(rotation=0, ha='center', fontsize=11)
plt.yticks(fontsize=11)

plt.tight_layout()
plt.show()

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --------------------------------------------------
# Reasignación directa de Estrato (según tu lógica)
# --------------------------------------------------
def reasignar_estrato_directo(estrato_valor):
    if pd.isna(estrato_valor) or str(estrato_valor).strip() == '':
        return 2  # Asignar 2 a valores vacíos
    elif estrato_valor == 0 or str(estrato_valor) == '0' or estrato_valor == 9 or str(estrato_valor) == '9':
        return 1  # Asignar 1 a 0 y 9
    else:
        try:
            return int(estrato_valor)
        except ValueError:
            return estrato_valor

# Aplicar reasignación
df_temp_a['Estrato'] = df_temp_a['Estrato'].apply(reasignar_estrato_directo)

# --------------------------------------------------
# Definir orden de estratos (ascendente)
# --------------------------------------------------
estrato_labels = sorted(df_temp_a['Estrato'].dropna().unique())

# Calcular medianas (sin FEX_C) y ponderadas (con FEX_C)
medianas_gasto = (
    df_temp_a
    .groupby('Estrato')['ratio_gastos_2025']
    .median()
    .reindex(estrato_labels)
)
medianas_gasto_w = _medianas_w_por_grupo(
    df_temp_a, 'Estrato', 'ratio_gastos_2025', orden=estrato_labels
)

sns.set_style("whitegrid")

plt.figure(figsize=(10, 7))

ax = sns.boxplot(
    x='Estrato',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    order=estrato_labels,
    ax=plt.gca()
)

# Eje Y en porcentaje con 2 decimales
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda y, _: f'{y*100:.2f}%')
)

# Anotar medianas sin FEX_C (blanco) y con FEX_C (naranja)
for i, estrato in enumerate(estrato_labels):
    valor   = medianas_gasto[estrato]
    valor_w = medianas_gasto_w.get(estrato, np.nan)
    ax.text(i, valor + (valor * 0.005),
            f'\u25cb {valor*100:.2f}%',
            ha='center', va='bottom', fontsize=11, fontweight='bold', color='white')
    if not np.isnan(valor_w):
        ax.text(i, valor_w - abs(valor_w) * 0.05,
                f'\u25c6 {valor_w*100:.2f}%',
                ha='center', va='top', fontsize=11, fontweight='bold', color='orange')

ax.legend(handles=[
    _Patch(facecolor='white', edgecolor='gray', label='\u25cb Sin FEX_C (muestra)'),
    _Patch(facecolor='orange', label='\u25c6 Con FEX_C (pob. estimada)')],
    loc='upper right', fontsize=9)
plt.title('Distribución del ratio gasto personal por Estrato\n'
          '(\u25cb mediana muestral  |  \u25c6 mediana ponderada FEX_C)', fontsize=13)
plt.xlabel('Estrato socioeconómico', fontsize=12)
plt.ylabel('Gasto / Ingreso (%)', fontsize=12)

plt.xticks(rotation=0, ha='center', fontsize=11)
plt.yticks(fontsize=11)

plt.tight_layout()
plt.show()

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Define labels for Estrato_Reasignado to ensure consistent order
estrato_reasignado_labels = sorted(df_temp_a['Estrato'].unique()) # Sort for logical order

# Apply Seaborn style as requested
sns.set_style("whitegrid")

plt.figure(figsize=(10, 6)) # Adjust figure size for Estrato

# Use Seaborn for the boxplot with specified palette and hidden outliers
ax = sns.boxplot(
    x='Estrato',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis', # Apply specified palette
    showfliers=False,  # Hide outliers as requested
    order=estrato_reasignado_labels # Ensure correct order of categories
)

# Calculate medians (explicitly setting observed=False for categorical groupby to suppress FutureWarning)
medians = df_temp_a.groupby('Estrato', observed=False)['ratio_gastos_2025'].median()

# Loop through each box and add median annotation with specified formatting
for i, group in enumerate(estrato_reasignado_labels): # Use 'estrato_reasignado_labels' to iterate through ordered groups
    if group in medians.index: # Check if median exists for the group
        median_val = medians[group]
        ax.text(
            i, median_val + 0.01, # Place just above the median line
            f'{median_val:.2f}',
            ha='center',
            va='bottom',
            fontsize=12,
            color='white',
            weight='semibold'
        )

plt.title('Distribución de ratio_gastos_2025 por Estrato (Sin Outliers y con Mediana)', fontsize=16) # Title with specific fontsize
plt.suptitle('') # Suppress automatic suptitle
plt.xlabel('Estrato', fontsize=12) # X-label with specific fontsize
plt.ylabel('ratio_gastos_2025', fontsize=12) # Y-label with specific fontsize

plt.xticks(rotation=45, ha='right', fontsize=10) # Rotate x-tick labels and set fontsize
plt.yticks(fontsize=10) # Set y-tick fontsize
plt.grid(axis='y', linestyle='--', alpha=0.7) # Keep grid
plt.tight_layout() # Adjust layout
plt.show()

# 1. Dominios metropolitanos principales
dominio_metro_principal = [
    'BOGOTÁ',
    'MEDELLÍN Y A.M.',
    'CALI',
    'BARRANQUILLA'
]

# 2. Dominios metropolitanos regionales
dominio_metro_regional = [
    'BUCARAMANGA Y A.M.',
    'PEREIRA Y A.M.',
    'MANIZALEZ Y A.M.',
    'CÚCUTA Y A.M.'
]

# 3. Ciudades intermedias
dominio_intermedias = [
    'CARTAGENA', 'SANTA MARTA', 'IBAGUÉ', 'NEIVA',
    'VILLAVICENCIO', 'MONTERÍA', 'VALLEDUPAR',
    'SINCELEJO', 'TUNJA'
]

# 4. Periferia urbana / satélites
dominio_periferia = [
    'SOLEDAD', 'YUMBO', 'RIONEGRO', 'BARRANCABERMEJA'
]

def agrupar_dominio(dominio):
    if dominio in dominio_metro_principal:
        return 'a_Metro_principal'
    elif dominio in dominio_metro_regional:
        return 'b_Metro_regional'
    elif dominio in dominio_intermedias:
        return 'c_Ciudad_intermedia'
    elif dominio in dominio_periferia:
        return 'd_Periferia_urbana'
    else:
        return 'e_Resto'

df_temp_a['dominio_agrup'] = df_temp_a['DOMINIO'].apply(agrupar_dominio)

df_temp_a['dominio_agrup'].value_counts(normalize=True).round(3)

import numpy as np

df_temp_a['tipo_vivienda_agrup'] = np.select(
    [
        df_temp_a['TipoVivienda_'] == 'Propia, totalmente pagada',
        df_temp_a['TipoVivienda_'] == 'Propia, la están pagando',
        df_temp_a['TipoVivienda_'] == 'En arriendo o subarriendo',
        df_temp_a['TipoVivienda_'].isin([
            'En usufructo',
            'Posesión sin titulo (Ocupante de hecho) ó prop...',
            'Otra'
        ])
    ],
    [
        'propia_pagada',
        'propia_en_pago',
        'arriendo',
        'tenencia_no_formal'
    ],
    default='otros'
)

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# --------------------------------------------------
# Definir orden lógico de tipo de vivienda agrupado
# --------------------------------------------------
tipo_vivienda_labels = [
    'tenencia_no_formal',
    'arriendo',
    'propia_pagada',
    'propia_en_pago'
]

# Calcular medianas (sin FEX_C) y ponderadas (con FEX_C)
medianas_gasto = (
    df_temp_a
    .groupby('tipo_vivienda_agrup')['ratio_gastos_2025']
    .median()
    .reindex(tipo_vivienda_labels)
)
medianas_gasto_w = _medianas_w_por_grupo(
    df_temp_a, 'tipo_vivienda_agrup', 'ratio_gastos_2025', orden=tipo_vivienda_labels
)

sns.set_style("whitegrid")

plt.figure(figsize=(10, 7))

ax = sns.boxplot(
    x='tipo_vivienda_agrup',
    y='ratio_gastos_2025',
    data=df_temp_a,
    palette='viridis',
    showfliers=False,
    order=tipo_vivienda_labels,
    ax=plt.gca()
)

# --------------------------------------------------
# Eje Y en porcentaje con 2 decimales
# --------------------------------------------------
ax.yaxis.set_major_formatter(
    FuncFormatter(lambda y, _: f'{y*100:.2f}%')
)

# Anotar medianas sin FEX_C (blanco) y con FEX_C (naranja)
for i, grupo in enumerate(tipo_vivienda_labels):
    valor   = medianas_gasto[grupo]
    valor_w = medianas_gasto_w.get(grupo, np.nan)
    if pd.notna(valor):
        ax.text(i, valor + (valor * 0.005),
                f'\u25cb {valor*100:.2f}%',
                ha='center', va='bottom', fontsize=11, fontweight='bold', color='white')
    if not np.isnan(valor_w):
        ax.text(i, valor_w - abs(valor_w) * 0.05,
                f'\u25c6 {valor_w*100:.2f}%',
                ha='center', va='top', fontsize=11, fontweight='bold', color='orange')

# --------------------------------------------------
# Títulos y etiquetas
# --------------------------------------------------
ax.legend(handles=[
    _Patch(facecolor='white', edgecolor='gray', label='\u25cb Sin FEX_C (muestra)'),
    _Patch(facecolor='orange', label='\u25c6 Con FEX_C (pob. estimada)')],
    loc='upper right', fontsize=9)
plt.title('Distribución del ratio gasto personal según tipo de tenencia de vivienda\n'
          '(\u25cb mediana muestral  |  \u25c6 mediana ponderada FEX_C)', fontsize=13)
plt.xlabel('Tipo de tenencia de la vivienda', fontsize=12)
plt.ylabel('Gasto / Ingreso (%)', fontsize=12)

plt.xticks(rotation=30, ha='right', fontsize=11)
plt.yticks(fontsize=11)

plt.tight_layout()
plt.show()


def estadisticos_ponderados(df, var, peso='FEX_C'):
    """Calcula media y mediana ponderadas."""
    w = pd.to_numeric(
        df[peso].astype(str).str.replace(',', '.', regex=False),
        errors='coerce'
    ).fillna(1.0)
    
    x = pd.to_numeric(df[var], errors='coerce')
    mask = x.notna() & w.notna()
    x, w = x[mask].values, w[mask].values
    
    # Media ponderada
    media_w = np.average(x, weights=w)
    
    # Mediana ponderada
    idx = np.argsort(x)
    x_s, w_s = x[idx], w[idx]
    cumw = w_s.cumsum() / w_s.sum()
    mediana_w = x_s[(cumw >= 0.5).argmax()]
    
    return round(media_w, 0), round(mediana_w, 0)


# ============================================================
# 📊 IMPACTO DEL FACTOR DE EXPANSIÓN FEX_C — RESUMEN GENERAL
# Muestra: medianas sin ponderar  |  Población: medianas con FEX_C
# ============================================================
import matplotlib.pyplot as plt
from matplotlib.patches import Patch as _Patch

_grupos_config = [
    ('nivel_educ_agrupado', ['a_Bajo','b_Medio_bajo','c_Medio_alto','d_Alto'],       'Nivel Educativo'),
    ('actividad_ppal',      None,                                                    'Actividad Principal'),
    ('Grupo_Edad',          ['18-24','25-34','35-44','45-54','55-64','65+'],          'Grupo de Edad'),
    ('EstadoCivil_hom',     ['Pareja < 2 años','Pareja \u2265 2 años','Viudo(a)',
                              'Separado/Divorciado','Soltero(a)','Casado(a)'],       'Estado Civil'),
    ('Grupo_Aportantes',    ['Hogares unipersonales','Hogares peque\u00f1os',
                              'Hogares medianos','Hogares grandes'],                 'Aportantes Hogar'),
    ('Estrato',             None,                                                    'Estrato'),
    ('tipo_vivienda_agrup', ['tenencia_no_formal','arriendo',
                              'propia_pagada','propia_en_pago'],                     'Tipo Vivienda'),
]

print("\n" + "="*70)
print("IMPACTO DEL FACTOR DE EXPANSIÓN FEX_C  —  variable: ratio_gastos_2025")
print("  ○ Sin FEX_C = mediana muestral simple")
print("  ◆ Con FEX_C = mediana ponderada por factor de expansión")
print("="*70)

for _gc, _ord, _titulo in _grupos_config:
    if _gc not in df_temp_a.columns:
        continue
    _t = tabla_comparativa_fexc(df_temp_a, _gc, orden=_ord)
    print(f"\n{'—'*50}  {_titulo}")
    with pd.option_context('display.float_format', '{:.2f}'.format,
                           'display.max_columns', 20, 'display.width', 130):
        print(_t.to_string())

# — Figura: delta_pp por variable —
_n_rows = sum(1 for gc, _, _ in _grupos_config if gc in df_temp_a.columns)
_fig, _axes = plt.subplots(_n_rows, 1, figsize=(12, 4 * _n_rows))
if _n_rows == 1:
    _axes = [_axes]

_fig.suptitle(
    'Δ Mediana ratio gasto/ingreso: Con FEX_C − Sin FEX_C  (puntos porcentuales)\n'
    'Verde ▲ = FEX_C sube la mediana  |  Rojo ▼ = FEX_C baja la mediana',
    fontsize=12, y=1.01
)

_ax_idx = 0
for _gc, _ord, _titulo in _grupos_config:
    if _gc not in df_temp_a.columns:
        continue
    _ax = _axes[_ax_idx]
    _ax_idx += 1
    _t = tabla_comparativa_fexc(df_temp_a, _gc, orden=_ord)
    _colores = ['#e74c3c' if v < 0 else '#2ecc71' for v in _t['delta_pp']]
    _xlabels = _t.index.astype(str).tolist()
    _ax.bar(range(len(_xlabels)), _t['delta_pp'], color=_colores, edgecolor='gray', linewidth=0.5)
    _ax.set_xticks(range(len(_xlabels)))
    _ax.set_xticklabels(_xlabels, rotation=30, ha='right', fontsize=9)
    _ax.axhline(0, color='black', linewidth=0.8)
    _ax.set_title(_titulo, fontsize=11, fontweight='bold')
    _ax.set_ylabel('\u0394 mediana (pp)', fontsize=9)
    for _j, _dv in enumerate(_t['delta_pp']):
        _ax.text(_j, _dv + (0.02 if _dv >= 0 else -0.04),
                 f'{_dv:+.2f}pp', ha='center',
                 va='bottom' if _dv >= 0 else 'top', fontsize=8)

plt.tight_layout()
plt.savefig(r'C:\Users\geros\OneDrive\Desktop\01_tesis_v4\impacto_fexc_resumen.png',
            dpi=150, bbox_inches='tight')
plt.show()
print("\nFigura guardada como 'impacto_fexc_resumen.png'")
